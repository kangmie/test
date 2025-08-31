from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from apps.tenants.models import Tenant, TenantAccess
from apps.products.models import Product
from .models import Order, OrderItem
from .forms import OrderForm, OrderItemFormSet

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

@login_required
def order_list_view(request):
    tenants = get_accessible_tenants(request.user)
    orders = Order.objects.filter(tenant__in=tenants).select_related('tenant')
    
    # Filter by tenant if specified
    tenant_filter = request.GET.get('tenant')
    if tenant_filter:
        orders = orders.filter(tenant_id=tenant_filter)
    
    return render(request, 'orders/order_list.html', {
        'orders': orders,
        'tenants': tenants,
        'selected_tenant': int(tenant_filter) if tenant_filter else None
    })

@login_required
def order_create_view(request):
    tenants = get_accessible_tenants(request.user)
    
    if request.method == 'POST':
        tenant_id = request.POST.get('tenant')
        tenant = get_object_or_404(Tenant, id=tenant_id) if tenant_id else None
        
        if not tenant or not check_tenant_access(request.user, tenant):
            messages.error(request, 'Anda tidak memiliki akses ke tenant ini.')
            return redirect('orders:list')
        
        form = OrderForm(request.POST)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    order = form.save(commit=False)
                    order.tenant = tenant
                    order.created_by = request.user
                    order.total_amount = 0  # Will be calculated after items are saved
                    order.save()
                    
                    # Process order items from POST data
                    items_data = []
                    product_ids = request.POST.getlist('product_id[]')
                    quantities = request.POST.getlist('qty[]')
                    
                    total_amount = 0
                    
                    for product_id, qty_str in zip(product_ids, quantities):
                        if product_id and qty_str:
                            try:
                                product = Product.objects.get(id=product_id, tenant=tenant)
                                qty = int(qty_str)
                                
                                if product.qty >= qty:
                                    order_item = OrderItem(
                                        order=order,
                                        product=product,
                                        qty=qty,
                                        unit_price=product.price
                                    )
                                    order_item.save()  # This will reduce stock automatically
                                    total_amount += order_item.subtotal
                                else:
                                    raise Exception(f'Stok {product.name} tidak mencukupi')
                            except (Product.DoesNotExist, ValueError) as e:
                                raise Exception(f'Error pada item: {str(e)}')
                    
                    if total_amount == 0:
                        raise Exception('Order harus memiliki minimal satu item')
                    
                    # Update total amount
                    order.total_amount = total_amount
                    order.save()
                    
                    messages.success(request, f'Order #{order.id} berhasil dibuat.')
                    return redirect('orders:detail', order_id=order.id)
                    
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
    else:
        form = OrderForm()
    
    return render(request, 'orders/order_form.html', {
        'form': form,
        'tenants': tenants,
        'title': 'Buat Order Baru'
    })

@login_required
def order_detail_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if not check_tenant_access(request.user, order.tenant):
        messages.error(request, 'Anda tidak memiliki akses ke order ini.')
        return redirect('orders:list')
    
    order_items = order.order_items.select_related('product', 'product__category')
    
    return render(request, 'orders/order_detail.html', {
        'order': order,
        'order_items': order_items
    })

@login_required
def get_products_by_tenant(request):
    """AJAX endpoint to get products by tenant"""
    tenant_id = request.GET.get('tenant_id')
    if tenant_id:
        tenant = get_object_or_404(Tenant, id=tenant_id)
        if check_tenant_access(request.user, tenant):
            products = Product.objects.filter(
                tenant=tenant,
                is_active=True,
                qty__gt=0
            ).values('id', 'name', 'sku', 'price', 'qty')
            
            return JsonResponse({'products': list(products)})
    
    return JsonResponse({'products': []})