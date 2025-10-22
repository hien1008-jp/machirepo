# main/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required # ログイン必須デコレーター

# ログイン後のリダイレクト先を振り分けるビュー
# ユーザーがログインしていないと、LOGIN_URLへリダイレクトされる
@login_required
def home_redirect(request):
    # ユーザーが管理者（is_staff または is_superuser）の場合
    if request.user.is_staff or request.user.is_superuser:
        # ★リダイレクト先を新しいURL名に変更
        return redirect('admin_home') # 'admin_home' は /manage/home/ を指す
    else:
        # それ以外（一般住民）の場合
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