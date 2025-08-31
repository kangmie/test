from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from apps.tenants.models import Tenant, TenantAccess
from .models import ProductCategory, Product
from .forms import ProductCategoryForm, ProductForm, StockAdjustmentForm

def get_accessible_tenants(user):
    """Get tenants that user can access"""
    if not hasattr(user, 'userprofile'):
        return Tenant.objects.none()
    
    if user.userprofile.role == 'client':
        return Tenant.objects.filter(owner=user)
    elif user.userprofile.role == 'crew':
        return Tenant.objects.filter(tenant_accesses__crew=user)
    return Tenant.objects.none()

def check_tenant_access(user, tenant):
    """Check if user has access to tenant"""
    if not hasattr(user, 'userprofile'):
        return False
    
    if user.userprofile.role == 'client':
        return tenant.owner == user
    elif user.userprofile.role == 'crew':
        return TenantAccess.objects.filter(tenant=tenant, crew=user).exists()
    return False

# CATEGORY VIEWS
@login_required
def product_delete_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if not check_tenant_access(request.user, product.tenant):
        messages.error(request, 'Anda tidak memiliki akses ke produk ini.')
        return redirect('products:list')
    
    product_name = product.name
    product.delete()
    messages.success(request, f'Produk {product_name} berhasil dihapus.')
    return redirect('products:list')

@login_required
def product_stock_adjustment_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if not check_tenant_access(request.user, product.tenant):
        messages.error(request, 'Anda tidak memiliki akses ke produk ini.')
        return redirect('products:list')
    
    if request.method == 'POST':
        form = StockAdjustmentForm(request.POST)
        if form.is_valid():
            adjustment_type = form.cleaned_data['adjustment_type']
            quantity = form.cleaned_data['quantity']
            
            old_qty = product.qty
            
            if adjustment_type == 'add':
                product.add_stock(quantity)
                action = f'Menambah {quantity} stok'
            elif adjustment_type == 'reduce':
                if product.qty >= quantity:
                    product.qty -= quantity
                    product.save()
                    action = f'Mengurangi {quantity} stok'
                else:
                    messages.error(request, 'Stok tidak mencukupi untuk dikurangi.')
                    form = StockAdjustmentForm()
                    return render(request, 'products/stock_adjustment.html', {
                        'form': form,
                        'product': product
                    })
            else:  # set
                product.qty = quantity
                product.save()
                action = f'Mengatur stok menjadi {quantity}'
            
            messages.success(request, f'{action}. Stok berubah dari {old_qty} menjadi {product.qty}.')
            return redirect('products:list')
    else:
        form = StockAdjustmentForm()
    
    return render(request, 'products/stock_adjustment.html', {
        'form': form,
        'product': product
    })

@login_required
def get_categories_by_tenant(request):
    """AJAX endpoint to get categories by tenant"""
    tenant_id = request.GET.get('tenant_id')
    if tenant_id:
        tenant = get_object_or_404(Tenant, id=tenant_id)
        if check_tenant_access(request.user, tenant):
            categories = ProductCategory.objects.filter(tenant=tenant).values('id', 'name')
            return JsonResponse({'categories': list(categories)})
    
    return JsonResponse({'categories': []})
def category_list_view(request):
    tenants = get_accessible_tenants(request.user)
    categories = ProductCategory.objects.filter(tenant__in=tenants).select_related('tenant')
    
    return render(request, 'products/category_list.html', {
        'categories': categories,
        'tenants': tenants
    })

@login_required
def category_create_view(request):
    tenants = get_accessible_tenants(request.user)
    
    if request.method == 'POST':
        form = ProductCategoryForm(request.POST)
        tenant_id = request.POST.get('tenant')
        
        if form.is_valid() and tenant_id:
            tenant = get_object_or_404(Tenant, id=tenant_id)
            if check_tenant_access(request.user, tenant):
                try:
                    category = form.save(commit=False)
                    category.tenant = tenant
                    category.created_by = request.user
                    category.save()
                    messages.success(request, f'Kategori {category.name} berhasil dibuat.')
                    return redirect('products:category_list')
                except Exception as e:
                    messages.error(request, f'Error: {str(e)}')
            else:
                messages.error(request, 'Anda tidak memiliki akses ke tenant ini.')
    else:
        form = ProductCategoryForm()
    
    return render(request, 'products/category_form.html', {
        'form': form,
        'tenants': tenants,
        'title': 'Tambah Kategori Baru'
    })

@login_required
def category_edit_view(request, category_id):
    category = get_object_or_404(ProductCategory, id=category_id)
    
    if not check_tenant_access(request.user, category.tenant):
        messages.error(request, 'Anda tidak memiliki akses ke kategori ini.')
        return redirect('products:category_list')
    
    if request.method == 'POST':
        form = ProductCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f'Kategori {category.name} berhasil diupdate.')
            return redirect('products:category_list')
    else:
        form = ProductCategoryForm(instance=category)
    
    return render(request, 'products/category_form.html', {
        'form': form,
        'category': category,
        'title': f'Edit Kategori - {category.name}'
    })

@login_required
def category_delete_view(request, category_id):
    category = get_object_or_404(ProductCategory, id=category_id)
    
    if not check_tenant_access(request.user, category.tenant):
        messages.error(request, 'Anda tidak memiliki akses ke kategori ini.')
        return redirect('products:category_list')
    
    category_name = category.name
    category.delete()
    messages.success(request, f'Kategori {category_name} berhasil dihapus.')
    return redirect('products:category_list')

# PRODUCT VIEWS
@login_required
def product_list_view(request):
    tenants = get_accessible_tenants(request.user)
    products = Product.objects.filter(tenant__in=tenants).select_related('tenant', 'category')
    
    # Filter by tenant if specified
    tenant_filter = request.GET.get('tenant')
    if tenant_filter:
        products = products.filter(tenant_id=tenant_filter)
    
    return render(request, 'products/product_list.html', {
        'products': products,
        'tenants': tenants,
        'selected_tenant': int(tenant_filter) if tenant_filter else None
    })

@login_required
def product_create_view(request):
    tenants = get_accessible_tenants(request.user)
    
    if request.method == 'POST':
        tenant_id = request.POST.get('tenant')
        tenant = get_object_or_404(Tenant, id=tenant_id) if tenant_id else None
        
        form = ProductForm(request.POST, tenant=tenant)
        
        if form.is_valid() and tenant and check_tenant_access(request.user, tenant):
            try:
                product = form.save(commit=False)
                product.tenant = tenant
                product.created_by = request.user
                product.save()
                messages.success(request, f'Produk {product.name} berhasil dibuat.')
                return redirect('products:list')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
    else:
        form = ProductForm()
    
    return render(request, 'products/product_form.html', {
        'form': form,
        'tenants': tenants,
        'title': 'Tambah Produk Baru'
    })

@login_required
def product_edit_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if not check_tenant_access(request.user, product.tenant):
        messages.error(request, 'Anda tidak memiliki akses ke produk ini.')
        return redirect('products:list')
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product, tenant=product.tenant)
        if form.is_valid():
            form.save()
            messages.success(request, f'Produk {product.name} berhasil diupdate.')
            return redirect('products:list')
    else:
        form = ProductForm(instance=product, tenant=product.tenant)
    
    return render(request, 'products/product_form.html', {
        'form': form,
        'product': product,
        'title': f'Edit Produk - {product.name}'
    })
