# main/urls.py （新規作成）

from django.urls import path
from . import views

urlpatterns = [
    # トップページ ('/') にアクセスがあったら views.index 関数を実行
    path('', views.index, name='index'), 
]