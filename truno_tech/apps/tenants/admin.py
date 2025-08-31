from django.contrib import admin
from .models import Tenant, TenantAccess

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'phone', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'owner']
    search_fields = ['name', 'owner__username', 'phone']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(TenantAccess)
class TenantAccessAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'crew', 'granted_by', 'granted_at']
    list_filter = ['granted_at', 'tenant__owner']
    search_fields = ['tenant__name', 'crew__username']