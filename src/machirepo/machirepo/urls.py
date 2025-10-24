"""machirepo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),  
    
    # Djangoの認証（ログイン、ログアウトなど）のURLを追加
    path('accounts/', include('django.contrib.auth.urls')),
]