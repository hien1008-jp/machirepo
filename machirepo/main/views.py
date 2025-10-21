from django.shortcuts import render

# トップページを描画する関数
def index(request):
    # 'index.html' テンプレートを描画して返す
    return render(request, 'index.html', {})