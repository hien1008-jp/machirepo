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

# main/forms.py (EmailAuthenticationForm クラス全体を置き換えてください)

class EmailAuthenticationForm(AuthenticationForm):
    """
    ユーザー名ではなくメールアドレスで認証を行うフォーム。
    """
    # ★★★ 修正箇所1: 認証失敗時のエラーメッセージを上書き ★★★
    error_messages = {
        'invalid_login': 'メールアドレスまたはパスワードが正しくありません。',
        
    }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        self.fields['username'].label = 'メールアドレス'
        self.error_css_class = 'is-invalid'
        
    def clean(self):
        cleaned_data = super().clean() 

        # 認証失敗時、またはフィールドエラーが存在する場合の処理
        if self.errors:
            
            # 項目ごとの赤枠を強制的に付与するロジック (変更なし)
            error_class = 'is-invalid'
            for field_name, field in self.fields.items():
                if field_name in self.errors:
                    existing_classes = field.widget.attrs.get('class', '')
                    field.widget.attrs['class'] = (existing_classes + ' ' + error_class).strip()
            
            # ★★★ 修正箇所2: フィールドエラーメッセージを削除/統一ロジック ★★★
            # AuthenticationFormのエラーはすでに 'invalid_login' に上書きされているため、
            # フィールドエラーだけをクリアし、エラーを non_field_errors に統合する
            
            # エラーを一時保存
            temp_errors = self.errors.copy() 
            
            # フィールドエラーは表示しないのでクリア
            self._errors = {} 

            # non_field_errors（フォーム上部）に統一メッセージを再追加
            # self.error_messages['invalid_login'] を使う
            self.add_error(None, self.error_messages['invalid_login'])
            
            return cleaned_data 
        
        # 認証ロジック (変更なし)
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        if username and password:
            try:
                user = User.objects.get(email__iexact=username)
            except User.DoesNotExist:
                # このValidationErrorは上書きされた 'invalid_login' メッセージを使用
                raise forms.ValidationError(
                    self.error_messages['invalid_login'], 
                    code='invalid_login'
                )
            
            if user.check_password(password):
                self.user_cache = user 
            else:
                # このValidationErrorも上書きされた 'invalid_login' メッセージを使用
                raise forms.ValidationError(
                    self.error_messages['invalid_login'], 
                    code='invalid_login'
                )
            
        return cleaned_data
    
    def get_user(self):
        return getattr(self, 'user_cache', None)