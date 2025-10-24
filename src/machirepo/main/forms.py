# main/forms.py

from django import forms
from django.contrib.auth.models import User

class ResidentRegistrationForm(forms.ModelForm):
    # パスワード確認なしの単一パスワードフィールドを定義
    password = forms.CharField(label='パスワード', widget=forms.PasswordInput)
    
    # 氏名（単一フィールド）を定義
    full_name = forms.CharField(label='氏名', max_length=150)
    
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