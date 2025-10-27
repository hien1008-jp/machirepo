from django.urls import path
from . import views
from django.contrib.auth import views as auth_views 
from .forms import EmailAuthenticationForm 
from django.contrib.auth.views import LogoutView


urlpatterns = [
    # トップページ（未ログイン時にログインボタンを表示するページ）
    path('', views.index, name='index'), 

    # ★★★ ログイン画面の追加 (URL定義が抜けていた原因を解消) ★★★
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html'
    ), name='login'),
    
    # ログアウト
    path('logout/', auth_views.LogoutView.as_view(), name="logout"), 
    
    # ログイン後に住民か管理者かを振り分け
    path('home/', views.home_redirect, name='home_redirect'), 
    
    # 住民トップ画面
    path('user/home/', views.user_home, name='user_home'), 
    
    # 管理者トップ画面
    path('manage/home/', views.admin_home, name='admin_home'), 

    # 新規登録画面
    path('signup/', views.ResidentRegisterView.as_view(), name='signup'),

    path('manage/users/', views.admin_user_list, name='admin_user_list'),

    path('manage/users/delete/<int:user_id>/', views.admin_user_delete_confirm, name='admin_user_delete_confirm'),

    path('manage/users/delete/done/', views.admin_user_delete_complete, name='admin_user_delete_complete'),
]