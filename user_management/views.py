# user_management/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from .forms import UserRegistrationForm, LoginForm
from django.contrib.auth.views import LoginView
from django.views import View
from .tokens import account_activation_token
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from .models import CustomUser
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.urls import reverse

# ログイン
class CustomLoginView(LoginView):
    template_name = 'user_management/login.html'
    redirect_authenticated_user = True
    form_class = LoginForm

    def get_success_url(self):
        return reverse('score_management:dashboard')

# 新規登録
class CustomRegisterView(View):
    def get(self, request):
        form = UserRegistrationForm()
        return render(request, 'user_management/register.html', {'form': form})
# 新規登録送信後のメッセージ
    def post(self, request):
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # commit = Falseだと、データベースに保存されず、インスタンスが返される
            user = form.save(commit=False)
            # 確認するまでログイン不可にする
            user.is_active = False
            user.save()
            current_site = get_current_site(request)
            mail_subject = 'アカウントを有効にしてください。'
            message = render_to_string('user_management/acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'protocol': 'http',
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(mail_subject, message, to=[to_email])
            email.send()
            return redirect('user_management:email_verification_sent')
        return render(request, 'user_management/register.html', {'form': form})

# エラー関連のビュー
User = get_user_model()

def activate(request, uidb64, token):
    print('Activation function called')  # すでにメールアドレスが有効化されている場合のエラー
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        print(f'User found: {user.email}')  # デバッグメッセージ
    except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
        print(f'Error: {e}')  # デバッグメッセージ
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'アカウントが有効化されました。')
        print('Account activated')  # デバッグメッセージ
        return redirect('user_management:activation_complete')
    else:
        messages.error(request, 'アクティベーションリンクが無効です。')
        print('Invalid activation link')  # デバッグメッセージ
        return redirect('user_management:login')

from score_management.forms import ScoreSettingForm

def render_view(request):
    # request tohanha HTTPリクエストの情報が入っている
    print(f'loginUser: {request.user}')
    print(f'isLogin: {request.user.is_authenticated}')
    print(f'{request.GET}')
    
    if request.GET.get('category') == "top":
        # redirectはページを飛ばすだけ
        return redirect('login')
    
    form = ScoreSettingForm(request.POST or None);
    
    # POSTリクエストかつformの内容が正しい場合
    if request.method == "POST" and form.is_valid():
        # フォームの内容を保存
        form.save()
        
        return redirect('login')
        
    
    # renderは色々情報を混ぜてHTMLを作成する
    context = {
        "title": "test",
        "user_list": User.objects.all(),
        "form": form
    }
    return render(request, 'render/render.html', context)


def redirect_view(request):
    
    return redirect('render-view')  # リダイレクト先のURL名を指定
