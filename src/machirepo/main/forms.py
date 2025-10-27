from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
# from django.contrib.auth import authenticate # ★★★ この行は不要になるため削除（authenticateは使わない）


# 新規登録フォーム (変更なし)
class ResidentRegistrationForm(forms.ModelForm):
    # ... (ResidentRegistrationForm クラスの内容は変更なし) ...
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_css_class = 'is-invalid' 
        
    password = forms.CharField(
        label='パスワード', 
        widget=forms.PasswordInput,
        error_messages={'required': '入力に誤りがあります。内容を確認してください。'} 
    )
    
    full_name = forms.CharField(
        label='氏名', 
        max_length=50,
        error_messages={
            'required': '入力に誤りがあります。内容を確認してください。',
            'max_length': '入力に誤りがあります。内容を確認してください。' 
        }
    )
    
    class Meta:
        model = User
        fields = ('email', ) 
        error_messages = {
            'email': {
                'required': '入力に誤りがあります。内容を確認してください。',
                'invalid': '入力に誤りがあります。内容を確認してください。', 
            },
        }
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("入力に誤りがあります。内容を確認してください。")
        return email

    def clean(self):
        cleaned_data = super().clean()
        if self._errors:
            self._errors = {}
            self.add_error(None, "入力に誤りがあります。内容を確認してください。") 
        return cleaned_data
        
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["full_name"]
        user.set_password(self.cleaned_data["password"])
        user.last_name = self.cleaned_data["full_name"]
        user.first_name = ""
        user.email = self.cleaned_data["email"]
        user.is_staff = False
        user.is_superuser = False
        if commit:
            user.save()
        return user



class EmailAuthenticationForm(AuthenticationForm):
    """
    ユーザー名ではなくメールアドレスで認証を行う、最も確実なフォーム。
    """
    # エラーメッセージを統一
    error_messages = {
        'invalid_login': 'メールアドレスまたはパスワードが正しくありません。',
        'inactive': 'このアカウントは非アクティブです。'
    }

    def __init__(self, *args, **kwargs):
        # request の処理を親クラスに合わせる
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        self.fields['username'].label = 'メールアドレス'
        self.error_css_class = 'is-invalid'

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        # 1. 空欄チェックと認証失敗の統一エラー
        if not username or not password:
            # どちらか、または両方空欄の場合、統一エラーを発生
            raise forms.ValidationError(
                self.error_messages['invalid_login'],
                code='invalid_login',
            )
            
        # 2. カスタム認証ロジック
        try:
            # メールアドレスでユーザーを検索
            user = User.objects.get(email__iexact=username)
        except User.DoesNotExist:
            user = None

        if user is not None and user.check_password(password):
            # 認証成功
            self.user_cache = user
            
            # 3. アクティブチェック
            if not self.user_cache.is_active:
                raise forms.ValidationError(self.error_messages['inactive'], code='inactive')
        else:
            # 認証失敗（ユーザー不在 or パスワード間違い）
            raise forms.ValidationError(
                self.error_messages['invalid_login'], code='invalid_login')

        return self.cleaned_data

    # 4. 認証成功時にユーザーを返すメソッド（必須）
    def get_user(self):
        return getattr(self, 'user_cache', None)