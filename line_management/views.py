# /line_management/views.py
import hmac
import hashlib
import base64
import logging
import requests
from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FollowEvent, StickerMessage
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import LineFriend, UserAction, LineSettings, Referral
from score_management.models import ScoreSetting, StatusSetting, Tag
from .forms import LineSettingsForm, LineFriendForm
import json
from django.http import JsonResponse
from django.views import View
from django.utils.dateformat import format
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
from django.db.models import Q
from django.utils import timezone
from datetime import datetime

# ロギングの設定
logger = logging.getLogger(__name__)

# LINE設定を取得する関数
def get_line_settings():
    settings = LineSettings.objects.first()
    if not settings:
        raise ValueError("LINE settings not found. Please configure your LINE settings.")
    return settings

# LINE設定を取得
line_settings = get_line_settings()
line_bot_api = LineBotApi(line_settings.line_access_token)
handler = WebhookHandler(line_settings.line_channel_secret)

def handle_message(event):
    text = event.message.text
    line_user_id = event.source.user_id
    reply_token = event.reply_token

    try:
        profile = line_bot_api.get_profile(line_user_id)
        display_name = profile.display_name
        picture_url = profile.picture_url

        line_friend, created = LineFriend.objects.get_or_create(
            line_user_id=line_user_id,
            defaults={
                'display_name': display_name,
                'picture_url': picture_url,
            }
        )

        if not created:
            line_friend.display_name = display_name
            line_friend.picture_url = picture_url
            line_friend.save()

        score_settings = ScoreSetting.objects.filter(action_type='speech', trigger=text)
        
        # スコア設定が存在する場合、保存
        if score_settings.exists():
            score_setting = score_settings.first()
            
            # ユーザーアクションを保存
            UserAction.objects.create(
                line_friend=line_friend,
                action_type='speech',
                score=score_setting.score,
                score_setting=score_setting,
                memo=score_setting.memo
            )
            
            # スコアの合計を取得する
            total_score = UserAction.objects.filter(line_friend=line_friend).aggregate(total=models.Sum('score'))['total'] or 0
            
            # タグが設定されている場合、タグを付与
            if score_setting.tag:
                line_friend.tags.add(score_setting.tag)

            # 応答メッセージを送信
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(text=f'{display_name}さん、あなたの発言 "{text}" に対して{score_setting.score}点が加算されました！')
            )
        else:
            # 一致するスコア設定がない場合、通常の応答
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(text=f'{display_name}さん、あなたの発言 "{text}" に対して点数は加算されませんでした！')
            )
    except LineBotApiError as e:
        # プロフィール情報の取得に失敗した場合の処理
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text="プロフィール情報の取得に失敗しました。")
        )
        logger.error("LineBotApiError: %s", str(e))

@login_required
def user_info_view(request):
    actions_list = UserAction.objects.select_related('line_friend').order_by('-date')
    
    paginator = Paginator(actions_list, 10)
    page_number = request.GET.get('page')
    actions = paginator.get_page(page_number)
    
    return render(request, 'line_management/user_info.html', {
        'actions': actions,
    })
    

def get_user_details(request, user_id):
    try:
        line_friend = LineFriend.objects.get(id=user_id)
        user_score = UserAction.objects.filter(line_friend=line_friend).first()

        data = {
            'line_user_id': line_friend.line_user_id,
            'display_name': line_friend.display_name,
            'picture_url': line_friend.picture_url,
            'total_score': line_friend.total_score(),
            'final_action_date': user_score.status.memo if user_score and user_score.status else None,
            'status': user_score.status.status_name if user_score and user_score.status else None,
            'short_memo': line_friend.short_memo, 
            'detail_memo': line_friend.memo if line_friend.detail_memo else "", 
            'tags': [{'name': tag.name, 'color': tag.color} for tag in line_friend.tags.all()]
        }

        return JsonResponse(data)
    except LineFriend.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    
    
