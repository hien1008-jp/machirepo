from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic.edit import CreateView
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count
from django.http import Http404, HttpResponse
from django.contrib.auth import logout
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.core.exceptions import ValidationError 
import logging
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile, SimpleUploadedFile 

# ロガーの設定
logger = logging.getLogger(__name__)

# モデルとフォームのインポート
from . import models 
from .forms import StatusUpdateForm, ResidentCreationForm, PhotoPostForm, ManualLocationForm 

# -----------------------------------------------------
# 権限チェックヘルパー
# -----------------------------------------------------
def is_staff_user(user):
    """Staff権限チェック用ヘルパー関数"""
    return user.is_authenticated and user.is_staff

# -----------------------------------------------------
# 1. 共通/認証関連ビュー
# -----------------------------------------------------

def index(request):
    """
    トップページ。認証済みユーザーはホームにリダイレクト。未認証はログイン画面などへ。
    """
    if request.user.is_authenticated:
        return redirect('home_redirect')
    
    return render(request, 'index.html')

def home_redirect(request):
    """認証後のリダイレクト先。権限によって画面を振り分ける。"""
    if not request.user.is_authenticated:
        return redirect('login')

    if request.user.is_staff:
        return redirect('admin_home')
    else:
        return redirect('user_home')

class ResidentRegisterView(CreateView):
    """新規ユーザー登録ビュー"""
    form_class = ResidentCreationForm
    model = get_user_model()
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'

def user_logout_view(request):
    """ユーザーログアウト (urls.pyの'logout/'に対応)"""
    logout(request)
    messages.success(request, "ログアウトしました。")
    return redirect('index')


# -----------------------------------------------------
# 2. ユーザー画面ビュー
# -----------------------------------------------------
@login_required
def user_home(request):
    posts = models.PhotoPost.objects.exclude(status='not_required').order_by('-posted_at')[:5]
    context = {'posts': posts}
    # ① 住民は住民用トップ画面から「新規投稿を行う」を押す (リンクとして配置されることを想定)
    return render(request, 'main/user_home.html', context)

@login_required
def my_page(request):
    my_posts = models.PhotoPost.objects.filter(user=request.user).order_by('-posted_at')
    context = {'my_posts': my_posts}
    return render(request, 'main/my_page.html', context)

def post_list(request):
    posts = models.PhotoPost.objects.exclude(status='not_required').order_by('-posted_at')
    context = {'posts': posts}
    return render(request, 'main/post_list.html', context)


# -----------------------------------------------------
# 3. 投稿フロービュー
# -----------------------------------------------------
@login_required
def photo_post_create(request):
    """基本フロー②/③/④ - 報告作成ステップ1: 写真/コメント入力 (タイトル処理を削除)"""
    post_data = request.session.get('post_data', {})
    
    # 【ステップ1クリーンアップ】
    if request.method == 'GET':
        # ★修正: titleもセッションクリア対象に追加★
        keys_to_remove = ['latitude', 'longitude', 'title']
        if any(k in post_data for k in keys_to_remove):
            post_data = {k: v for k, v in post_data.items() if k not in keys_to_remove}
            request.session['post_data'] = post_data
            logger.info("--- SESSION CLEANUP: Old location and title data cleared from session on Step 1 GET. ---")

    if request.method == 'POST':
        form = PhotoPostForm(request.POST, request.FILES, initial=post_data)
        
        if form.is_valid():
            cleaned_data = form.cleaned_data
            
            # --- 画像ファイルのセッション保存 ---
            photo_file = request.FILES.get('photo')
            if photo_file:
                # ファイルオブジェクトをシリアライズ可能なデータに変換し、別枠で保存
                file_content = photo_file.read() 
                request.session['post_photo_data'] = {
                    'content': file_content.decode('latin-1'), 
                    'name': photo_file.name,
                    'content_type': photo_file.content_type,
                    'size': photo_file.size,
                }
            elif 'post_photo_data' in request.session:
                pass
            else:
                if 'post_photo_data' in request.session:
                    del request.session['post_photo_data']
            
            
            # --- 必須フィールドの自動生成/補完 ---
            # ★削除: タイトル自動生成ロジックを削除★
            # if not cleaned_data.get('title'):
            #     comment = cleaned_data.get('comment', '写真報告')
            #     cleaned_data['title'] = comment[:20] if len(comment) > 0 else '写真報告'

            # タグデータをセッションに安全に保存するため、PKのリストに変換
            tags_data = cleaned_data.get('tags')
            if tags_data and hasattr(tags_data[0], 'pk'):
                cleaned_data['tags'] = [tag.pk for tag in tags_data]
            
            # --- フォームデータをセッションに保存 (修正点) ---
            # cleaned_dataから、JSONシリアライズできないphotoオブジェクトを削除する
            post_data_to_save = {k: v for k, v in cleaned_data.items() if k != 'photo'}
            
            # 緯度・経度の既存値があれば保持
            if post_data.get('latitude'):
                post_data_to_save['latitude'] = post_data.get('latitude')
            if post_data.get('longitude'):
                post_data_to_save['longitude'] = post_data.get('longitude')
            
            # ★修正: titleフィールドがセッションに残らないように明示的に削除 (フォームから削除されている前提)
            if 'title' in post_data_to_save:
                del post_data_to_save['title']
                
            request.session['post_data'] = post_data_to_save
            
            # 基本フロー⑤の起点へ: 位置情報取得の起点となるステップ2へリダイレクト
            return redirect('photo_post_manual_location')
        else:
            # === DEBUG/代替フロー①：必須項目未入力エラー処理 ===
            logger.error("PhotoPostForm validation failed: %s", form.errors)
            messages.error(request, "投稿内容にエラーがあります。不足している必須項目（写真、カテゴリ、コメント）を確認するか、写真のファイルサイズ（最大5MB）を確認してください。")
    
    # GETリクエスト、またはPOST失敗時
    else:
        # GETリクエストの場合、セッションからデータを取得してフォームに設定
        # ★修正: titleを初期値から除外★
        initial_data = {k: v for k, v in post_data.items() if k != 'title'}
        form = PhotoPostForm(initial=initial_data)
    
    # ② システムは投稿画面を表示する
    return render(request, 'main/photo_post_create.html', {'form': form, 'step': 1})

