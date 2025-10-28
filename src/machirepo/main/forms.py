from django import forms
from django.contrib.auth import get_user_model 
from django.core.validators import MinLengthValidator
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import PhotoPost, Tag 
from . import models 


# settings.pyで指定されたユーザーモデルを取得
User = get_user_model() 

# -----------------------------------------------------
# 1. 新規登録フォーム (ResidentCreationForm)
# -----------------------------------------------------
class ResidentCreationForm(UserCreationForm):
    """
    新規ユーザー（居住者）登録用フォーム。
    UserCreationFormを継承し、氏名とメールアドレスを追加。
    """
    
    full_name = forms.CharField(
        label='氏名', 
        max_length=50,
        error_messages={
            'required': '入力に誤りがあります。内容を確認してください。',
            'max_length': '入力に誤りがあります。内容を確認してください.' 
        }
    )
    
    class Meta(UserCreationForm.Meta):
        model = User
        # 'username'は親クラスが持つ。ここでは'email'とカスタムの'full_name'を追加
        fields = ('email', 'full_name') 

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("入力に誤りがあります。内容を確認してください。")
        return email

    def save(self, commit=True):
        # パスワードのハッシュ化（暗号化）は親クラスに任せるため、まず親のsave()を実行
        user = super().save(commit=False)
        
        # カスタムフィールドの値を標準フィールドに割り当てる
        # usernameは認証に使用されるため、ここでは氏名を設定
        user.username = self.cleaned_data["full_name"] 
        user.last_name = self.cleaned_data["full_name"]
        user.first_name = "" 
        user.email = self.cleaned_data["email"] 
        user.is_staff = False
        user.is_superuser = False
        
        if commit:
            user.save()
        return user


# -----------------------------------------------------
# 2. ログインフォーム (EmailAuthenticationForm)
# -----------------------------------------------------
class EmailAuthenticationForm(AuthenticationForm):
    """
    ユーザー名ではなくメールアドレスで認証を行うフォーム。
    """
    error_messages = {
        'invalid_login': 'メールアドレスまたはパスワードが正しくありません。',
        'inactive': 'このアカウントは非アクティブです。'
    }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'メールアドレス'
        self.error_css_class = 'is-invalid'

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if not username or not password:
            raise forms.ValidationError(self.error_messages['invalid_login'], code='invalid_login')
            
        try:
            # メールアドレスでユーザーを検索
            user = User.objects.get(email__iexact=username)
        except User.DoesNotExist:
            user = None

        if user is not None and user.check_password(password):
            self.user_cache = user
            
            if not self.user_cache.is_active:
                raise forms.ValidationError(self.error_messages['inactive'], code='inactive')
        else:
            # 認証失敗（ユーザー不在 or パスワード間違い）
            raise forms.ValidationError(self.error_messages['invalid_login'], code='invalid_login')

        return self.cleaned_data

    def get_user(self):
        return getattr(self, 'user_cache', None)
    
    
# -----------------------------------------------------
# 3. 投稿作成フォーム (PhotoPostForm)
# -----------------------------------------------------
class PhotoPostForm(forms.ModelForm):
   
    tags = forms.ModelChoiceField(
        queryset=models.Tag.objects.all().order_by('name'),
        empty_label="カテゴリーを選択してください",
        label="カテゴリ",
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True # 必須にする場合はTrue
    )
    # commentフィールドを必須として再定義
    comment = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': '状況を詳しく説明してください (必須)'}),
        required=True, # コメントは必須
        label="状況説明"
    )

    class Meta:
        model = PhotoPost
        # Step 1で必要なフィールドのみを含める
        # ★titleフィールドをfieldsから削除★
        fields = ('photo', 'tags', 'comment', 'latitude', 'longitude')
        
        # photoフィールドはModelFormのデフォルトでrequired=True (null=False) のはず

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # エラーログに表示された、必須ではないフィールドを明示的に非必須にする
        self.fields['latitude'].required = False 
        self.fields['longitude'].required = False 
        # ★titleフィールドの非必須設定を削除★ (Meta.fieldsから削除したため)
        
        # フォームのスタイル設定
        for name, field in self.fields.items():
            if name != 'tags':
                field.widget.attrs.update({
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition duration-150'
                })
        
        # photo inputのクラスを上書き
        if 'photo' in self.fields:
            self.fields['photo'].widget.attrs.update({
                'class': 'w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none'
            })


class ManualLocationForm(forms.Form):
    """基本フロー② - 位置情報の手動入力フォーム（★コメント入力専用に変更★）"""
    comment = forms.CharField(
        label="詳細情報（必須）",
        required=True,
        widget=forms.Textarea(attrs={'rows': 5, 'placeholder': '例: 交差点の北西角が陥没しています。発生時期は不明です。'}),
        help_text="具体的な状況や発生時期、危険性などを詳しく記述してください。",
        validators=[MinLengthValidator(10, message='詳細情報は10文字以上で入力してください。')]
    )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition duration-150'
            })

# -----------------------------------------------------
# 4. 位置情報手動入力フォーム (ManualLocationForm)
# -----------------------------------------------------
class ManualLocationForm(forms.Form):
    location_name = forms.CharField(label="地名（任意）", max_length=255, required=False)


# -----------------------------------------------------
# 5. 管理者向け：ステータス更新フォーム (StatusUpdateForm)
# -----------------------------------------------------
class StatusUpdateForm(forms.ModelForm):
    """
    管理者による報告ステータスと優先順位の更新に使用するフォーム
    """
    class Meta:
        model = PhotoPost
        fields = ('status', 'priority', 'admin_note')
        labels = {
            'status': '対応ステータス',
            'priority': '対応優先順位',
            'admin_note': '対応内容/判断結果（メモ）',
        }
        widgets = {
            'admin_note': forms.Textarea(attrs={'rows': 5}),
        }