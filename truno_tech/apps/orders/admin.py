from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['subtotal']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'tenant', 'customer_name', 'customer_phone', 'total_amount_display', 'total_qty', 'created_by', 'created_at']
    list_filter = ['tenant', 'created_at', 'created_by']
    search_fields = ['customer_name', 'customer_phone', 'tenant__name']
    readonly_fields = ['total_amount', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('tenant', 'created_by')

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'qty', 'unit_price_display', 'subtotal_display']
    list_filter = ['order__tenant', 'product__category']
    search_fields = ['product__name', 'order__customer_name']
    readonly_fields = ['subtotal']