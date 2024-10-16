# /line_management/views.py

# 標準ライブラリのインポート
import hmac
import hashlib
import base64
import logging
import json
from datetime import datetime

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
    # 現在のユーザーに紐づく LineSettings を取得
    line_settings = LineSettings.objects.filter(user=request.user).first()

    if not line_settings:
        return render(request, 'line_management/user_info.html', {
            'actions': [],  # データがない場合は空のリストを渡す
        })

    # LineSettings に紐づく LineFriend を取得
    line_friends = LineFriend.objects.filter(line_settings=line_settings)

    # LINE友達に関連するアクションを取得
    actions = UserAction.objects.filter(line_friend__in=line_friends).select_related('line_friend')

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
    from .decorators import check_line_settings
    from line_management.decorators import check_user_data_access
    # ログインしているユーザーに紐づくLineFriendのみを取得
    line_friends = LineFriend.objects.filter(user=request.user)
    order = request.GET.get('order', '-total_score')

    # 日付の絞り込み
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timezone.timedelta(days=1)  # 終了日は1日加算

        # 日付範囲でアクションを絞り込み、スコアを集計
        line_friends = line_friends.annotate(
            total_score=Coalesce(
                Sum('actions__score', filter=Q(actions__date__range=(start_date, end_date))),
                Value(0)
            )
        ).order_by(order)
    else:
        # 絞り込みなしでスコアを集計
        line_friends = line_friends.annotate(
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
    
# グローバルスコープで宣言（初期化はしない）
line_bot_api = None
handler = None

@csrf_exempt
def callback(request, user_id):  # 'user_id'を引数に追加
    global line_bot_api, handler  # グローバル変数を使用

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

    # LINE APIの初期化（グローバルスコープに反映）
    line_bot_api = LineBotApi(line_settings.line_access_token)
    handler = WebhookHandler(line_settings.line_channel_secret)

    # 動的にイベントハンドラを追加
    @handler.add(MessageEvent, message=TextMessage)
    def handle_message(event):
        process_message(event)  # メッセージ処理の関数を呼び出し

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


def process_message(event):
    """メッセージを処理する関数"""
    from score_management.models import ScoreSetting

    text = event.message.text
    line_user_id = event.source.user_id
    reply_token = event.reply_token

    try:
        profile = line_bot_api.get_profile(line_user_id)
        display_name = profile.display_name
        picture_url = profile.picture_url

        # LineSettingsを取得
        line_settings = LineSettings.objects.first()

        line_friend, created = LineFriend.objects.get_or_create(
            line_user_id=line_user_id,
            defaults={
                'display_name': display_name,
                'picture_url': picture_url,
                'line_settings': line_settings
            }
        )

        if not created:
            line_friend.display_name = display_name
            line_friend.picture_url = picture_url
            line_friend.save()

        score_settings = ScoreSetting.objects.filter(action_type='speech', trigger=text)

        if score_settings.exists():
            score_setting = score_settings.first()
            UserAction.objects.create(
                line_friend=line_friend,
                action_type='speech',
                score=score_setting.score,
                score_setting=score_setting,
                memo=score_setting.memo
            )

            total_score = UserAction.objects.filter(line_friend=line_friend).aggregate(
                total=models.Sum('score'))['total'] or 0

            if score_setting.tag:
                line_friend.tags.add(score_setting.tag)

            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(text=f'{display_name}さん、"{text}" に{score_setting.score}点が加算されました！')
            )
        else:
            line_bot_api.reply_message(
                reply_token,
                TextSendMessage(text=f'{display_name}さん、"{text}" に点数は加算されませんでした。')
            )
    except LineBotApiError as e:
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text="プロフィール情報の取得に失敗しました。")
        )
        logger.error(f"LineBotApiError: {str(e)}")



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

# ユーザーアクションのステータスを更新
@login_required
def liff_access_view(request, pk):
    score = get_object_or_404(ScoreSetting, pk=pk)
    line_settings = LineSettings.objects.filter(user=request.user).first()

    if not line_settings or not line_settings.liff_id:
        return render(request, 'line_management/error.html', {
            'error_message': 'LIFF IDが設定されていません。',
        })

    return render(request, 'line_management/liff_template.html', {
        'link_score': score,
        'liff_id': line_settings.liff_id,
    })

@csrf_exempt
def link_redirect_view(request, pk):
    from score_management.models import ScoreSetting
    
    link_score = get_object_or_404(ScoreSetting, pk=pk)
    return render(request, 'line_management/liff_score_settings.html', {
        'link_score': link_score,
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
            response.raise_for_status()  # エラー時に例外を発生させる

            line_profile = response.json()
            line_user_id = line_profile.get('userId')
            display_name = line_profile.get('displayName', '不明なユーザー')
            picture_url = line_profile.get('pictureUrl', '')

            if not line_user_id:
                return JsonResponse({'error': 'ユーザーIDが見つかりませんでした。'}, status=400)

            # LineFriendを取得または作成
            line_friend, created = LineFriend.objects.get_or_create(
                line_user_id=line_user_id,
                defaults={'display_name': display_name, 'picture_url': picture_url}
            )

            # スコア設定を取得
            link_score = get_object_or_404(ScoreSetting, pk=pk)

            # アクションを作成
            UserAction.objects.create(
                line_friend=line_friend,
                action_type='link', 
                score=link_score.score,
                score_setting=link_score,
                memo=link_score.memo
            )

            # タグがあれば追加
            if link_score.tag:
                line_friend.tags.add(link_score.tag)

            return JsonResponse({
                'line_user_id': line_user_id,
                'link_url': link_score.trigger,
            }, status=200)

        except requests.exceptions.RequestException as e:
            return JsonResponse({'error': f'LINE APIリクエストでエラーが発生しました: {str(e)}'}, status=400)

    return JsonResponse({'error': '無効なリクエストメソッドです。'}, status=405)

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
