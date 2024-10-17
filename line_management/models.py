# line_management/models.py
from django.db import models
from user_management.models import CustomUser
from django.conf import settings
from django.core.exceptions import ValidationError

# LINE IDを登録するためのモデル
class LineSettings(models.Model):
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='line_settings',
    )
    line_channel_id = models.CharField(max_length=255)
    line_channel_secret = models.CharField(max_length=255)
    line_access_token = models.CharField(max_length=255)
    liff_id = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return f"LINE Settings for {self.user.email}"
        
# タグテーブル
class Tag(models.Model):
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # 既に同じ名前のタグが存在するかチェック
        existing_tag = Tag.objects.filter(user=self.user, name=self.name).first()
        
        if existing_tag and existing_tag.id != self.id:
            raise ValidationError(f"タグ '{self.name}' は既に存在しています。")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
# 流入経路
class Referral(models.Model):
    user = models.ForeignKey(
    settings.AUTH_USER_MODEL, 
    on_delete=models.CASCADE, 
    related_name='referrals' 
)
    name = models.CharField(max_length=255)  
    url = models.URLField()  
    created_at = models.DateTimeField(auto_now_add=True)  

    def __str__(self):
        return self.name
    
    def generate_tracking_link(self):
        base_url = "https://87b1-111-102-194-193.ngrok-free.app/line/liff/{}/tracking/".format(self.pk)  # 実際のドメインに変更
        return base_url


# LINE友達テーブル
class LineFriend(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        null=True, blank=True
    )
    line_settings = models.ForeignKey(
        LineSettings, 
        on_delete=models.CASCADE, 
        related_name='line_friends'
    )
    line_user_id = models.CharField(max_length=255) 
    display_name = models.CharField(max_length=255)
    picture_url = models.URLField(null=True, blank=True)
    short_memo = models.CharField(max_length=50, null=True, blank=True) 
    detail_memo = models.TextField(null=True, blank=True) 
    tags = models.ManyToManyField(Tag, blank=True)  

    def __str__(self):
        return self.display_name
    
    def total_score(self):
        return self.actions.aggregate(total=models.Sum('score'))['total'] or 0

    def get_final_action_date(self):
        latest_action = self.actions.order_by('-date').first()
        return latest_action.date if latest_action else None
    
# ユーザーのアクションを取得する
class UserAction(models.Model):
    ACTION_TYPE_CHOICES = [
    ('link', 'リンク'),
    ('speech', '発話'),
]
    line_friend = models.ForeignKey(LineFriend, related_name='actions', on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    action_type = models.CharField(max_length=50, choices=ACTION_TYPE_CHOICES)
    score = models.IntegerField()
    score_setting = models.ForeignKey('score_management.ScoreSetting', on_delete=models.SET_NULL, null=True, blank=True)
    memo = models.TextField(null=True, blank=True)
    referral = models.ForeignKey(Referral, on_delete=models.SET_NULL, null=True, blank=True)  

    def __str__(self):
        return f"{self.line_friend.display_name} - {self.action_type} - {self.date}"
