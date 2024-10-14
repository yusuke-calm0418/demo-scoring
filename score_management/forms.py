# score_management/forms.py
from django import forms
from .models import ScoreSetting, StatusSetting, Tag
from django.core.exceptions import ValidationError

class ScoreSettingForm(forms.ModelForm):
    class Meta:
        model = ScoreSetting
        fields = ['action_type', 'trigger', 'score', 'tag', 'memo']
        widgets = {
            'action_type': forms.Select(choices=ScoreSetting.ACTION_TYPE_CHOICES),
        }

    def __init__(self, *args, **kwargs):
        super(ScoreSettingForm, self).__init__(*args, **kwargs)
        self.fields["action_type"].widget.attrs["class"] = "w-full px-3 py-2 border rounded-md focus:outline-none focus:ring focus:border-blue-300"
        self.fields["action_type"].widget.attrs["placeholder"] = "アクションタイプ"
        
    def clean(self):
        cleaned_data = super().clean()
        tag_name = cleaned_data.get('tag_name')
        if tag_name:
            if Tag.objects.filter(name=tag_name).exists():
                raise ValidationError(f' "{tag_name}" は既に存在します。')
        return cleaned_data    

class StatusSettingForm(forms.ModelForm):
    class Meta:
        model = StatusSetting
        fields = ['status_name', 'color', 'memo']
