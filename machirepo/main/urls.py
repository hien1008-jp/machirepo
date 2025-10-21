# main/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # 従来のトップページ（未ログイン時にログインボタンを表示するページなど）
    path('', views.index, name='index'), 
    
    # ★追加: ログイン後の振り分けビューを登録
    path('home/', views.home_redirect, name='home_redirect'), 
    
    # ★追加: 住民トップページ
    path('user/home/', views.user_home, name='user_home'), 
    
    # ★追加: 管理者トップページ
    path('manage/home/', views.admin_home, name='admin_home'), 
]