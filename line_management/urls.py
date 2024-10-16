from django.urls import path
from . import views

app_name = "line_management"

urlpatterns = [
    path('line_friend/<int:line_friend_id>/', views.line_friend_detail_view, name='line_friend_detail'),
    path('user_info/', views.user_info_view, name='user_info'),
    path('settings/', views.get_line_settings, name='line_settings'),
    path('callback/', views.callback, name='callback'),
    path('callback/<int:user_id>/', views.callback, name='line_callback'),
    path('line_friends/', views.line_friends_list, name='line_friends_list'),
    path('api/user/<int:user_id>/', views.UserDetailAPIView.as_view(), name='user_detail_api'),
    path('api/user/<int:user_id>/update_memo/', views.UpdateMemoView.as_view(), name='update_memo'),
    path('liff/', views.liff_access_view, name='liff-access'),
    path('liff/<int:pk>/', views.link_redirect_view, name='link-redirect'),
    path('verify-token/<int:pk>/', views.verify_token, name='verify_token'),
    path('referral/', views.referral_source_view, name='referral_source'),
    path('referral/<int:referral_id>/qr/', views.qr_code_view, name='qr_code'),
]
