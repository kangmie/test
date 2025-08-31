from django.contrib import admin
from .models import ProductCategory, Product

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'tenant', 'created_by', 'created_at']
    list_filter = ['tenant', 'created_at']
    search_fields = ['name', 'tenant__name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'category', 'tenant', 'qty', 'price', 'is_active', 'created_at']
    list_filter = ['is_active', 'tenant', 'category', 'created_at']
    search_fields = ['name', 'sku', 'tenant__name']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['qty', 'price', 'is_active']