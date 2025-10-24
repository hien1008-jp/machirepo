# main/urls.py

from django.urls import path
from . import views

urlpatterns = [
    #トップページ（未ログイン時にログインボタンを表示するページ）
    path('', views.index, name='index'), 
    
    #ログイン後に住民か管理者かを振り分け
    path('home/', views.home_redirect, name='home_redirect'), 
    
    #住民トップ画面
    path('user/home/', views.user_home, name='user_home'), 
    
    #管理者トップ画面
    path('manage/home/', views.admin_home, name='admin_home'), 

    #新規登録画面
    path('signup/', views.ResidentRegisterView.as_view(), name='signup'),
]