# /line_management/views.py

# 標準ライブラリのインポート
import hmac
import hashlib
import base64
import logging
import json
from datetime import datetime, timedelta
import qrcode
from io import BytesIO

# サードパーティライブラリのインポート
import requests
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FollowEvent, StickerMessage

# Djangoライブラリのインポート
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Sum, Value, Q
from django.db.models.functions import Coalesce
from django.http import (
    HttpResponse, HttpResponseForbidden, HttpResponseBadRequest, JsonResponse
)
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.dateformat import format
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from .decorators import check_line_settings
from .forms import LineSettingsForm
from .models import LineSettings, LineFriend, UserAction, Referral
from django.views.decorators.http import require_GET, require_POST
from user_management.models import CustomUser
from django.utils.crypto import get_random_string


# ロギングの設定
logger = logging.getLogger(__name__)

@login_required
def get_line_settings(request):
    # 現在のユーザーのLINE設定を取得
    settings = LineSettings.objects.filter(user=request.user).first()
    
    if settings:
        logger.info(f"LINE Settings found: Channel ID - {settings.line_channel_id}, User - {settings.user}")
    else:
        logger.warning(f"LINE Settings not found for user: {request.user}")

    # POSTリクエスト処理
    if request.method == 'POST':
        form = LineSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            line_settings = form.save(commit=False)  # 一時保存
            line_settings.user = request.user  # 現在のユーザーをセット
            line_settings.save()  # データベースに保存

            return redirect('line_management:line_settings')
    else:
        # 初期化時にフォームが有効か確認
        form = LineSettingsForm(instance=settings)

    # テンプレートをレンダリングして返す
    return render(request, 'line_management/line_settings.html', {
        'form': form,
        'settings': settings
    })

@login_required
def user_info_view(request):
    line_settings = LineSettings.objects.filter(user=request.user).first()

    if not line_settings:
        return render(request, 'line_management/user_info.html', {
            'actions': [], 
        })

    line_friends = LineFriend.objects.filter(line_settings=line_settings)

    # LINE友達に関連するアクションを取得
    actions = UserAction.objects.filter(line_friend__in=line_friends).select_related('line_friend').order_by('-date')


    # テンプレートにデータを渡してレンダリング
    return render(request, 'line_management/user_info.html', {
        'actions': actions,
    })
    
@login_required
@require_GET
def get_user_details(request, user_id):
    line_settings = LineSettings.objects.filter(user=request.user).first()
    if not line_settings:
        return JsonResponse({'error': 'LINE設定が見つかりません'}, status=404)
    
    # LineSettingsに紐づく友達か確認
    line_friend = get_object_or_404(LineFriend, id=user_id, line_settings=line_settings)

    # 友達の詳細データをJSONで返す
    data = {
        'id': line_friend.id,
        'display_name': line_friend.display_name,
        'picture_url': line_friend.picture_url,
        'short_memo': line_friend.short_memo,
        'detail_memo': line_friend.detail_memo,
        'total_score': line_friend.total_score(),
        'final_action_date': line_friend.get_final_action_date(),
        'tags': [{'name': tag.name, 'color': tag.color} for tag in line_friend.tags.all()],
    }
    return JsonResponse(data)
    
@login_required
@check_line_settings
def line_friends_list(request):
    from .decorators import check_user_data_access  # 必要に応じてインポート

    # ログインしているユーザーの公式LINE設定を取得
    line_settings = LineSettings.objects.filter(user=request.user).first()
    
    # 公式LINE設定が見つからない場合はエラー
    if not line_settings:
        return HttpResponseBadRequest("LINE設定が見つかりません。")

    # ログインしているユーザーに紐づくLINE友達のみを取得
    line_friends = LineFriend.objects.filter(line_settings=line_settings)
    
    # 並び替えの処理
    order = request.GET.get('order', '-total_score')
    
    # 日付絞り込み
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    if start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
        # 日付範囲でアクションを絞り込み、スコアを集計
        line_friends = line_friends.annotate(
            total_score=Coalesce(
                Sum('actions__score', filter=Q(actions__date__range=(start_date, end_date))),
                Value(0)
            )
        ).order_by(order)
    else:
        # 日付絞り込みがない場合、全期間でスコアを集計
        line_friends = line_friends.annotate(
            total_score=Coalesce(Sum('actions__score'), Value(0))
        ).order_by(order)

    line_friends_data = []
    for friend in line_friends:
        last_action = UserAction.objects.filter(line_friend=friend).order_by('-date').first()
        final_action_date = last_action.date if last_action else None
        tags = friend.tags.all()
        tags_data = [{'name': tag.name, 'color': tag.color} for tag in tags]
        
        # データ構造に必要な情報を追加
        line_friends_data.append({
            'friend': friend,
            'final_action_date': final_action_date,
            'short_memo': friend.short_memo,
            'tags': tags_data,
            'total_score': friend.total_score
        })

    # テンプレートにデータを渡してレンダリング
    return render(request, 'line_management/line_friends_list.html', {
        'line_friends_data': line_friends_data,
        'order': order,
        'start_date': start_date_str,
        'end_date': end_date_str,
    })
    
