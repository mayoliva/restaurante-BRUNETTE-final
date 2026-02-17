from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from productos.models import Producto
from caja.models import Caja
from django.conf import settings  # Para usar AUTH_USER_MODEL

class Venta(models.Model):
    ESTADOS_PEDIDO = [
        ('pendiente', 'Pendiente'),
        ('procesando', 'Procesando'),
        ('completado', 'Completado'),
    ]

    ESTADOS_FACTURACION = [
        ('pendiente', 'Pendiente'),
        ('facturado', 'Facturado'),
        ('cancelado', 'Cancelado'),
    ]

    TIPO_PAGO = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
    ]

    productos = models.ManyToManyField(Producto, through='VentaProducto')
    fecha_venta = models.DateTimeField(auto_now_add=True)
    estado_pedido = models.CharField(max_length=20, choices=ESTADOS_PEDIDO, default='pendiente')
    estado_facturacion = models.CharField(max_length=20, choices=ESTADOS_FACTURACION, default='pendiente')
    tipo_pago = models.CharField(max_length=20, choices=TIPO_PAGO, default='efectivo')
    caja = models.ForeignKey(Caja, on_delete=models.CASCADE, null=True, blank=True)
    customer_name = models.CharField(max_length=100)  # Nuevo campo añadido

    def __str__(self):
        return f'Venta #{self.id} - {self.fecha_venta.strftime("%Y-%m-%d %H:%M")}'

    def total(self):
        return sum([vp.producto.precio * vp.cantidad for vp in self.ventaproducto_set.all()])

class VentaProducto(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()

    def __str__(self):
        return f'{self.producto.nombre} x {self.cantidad}'

@receiver(post_save, sender=Venta)
def actualizar_stock(sender, instance, created, **kwargs):
    if not created:
        venta_anterior = Venta.objects.get(pk=instance.pk)
        if venta_anterior.estado_facturacion != 'facturado' and instance.estado_facturacion == 'facturado':
            for vp in instance.ventaproducto_set.all():
                producto = vp.producto
                if producto.stock >= vp.cantidad:
                    producto.stock -= vp.cantidad
                    producto.save()
                else:
                    pass  # Manejar caso de stock insuficiente

class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('Venta', 'Venta'),
        ('ingreso', 'Ingreso'),
        ('egreso', 'Egreso'),
    )

    PAYMENT_TYPES = (
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
    )

    caja = models.ForeignKey('caja.Caja', on_delete=models.CASCADE, related_name='ventas_transaction_set')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ventas_transactions'  # Añadir related_name único
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    payment_type = models.CharField(max_length=15, choices=PAYMENT_TYPES, null=True, blank=True)

    def __str__(self):
        return f'{self.transaction_type} - {self.amount} ({self.payment_type})'