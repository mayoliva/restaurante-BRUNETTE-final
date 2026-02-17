from django import forms
from .models import Caja

class AperturaCajaForm(forms.ModelForm):
    saldo_inicial = forms.DecimalField(
        max_digits=10, decimal_places=2,
        label="Saldo Inicial",
        widget=forms.NumberInput(attrs={'step': '0.01'})
    )

    class Meta:
        model = Caja
        fields = ['saldo_inicial']  # Solo saldo inicial

    def __init__(self, *args, **kwargs):
        super(AperturaCajaForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.label = field.label.capitalize()

    def clean_saldo_inicial(self):
        saldo_inicial = self.cleaned_data['saldo_inicial']
        # Asegurarse de que el saldo inicial sea mayor que cero
        if saldo_inicial <= 0:
            raise forms.ValidationError("El saldo inicial debe ser mayor que cero.")
        return saldo_inicial
