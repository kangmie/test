from django.db import models
from django.contrib.auth.models import User
from apps.tenants.models import Tenant

class Bahan(models.Model):
    """Master data bahan untuk perhitungan HPP"""
    nama_bahan = models.CharField(max_length=100)
    harga_satuan = models.BigIntegerField()  # Price per unit in rupiah
    satuan = models.CharField(max_length=20, default='kg')  # Unit: kg, gram, liter, etc
    keterangan = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.nama_bahan} - {self.harga_satuan_display}/{self.satuan}"
    
    @property
    def harga_satuan_display(self):
        """Display price in rupiah format"""
        return f"Rp {self.harga_satuan:,}"
    
    class Meta:
        db_table = 'bahan'
        ordering = ['nama_bahan']
        verbose_name_plural = 'Bahan'

class HPP(models.Model):
    """Main HPP record per tenant per period"""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='hpp_records')
    periode = models.CharField(max_length=7, help_text="Format: YYYY-MM")  # e.g., "2024-01"
    amount_total = models.BigIntegerField()  # Total HPP amount
    catatan = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"HPP {self.tenant.name} - {self.periode}"
    
    @property
    def amount_total_display(self):
        """Display total amount in rupiah format"""
        return f"Rp {self.amount_total:,}"
    
    def calculate_total(self):
        """Calculate total amount from HPP details"""
        total = self.hpp_details.aggregate(
            total=models.Sum('subtotal')
        )['total'] or 0
        return total
    
    def save(self, *args, **kwargs):
        if not self.amount_total:
            # Calculate total after saving details
            super().save(*args, **kwargs)
            self.amount_total = self.calculate_total()
            super().save(update_fields=['amount_total'])
        else:
            super().save(*args, **kwargs)
    
    class Meta:
        db_table = 'hpp'
        unique_together = ['tenant', 'periode']
        ordering = ['-periode']

class HPPDetail(models.Model):
    """HPP detail components (unit cost breakdown)"""
    hpp = models.ForeignKey(HPP, on_delete=models.CASCADE, related_name='hpp_details')
    bahan = models.ForeignKey(Bahan, on_delete=models.CASCADE)
    qty = models.DecimalField(max_digits=10, decimal_places=2)  # Quantity used
    harga_satuan = models.BigIntegerField()  # Price per unit at time of record
    subtotal = models.BigIntegerField()  # qty * harga_satuan
    
    def __str__(self):
        return f"{self.bahan.nama_bahan} - {self.qty} {self.bahan.satuan}"
    
    @property
    def harga_satuan_display(self):
        """Display unit price in rupiah format"""
        return f"Rp {self.harga_satuan:,}"
    
    @property
    def subtotal_display(self):
        """Display subtotal in rupiah format"""
        return f"Rp {self.subtotal:,}"
    
    def save(self, *args, **kwargs):
        # Set price from bahan's current price if not set
        if not self.harga_satuan:
            self.harga_satuan = self.bahan.harga_satuan
        
        # Calculate subtotal
        self.subtotal = int(float(self.qty) * self.harga_satuan)
        
        super().save(*args, **kwargs)
        
        # Update HPP total
        self.hpp.amount_total = self.hpp.calculate_total()
        self.hpp.save(update_fields=['amount_total'])
    
    class Meta:
        db_table = 'hpp_details'