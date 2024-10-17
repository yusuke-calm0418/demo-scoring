# score_management/models.py
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from line_management.models import LineFriend, Tag
from django.utils.crypto import get_random_string
import random, string
from urllib.parse import urlencode
from django.apps import apps
from django.core.exceptions import ValidationError

# スコア設定テーブル
class ScoreSetting(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ACTION_TYPE_CHOICES = [
        ('link', 'リンク'),
        ('speech', '発話'),
    ]
    action_type = models.CharField(max_length=10, choices=ACTION_TYPE_CHOICES)
    trigger = models.CharField(max_length=100)
    score = models.IntegerField()
    memo = models.TextField(blank=True, null=True)
    tag = models.ForeignKey('line_management.Tag', on_delete=models.SET_NULL, null=True, blank=True, related_name='score_settings')
    tracking_link = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.get_action_type_display()} - {self.trigger} - {self.score}"

    def generate_tracking_link(self):
        base_url = "https://87b1-111-102-194-193.ngrok-free.app/line/liff/"
        return f"{base_url}{self.pk}"

    def save(self, *args, **kwargs):
    
        if not self.pk:
            super().save(*args, **kwargs)
            
        if self.action_type == 'link' and not self.tracking_link:
            self.tracking_link = self.generate_tracking_link()

    # 再度保存してトラッキングリンクを保存
        super().save(*args, **kwargs)