@login_required
def line_friends_list(request):
    line_friends = LineFriend.objects.all()
    order = request.GET.get('order', '-total_score')
    
    # 日付の絞り込み
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timezone.timedelta(days=1)  # 終了日は1日加算
        
        # 日付範囲でアクションを絞り込み、スコアを集計
        line_friends = LineFriend.objects.annotate(
            total_score=Coalesce(
                Sum('actions__score', filter=Q(actions__date__range=(start_date, end_date))),
                Value(0)
            )
        ).order_by(order)
    else:
        # 絞り込みなしでスコアを集計
        line_friends = LineFriend.objects.annotate(
            total_score=Coalesce(Sum('actions__score'), Value(0))
        ).order_by(order)

    line_friends_data = []

    for friend in line_friends:
        # 最終アクションの日付を取得
        last_action = UserAction.objects.filter(line_friend=friend).order_by('-date').first()
        final_action_date = last_action.date if last_action else None

        # タグを取得
        tags = friend.tags.all()

        # タグ情報をリスト化
        tags_data = [{'name': tag.name, 'color': tag.color} for tag in tags]

        # line_friends_data に追加
        line_friends_data.append({
            'friend': friend,
            'final_action_date': final_action_date,
            'short_memo': friend.short_memo,
            'detail_memo': friend.detail_memo,
            'tags': tags_data,
            'total_score': friend.total_score,  # 絞り込みの結果に基づく合計スコア
        })

    return render(request, 'line_management/line_friends_list.html', {
        'line_friends_data': line_friends_data,
        'order': order,
        'start_date': start_date_str,
        'end_date': end_date_str,
    })

@csrf_exempt
def callback(request):
    # get X-Line-Signature header value
    signature = request.META['HTTP_X_LINE_SIGNATURE']

    # get request body as text
    body = request.body.decode('utf-8')
    logger.debug("Request body: %s", body)
    
    # リクエストbodyをデコードして取得
    request_json = json.loads(body)
    if not request_json["events"]:
        return HttpResponse('OK')
    
    events = request_json['events']
    for event in events:
        event_type = event['type']
        logger.debug(f"Handling event type: {event_type}")
        
        # メッセージイベントの場合
        if event_type == 'message':
            messagetype = event['message']['type']
            if messagetype == 'text':
                handle_message(MessageEvent.new_from_json_dict(event))
            elif messagetype == 'sticker':
                handle_sticker(MessageEvent.new_from_json_dict(event))
            elif messagetype == 'image':
                handle_image(MessageEvent.new_from_json_dict(event))
        # フォローイベントの場合
        elif event_type == 'follow':
            line_user_id = event['source']['userId']
            line_friend = get_object_or_404(LineFriend, line_user_id=line_user_id)
            line_friend.is_blocked = False
            line_friend.save()
            handle_follow(FollowEvent.new_from_json_dict(event))
    
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("Invalid signature. Check your channel access token/channel secret.")
        return HttpResponse(status=400)
    except Exception as e:
        logger.error("Error: %s", str(e))
        return HttpResponseBadRequest()
    return HttpResponse('OK')


@login_required
def line_friend_detail_view(request, line_friend_id):
    line_friend = get_object_or_404(LineFriend, id=line_friend_id)
    return render(request, 'line_management/line_friend_detail.html', {'line_friend': line_friend})

@login_required
def line_settings_view(request):
    try:
        settings = LineSettings.objects.get(user=request.user)
    except LineSettings.DoesNotExist:
        settings = None
    
    if request.method == 'POST':
        form = LineSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            line_settings = form.save(commit=False)
            line_settings.user = request.user
            line_settings.save()
            return redirect('line_settings')
    else:
        form = LineSettingsForm(instance=settings)
    
    return render(request, 'line_management/line_settings.html', {'form': form})

def user_detail_api(request, user_id):
    line_friend = LineFriend.objects.get(id=user_id)
    user_actions = UserAction.objects.filter(line_friend=line_friend).select_related('line_friend')
    actions_data = [
        {
            'action_type': action.action_type,
            'score': action.score,
            'memo': action.memo,
            'date': action.date.strftime('%Y-%m-%d %H:%M:%S'),
            'tags': [{'name': tag.name, 'color': tag.color} for tag in action.line_friend.tags.all()],
        }
        for action in user_actions
    ]
    
    data = {
        'id': line_friend.id,
        'display_name': line_friend.display_name,
        'picture_url': line_friend.picture_url,
        'total_score': line_friend.total_score(),
        'final_action_date': line_friend.get_final_action_date(),
        'actions': actions_data,
        'short_memo': line_friend.short_memo,
        'detail_memo': line_friend.detail_memo
    }
    
    return JsonResponse(data)

