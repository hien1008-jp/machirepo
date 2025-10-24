# main/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required 
from django.urls import reverse_lazy 
from django.views.generic.edit import CreateView 
from .forms import ResidentRegistrationForm 
from django.shortcuts import redirect


# ★★★ 1. トップページ（index）: ログイン状態による振り分け ★★★
def index(request):
    if request.user.is_authenticated:
        # ログイン済みの場合、振り分けビューへリダイレクト
        return redirect('home_redirect') 
    
    # ログインしていない場合、通常のトップページをレンダリング
    return render(request, 'index.html', {})


#権限による振り分け
@login_required 
def home_redirect(request):
    # ユーザーが管理者の場合
    if request.user.is_staff or request.user.is_superuser:
        return redirect('admin_home')
    else: # それ以外（一般住民）の場合
        return redirect('user_home')

# ★★★ 3. 住民トップページ ★★★
@login_required
def user_home(request):
    return render(request, 'main/user_home.html', {})

# ★★★ 4. 管理者トップページ ★★★
@login_required
def admin_home(request):
    return render(request, 'main/admin_home.html', {})


class ResidentRegisterView(CreateView):
    form_class = ResidentRegistrationForm 
    success_url = reverse_lazy('login') 
    template_name = 'registration/signup.html' # signupに遷移するようにすること