@login_required
def photo_post_manual_location(request):
    """基本フロー⑤/代替④ - 報告作成ステップ2: 位置情報の確認・手動設定"""
    post_data = request.session.get('post_data')
    
    # ステップ1のデータがない場合、最初のステップに戻す
    if not post_data:
        messages.error(request, "報告のデータが見つかりませんでした。最初からやり直してください。")
        return redirect('photo_post_create')
    
    if request.method == 'POST':
        # 代替フロー④-2: 手動入力フォームからのPOST
        form = ManualLocationForm(request.POST)
        if form.is_valid():
            # コメントをセッションデータに追加・更新 (ManualLocationFormはコメント専用)
            post_data.update(form.cleaned_data)
            request.session['post_data'] = post_data
            
            # 代替フロー④-3: 投稿内容確認画面へリダイレクト
            return redirect('photo_post_confirm')
        else:
            # バリデーションに失敗した場合 (コメント必須など)
            messages.error(request, "入力されたコメントが正しくありません。詳細コメントは必須です。") # メッセージをコメント入力用に調整

    else:
        # GETリクエストの場合
        form = ManualLocationForm(initial=post_data)
        
    context = {
        'manual_form': form, 
        'post_data': post_data,
        'step': 2
    }
    return render(request, 'main/photo_post_manual_location.html', context)

@login_required
def photo_post_confirm(request):
    """基本フロー⑥/⑦/⑧ - 報告作成ステップ3: 最終確認と保存"""
    post_data = request.session.get('post_data')
    photo_file_data = request.session.get('post_photo_data') 

    # データを取得できていない場合、ステップ1に戻る
    if not post_data:
        messages.error(request, "データが不足しています。最初からやり直してください。")
        return redirect('photo_post_create')
    
    # 【位置情報の上書き/確認】
    # Step2からのJSリダイレクトによる位置情報取得のロジックは、位置情報不要の仕様では機能しないため、
    # そのまま残しますが、緯度経度は空のままになります。
    latitude_query = request.GET.get('latitude')
    longitude_query = request.GET.get('longitude')
    
    if latitude_query and longitude_query:
        post_data['latitude'] = latitude_query
        post_data['longitude'] = longitude_query
        request.session['post_data'] = post_data
        logger.info("--- GEOLOCATION SUCCESS: Location data updated from query params. ---")
    
    # 基本フロー⑦: POSTリクエスト（「この内容で投稿する」）
    if request.method == 'POST':
        try:
            # 緯度・経度の値を取得
            latitude_val = post_data.get('latitude')
            longitude_val = post_data.get('longitude')
            
            # NOT NULL制約違反を回避するため、None/空の場合は 0.0 を設定
            if not latitude_val:
                latitude_val = 0.0
            else:
                try:
                    latitude_val = float(latitude_val)
                except ValueError:
                    latitude_val = 0.0 

            if not longitude_val:
                longitude_val = 0.0
            else:
                try:
                    longitude_val = float(longitude_val)
                except ValueError:
                    longitude_val = 0.0 
            
            # 1. セッションデータからインスタンスを作成
            new_post = models.PhotoPost(
                user=request.user,
                # ★修正: titleはセッションから取得せず、Noneを設定★
                title=None, 
                comment=post_data.get('comment'),
                latitude=latitude_val, 
                longitude=longitude_val, 
            )
            
            # 2. 画像ファイルの再構築とインスタンスへのセット
            if photo_file_data:
                file_content = photo_file_data['content'].encode('latin-1') 
                reconstructed_file = SimpleUploadedFile(
                    name=photo_file_data['name'],
                    content=file_content,
                    content_type=photo_file_data['content_type']
                )
                new_post.photo = reconstructed_file
            
            # 3. モデルの検証と保存
            new_post.full_clean()
            new_post.save()
            
            # 4. ManyToManyField (タグ) を保存 (PKリストからインスタンスに変換)
            tags_list = post_data.get('tags', []) 
            if tags_list:
                tag_instances = models.Tag.objects.filter(pk__in=tags_list)
                new_post.tags.set(tag_instances) 
            
            # 5. 成功したらセッションデータをクリア
            del request.session['post_data']
            if 'post_photo_data' in request.session:
                 del request.session['post_photo_data']
            
            # 6. 完了画面へリダイレクト（基本フロー⑧）
            messages.success(request, "報告を送信しました。")
            return redirect('photo_post_done')
            
        except ValidationError as e:
            # データ検証エラー：緯度経度以外のエラー
            error_messages = "\n".join([f"「{k}」: {v[0]}" for k, v in e.message_dict.items()])
            messages.error(request, f"**データ検証エラー**：投稿の保存に必要な情報が不足しています。不足フィールド:\n{error_messages}")
            
            # エラー発生時はステップ1に戻す
            return redirect('photo_post_create')
            
        except Exception as e:
            # 代替フロー②：投稿時に通信エラーが発生した場合
            logger.error("--- FATAL ERROR: 報告保存時の予期せぬ一般エラーが発生 ---", exc_info=True)
            messages.error(request, f"**投稿通信エラー**：報告の保存中に予期せぬエラーが発生しました。再度投稿してください。エラー: {e}")
            return redirect('photo_post_create')
            
    # GETリクエスト時 (確認画面の表示)
    context = {
        'post_data': post_data,
        'step': 3
    }
    return render(request, 'main/photo_post_confirm.html', context)

