from django import forms
from django.forms import inlineformset_factory
from .models import Order, OrderItem
from apps.products.models import Product

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['customer_name', 'customer_phone', 'customer_address']
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'customer_name': 'Nama Pelanggan',
            'customer_phone': 'No. Telepon Pelanggan',
            'customer_address': 'Alamat Pelanggan',
        }

class OrderItemForm(forms.ModelForm):
    product = forms.ModelChoiceField(
        queryset=Product.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control product-select'}),
        label='Produk'
    )
    qty = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control qty-input'}),
        label='Jumlah'
    )
    
    class Meta:
        model = OrderItem
        fields = ['product', 'qty']
    
    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        if tenant:
            self.fields['product'].queryset = Product.objects.filter(
                tenant=tenant,
                is_active=True,
                qty__gt=0
            ).select_related('category')
    
    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        qty = cleaned_data.get('qty')
        
        if product and qty:
            if product.qty < qty:
                raise forms.ValidationError(
                    f'Stok {product.name} tidak mencukupi. Stok tersedia: {product.qty}'
                )
        
        return cleaned_data

# Create formset for order items
OrderItemFormSet = inlineformset_factory(
    Order,
    OrderItem,
    form=OrderItemForm,
    extra=1,
    min_num=1,
    validate_min=True,
    can_delete=True
)