from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from apps.tenants.models import Tenant
from .models import Bahan, HPP, HPPDetail
from .forms import BahanForm, HPPForm, HPPDetailFormSet

def check_client_permission(user):
    """Helper function to check if user is client (only clients can manage HPP)"""
    return hasattr(user, 'userprofile') and user.userprofile.role == 'client'

# BAHAN VIEWS
@login_required
def bahan_list_view(request):
    if not check_client_permission(request.user):
        messages.error(request, 'Anda tidak memiliki akses untuk mengelola bahan.')
        return redirect('dashboard:home')
    
    bahan_list = Bahan.objects.filter(created_by=request.user, is_active=True)
    
    return render(request, 'hpp/bahan_list.html', {
        'bahan_list': bahan_list
    })

@login_required
def bahan_create_view(request):
    if not check_client_permission(request.user):
        messages.error(request, 'Anda tidak memiliki akses untuk mengelola bahan.')
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        form = BahanForm(request.POST)
        if form.is_valid():
            bahan = form.save(commit=False)
            bahan.created_by = request.user
            bahan.save()
            messages.success(request, f'Bahan {bahan.nama_bahan} berhasil dibuat.')
            return redirect('hpp:bahan_list')
    else:
        form = BahanForm()
    
    return render(request, 'hpp/bahan_form.html', {
        'form': form,
        'title': 'Tambah Bahan Baru'
    })

@login_required
def bahan_edit_view(request, bahan_id):
    if not check_client_permission(request.user):
        messages.error(request, 'Anda tidak memiliki akses untuk mengelola bahan.')
        return redirect('dashboard:home')
    
    bahan = get_object_or_404(Bahan, id=bahan_id, created_by=request.user)
    
    if request.method == 'POST':
        form = BahanForm(request.POST, instance=bahan)
        if form.is_valid():
            form.save()
            messages.success(request, f'Bahan {bahan.nama_bahan} berhasil diupdate.')
            return redirect('hpp:bahan_list')
    else:
        form = BahanForm(instance=bahan)
    
    return render(request, 'hpp/bahan_form.html', {
        'form': form,
        'bahan': bahan,
        'title': f'Edit Bahan - {bahan.nama_bahan}'
    })

@login_required
def bahan_delete_view(request, bahan_id):
    if not check_client_permission(request.user):
        messages.error(request, 'Anda tidak memiliki akses untuk mengelola bahan.')
        return redirect('dashboard:home')
    
    bahan = get_object_or_404(Bahan, id=bahan_id, created_by=request.user)
    
    # Soft delete
    bahan.is_active = False
    bahan.save()
    messages.success(request, f'Bahan {bahan.nama_bahan} berhasil dihapus.')
    return redirect('hpp:bahan_list')

# HPP VIEWS
@login_required
def hpp_list_view(request):
    if not check_client_permission(request.user):
        messages.error(request, 'Anda tidak memiliki akses untuk mengelola HPP.')
        return redirect('dashboard:home')
    
    tenants = Tenant.objects.filter(owner=request.user)
    hpp_records = HPP.objects.filter(tenant__owner=request.user).select_related('tenant')
    
    # Filter by tenant if specified
    tenant_filter = request.GET.get('tenant')
    if tenant_filter:
        hpp_records = hpp_records.filter(tenant_id=tenant_filter)
    
    return render(request, 'hpp/hpp_list.html', {
        'hpp_records': hpp_records,
        'tenants': tenants,
        'selected_tenant': int(tenant_filter) if tenant_filter else None
    })

@login_required
def hpp_create_view(request):
    if not check_client_permission(request.user):
        messages.error(request, 'Anda tidak memiliki akses untuk mengelola HPP.')
        return redirect('dashboard:home')
    
    tenants = Tenant.objects.filter(owner=request.user)
    
    if request.method == 'POST':
        tenant_id = request.POST.get('tenant')
        tenant = get_object_or_404(Tenant, id=tenant_id, owner=request.user) if tenant_id else None
        
        if not tenant:
            messages.error(request, 'Pilih tenant terlebih dahulu.')
            return render(request, 'hpp/hpp_form.html', {
                'form': HPPForm(),
                'tenants': tenants,
                'title': 'Buat HPP Baru'
            })
        
        form = HPPForm(request.POST)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    hpp = form.save(commit=False)
                    hpp.tenant = tenant
                    hpp.created_by = request.user
                    hpp.amount_total = 0
                    hpp.save()
                    
                    # Process HPP details from POST data
                    bahan_ids = request.POST.getlist('bahan_id[]')
                    quantities = request.POST.getlist('qty[]')
                    
                    total_amount = 0
                    
                    for bahan_id, qty_str in zip(bahan_ids, quantities):
                        if bahan_id and qty_str:
                            try:
                                bahan = Bahan.objects.get(id=bahan_id)
                                qty = float(qty_str)
                                
                                hpp_detail = HPPDetail(
                                    hpp=hpp,
                                    bahan=bahan,
                                    qty=qty
                                )
                                hpp_detail.save()  # This will calculate subtotal automatically
                                total_amount += hpp_detail.subtotal
                            except (Bahan.DoesNotExist, ValueError) as e:
                                raise Exception(f'Error pada bahan: {str(e)}')
                    
                    if total_amount == 0:
                        raise Exception('HPP harus memiliki minimal satu bahan')
                    
                    # Update total amount
                    hpp.amount_total = total_amount
                    hpp.save()
                    
                    messages.success(request, f'HPP {hpp.periode} untuk {hpp.tenant.name} berhasil dibuat.')
                    return redirect('hpp:detail', hpp_id=hpp.id)
                    
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
    else:
        form = HPPForm()
    
    return render(request, 'hpp/hpp_form.html', {
        'form': form,
        'tenants': tenants,
        'title': 'Buat HPP Baru'
    })

@login_required
def hpp_detail_view(request, hpp_id):
    if not check_client_permission(request.user):
        messages.error(request, 'Anda tidak memiliki akses untuk mengelola HPP.')
        return redirect('dashboard:home')
    
    hpp = get_object_or_404(HPP, id=hpp_id, tenant__owner=request.user)
    hpp_details = hpp.hpp_details.select_related('bahan')
    
    return render(request, 'hpp/hpp_detail.html', {
        'hpp': hpp,
        'hpp_details': hpp_details
    })

@login_required
def get_bahan_data(request):
    """AJAX endpoint to get bahan data"""
    if check_client_permission(request.user):
        bahan_list = Bahan.objects.filter(
            created_by=request.user,
            is_active=True
        ).values('id', 'nama_bahan', 'harga_satuan', 'satuan')
        
        return JsonResponse({'bahan': list(bahan_list)})
    
    return JsonResponse({'bahan': []})