@login_required
def photo_post_done(request):
    """報告作成完了（基本フロー⑧）"""
    return render(request, 'main/photo_post_complete.html', {})


# -----------------------------------------------------
# 4. 管理者画面ビュー（スタッフ権限限定）
# -----------------------------------------------------

@user_passes_test(is_staff_user, login_url='/')
def admin_home(request):
    total_posts = models.PhotoPost.objects.count()
    new_posts_count = models.PhotoPost.objects.filter(status='new').count()
    
    context = {
        'total_posts': total_posts,
        'new_posts_count': new_posts_count
    }
    return render(request, 'main/admin_home.html', context)


@user_passes_test(is_staff_user, login_url='/')
def admin_user_list(request):
    return HttpResponse("<h2>管理者: ユーザー一覧</h2>")

@user_passes_test(is_staff_user, login_url='/')
def admin_user_delete_confirm(request, user_id):
    return HttpResponse(f"<h2>管理者: ユーザー削除確認 (ID: {user_id})</h2>")

@user_passes_test(is_staff_user, login_url='/')
def admin_user_delete_complete(request):
    return HttpResponse("<h2>管理者: ユーザー削除完了</h2>")


# --- 管理者向け：報告の確認・記録機能 ---

@user_passes_test(is_staff_user, login_url='/')
def admin_post_list(request):
    status_filter = request.GET.get('status', None)
    
    posts = models.PhotoPost.objects.all().select_related('user').prefetch_related('tags')
    
    valid_statuses = dict(models.PhotoPost.STATUS_CHOICES).keys()
    if status_filter in valid_statuses:
        posts = posts.filter(status=status_filter)
    
    context = {
        'posts': posts,
        'status_filter': status_filter
    }
    return render(request, 'main/admin_reports.html', context)


@user_passes_test(is_staff_user, login_url='/')
def admin_post_detail(request, post_id):
    post = get_object_or_404(models.PhotoPost, pk=post_id)
    context = {'post': post}
    return render(request, 'main/admin_post_detail.html', context)


@user_passes_test(is_staff_user, login_url='/')
def admin_post_status_edit(request, post_id):
    post = get_object_or_404(models.PhotoPost, pk=post_id)
    
    if request.method == 'POST':
        form = StatusUpdateForm(request.POST, instance=post)
        if form.is_valid():
            updated_post = form.save(commit=False)
            
            if updated_post.status == 'completed' and not updated_post.completed_at:
                updated_post.completed_at = timezone.now()
            
            elif updated_post.status != 'completed' and updated_post.completed_at:
                updated_post.completed_at = None 

            updated_post.save()
            messages.success(request, f"報告 (ID: {post_id}) のステータスを更新しました。")
            return redirect('admin_status_edit_done', post_id=post.pk)
    else:
        form = StatusUpdateForm(instance=post)
        
    context = {
        'form': form,
        'post': post
    }
    return render(request, 'main/admin_post_status_edit.html', context)


@user_passes_test(is_staff_user, login_url='/')
def admin_status_edit_done(request, post_id):
    """ステータス編集完了画面"""
    post = get_object_or_404(models.PhotoPost, pk=post_id)
    context = {'post': post}
    return render(request, 'main/admin_status_complete.html', context)