@csrf_exempt
def callback(request, user_id):
    signature = request.META.get('HTTP_X_LINE_SIGNATURE', '')
    body = request.body.decode('utf-8')

    print(f"Signature: {signature}")
    print(f"Request Body: {body}")

    # user_idに基づいてLineSettingsを取得
    try:
        line_settings = LineSettings.objects.get(user__id=user_id)
    except LineSettings.DoesNotExist:
        print(f"No LineSettings found for user with id: {user_id}")
        return HttpResponseForbidden("Invalid user or settings")

    # LINE APIの初期化
    line_bot_api = LineBotApi(line_settings.line_access_token)
    handler = WebhookHandler(line_settings.line_channel_secret)

    # メッセージイベントのハンドラを動的に定義
    @handler.add(MessageEvent, message=TextMessage)
    def handle_message(event):
        process_message(event, line_settings, line_bot_api)  # line_bot_apiを渡す

    try:
        handler.handle(body, signature)
        print("Handler executed successfully")
    except InvalidSignatureError:
        print("Invalid signature")
        return HttpResponseForbidden()
    except Exception as e:
        print(f"Error: {str(e)}")
        return HttpResponseBadRequest()

    return HttpResponse('OK')

def process_message(event, line_settings, line_bot_api):
    from score_management.models import ScoreSetting

    text = event.message.text  # 発話内容
    line_user_id = event.source.user_id  # ユーザーのLINE ID
    reply_token = event.reply_token  # 応答トークン

    try:
        # LINE友達の情報を取得
        line_friend = LineFriend.objects.get(line_user_id=line_user_id, line_settings=line_settings)
    except LineFriend.DoesNotExist:
        # LINE友達が見つからない場合は新しく保存する
        profile = line_bot_api.get_profile(line_user_id)  # プロフィールを取得
        line_friend = LineFriend.objects.create(
            line_user_id=line_user_id,
            line_settings=line_settings,
            display_name=profile.display_name,  # 表示名
            picture_url=profile.picture_url  # プロフィール画像URL
        )

    # スコア設定を公式LINEに紐づけて取得
    score_settings = ScoreSetting.objects.filter(
        user=line_settings.user, action_type='speech', trigger=text
    )

    if score_settings.exists():
        score_setting = score_settings.first()

        # アクションの保存
        UserAction.objects.create(
            line_friend=line_friend,
            action_type='speech',
            score=score_setting.score,
            score_setting=score_setting,
            memo=score_setting.memo
        )

        # タグが設定されている場合に付与
        if score_setting.tag:
            line_friend.tags.add(score_setting.tag)

        total_score = (
            UserAction.objects.filter(line_friend=line_friend)
            .aggregate(total=models.Sum('score'))['total'] or 0
        )

        # 応答メッセージを送信
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(
                text=f'{line_friend.display_name}さん、"{text}" に対して{score_setting.score}点が加算されました！'
            )
        )
    else:
        # スコア設定が見つからない場合の応答
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text=f'"{text}" に対するスコア設定が見つかりませんでした。')
        )

@login_required
def line_friend_detail_view(request, line_friend_id):
    from .models import LineFriend  # 関数内インポート
    
    line_friend = get_object_or_404(LineFriend, id=line_friend_id)
    return render(request, 'line_management/line_friend_detail.html', {'line_friend': line_friend})