# LINE友達情報をAPIで取得
class UserDetailAPIView(View):
    def get(self, request, user_id):
        try:
            line_friend = LineFriend.objects.get(id=user_id)
            final_action_date = line_friend.get_final_action_date()
            formatted_date = format(final_action_date, 'Y年m月d日 H:i') if final_action_date else None
            data = {
                'display_name': line_friend.display_name,
                'picture_url': line_friend.picture_url, 
                'total_score': line_friend.total_score(), 
                'final_action_date': formatted_date,
                'id': line_friend.id, 
                'short_memo': line_friend.short_memo, 
                'detail_memo': line_friend.detail_memo, 
                'tags': [{'name': tag.name, 'color': tag.color} for tag in line_friend.tags.all()]

            }
            return JsonResponse(data)
        except LineFriend.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
        
@method_decorator(csrf_exempt, name='dispatch')
class UpdateMemoView(View):
    def post(self, request, user_id):
        try:
            line_friend = LineFriend.objects.get(id=user_id)
            data = json.loads(request.body)

            # ショートメモを更新（存在する場合）
            if 'short_memo' in data:
                line_friend.short_memo = data.get('short_memo', '')

            # 詳細メモを更新（存在する場合）
            if 'detail_memo' in data:
                line_friend.detail_memo = data.get('detail_memo', '') 

            line_friend.save()

            return JsonResponse({'success': True})
        except LineFriend.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'User not found'}, status=404)

# ユーザーアクションのステータスを更新
def liff_access_view(request):
    return render(request, 'line_management/liff_template.html')

def link_redirect_view(request, pk):
    link_score = get_object_or_404(ScoreSetting, pk=pk)
    context = {
        'link_score':link_score,
    }
    return render(request, 'line_management/liff_score_settings.html', context)

# リンククリックの処理（LIFF）
def verify_token(request, pk):
    if request.method == 'POST':
        access_token = request.POST.get('access_token')
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get('https://api.line.me/v2/profile', headers=headers)
        if response.status_code == 200:
            line_profile = response.json()
            line_user_id = line_profile['userId']
            
            if line_user_id:
                user, created = LineFriend.objects.get_or_create(line_user_id=line_user_id)
                
                link_score = get_object_or_404(ScoreSetting, pk=pk)
                score_to_add = link_score.score
                
                UserAction.objects.create(
                    line_friend=user,
                    action_type='link', 
                    score=score_to_add,
                    score_setting=link_score,
                    memo=link_score.memo
                )
                
                if link_score.tag:
                    user.tags.add(link_score.tag)

                return JsonResponse({
                    'line_user_id': line_user_id,
                    'link_url': link_score.trigger,
                }, status=200)
            else:
                return JsonResponse({'error': 'ユーザーIDが見つかりませんでした。'}, status=400)
        else:
            return JsonResponse({'error': '無効なアクセストークンです。'}, status=400)
    return JsonResponse({'error': '無効なリクエストメソッドです。'}, status=400)

# 流入経路
def referral_source_view(request):
    if request.method == 'POST':
        name = request.POST.get('referral_name')
        referral_url = f"https://example.com/referral/{name}"
        Referral.objects.create(name=name, url=referral_url)
        return redirect('line_management:referral_source')

    referrals = Referral.objects.all()
    return render(request, 'line_management/referral_source.html', {'referrals': referrals})

# QRコードの表示
def qr_code_view(request, referral_id):
    referral = Referral.objects.get(id=referral_id)
    qr = qrcode.make(referral.url)
    buf = BytesIO()
    qr.save(buf, format='PNG')
    qr_code_url = f"data:image/png;base64,{buf.getvalue().decode('utf-8')}"
    return render(request, 'line_management/qr_code.html', {'qr_code_url': qr_code_url})
