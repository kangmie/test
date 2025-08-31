from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from .models import UserProfile
from .forms import LoginForm, ClientCreationForm, CrewCreationForm

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
        
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard:home')
            else:
                messages.error(request, 'Username atau password salah.')
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('accounts:login')

@login_required
def profile_view(request):
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        # Create profile if not exists
        profile = UserProfile.objects.create(user=request.user, role='client')
    
    return render(request, 'accounts/profile.html', {'profile': profile})

@login_required
def create_client_view(request):
    # Only superuser can create client
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'superuser':
        messages.error(request, 'Anda tidak memiliki akses untuk membuat client.')
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        form = ClientCreationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    
                    # Create UserProfile
                    profile = UserProfile.objects.create(
                        user=user,
                        role='client',
                        phone=form.cleaned_data.get('phone', ''),
                        address=form.cleaned_data.get('address', ''),
                        max_tenants=form.cleaned_data['max_tenants'],
                        created_by=request.user
                    )
                    
                    messages.success(request, f'Client {user.username} berhasil dibuat.')
                    return redirect('accounts:create_client')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
    else:
        form = ClientCreationForm()
    
    # Get all clients created by this superuser
    clients = User.objects.filter(userprofile__role='client', userprofile__created_by=request.user)
    
    return render(request, 'accounts/create_client.html', {
        'form': form,
        'clients': clients
    })

@login_required
def create_crew_view(request):
    # Only client can create crew
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'client':
        messages.error(request, 'Anda tidak memiliki akses untuk membuat crew.')
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        form = CrewCreationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    
                    # Create UserProfile
                    profile = UserProfile.objects.create(
                        user=user,
                        role='crew',
                        phone=form.cleaned_data.get('phone', ''),
                        created_by=request.user
                    )
                    
                    messages.success(request, f'Crew {user.username} berhasil dibuat.')
                    return redirect('accounts:create_crew')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
    else:
        form = CrewCreationForm()
    
    # Get all crews created by this client
    crews = User.objects.filter(userprofile__role='crew', userprofile__created_by=request.user)
    
    return render(request, 'accounts/create_crew.html', {
        'form': form,
        'crews': crews
    })

@login_required
def delete_user_view(request, user_id):
    user_to_delete = get_object_or_404(User, id=user_id)
    
    # Check permission
    if not hasattr(request.user, 'userprofile'):
        messages.error(request, 'Akses ditolak.')
        return redirect('dashboard:home')
        
    current_profile = request.user.userprofile
    target_profile = user_to_delete.userprofile
    
    # Superuser can delete clients, clients can delete crews
    if (current_profile.role == 'superuser' and target_profile.role == 'client' and 
        target_profile.created_by == request.user) or \
       (current_profile.role == 'client' and target_profile.role == 'crew' and 
        target_profile.created_by == request.user):
        
        username = user_to_delete.username
        user_to_delete.delete()
        messages.success(request, f'User {username} berhasil dihapus.')
        
        if current_profile.role == 'superuser':
            return redirect('accounts:create_client')
        else:
            return redirect('accounts:create_crew')
    else:
        messages.error(request, 'Anda tidak memiliki izin untuk menghapus user ini.')
        return redirect('dashboard:home')