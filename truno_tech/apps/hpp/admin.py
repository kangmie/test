from django.contrib import admin
from .models import Bahan, HPP, HPPDetail

@admin.register(Bahan)
class BahanAdmin(admin.ModelAdmin):
    list_display = ['nama_bahan', 'harga_satuan_display', 'satuan', 'is_active', 'created_by', 'created_at']
    list_filter = ['is_active', 'created_at', 'created_by']
    search_fields = ['nama_bahan']
    readonly_fields = ['created_at', 'updated_at']

class HPPDetailInline(admin.TabularInline):
    model = HPPDetail
    extra = 0
    readonly_fields = ['subtotal']

@admin.register(HPP)
class HPPAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'periode', 'amount_total_display', 'created_by', 'created_at']
    list_filter = ['tenant', 'periode', 'created_at']
    search_fields = ['tenant__name', 'periode']
    readonly_fields = ['amount_total', 'created_at', 'updated_at']
    inlines = [HPPDetailInline]

@admin.register(HPPDetail)
class HPPDetailAdmin(admin.ModelAdmin):
    list_display = ['hpp', 'bahan', 'qty', 'harga_satuan_display', 'subtotal_display']
    list_filter = ['hpp__tenant', 'bahan']
    search_fields = ['bahan__nama_bahan', 'hpp__periode']