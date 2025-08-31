from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, F
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import datetime, timedelta

from apps.tenants.models import Tenant, TenantAccess
from apps.products.models import Product
from apps.orders.models import Order, OrderItem
from apps.hpp.models import HPP


def get_accessible_tenants(user):
    """Get tenants that user can access"""
    # reverse name default dari OneToOne(UserProfile.user) = 'userprofile'
    if not hasattr(user, 'userprofile'):
        return Tenant.objects.none()

    role = user.userprofile.role
    if role == 'client':
        return Tenant.objects.filter(owner=user)
    elif role == 'crew':
        # pastikan related_name di TenantAccess sesuai (mis. 'tenant_accesses')
        return Tenant.objects.filter(tenant_accesses__crew=user)
    return Tenant.objects.none()


@login_required
def dashboard_home_view(request):
    # validasi profile ada
    if not hasattr(request.user, 'userprofile'):
        messages.error(request, 'Profile tidak ditemukan.')
        return redirect('accounts:login')

    user_role = request.user.userprofile.role

    if user_role == 'superuser':
        # FIX: 'created_users' adalah queryset UserProfile, jadi filter langsung ke field 'role'
        return render(request, 'dashboard/superuser_dashboard.html', {
            'total_clients': request.user.created_users.filter(role='client').count()
        })

    # Tenants yang bisa diakses
    tenants = get_accessible_tenants(request.user)
    if not tenants.exists():
        return render(request, 'dashboard/no_access.html')

    # Rentang tanggal (30 hari terakhir)
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    # Statistik dasar
    stats = {
        'total_tenants': tenants.count(),
        'total_products': Product.objects.filter(tenant__in=tenants).count(),
        'total_orders': Order.objects.filter(tenant__in=tenants).count(),
        'total_revenue': Order.objects.filter(tenant__in=tenants).aggregate(
            total=Sum('total_amount')
        )['total'] or 0,
    }

    # Order terbaru
    recent_orders = (
        Order.objects
        .filter(tenant__in=tenants)
        .select_related('tenant')
        .order_by('-created_at')[:5]
    )

    # Produk stok menipis
    low_stock_products = (
        Product.objects
        .filter(tenant__in=tenants, qty__lte=5, is_active=True)
        .select_related('tenant', 'category')
        .order_by('qty')[:5]
    )

    # Top products (khusus client)
    top_products = None
    if user_role == 'client':
        top_products = (
            OrderItem.objects
            .filter(order__tenant__in=tenants, order__created_at__gte=start_date)
            .values('product__name', 'product__tenant__name')
            .annotate(
                total_qty=Sum('qty'),
                total_revenue=Sum(F('qty') * F('unit_price'))
            )
            .order_by('-total_revenue')[:5]
        )

    context = {
        'user_role': user_role,
        'stats': stats,
        'recent_orders': recent_orders,
        'low_stock_products': low_stock_products,
        'top_products': top_products,
    }
    return render(request, 'dashboard/dashboard.html', context)


@login_required
def tenant_analytics_view(request, tenant_id=None):
    """Detailed analytics for specific tenant (client only)"""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'client':
        messages.error(request, 'Anda tidak memiliki akses ke analisis.')
        return redirect('dashboard:home')

    tenants = Tenant.objects.filter(owner=request.user)

    if tenant_id:
        tenant = tenants.filter(id=tenant_id).first()
        if not tenant:
            messages.error(request, 'Tenant tidak ditemukan.')
            return redirect('dashboard:home')
    else:
        tenant = tenants.first()
        if not tenant:
            messages.error(request, 'Tidak ada tenant yang tersedia.')
            return redirect('dashboard:home')

    # Rentang tanggal (30 hari terakhir)
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    # Data order & revenue
    orders = Order.objects.filter(tenant=tenant, created_at__date__gte=start_date)

    # Daily revenue — ganti .extra() ke TruncDate (lebih aman & portable)
    daily_revenue = (
        orders
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(
            revenue=Sum('total_amount'),
            order_count=Count('id')
        )
        .order_by('day')
    )

    # Top products untuk tenant ini
    top_products = (
        OrderItem.objects
        .filter(order__tenant=tenant, order__created_at__date__gte=start_date)
        .values('product__name')
        .annotate(
            total_qty=Sum('qty'),
            total_revenue=Sum(F('qty') * F('unit_price'))
        )
        .order_by('-total_revenue')[:10]
    )

    # Analisis pelanggan
    customer_analysis = (
        orders
        .exclude(customer_name__isnull=True, customer_name__exact='')
        .values('customer_name', 'customer_phone')
        .annotate(
            order_count=Count('id'),
            total_spent=Sum('total_amount')
        )
        .order_by('-total_spent')[:10]
    )

    # Data HPP
    hpp_records = HPP.objects.filter(tenant=tenant).order_by('-periode')[:6]

    # Hitung margin jika ada data HPP
    margin_data = []
    for hpp in hpp_records:
        period_start = datetime.strptime(hpp.periode, '%Y-%m').date()
        period_end = (period_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)

        period_revenue = (
            Order.objects
            .filter(
                tenant=tenant,
                created_at__date__gte=period_start,
                created_at__date__lte=period_end
            )
            .aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        )

        margin = period_revenue - hpp.amount_total
        margin_percentage = (margin / period_revenue * 100) if period_revenue > 0 else 0

        margin_data.append({
            'periode': hpp.periode,
            'revenue': period_revenue,
            'hpp': hpp.amount_total,
            'margin': margin,
            'margin_percentage': margin_percentage,
        })

    context = {
        'tenant': tenant,
        'tenants': tenants,
        'daily_revenue': daily_revenue,
        'top_products': top_products,
        'customer_analysis': customer_analysis,
        'margin_data': margin_data,
        'date_range': f"{start_date} - {end_date}",
    }
    return render(request, 'dashboard/tenant_analytics.html', context)
