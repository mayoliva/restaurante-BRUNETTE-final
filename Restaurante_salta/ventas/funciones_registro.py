# funciones_registro.py

from .models import Transaction

def registrar_venta(caja, user, amount, payment_type):
    Transaction.objects.create(
        caja=caja,
        user=user,
        amount=amount,
        transaction_type='Venta',
        payment_type=payment_type
    )

def registrar_ingreso(caja, user, amount):
    Transaction.objects.create(
        caja=caja,
        user=user,
        amount=amount,
        transaction_type='ingreso',
        payment_type='efectivo'  # Los ingresos siempre serán en efectivo
    )

def registrar_egreso(caja, user, amount):
    Transaction.objects.create(
        caja=caja,
        user=user,
        amount=amount,
        transaction_type='egreso',
        payment_type='efectivo'  # Los egresos siempre serán en efectivo
    )
