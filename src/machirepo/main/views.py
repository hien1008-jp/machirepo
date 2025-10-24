
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required 
from django.urls import reverse_lazy # リダイレクト先のURLを指定するために使用
from django.views.generic.edit import CreateView # 汎用ビュー（簡単！）を使用

from .forms import ResidentRegistrationForm 

@login_required
def home_redirect(request):
    # ユーザーが管理者の場合
    if request.user.is_staff or request.user.is_superuser:
        return redirect('admin_home') #admin_home.html
    else:   # それ以外（一般住民）の場合
        return redirect('user_home')

# 住民トップページ (ログイン必須)
@login_required
def user_home(request):
    return render(request, 'main/user_home.html', {})

# 管理者トップページ (ログイン必須)
@login_required
def admin_home(request):
    return render(request, 'main/admin_home.html', {})

# 従来のトップページ（index.html）は、ログイン導線用として残しておいてもOK
def index(request):
    return render(request, 'index.html', {})




class ResidentRegisterView(CreateView):
    # ★修正: 使用するフォームを ResidentRegistrationForm に変更
    form_class = ResidentRegistrationForm 
    
    # 成功時のリダイレクト先をログインページに指定
    success_url = reverse_lazy('login') 
    
    # テンプレート名はそのまま
    template_name = 'registration/signup.html'
