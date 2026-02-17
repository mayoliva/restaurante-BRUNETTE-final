from django.db import models
from django.conf import settings  # Para usar AUTH_USER_MODEL
from productos.models import Producto

class Caja(models.Model):
    nombre = models.CharField(max_length=50, default="Caja 1")  # Caja única
    saldo_inicial = models.DecimalField(max_digits=10, decimal_places=2)
    saldo_final = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    abierta = models.BooleanField(default=False)
    fecha_apertura = models.DateTimeField(null=True, blank=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)  # Relación con el usuario

    def __str__(self):
        return f"Caja Nº {self.nombre.split()[1]}"

    def obtener_ventas_facturadas(self):
        return self.venta_set.filter(estado_facturacion='facturado')

    def total_ventas_efectivo(self):
        ventas_efectivo = self.obtener_ventas_facturadas().filter(tipo_pago='efectivo')
        total = sum(v.total() for v in ventas_efectivo)
        return total

    def total_ventas_transferencia(self):
        ventas_transferencia = self.obtener_ventas_facturadas().filter(tipo_pago='transferencia')
        total = sum(v.total() for v in ventas_transferencia)
        return total

    def calcular_saldo_final(self):
        self.saldo_final = self.saldo_inicial + self.total_ventas_efectivo() + self.total_ventas_transferencia()
        self.save()

class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('Apertura', 'Apertura'),
        ('Cierre', 'Cierre'),
    )

    caja = models.ForeignKey('Caja', on_delete=models.CASCADE, related_name='caja_transactions')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='caja_transactions'  # Añadir related_name único
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)

    def __str__(self):
        return f'{self.transaction_type} - {self.amount}'
