# line_management/urls.py
from django.urls import path
from .views import line_friend_detail_view, user_info_view, line_settings_view, callback, user_detail_api, line_friends_list
from .views import UserDetailAPIView, UpdateMemoView, liff_access_view, referral_source_view, qr_code_view
from . import views

app_name ="line_management"

urlpatterns = [
    path('line_friend/<int:line_friend_id>/', line_friend_detail_view, name='line_friend_detail'),  # line_friend_detailビューにURLを設定
    path('user_info/', user_info_view, name='user_info'),  # user_infoビューにURLを設定
    path('settings/', line_settings_view, name='line_settings'),
    path('callback/', callback, name='callback'),
    path('line_friends/', line_friends_list, name='line_friends_list'),
    path('api/user/<int:user_id>/', UserDetailAPIView.as_view(), name='user_detail_api'),
    path('api/user/<int:user_id>/update_memo/', UpdateMemoView.as_view(), name='update_memo'),  # この部分が必要
    path('liff/', liff_access_view, name='liff-access'), # LIFFに登録するエンドポイントURL
    path('liff/<int:pk>/', views.link_redirect_view, name="link-redirect"),
    path('verify-token/<int:pk>/', views.verify_token, name='verify_token'),
    path('referral/', referral_source_view, name='referral_source'),
    path('referral/<int:referral_id>/qr/', qr_code_view, name='qr_code'),
]
