# line_management/forms.py
from django import forms
from .models import LineSettings, Tag, LineFriend

class LineSettingsForm(forms.ModelForm):
    class Meta:
        model = LineSettings
        fields = ['line_channel_id', 'line_channel_secret', 'line_access_token']
        widgets = {
            'line_channel_id': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring focus:border-blue-300',
                'placeholder': 'チャネルID'
            }),
            'line_channel_secret': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring focus:border-blue-300',
                'placeholder': 'チャネルシークレット'
            }),
            'line_access_token': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring focus:border-blue-300',
                'placeholder': 'チャネルアクセストークン'
            }),
            'liff_id': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring focus:border-blue-300',
                'placeholder': 'LIFF IDを入力してください'
            }),
        }

        
        
class Tag():
    class Meta:
        model = Tag
        fields = ['name', 'color']

class LineFriendForm(forms.ModelForm):
    class Meta:
        model = LineFriend
        fields = ['line_user_id', 'display_name', 'picture_url', 'short_memo', 'detail_memo']  # memoフィールドを含める
