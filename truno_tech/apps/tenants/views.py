from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Tenant, TenantAccess
from .forms import TenantForm, TenantAccessForm


def check_client_permission(user):
    """User harus punya profile dan role 'client'."""
    return hasattr(user, 'userprofile') and user.userprofile.role == 'client'


@login_required
def tenant_list_view(request):
    if not check_client_permission(request.user):
        messages.error(request, 'Anda tidak memiliki akses untuk mengelola tenant.')
        return redirect('dashboard:home')

    tenants = Tenant.objects.filter(owner=request.user)
    return render(request, 'tenants/tenant_list.html', {'tenants': tenants})


@login_required
def tenant_create_view(request):
    if not check_client_permission(request.user):
        messages.error(request, 'Anda tidak memiliki akses untuk mengelola tenant.')
        return redirect('dashboard:home')

    if request.method == 'POST':
        form = TenantForm(request.POST, request.FILES)  # kalau ada upload logo dsb
        if form.is_valid():
            try:
                tenant = form.save(commit=False)
                # PENTING: set owner sebelum save (agar clean() punya owner_id)
                tenant.owner = request.user
                tenant.save()
                messages.success(request, f'Tenant {tenant.name} berhasil dibuat.')
                return redirect('tenants:list')
            except ValidationError as e:
                # full_clean() bisa raise ValidationError dari clean()
                messages.error(request, e.messages[0] if hasattr(e, 'messages') else str(e))
        else:
            messages.error(request, 'Periksa kembali data yang diisi.')
    else:
        form = TenantForm()

    return render(request, 'tenants/tenant_form.html', {
        'form': form,
        'title': 'Tambah Tenant Baru'
    })


@login_required
def tenant_edit_view(request, tenant_id):
    if not check_client_permission(request.user):
        messages.error(request, 'Anda tidak memiliki akses untuk mengelola tenant.')
        return redirect('dashboard:home')

    tenant = get_object_or_404(Tenant, id=tenant_id, owner=request.user)

    if request.method == 'POST':
        form = TenantForm(request.POST, request.FILES, instance=tenant)
        if form.is_valid():
            try:
                # owner sudah ada; tidak perlu diubah
                form.save()
                messages.success(request, f'Tenant {tenant.name} berhasil diupdate.')
                return redirect('tenants:list')
            except ValidationError as e:
                messages.error(request, e.messages[0] if hasattr(e, 'messages') else str(e))
        else:
            messages.error(request, 'Periksa kembali data yang diisi.')
    else:
        form = TenantForm(instance=tenant)

    return render(request, 'tenants/tenant_form.html', {
        'form': form,
        'title': f'Edit Tenant - {tenant.name}',
        'tenant': tenant
    })


@login_required
def tenant_detail_view(request, tenant_id):
    if not check_client_permission(request.user):
        messages.error(request, 'Anda tidak memiliki akses untuk mengelola tenant.')
        return redirect('dashboard:home')

    tenant = get_object_or_404(Tenant, id=tenant_id, owner=request.user)
    accesses = TenantAccess.objects.filter(tenant=tenant).select_related('crew')

    if request.method == 'POST':
        access_form = TenantAccessForm(request.POST, owner=request.user, tenant=tenant)
        if access_form.is_valid():
            try:
                with transaction.atomic():
                    access = access_form.save(commit=False)
                    access.tenant = tenant
                    access.granted_by = request.user
                    access.save()
                messages.success(request, 'Akses crew berhasil ditambahkan.')
                return redirect('tenants:detail', tenant_id=tenant.id)
            except ValidationError as e:
                messages.error(request, e.messages[0] if hasattr(e, 'messages') else str(e))
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
        else:
            messages.error(request, 'Periksa kembali data akses yang diisi.')
    else:
        access_form = TenantAccessForm(owner=request.user, tenant=tenant)

    return render(request, 'tenants/tenant_detail.html', {
        'tenant': tenant,
        'accesses': accesses,
        'access_form': access_form
    })


@login_required
def tenant_delete_view(request, tenant_id):
    if not check_client_permission(request.user):
        messages.error(request, 'Anda tidak memiliki akses untuk mengelola tenant.')
        return redirect('dashboard:home')

    tenant = get_object_or_404(Tenant, id=tenant_id, owner=request.user)
    tenant_name = tenant.name
    tenant.delete()
    messages.success(request, f'Tenant {tenant_name} berhasil dihapus.')
    return redirect('tenants:list')


@login_required
def remove_crew_access_view(request, tenant_id, access_id):
    if not check_client_permission(request.user):
        messages.error(request, 'Anda tidak memiliki akses untuk mengelola tenant.')
        return redirect('dashboard:home')

    tenant = get_object_or_404(Tenant, id=tenant_id, owner=request.user)
    access = get_object_or_404(TenantAccess, id=access_id, tenant=tenant)

    crew_name = access.crew.get_full_name() or access.crew.username
    access.delete()
    messages.success(request, f'Akses crew {crew_name} berhasil dihapus.')
    return redirect('tenants:detail', tenant_id=tenant.id)
