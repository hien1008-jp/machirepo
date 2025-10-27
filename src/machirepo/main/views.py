from django.urls import reverse_lazy 
from django.views.generic.edit import CreateView 
from .forms import ResidentRegistrationForm 
from django.shortcuts import redirect
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required 
from django.contrib.auth.models import User
from django.http import HttpResponse

def index(request):
    if request.user.is_authenticated:
        return redirect('home_redirect') 
    
    return render(request, 'index.html', {})


@login_required 
def home_redirect(request):
    if request.user.is_staff or request.user.is_superuser:
        return redirect('admin_home')
    else:
        return redirect('user_home')

@login_required
def user_home(request):
    return render(request, 'main/user_home.html', {})

@login_required
def admin_home(request):
    return render(request, 'main/admin_home.html', {})


class ResidentRegisterView(CreateView):
    form_class = ResidentRegistrationForm 
    success_url = reverse_lazy('login') 
    template_name = 'registration/signup.html' 


@login_required
def admin_user_list(request):
    if not request.user.is_staff and not request.user.is_superuser:
        return redirect('home_redirect') 

    users = User.objects.filter(is_superuser=False, is_staff=False).order_by('-date_joined')
    
    context = {
        'users': users
    }
    return render(request, 'main/admin_users.html', context) 

@login_required
def admin_user_delete_confirm(request, user_id):
    if not request.user.is_staff and not request.user.is_superuser:
        return redirect('home_redirect')

    target_user = get_object_or_404(User.objects.filter(is_superuser=False, is_staff=False), pk=user_id)

    if request.method == 'POST':
        target_user.delete()
        return redirect('admin_user_delete_complete') 
    
    return redirect('admin_user_list')



@login_required
def admin_user_delete_complete(request):
    if not request.user.is_staff and not request.user.is_superuser:
        return redirect('home_redirect')
        
    return render(request, 'main/admin_delete_complete.html')