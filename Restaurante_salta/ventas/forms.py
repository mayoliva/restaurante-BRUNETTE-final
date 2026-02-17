from django import forms
from .models import Venta, VentaProducto
from caja.models import Transaction, Caja  # Importa el modelo Transaction desde caja.models

class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ['customer_name', 'tipo_pago']  # Incluye otros campos relevantes

    def __init__(self, *args, **kwargs):
        super(VentaForm, self).__init__(*args, **kwargs)
        self.fields['customer_name'].required = True

class VentaProductoForm(forms.ModelForm):
    class Meta:
        model = VentaProducto
        fields = ['producto', 'cantidad']

VentaProductoFormSet = forms.inlineformset_factory(
    Venta,
    VentaProducto,
    form=VentaProductoForm,
    extra=1,
    can_delete=True
)

class TransaccionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['amount', 'caja']  # Excluir el campo transaction_type
        labels = {
            'amount': 'Monto',
            'caja': 'Caja'
        }

    def __init__(self, *args, **kwargs):
        super(TransaccionForm, self).__init__(*args, **kwargs)
        self.fields['caja'].queryset = Caja.objects.filter(abierta=True)  # Filtrar solo las cajas abiertas
