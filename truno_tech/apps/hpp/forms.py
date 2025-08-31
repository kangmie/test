from django import forms
from django.forms import inlineformset_factory
from .models import Bahan, HPP, HPPDetail

class BahanForm(forms.ModelForm):
    harga_satuan = forms.IntegerField(
        label='Harga Satuan (Rp)',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Bahan
        fields = ['nama_bahan', 'harga_satuan', 'satuan', 'keterangan']
        widgets = {
            'nama_bahan': forms.TextInput(attrs={'class': 'form-control'}),
            'satuan': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'kg, gram, liter, dll'}),
            'keterangan': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'nama_bahan': 'Nama Bahan',
            'harga_satuan': 'Harga Satuan (Rp)',
            'satuan': 'Satuan',
            'keterangan': 'Keterangan',
        }

class HPPForm(forms.ModelForm):
    periode = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'type': 'month'}),
        label='Periode (Bulan-Tahun)'
    )
    
    class Meta:
        model = HPP
        fields = ['periode', 'catatan']
        widgets = {
            'catatan': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'periode': 'Periode',
            'catatan': 'Catatan',
        }

class HPPDetailForm(forms.ModelForm):
    bahan = forms.ModelChoiceField(
        queryset=Bahan.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control bahan-select'}),
        label='Bahan'
    )
    qty = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control qty-input', 'step': '0.01'}),
        label='Jumlah'
    )
    
    class Meta:
        model = HPPDetail
        fields = ['bahan', 'qty']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['bahan'].queryset = Bahan.objects.filter(is_active=True)

# Create formset for HPP details
HPPDetailFormSet = inlineformset_factory(
    HPP,
    HPPDetail,
    form=HPPDetailForm,
    extra=1,
    min_num=1,
    validate_min=True,
    can_delete=True
)