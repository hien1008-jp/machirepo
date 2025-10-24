# main/forms.py

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate

class ResidentRegistrationForm(forms.ModelForm):
    # パスワード確認なしの単一パスワードフィールドを定義
    password = forms.CharField(label='パスワード', widget=forms.PasswordInput)
    
    # 氏名（単一フィールド）を定義
    full_name = forms.CharField(label='氏名', max_length=50)
    
    class Meta:
        model = User
        # ★★★ 修正箇所: Userモデルに存在するフィールドのみを指定 ★★★
        # full_name と password は ModelForm 外で定義されているため、fieldsから除外
        fields = ('email', ) 
        
    def clean_email(self):
        # メールアドレスの重複チェック
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("このメールアドレスは既に登録されています。")
        return email

    def save(self, commit=True):
        # ModelFormのsaveメソッドを呼び出し、ユーザーオブジェクトを取得
        # fieldsにemailのみを指定したことで、super().save()はemailだけを処理します。
        user = super().save(commit=False)
        
        # 1. usernameに氏名の値を設定 (前回の希望通り)
        user.username = self.cleaned_data["full_name"] 
        
        # 2. パスワードのハッシュ化
        user.set_password(self.cleaned_data["password"])
        
        # 3. 氏名とメールアドレスの設定
        user.last_name = self.cleaned_data["full_name"] 
        user.first_name = "" 
        user.email = self.cleaned_data["email"]

        # 4. 住民アカウントとして設定
        user.is_staff = False
        user.is_superuser = False
        
        if commit:
            user.save()
        return user
    


class EmailAuthenticationForm(AuthenticationForm):
    """
    ユーザー名ではなくメールアドレスで認証を行うフォーム。
    """
    # フォームフィールドは AuthenticationForm のものをそのまま使用
    # username (ラベルを「メールアドレス」に変更) と password

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ラベルを「ユーザー名」から「メールアドレス」に変更
        self.fields['username'].label = 'メールアドレス'

    def clean(self):
        # 標準のcleanメソッドをオーバーライドし、usernameの代わりにemailでユーザーを検索
        
        username = self.cleaned_data.get('username') # ここにはユーザーが入力したメールアドレスが入る
        password = self.cleaned_data.get('password')

        if username and password:
            self.user_cache = authenticate(self.request, username=username, password=password)
            
            # 標準では username でユーザー検索されるが、
            # カスタムバックエンド (後で削除します) が存在しない前提の場合、
            # 認証失敗後にこの clean メソッド内で手動でユーザーを検索する必要がある
            
            # --- カスタム認証ロジック開始 ---
            try:
                # 入力されたusername（＝メールアドレス）でUserモデルから検索
                user = User.objects.get(email__iexact=username)
            except User.DoesNotExist:
                # ユーザーが見つからなければ、認証失敗としてエラーメッセージをセット
                raise forms.ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid_login',
                    params={'username': self.username_field.verbose_name},
                )
            
            # パスワードチェック
            if user.check_password(password):
                self.user_cache = user # 認証成功、ユーザーをキャッシュ
            else:
                # パスワードが間違っている場合
                raise forms.ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid_login',
                    params={'username': self.username_field.verbose_name},
                )
            # --- カスタム認証ロジック終了 ---
            
        return self.cleaned_data

    # authenticate関数を使用するために、requestオブジェクトを保存
    def get_user(self, request=None):
        return self.user_cache