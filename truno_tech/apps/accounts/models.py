from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator, MaxLengthValidator

class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('superuser', 'Super User'),
        ('client', 'Client/Owner'),
        ('crew', 'Crew'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    max_tenants = models.IntegerField(default=1, help_text="Maksimal tenant yang dapat dibuat (hanya untuk client)")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_users')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    class Meta:
        db_table = 'user_profiles'