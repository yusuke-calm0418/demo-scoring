# score_management/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import ScoreSetting, Tag, Link
from .forms import ScoreSettingForm
from django.utils.decorators import method_decorator
from django.views import View
from django.http import HttpResponseBadRequest, JsonResponse
# from line_management.models import LineFriend, UserAction
from urllib.parse import unquote
from django.utils.http import urlencode
import logging 
from django.db.models import Count, Max, Sum
from django.db.models.functions import Coalesce
from django.db.models import Value 



logger = logging.getLogger(__name__)

@login_required
def dashboard_view(request):
    from line_management.models import UserAction, LineFriend  # 関数内インポート
    from .forms import ScoreSettingForm  # 関数内インポート
    
    if request.method == 'POST':
        form = ScoreSettingForm(request.POST)
        if form.is_valid():
            score_setting = form.save(commit=False)
            score_setting.user = request.user
            score_setting.save()
            return redirect('score_management:dashboard')
    else:
        form = ScoreSettingForm()

    # 最新の5件のアクションを取得
    recent_actions = UserAction.objects.select_related('line_friend').order_by('-date')[:5]

    # 発話アクションのトリガーごとの集計（最大5件）
    speech_triggers = UserAction.objects.filter(action_type='speech').values('memo').annotate(total=Count('memo')).order_by('-total')[:5]

    # リンクアクションのトリガーごとの集計（最大5件）
    link_triggers = UserAction.objects.filter(action_type='link').values('memo').annotate(total=Count('memo')).order_by('-total')[:5]

    # スコアが高い順にユーザーを取得し、最終アクション日を含める（最大10件）
    top_line_friends = LineFriend.objects.annotate(
        total_score=Coalesce(Sum('actions__score'), Value(0))  # アクションがない場合に 0 を使用
    ).order_by('-total_score')[:10]  # スコアの高い順に並べる


    # スコアランキング、直近のアクション、アクション解析をビューに渡す
    return render(request, 'score_management/dashboard.html', {
        'form': form,
        'recent_actions': recent_actions,
        'speech_triggers': speech_triggers,
        'link_triggers': link_triggers,
        'top_line_friends': top_line_friends,
    })
    
@login_required
def score_settings_view(request):
    company = request.user.company
    scores = ScoreSetting.objects.filter(company=company)
    return render(request, 'score_management/score_settings.html', {'scores': scores})



def generate_tracking_link(original_url, line_user_id):
    params = {'line_user_id': line_user_id}
    tracking_url = f"{original_url}?{urlencode(params)}"
    return tracking_url

class ScoreSettingsView(View):
    @method_decorator(login_required)
    def get(self, request):
        from .forms import ScoreSettingForm  # 関数内インポート
        from .models import ScoreSetting  # 関数内インポート
        
        form = ScoreSettingForm()
        scores = ScoreSetting.objects.filter(user=request.user)
        tags = Tag.objects.all()  #タグを取得
        return render(request, 'score_management/score_settings.html', {'form': form, 'scores': scores , 'tags': tags})

    @method_decorator(login_required)
    def post(self, request):
        form = ScoreSettingForm(request.POST)
        if form.is_valid():
            # タグ情報を取得
            tag_name = request.POST.get('tag_name')
            tag_color = request.POST.get('tag_color')

            # タグが既に存在するか確認
            tag, created = Tag.objects.get_or_create(name=tag_name)
            
            if not created:
                # タグが存在する場合、エラーメッセージを追加
                form.add_error(None, f'タグ "{tag_name}" は既に存在します。')
            else:
                # 新規タグが作成された場合、カラーを設定
                tag.color = tag_color
                tag.save()
                
                score_setting = form.save(commit=False)
                score_setting.user = request.user
                score_setting.tag = tag  # タグをスコア設定に関連付ける
                
                score_setting.save()
                
                return redirect('score_management:score_settings')
        
        # フォームが無効な場合、または同名エラーが発生した場合
        scores = ScoreSetting.objects.filter(user=request.user)
        return render(request, 'score_management/score_settings.html', {'form': form, 'scores': scores})

# 設定ページを提供
@login_required
def settings_view(request):
    return render(request, 'score_management/settings.html')

# ユーザー情報ページを提供
@login_required
def user_info_view(request):
    return render(request, 'line_management/user_info.html')

# リンククリック時のスコア加算処理
def track_link(request):
    original_url = request.GET.get('url')
    line_user_id = request.GET.get('line_user_id')

    if not original_url or not line_user_id:
        return HttpResponseBadRequest("Missing URL or line_user_id parameter")

    try:
        # LINEユーザーを取得
        line_friend = LineFriend.objects.get(line_user_id=line_user_id)
    except LineFriend.DoesNotExist:
        return HttpResponseBadRequest("Line friend not found")

    # スコア設定を取得
    try:
        score_setting = ScoreSetting.objects.get(action_type='link', trigger=original_url)
    except ScoreSetting.DoesNotExist:
        return HttpResponseBadRequest("No matching score setting found")

    # UserAction テーブルにリンククリックのアクションを保存
    UserAction.objects.create(
        line_friend=line_friend,
        action_type='link',
        score=score_setting.score,
        score_setting=score_setting,
        memo=score_setting.memo  # メモを保存
    )

    # タグが設定されている場合、タグを付与
    if score_setting.tag:
        line_friend.tags.add(score_setting.tag)

    # 元のURLにリダイレクト
    return redirect(original_url)


# スコア設定編集
@login_required
def edit_score_setting(request, score_id):
    score_setting = get_object_or_404(ScoreSetting, id=score_id, user=request.user)
    
    if request.method == 'POST':
        form = ScoreSettingForm(request.POST, instance=score_setting)
        if form.is_valid():
            tag_name = request.POST.get('tag_name')
            tag_color = request.POST.get('tag_color', '#ffffff' if score_setting.tag is None else score_setting.tag.color)
            tag, created = Tag.objects.get_or_create(name=tag_name)

            if not created:
                tag.color = tag_color
                tag.save()  

            score_setting = form.save(commit=False)
            score_setting.tag = tag
            score_setting.save()
            return redirect('score_management:score_settings')
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors})

    else:
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
