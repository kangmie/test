from django import forms
from .models import ProductCategory, Product

class ProductCategoryForm(forms.ModelForm):
    class Meta:
        model = ProductCategory
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'name': 'Nama Kategori',
            'description': 'Deskripsi',
        }

class ProductForm(forms.ModelForm):
    price = forms.IntegerField(
        label='Harga (Rp)',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Product
        fields = ['category', 'sku', 'name', 'description', 'qty', 'price']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'sku': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'qty': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'category': 'Kategori',
            'sku': 'SKU',
            'name': 'Nama Produk',
            'description': 'Deskripsi',
            'qty': 'Stok',
            'price': 'Harga (Rp)',
        }
    
    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        if tenant:
            self.fields['category'].queryset = ProductCategory.objects.filter(tenant=tenant)

class StockAdjustmentForm(forms.Form):
    ADJUSTMENT_TYPES = [
        ('add', 'Tambah Stok'),
        ('reduce', 'Kurangi Stok'),
        ('set', 'Set Stok'),
    ]
    
    adjustment_type = forms.ChoiceField(
        choices=ADJUSTMENT_TYPES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Jenis Penyesuaian'
    )
    quantity = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Jumlah'
    )
    notes = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Catatan (opsional)'}),
        label='Catatan'
    )