"""machirepo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
"""
# machirepo/urls.py

from django.contrib import admin 
from django.urls import path, include
from django.contrib.auth import views as auth_views 
from main.forms import EmailAuthenticationForm 

urlpatterns = [
    # ここで admin が使用されています
    path('admin/', admin.site.urls),
    
    path('', include('main.urls')),
    
    # ログインビューのオーバーライド
    path('accounts/login/', 
         auth_views.LoginView.as_view(
             template_name='registration/login.html', 
             authentication_form=EmailAuthenticationForm
         ), 
         name='login'),
         
    # 標準認証URLをインクルード
    path('accounts/', include('django.contrib.auth.urls')), 
]