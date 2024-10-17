# line_management/urls.py
from django.urls import path
from . import views

app_name = "line_management"

urlpatterns = [
    # LINE友達の詳細表示
    path('line_friend/<int:line_friend_id>/', views.line_friend_detail_view, name='line_friend_detail'),

    # ユーザー情報表示
    path('user_info/', views.user_info_view, name='user_info'),

    # LINE設定取得
    path('settings/', views.get_line_settings, name='line_settings'),

    # LINEコールバック
    path('callback/', views.callback, name='callback'),
    path('callback/<int:user_id>/', views.callback, name='line_callback'),

    # LINE友達リスト表示
    path('line_friends/', views.line_friends_list, name='line_friends_list'),

    # APIビュー: ユーザーの詳細取得
    path('api/user/<int:user_id>/', views.UserDetailAPIView.as_view(), name='user_detail_api'),
    path('api/user/<int:user_id>/update_memo/', views.UpdateMemoView.as_view(), name='update_memo'),

    # LIFF関連ビュー
    path('liff/<int:pk>/score/', views.liff_score_view, name='liff_score'),  # スコア加算用
    path('liff/<int:pk>/tracking/', views.liff_tracking_view, name='liff_tracking'),  # 流入経路保存用

    # スコア加算後のリダイレクト処理
    path('liff/<int:pk>/redirect/', views.link_redirect_view, name='link-redirect'),

    # アクセストークン検証
    path('verify-token/<int:pk>/', views.verify_token, name='verify_token'),

    # 流入経路の管理
    path('referral-source/', views.referral_source_view, name='referral_source'),  
    path('referral/<int:referral_id>/', views.track_referral_view, name='track_referral'),
    path('referral/liff/<int:referral_id>/', views.liff_landing_view, name='liff_landing'),

    # 流入経路情報の保存
    path('save-referral-info/<int:user_id>/', views.save_referral_info, name='save_referral_info'),

    # QRコード生成
    path('qr-code/<int:referral_id>/', views.qr_code_view, name='qr_code'),
    
    path('liff/', views.liff_handler_view, name='liff_handler'),
]