@login_required
def line_settings_view(request):
    # 現在のユーザーの LineSettings インスタンスを取得
    try:
        settings = LineSettings.objects.get(user=request.user)
    except LineSettings.DoesNotExist:
        settings = None  # 存在しない場合は None に設定
    
    if request.method == 'POST':
        form = LineSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            line_settings = form.save(commit=False)
            line_settings.user = request.user  # 現在のユーザーに紐づけ
            line_settings.save()  # データベースに保存
            return redirect('line_management:line_settings')
    else:
        form = LineSettingsForm(instance=settings)  # フォームに既存の設定を表示

    # テンプレートにデータを渡してレンダリング
    return render(request, 'line_management/line_settings.html', {
        'form': form,
        'settings': settings
    })

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


def liff_handler_view(request):
    state = request.GET.get('state', '')  # クエリパラメータ 'state' を取得

    if state == 'score':
        return render(request, 'line_management/liff_score_settings.html')
    elif state == 'tracking':
        return render(request, 'line_management/liff_landing.html')
    else:
        return render(request, 'line_management/error.html', {'error': '無効な状態パラメータです。'})


# リンククリックでスコア加算用のビュー
@login_required
def liff_template_view(request, pk):
    score_setting = get_object_or_404(ScoreSetting, pk=pk)
    line_settings = get_object_or_404(LineSettings, user=request.user)

    context = {
        'liff_id': line_settings.liff_id,
        'link_score': score_setting,
        'line_url': 'https://lin.ee/WTB3y2q',  # LINE友達追加リンク
    }
    return render(request, 'line_management/liff_template.html', context)


# リンククリックでスコア加算用のビュー
@login_required
def liff_score_view(request, pk):
    score_setting = get_object_or_404(ScoreSetting, pk=pk)
    line_settings = get_object_or_404(LineSettings, user=request.user)

    context = {
        'liff_id': line_settings.liff_id,
        'link_score': score_setting,
        'line_url': 'https://lin.ee/WTB3y2q',  # LINE友達追加リンク
    }
    return render(request, 'line_management/liff_score_template.html', context)


@csrf_exempt
def liff_access_view(request, pk):
    score = get_object_or_404(ScoreSetting, pk=pk)

    access_token = request.POST.get('access_token')

    if not access_token:
        return JsonResponse({'error': 'アクセストークンが提供されていません。'}, status=400)

    headers = {'Authorization': f'Bearer {access_token}'}

    try:
        response = requests.get('https://api.line.me/v2/profile', headers=headers)
        response.raise_for_status()  # エラー時に例外を発生させる

        line_profile = response.json()
        line_user_id = line_profile.get('userId')
        display_name = line_profile.get('displayName', '不明なユーザー')

        if not line_user_id:
            return JsonResponse({'error': 'ユーザーIDが見つかりませんでした。'}, status=400)

        line_friend, created = LineFriend.objects.get_or_create(
            line_user_id=line_user_id,
            defaults={'display_name': display_name}
        )

        return render(request, 'line_management/liff_template.html', {
            'link_score': score,
            'liff_id': 'YOUR_LIFF_ID_HERE',  # 必要に応じてLINEの設定からLIFF IDを取得
        })

    except requests.exceptions.RequestException as e:
        return JsonResponse({'error': f'LINE APIリクエストでエラーが発生しました: {str(e)}'}, status=400)


@csrf_exempt
def link_redirect_view(request, pk):
    line_settings = LineSettings.objects.filter(user=request.user).first()
    link_score = get_object_or_404(ScoreSetting, pk=pk)
    return render(request, 'line_management/liff_score_settings.html', {
        'link_score': link_score,
        'liff_id': line_settings.liff_id,
    })


