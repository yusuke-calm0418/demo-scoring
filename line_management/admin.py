# line_management/admin.py
from django.contrib import admin
from .models import LineFriend, LineSettings, UserAction, Tag

class LineSettingsAdmin(admin.ModelAdmin):
    list_display = ['line_channel_id', 'line_channel_secret', 'line_access_token']
    search_fields = ('user__email', 'line_channel_id')

@admin.register(LineFriend)
class LineFriendAdmin(admin.ModelAdmin):
    list_display = ('line_user_id', 'display_name', 'total_score', 'picture_url', 'short_memo', 'detail_memo', 'display_tags')  # 修正: 'tags'をカスタムメソッドに変更
    search_fields = ('line_user_id', 'display_name', 'status_message')

    def total_score(self, obj):
        return obj.total_score()

    total_score.short_description = 'Total Score'

    # カスタムメソッドでタグを表示
    def display_tags(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])  # タグの名前をカンマで区切って表示

    display_tags.short_description = 'Tags'  # 管理画面で表示される列の名前

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
