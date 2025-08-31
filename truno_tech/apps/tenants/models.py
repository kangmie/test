from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Tenant(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tenants')
    name = models.CharField(max_length=200)
    address = models.TextField()
    phone = models.CharField(max_length=15)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        # JANGAN dereference owner jika belum ada
        if self.owner_id:
            return f"{self.name} - {self.owner.username}"
        return self.name

    def clean(self):
        """
        Validasi limit tenant untuk owner (berdasar UserProfile.max_tenants).
        Hindari akses relasi jika owner belum diisi.
        """
        # Saat create dengan form.save(commit=False), owner bisa belum ter-set.
        if not self.owner_id:
            return

        # Ambil profil dengan aman
        userprofile = getattr(self.owner, 'userprofile', None)
        if not userprofile:
            return

        max_tenants = userprofile.max_tenants
        # Hitung tenant milik owner saat ini
        current_count = Tenant.objects.filter(owner=self.owner).count()

        # Jika create (belum punya pk) dan bakal melewati batas
        if not self.pk and current_count >= max_tenants:
            raise ValidationError(f'Maksimal {max_tenants} tenant yang dapat dibuat.')

    def save(self, *args, **kwargs):
        # full_clean() memanggil clean(); sudah aman dengan guard di atas
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'tenants'
        ordering = ['-created_at']


class TenantAccess(models.Model):
    """Akses crew ke tenant tertentu"""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='tenant_accesses')
    crew = models.ForeignKey(User, on_delete=models.CASCADE, related_name='crew_accesses')
    granted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='granted_accesses')
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tenant_accesses'
        unique_together = ['tenant', 'crew']

    def __str__(self):
        # Guard defensif (kalau salah satu belum ada)
        tenant_name = self.tenant.name if getattr(self, 'tenant_id', None) else '-'
        crew_name = self.crew.username if getattr(self, 'crew_id', None) else '-'
        return f"{crew_name} -> {tenant_name}"
