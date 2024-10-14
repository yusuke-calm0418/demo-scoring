from typing import Any
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from django.contrib.auth.forms import AuthenticationForm

class UserRegistrationForm(UserCreationForm):
    company_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring focus:border-blue-300',
            'placeholder': '株式会社〇〇'
        })
    )
    full_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring focus:border-blue-300',
            'placeholder': '氏名'
        })
    )
    kana_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring focus:border-blue-300',
            'placeholder': 'カナ'
        })
    )
    phone_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring focus:border-blue-300',
            'placeholder': '電話番号'
        })
    )
    postal_code = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring focus:border-blue-300',
            'placeholder': '郵便番号'
        })
    )
    address = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring focus:border-blue-300',
            'placeholder': '住所（任意）'
        })
    )
    industry = forms.ChoiceField(
        choices=[
            ('IT', 'IT業'),
            ('Manufacturing', '製造業'),
            ('Retail', '小売業'),
            ('Healthcare', '医療業'),
            ('Other', 'その他')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring focus:border-blue-300'
        })
    )
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.name = self.cleaned_data.get('full_name')
        if commit:
            user.save()
        return user

    class Meta:
        model = CustomUser
        fields = (
            'email', 'company_name', 'full_name', 'kana_name', 'phone_number', 
            'postal_code', 'address', 'industry', 'password1', 'password2'
        )
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring focus:border-blue-300',
                'placeholder': 'example@example.com'
            }),
        }
        
class LoginForm(AuthenticationForm):
    username = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring focus:border-blue-300',
        'placeholder': 'example@example.com',
        'required': 'required',
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring focus:border-blue-300',
        'id': 'password-field',  
        'placeholder': 'パスワード',
        'required': 'required',
    }))