@csrf_exempt  # CSRFチェックを回避する
def verify_token(request, pk):
    if request.method == 'POST':
        access_token = request.POST.get('access_token')

        if not access_token:
            return JsonResponse({'error': 'アクセストークンが提供されていません。'}, status=400)

        headers = {'Authorization': f'Bearer {access_token}'}

        try:
            response = requests.get('https://api.line.me/v2/profile', headers=headers)
            response.raise_for_status()
            line_profile = response.json()
            line_user_id = line_profile.get('userId')
            display_name = line_profile.get('displayName', '不明なユーザー')
            picture_url = line_profile.get('pictureUrl', '')

            if not line_user_id:
                return JsonResponse({'error': 'ユーザーIDが見つかりませんでした。'}, status=400)

            line_friend, created = LineFriend.objects.get_or_create(
                line_user_id=line_user_id,
                defaults={'display_name': display_name, 'picture_url': picture_url}
            )

            link_score = get_object_or_404(ScoreSetting, pk=pk)

            UserAction.objects.create(
                line_friend=line_friend,
                action_type='link',
                score=link_score.score,
                score_setting=link_score,
                memo=link_score.memo
            )

            if link_score.tag:
                line_friend.tags.add(link_score.tag)

            return JsonResponse({
                'line_user_id': line_user_id,
                'link_url': link_score.trigger,
            }, status=200)

        except requests.exceptions.RequestException as e:
            return JsonResponse({'error': f'LINE APIリクエストでエラーが発生しました: {str(e)}'}, status=400)

    return JsonResponse({'error': '無効なリクエストメソッドです。'}, status=405)


@login_required
def referral_source_view(request):
    if request.method == 'POST':
        referral_name = request.POST.get('referral_name')
        referral = Referral(user=request.user, name=referral_name)
        referral.save()
        referral.url = referral.generate_tracking_link()
        referral.save()
        return redirect('line_management:referral_source')

    referrals = Referral.objects.filter(user=request.user)
    return render(request, 'line_management/referral_source.html', {'referrals': referrals})


@csrf_exempt
def track_referral_view(request, referral_id):
    referral = get_object_or_404(Referral, pk=referral_id)
    return redirect('line_management:liff_landing', referral_id=referral.id)


def qr_code_view(request, referral_id):
    referral = Referral.objects.get(id=referral_id)
    qr = qrcode.make(referral.url)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return render(request, 'line_management/qr_code.html', {
        'qr_code_url': f"data:image/png;base64,{qr_code_base64}",
    })


@login_required
def liff_landing_view(request, referral_id):
    line_settings = get_object_or_404(LineSettings, user=request.user)

    context = {
        'liff_id': line_settings.liff_id,
        'line_id': line_settings.line_channel_id,
        'route': referral_id,
        'line_url': 'https://lin.ee/WTB3y2q',  # LINE友達追加リンク
    }

    return render(request, 'line_management/liff_landing.html', context)


@login_required
def liff_tracking_view(request, pk):
    line_settings = get_object_or_404(LineSettings, user=request.user)

    context = {
        'liff_id': line_settings.liff_id,
        'line_id': line_settings.line_channel_id,
        'route': pk,
        'line_url': 'https://lin.ee/WTB3y2q',  # LINE友達追加リンク
    }
    return render(request, 'line_management/liff_tracking_template.html', context)


@csrf_exempt
@login_required
def save_referral_info(request, user_id):
    if request.method == 'POST':
        access_token = request.POST.get('access_token')
        route = request.GET.get('route')

        if not access_token:
            return JsonResponse({'error': 'アクセストークンが提供されていません。'}, status=400)

        headers = {'Authorization': f'Bearer {access_token}'}

        try:
            response = requests.get('https://api.line.me/v2/profile', headers=headers)
            response.raise_for_status()
            line_profile = response.json()
            line_user_id = line_profile['userId']
            display_name = line_profile.get('displayName', '不明なユーザー')
            picture_url = line_profile.get('pictureUrl', '')

            line_settings = get_object_or_404(LineSettings, user_id=user_id)
            line_friend, created = LineFriend.objects.get_or_create(
                line_user_id=line_user_id,
                line_settings=line_settings,
                defaults={'display_name': display_name, 'picture_url': picture_url}
            )

            if route:
                referral = get_object_or_404(Referral, id=route, user_id=user_id)
                UserAction.objects.create(
                    line_friend=line_friend,
                    action_type='link',
                    score=10,
                    memo='流入経路からの友達追加',
                    referral=referral
                )

            return JsonResponse({'status': 'success', 'line_name': line_friend.display_name}, status=200)

        except requests.exceptions.RequestException as e:
            return JsonResponse({'error': f'LINE APIリクエストでエラー  {str(e)}'}, status=400)
