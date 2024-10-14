# user_management/urls.py
from django.urls import path
from django.views.generic import TemplateView
from .views import CustomLoginView, CustomRegisterView, activate
from django.contrib.auth import views as auth_views
from . import views

app_name = "user_management"

urlpatterns = [
    path('', CustomLoginView.as_view(), name='root_login'), 
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='user_management:login'), name='logout'),
    path('register/', CustomRegisterView.as_view(), name='register'),
    path('activate/<uidb64>/<token>/', activate, name='activate'),
    path('email-verification-sent/', TemplateView.as_view(template_name='user_management/email_verification_sent.html'), name='email_verification_sent'),
    path('dashboard/', TemplateView.as_view(template_name='score_management/dashboard.html'), name='dashboard'),
    path('activation_complete/', TemplateView.as_view(template_name='user_management/activation_complete.html'), name='activation_complete'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='user_management/password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='user_management/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='user_management/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='user_management/password_reset_complete.html'), name='password_reset_complete'),
    path("render/", views.render_view, name="render-view"),
    path("redirect/", views.redirect_view, name="redirect-view"),
]
