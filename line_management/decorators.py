from functools import wraps
from django.http import HttpResponseForbidden
from .models import LineSettings

def check_line_settings(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            # 現在のユーザーに紐づく LINE 設定を取得
            line_settings = LineSettings.objects.get(user=request.user)
        except LineSettings.DoesNotExist:
            # 設定がない場合はアクセス禁止を返す
            return HttpResponseForbidden("LINE設定が見つかりません。")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def check_user_data_access(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # line_friend_id からデータを取得し、ユーザーに紐づくか確認
        line_friend_id = kwargs.get('line_friend_id')
        if line_friend_id:
            line_friend = LineFriend.objects.filter(id=line_friend_id, user=request.user).first()
            if not line_friend:
                return HttpResponseForbidden("他のユーザーのデータにアクセスする権限がありません。")
        return view_func(request, *args, **kwargs)
    return _wrapped_view
