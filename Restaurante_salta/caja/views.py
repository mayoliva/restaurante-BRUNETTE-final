from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Caja, Transaction  # Importar el modelo Transaction
from .forms import AperturaCajaForm
from django.contrib.auth.decorators import login_required  # Asegurar que solo usuarios logueados puedan acceder
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from ventas.models import Venta 
from django.db.models import Sum

@login_required
def apertura_caja(request):
    # Verificar si el usuario actual tiene una caja abierta
    caja_abierta_usuario = Caja.objects.filter(abierta=True, usuario=request.user).first()
    
    if request.method == "POST":
        form = AperturaCajaForm(request.POST)
        if form.is_valid():
            saldo_inicial = form.cleaned_data['saldo_inicial']
            
            if caja_abierta_usuario:
                messages.error(request, 'Ya tienes una caja abierta. Debes cerrarla antes de abrir una nueva.')
                return redirect('caja:detalle_caja', caja_id=caja_abierta_usuario.id)
            
            nueva_caja = Caja.objects.create(
                saldo_inicial=saldo_inicial,
                abierta=True,
                fecha_apertura=timezone.now(),
                usuario=request.user
            )
            
            Transaction.objects.create(
                caja=nueva_caja,
                user=request.user,
                amount=saldo_inicial,
                transaction_type='Apertura de caja'
            )

            return redirect('caja:detalle_caja', caja_id=nueva_caja.id)
    else:
        form = AperturaCajaForm()

    return render(request, 'caja/apertura_caja.html', {'form': form, 'caja_abierta_usuario': caja_abierta_usuario})

@login_required
def detalle_caja(request, caja_id):
    caja = get_object_or_404(Caja, id=caja_id)
    ventas = caja.obtener_ventas_facturadas()
    transacciones = caja.ventas_transaction_set.all()  # Usar el related_name correcto

    # Calcular subtotales de ventas por tipo de pago
    subtotal_ventas_efectivo = transacciones.filter(transaction_type='Venta', payment_type='efectivo').aggregate(total=Sum('amount'))['total'] or 0
    subtotal_ventas_transferencia = transacciones.filter(transaction_type='Venta', payment_type='transferencia').aggregate(total=Sum('amount'))['total'] or 0

    # Calcular otros ingresos excluyendo las ventas
    subtotal_ingresos = transacciones.filter(transaction_type='ingreso').aggregate(total=Sum('amount'))['total'] or 0

    # Calcular egresos
    subtotal_egresos = transacciones.filter(transaction_type='egreso').aggregate(total=Sum('amount'))['total'] or 0

    # Calcular el saldo final incluyendo tanto las ventas en efectivo como por transferencia
    saldo_final = caja.saldo_inicial + subtotal_ventas_efectivo + subtotal_ventas_transferencia + subtotal_ingresos - subtotal_egresos

    return render(request, 'caja/detalle_caja.html', {
        'caja': caja,
        'ventas': ventas,
        'transacciones': transacciones,
        'subtotal_ventas_efectivo': subtotal_ventas_efectivo,
        'subtotal_ventas_transferencia': subtotal_ventas_transferencia,
        'subtotal_ingresos': subtotal_ingresos,
        'subtotal_egresos': subtotal_egresos,
        'saldo_final': saldo_final,
    })
    
@login_required
def cierre_caja(request, caja_id):
    caja = get_object_or_404(Caja, id=caja_id)
    
    # Verificar si hay pedidos pendientes en cocina
    pedidos_en_cocina = Venta.objects.filter(estado_pedido='pendiente').exists()
    if pedidos_en_cocina:
        messages.error(request, "No se puede cerrar la caja porque hay pedidos pendientes en cocina.")
        return redirect('caja:detalle_caja', caja_id=caja.id)
    
    if caja.fecha_cierre is None:
        caja.fecha_cierre = timezone.now()
        caja.abierta = False
        caja.calcular_saldo_final()
        caja.save()
        
        Transaction.objects.create(
            caja=caja,
            user=request.user,
            amount=caja.saldo_final,
            transaction_type='Cierre de caja'
        )
        
        messages.success(request, "La caja se ha cerrado exitosamente.")
        return redirect('caja:detalle_caja', caja_id=caja.id)
    else:
        messages.warning(request, "La caja ya está cerrada.")
        return redirect('caja:detalle_caja', caja_id=caja.id)
    
@login_required
def lista_transacciones(request):
    usuario = request.GET.get('usuario')
    tipo_transaccion = request.GET.get('tipo_transaccion')
    
    try:
        caja_activa = Caja.objects.get(abierta=True)
        transacciones = Transaction.objects.filter(caja=caja_activa)
    except ObjectDoesNotExist:
        transacciones = Transaction.objects.none()
        messages.warning(request, 'No hay caja abierta actualmente.')
    
    # Filtrar transacciones por usuario y tipo de transacción si se proporcionan
    if usuario:
        transacciones = transacciones.filter(user__username__icontains=usuario)
    if tipo_transaccion:
        transacciones = transacciones.filter(transaction_type__icontains=tipo_transaccion)
    
    return render(request, 'caja/transacciones_list.html', {'transacciones': transacciones})

@login_required
def detalle_transaccion(request, transaccion_id):
    transaccion = get_object_or_404(Transaction, id=transaccion_id)
    return render(request, 'caja/transaccion_detail.html', {'transaccion': transaccion})

@login_required
def lista_cajas_cerradas(request):
    cajas_cerradas = Caja.objects.filter(abierta=False).order_by('-fecha_cierre')
    return render(request, 'caja/lista_cajas_cerradas.html', {'cajas_cerradas': cajas_cerradas})