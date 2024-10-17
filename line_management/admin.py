# line_management/admin.py
from django.contrib import admin
from .models import LineFriend, LineSettings, UserAction, Tag, Referral

class LineSettingsAdmin(admin.ModelAdmin):
    list_display = ['line_channel_id', 'line_channel_secret', 'line_access_token']
    search_fields = ('user__email', 'line_channel_id')

@admin.register(LineFriend)
class LineFriendAdmin(admin.ModelAdmin):
    list_display = ('line_user_id', 'display_name', 'total_score', 'picture_url', 'short_memo', 'detail_memo', 'display_tags')  
    search_fields = ('line_user_id', 'display_name', 'status_message')

    def total_score(self, obj):
        return obj.total_score()

    total_score.short_description = 'Total Score'


    def display_tags(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])  

    display_tags.short_description = 'Tags' 

admin.site.register(LineSettings, LineSettingsAdmin)


@admin.register(UserAction)
class UserActionAdmin(admin.ModelAdmin):
    list_display = ('line_friend', 'date', 'action_type', 'score', 'memo')
    search_fields = ('line_friend__display_name', 'action_type', 'memo')
    list_filter = ('action_type', 'date')

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color')
    search_fields = ('name', 'color')
    list_filter = ('created_at', 'updated_at')

# Referralモデルを管理サイトに追加
@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'name', 'url', 'created_at')  # 表示するカラム
    search_fields = ('name',)  # 検索フィールド

    # リスト表示の順序を指定
    ordering = ('-created_at',)
