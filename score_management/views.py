# score_management/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import ScoreSetting, Tag
from .forms import ScoreSettingForm
from django.utils.decorators import method_decorator
from django.views import View
from django.http import HttpResponseBadRequest, JsonResponse
from urllib.parse import unquote
from django.utils.http import urlencode
import logging 
from django.db.models import Count, Max, Sum
from django.db.models.functions import Coalesce
from django.db.models import Value 


logger = logging.getLogger(__name__)

@login_required
def dashboard_view(request):
    from line_management.models import UserAction, LineFriend, LineSettings

    # 現在のユーザーに関連する LineSettings を取得
    line_settings = LineSettings.objects.filter(user=request.user).first()
    if not line_settings:
        return render(request, 'score_management/dashboard.html', {
            'error_message': 'LINE設定が見つかりません。',
        })

    # LineSettings に関連する友達を取得
    user_line_friends = LineFriend.objects.filter(line_settings=line_settings)

    # 最近のアクション（最新5件）
    recent_actions = (
        UserAction.objects.filter(line_friend__in=user_line_friends)
        .select_related('line_friend')
        .order_by('-date')[:5]
    )

    # 発話アクションの集計
    speech_triggers = (
        UserAction.objects.filter(line_friend__in=user_line_friends, action_type='speech')
        .values('memo')
        .annotate(total=Count('memo'))
        .order_by('-total')[:5]
    )

    # リンクアクションの集計
    link_triggers = (
        UserAction.objects.filter(line_friend__in=user_line_friends, action_type='link')
        .values('memo')
        .annotate(total=Count('memo'))
        .order_by('-total')[:5]
    )

    # スコア順でLINE友達を表示
    top_line_friends = (
        user_line_friends.annotate(
            total_score=Coalesce(Sum('actions__score'), Value(0))
        ).order_by('-total_score')[:10]
    )

    # フォーム処理
    if request.method == 'POST':
        form = ScoreSettingForm(request.POST)
        if form.is_valid():
            score_setting = form.save(commit=False)
            score_setting.user = request.user  # 現在のユーザーに紐づけ
            score_setting.save()
            return redirect('score_management:dashboard')
    else:
        form = ScoreSettingForm()

    # テンプレートにデータを渡してレンダリング
    return render(request, 'score_management/dashboard.html', {
        'form': form,
        'recent_actions': recent_actions,
        'speech_triggers': speech_triggers,
        'link_triggers': link_triggers,
        'top_line_friends': top_line_friends,
    })

def generate_tracking_link(original_url, line_user_id):
    params = {'line_user_id': line_user_id}
    tracking_url = f"{original_url}?{urlencode(params)}"
    return tracking_url
        
@login_required
def score_settings_view(request):
    scores = ScoreSetting.objects.filter(user=request.user)

    if request.method == 'POST':
        form = ScoreSettingForm(request.POST, user=request.user)  # フォームにユーザーを渡す
        if form.is_valid():
            form.save()  # フォームが保存される際に、ユーザーがセットされる
            return redirect('score_management:score_settings')
    else:
        form = ScoreSettingForm(user=request.user)  # GETリクエストの場合も同様にユーザーを渡す

    return render(request, 'score_management/score_settings.html', {
        'form': form,
        'scores': scores,
    })


# 設定ページを提供
@login_required
def settings_view(request):
    return render(request, 'score_management/settings.html')

# ユーザー情報ページを提供
@login_required
def user_info_view(request):
    """ログインユーザーに関連するLINE友達のアクション履歴を表示"""

    # ログインユーザーに関連するLINE友達を取得
    line_friends = LineFriend.objects.filter(line_settings__user=request.user)

    # 取得した友達に基づくアクション履歴を取得
    actions = UserAction.objects.filter(line_friend__in=line_friends).select_related('line_friend', 'score_setting')

    # テンプレートにデータを渡してレンダリング
    return render(request, 'line_management/user_info.html', {
        'actions': actions,
    })

# リンククリック時のスコア加算処理
def track_link(request):
    original_url = request.GET.get('url')
    line_user_id = request.GET.get('line_user_id')

    if not original_url or not line_user_id:
        return HttpResponseBadRequest("Missing URL or line_user_id parameter")

    try:
        # 現在のユーザーに関連するLINE友達を取得
        line_friend = LineFriend.objects.get(line_user_id=line_user_id, user=request.user)
    except LineFriend.DoesNotExist:
        return HttpResponseBadRequest("Line friend not found")

    try:
        # 現在のユーザーに関連するスコア設定を取得
        score_setting = ScoreSetting.objects.get(
            user=request.user, action_type='link', trigger=original_url
        )
    except ScoreSetting.DoesNotExist:
        return HttpResponseBadRequest("No matching score setting found")

    # リンククリックのアクションを保存
    UserAction.objects.create(
        line_friend=line_friend,
        action_type='link',
        score=score_setting.score,
        score_setting=score_setting,
        memo=score_setting.memo
    )

    # タグが設定されている場合、タグを付与
    if score_setting.tag:
        line_friend.tags.add(score_setting.tag)

    return redirect(original_url)

#   スコア編集機能
@login_required
def edit_score_setting(request, score_id):
    score_setting = get_object_or_404(ScoreSetting, id=score_id, user=request.user)

    if request.method == 'POST':
        form = ScoreSettingForm(request.POST, instance=score_setting)
        if form.is_valid():
            tag_name = request.POST.get('tag_name')
            tag_color = request.POST.get('tag_color', '#ffffff' if score_setting.tag is None else score_setting.tag.color)

            # タグが変更されていない場合は既存のタグを使い、カラーのみ更新
            if score_setting.tag and score_setting.tag.name == tag_name:
                # タグ名が変更されていない場合は、カラーのみ更新
                tag = score_setting.tag
                if tag.color != tag_color:
                    tag.color = tag_color
                    tag.save()
            else:
                # タグ名が変更された場合、既存のタグを確認
                existing_tag = Tag.objects.filter(name=tag_name, user=request.user).first()
                if existing_tag:
                    # 既存タグがある場合はそれを使用し、カラーを更新
                    if existing_tag.color != tag_color:
                        existing_tag.color = tag_color
                        existing_tag.save()
                    tag = existing_tag
                else:
                    tag = Tag.objects.create(name=tag_name, user=request.user, color=tag_color)

            # 古いタグが他に使われていない場合は削除
            if score_setting.tag and score_setting.tag != tag:
                old_tag = score_setting.tag
                score_setting.tag = tag
                score_setting.save()

                # もし他のスコア設定で古いタグが使われていない場合は削除
                if not ScoreSetting.objects.filter(tag=old_tag).exists():
                    old_tag.delete()

            # スコア設定を保存
            score_setting.save()
            return redirect('score_management:score_settings')
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors})

    return JsonResponse({
        'action_type': score_setting.action_type,
        'trigger': score_setting.trigger,
        'score': score_setting.score,
        'memo': score_setting.memo,
        'tag_name': score_setting.tag.name if score_setting.tag else '',
        'tag_color': score_setting.tag.color if score_setting.tag else '#ffffff'
    })



# スコア削除機能
@login_required
def delete_score_setting(request, score_id):
    score_setting = get_object_or_404(ScoreSetting, id=score_id, user=request.user)
    tag = score_setting.tag  # スコア設定のタグを取得

    if request.method == 'POST':
        score_setting.delete()
        
        # タグが他に使用されていない場合、タグも削除する
        if tag and not ScoreSetting.objects.filter(tag=tag).exists():
            tag.delete()

        return redirect('score_management:score_settings')

    return redirect('score_management:score_settings')
