# myproject/score_management/urls.py
from django.urls import path
from .views import dashboard_view, settings_view, user_info_view, track_link
from . views import edit_score_setting, delete_score_setting, score_settings_view
from . import views

app_name = "score_management"

urlpatterns = [
    path('score_settings/', score_settings_view, name='score_settings'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('settings/', settings_view, name='settings'),
    path('user_info/', user_info_view, name='user_info'),
    path('track_link/<int:link_id>/', track_link, name='track_link'), 
    path('edit/<int:score_id>/', edit_score_setting, name='edit_score_setting'),
    path('delete/<int:score_id>/', delete_score_setting, name='delete_score_setting'),
]

