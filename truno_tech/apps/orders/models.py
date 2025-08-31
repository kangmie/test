from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from apps.tenants.models import Tenant
from apps.products.models import Product

class Order(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='orders')
    customer_name = models.CharField(max_length=200, blank=True, null=True)
    customer_phone = models.CharField(max_length=15, blank=True, null=True)
    customer_address = models.TextField(blank=True, null=True)
    total_amount = models.BigIntegerField()  # Total amount in cents/rupiah
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order #{self.id} - {self.tenant.name} - {self.total_amount_display}"
    
    @property
    def total_amount_display(self):
        """Display total amount in rupiah format"""
        return f"Rp {self.total_amount:,}"
    
    @property
    def total_qty(self):
        """Total quantity of all items"""
        return self.order_items.aggregate(models.Sum('qty'))['qty__sum'] or 0
    
    def calculate_total(self):
        """Calculate total amount from order items"""
        total = self.order_items.aggregate(
            total=models.Sum(models.F('qty') * models.F('unit_price'))
        )['total'] or 0
        return total
    
    def save(self, *args, **kwargs):
        if not self.total_amount:
            self.total_amount = self.calculate_total()
        super().save(*args, **kwargs)
    
    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    qty = models.IntegerField()
    unit_price = models.BigIntegerField()  # Price per item at time of order
    subtotal = models.BigIntegerField()  # qty * unit_price
    
    def __str__(self):
        return f"{self.product.name} x {self.qty}"
    
    @property
    def unit_price_display(self):
        """Display unit price in rupiah format"""
        return f"Rp {self.unit_price:,}"
    
    @property
    def subtotal_display(self):
        """Display subtotal in rupiah format"""
        return f"Rp {self.subtotal:,}"
    
    def clean(self):
        # Check if product has enough stock
        if self.product and self.qty:
            if self.product.qty < self.qty:
                raise ValidationError(f'Stok {self.product.name} tidak mencukupi. Stok tersedia: {self.product.qty}')
    
    def save(self, *args, **kwargs):
        self.full_clean()
        
        # Set unit price from product's current price
        if not self.unit_price:
            self.unit_price = self.product.price
        
        # Calculate subtotal
        self.subtotal = self.qty * self.unit_price
        
        # Check if this is a new order item (reduce stock)
        is_new = self.pk is None
        
        super().save(*args, **kwargs)
        
        # Reduce product stock for new items
        if is_new:
            self.product.reduce_stock(self.qty)
    
    class Meta:
        db_table = 'order_items'