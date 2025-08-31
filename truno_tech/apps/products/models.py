from django.db import models
from django.contrib.auth.models import User
from apps.tenants.models import Tenant

class ProductCategory(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.tenant.name}"
    
    class Meta:
        db_table = 'product_categories'
        unique_together = ['tenant', 'name']
        ordering = ['name']

class Product(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, related_name='products')
    sku = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    qty = models.IntegerField(default=0)
    price = models.BigIntegerField()  # Price in cents/rupiah
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.sku})"
    
    @property
    def price_display(self):
        """Display price in rupiah format"""
        return f"Rp {self.price:,}"
    
    def reduce_stock(self, quantity):
        """Reduce stock when order is made"""
        if self.qty >= quantity:
            self.qty -= quantity
            self.save()
            return True
        return False
    
    def add_stock(self, quantity):
        """Add stock"""
        self.qty += quantity
        self.save()
    
    class Meta:
        db_table = 'products'
        unique_together = ['tenant', 'sku']
        ordering = ['name']