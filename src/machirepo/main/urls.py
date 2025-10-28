from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
# from .forms import EmailAuthenticationForm # フォームはビューや設定側で指定するため、URLconfからは削除

# アプリケーションの名前空間


urlpatterns = [
    # -----------------------------------------------------
    # 1. 共通/認証関連
    # -----------------------------------------------------
    
    # トップページ（未ログイン時にログインボタン等を表示）
    path('', views.index, name='index'),
    
    # ログイン (Django標準のLoginViewを使用)
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html'
    ), name='login'),
    
    # ログアウト (Django標準のLogoutViewを使用)
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # 新規登録画面 (2つ目のリストにのみ存在)
    path('signup/', views.ResidentRegisterView.as_view(), name='signup'),

    # 認証後のリダイレクト先（ユーザー種別（住民/管理者）を振り分け）
    path('home/', views.home_redirect, name='home_redirect'),
    
    # -----------------------------------------------------
    # 2. ユーザー画面（住民）
    # -----------------------------------------------------
    # 住民トップ画面（1つ目のリストの'user/'と2つ目のリストの'user/home/'を統合）
    path('user/home/', views.user_home, name='user_home'),
    
    # マイページ (1つ目のリストから)
    path('mypage/', views.my_page, name='my_page'),
    
    # 投稿一覧 (1つ目のリストから)
    path('posts/', views.post_list, name='post_list'),
    
    # -----------------------------------------------------
    # 3. 投稿フロー (マルチステップ) (1つ目のリストから)
    # -----------------------------------------------------
    path('post/create/', views.photo_post_create, name='photo_post_create'),
    path('post/manual_location/', views.photo_post_manual_location, name='photo_post_manual_location'),
    path('post/confirm/', views.photo_post_confirm, name='photo_post_confirm'),
    path('post/done/', views.photo_post_done, name='photo_post_done'),
    
    # -----------------------------------------------------
    # 4. 管理者画面 (プレフィックスを'manage/'に統一)
    # -----------------------------------------------------
    
    # 管理者トップ画面
    path('manage/home/', views.admin_home, name='admin_home'),
    
    # 管理者向け：ユーザー管理
    path('manage/users/', views.admin_user_list, name='admin_user_list'),
    path('manage/users/delete/<int:user_id>/', views.admin_user_delete_confirm, name='admin_user_delete_confirm'), # URL名の変更と'confirm'の削除
    path('manage/users/delete/done/', views.admin_user_delete_complete, name='admin_user_delete_complete'), # 完了画面 (2つ目のリストに'done'、1つ目のリストに'complete'があるため、'complete'を優先し'done'に統一)

    # 管理者向け：報告の確認・記録 (1つ目のリストから、プレフィックスを'manage/'に変更)
    path('manage/posts/', views.admin_post_list, name='admin_post_list'),
    path('manage/posts/<int:post_id>/detail/', views.admin_post_detail, name='admin_post_detail'),
    path('manage/posts/<int:post_id>/edit_status/', views.admin_post_status_edit, name='admin_post_status_edit'),
    path('manage/posts/<int:post_id>/status_done/', views.admin_status_edit_done, name='admin_status_edit_done'),
]