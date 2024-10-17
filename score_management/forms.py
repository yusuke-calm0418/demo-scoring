from django import forms
from .models import ScoreSetting, Tag

class ScoreSettingForm(forms.ModelForm):
    tag_name = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring focus:border-blue-300',
        'placeholder': 'タグ名'
    }))
    tag_color = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring focus:border-blue-300',
        'placeholder': 'タグカラー'
    }))
    
    class Meta:
        model = ScoreSetting
        fields = ['action_type', 'trigger', 'score', 'memo']
        widgets = {
            'action_type': forms.Select(choices=ScoreSetting.ACTION_TYPE_CHOICES),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(ScoreSettingForm, self).__init__(*args, **kwargs)
        self.fields["action_type"].widget.attrs["class"] = "w-full px-3 py-2 border rounded-md focus:outline-none focus:ring focus:border-blue-300"
        self.fields["action_type"].widget.attrs["placeholder"] = "アクションタイプ"

    def save(self, commit=True):
        instance = super().save(commit=False)
        tag_name = self.cleaned_data.get('tag_name')
        tag_color = self.cleaned_data.get('tag_color')

        # ビューでタグの重複チェックを行うため、ここでは新規タグ作成のみ
        if tag_name:
            tag, created = Tag.objects.get_or_create(
                name=tag_name,
                user=self.user,  # タグを現在のユーザーに紐付ける
                defaults={'color': tag_color}
            )
            instance.tag = tag
        
        if self.user:
            instance.user = self.user  

        if commit:
            instance.save()  
        return instance
