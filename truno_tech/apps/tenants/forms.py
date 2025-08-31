from django import forms
from django.contrib.auth.models import User

from .models import Tenant, TenantAccess


class TenantForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ['name', 'address', 'phone']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'Nama Tenant',
            'address': 'Alamat',
            'phone': 'No. Telepon',
        }


class TenantAccessForm(forms.ModelForm):
    crew = forms.ModelChoiceField(
        queryset=User.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Pilih Crew',
        required=True,
        empty_label='— Pilih crew —'
    )

    class Meta:
        model = TenantAccess
        fields = ['crew']

    def __init__(self, *args, **kwargs):
        # owner & tenant DIWAJIBKAN saat pakai form ini
        self.owner = kwargs.pop('owner', None)
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

        qs = User.objects.none()
        if self.owner is not None:
            # Crew yang dibuat oleh owner (lewat UserProfile.created_by = owner)
            # dan belum punya akses ke tenant ini
            existing_ids = []
            if self.tenant is not None:
                existing_ids = (
                    TenantAccess.objects
                    .filter(tenant=self.tenant)
                    .values_list('crew_id', flat=True)
                )

            qs = (
                User.objects
                .filter(userprofile__role='crew', userprofile__created_by=self.owner)
                .exclude(id__in=existing_ids)
                .order_by('username')
            )

        self.fields['crew'].queryset = qs

        # Jika tak ada kandidat crew, kasih hint di help_text
        if not qs.exists():
            self.fields['crew'].help_text = 'Tidak ada crew yang tersedia untuk ditambahkan.'

    def clean_crew(self):
        crew = self.cleaned_data.get('crew')

        # Validasi defensif: pastikan owner/tenant dikirim ke form
        if self.owner is None or self.tenant is None:
            raise forms.ValidationError('Konfigurasi form tidak lengkap (owner/tenant).')

        # Pastikan crew valid: role = crew & created_by = owner
        if not hasattr(crew, 'userprofile'):
            raise forms.ValidationError('User yang dipilih tidak memiliki profil.')

        if crew.userprofile.role != 'crew':
            raise forms.ValidationError('User yang dipilih bukan crew.')

        if crew.userprofile.created_by_id != self.owner.id:
            raise forms.ValidationError('Crew ini tidak terdaftar di bawah akun Anda.')

        # Pastikan belum punya akses ke tenant ini
        if TenantAccess.objects.filter(tenant=self.tenant, crew=crew).exists():
            raise forms.ValidationError('Crew ini sudah memiliki akses ke tenant tersebut.')

        return crew
