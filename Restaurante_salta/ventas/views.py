from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from .models import Venta, VentaProducto, Producto
from .forms import VentaForm
from caja.models import Caja, Transaction  # Importa Transaction desde caja.models
from decimal import Decimal
from django.db.models import Q
from .forms import TransaccionForm  # Asegúrate de importar el formulario necesario
from django.contrib.auth.decorators import login_required
import os
from django.db import models
from django.db import transaction
from django.shortcuts import render
from django.db.models import Sum, Count
from .models import Venta
from caja.models import Caja
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
from .funciones_registro import registrar_venta, registrar_ingreso, registrar_egreso  # Importa las funciones aquí
import json
from django.db.models.functions import TruncDate
from django.db.models import Sum

@login_required
def lista_ventas(request, caja_id=None):  # caja_id para las ventas de caja cerrada
    try:
        if caja_id:
            caja = Caja.objects.get(id=caja_id, abierta=False)  # Caja cerrada
            ventas = Venta.objects.filter(caja=caja)
            es_caja_cerrada = True  # Bandera para identificar caja cerrada
        else:
            caja_activa = Caja.objects.get(abierta=True)  # Caja activa
            ventas = Venta.objects.filter(caja=caja_activa)
            es_caja_cerrada = False
    except ObjectDoesNotExist:
        ventas = Venta.objects.none()
        es_caja_cerrada = False
        if not caja_id:
            messages.warning(request, 'No hay caja abierta actualmente.')
    
    # Filtrar por fecha y cliente
    fecha = request.GET.get('fecha')
    nombre = request.GET.get('nombre')
    
    if fecha:
        ventas = ventas.filter(fecha_venta__date=fecha)
    if nombre:
        ventas = ventas.filter(customer_name__icontains=nombre)
    
    pedidos_completados = ventas.filter(estado_pedido='completado')
    pedidos_espera = ventas.filter(estado_pedido='pendiente')

    return render(request, 'ventas/lista_ventas.html', {
        'ventas': ventas,
        'pedidos_completados': pedidos_completados,
        'pedidos_espera': pedidos_espera,
        'es_caja_cerrada': es_caja_cerrada,  # Agregar esta bandera al contexto
    })

@login_required
def crear_venta(request):
    try:
        caja_activa = Caja.objects.get(abierta=True)
    except ObjectDoesNotExist:
        return render(request, 'ventas/no_hay_caja_abierta.html')

    productos = Producto.objects.filter(is_active=True)  # Solo productos activos
    carrito = request.session.get('carrito', {})
    total_carrito = Decimal(0)

    # Guardar y mantener el nombre del cliente en la sesión
    customer_name = request.POST.get('customer_name', request.session.get('customer_name', ''))
    request.session['customer_name'] = customer_name

    if request.method == 'POST':
        producto_id = request.POST.get('producto')
        cantidad = int(request.POST.get('cantidad', 1))
        metodo_pago = request.POST.get('metodo_pago', 'efectivo')

        if 'añadir_al_carrito' in request.POST and producto_id:
            producto = get_object_or_404(Producto, id=producto_id)
            if producto.stock >= cantidad:
                carrito[producto_id] = carrito.get(producto_id, {'nombre': producto.nombre, 'cantidad': 0, 'precio': float(producto.precio)})
                carrito[producto_id]['cantidad'] += cantidad
                request.session['carrito'] = carrito
            else:
                messages.error(request, 'Stock insuficiente para este producto.')

        elif 'borrar_producto' in request.POST:
            producto_id = request.POST.get('producto_id')
            if producto_id in carrito:
                del carrito[producto_id]
                request.session['carrito'] = carrito

        elif 'confirmar_pedido' in request.POST:
            if not carrito:
                messages.error(request, 'El carrito está vacío.')
            else:
                with transaction.atomic():
                    venta = Venta.objects.create(caja=caja_activa, tipo_pago=metodo_pago, customer_name=customer_name, estado_facturacion='Sin facturar')
                    for producto_id, detalles in carrito.items():
                        producto = get_object_or_404(Producto, id=producto_id)
                        if producto.stock >= detalles['cantidad']:
                            VentaProducto.objects.create(venta=venta, producto=producto, cantidad=detalles['cantidad'])
                            producto.stock -= detalles['cantidad']
                            producto.save()
                        else:
                            messages.error(request, f'Stock insuficiente para {producto.nombre}.')
                            transaction.set_rollback(True)
                            return render(request, 'ventas/crear_venta.html', {'productos': productos, 'carrito': carrito, 'total_carrito': total_carrito})
                    venta.estado_pedido = 'pendiente'
                    venta.save()
                    generar_ticket(venta)
                    request.session['carrito'] = {}
                    request.session['customer_name'] = ''
                    messages.success(request, f"Ticket generado correctamente para la venta #{venta.id}")
                    return redirect('ventas:lista_ventas')

    total_carrito = sum(Decimal(detalles['precio']) * detalles['cantidad'] for detalles in carrito.values())
    return render(request, 'ventas/crear_venta.html', {'productos': productos, 'carrito': carrito, 'total_carrito': float(total_carrito)})

def generar_ticket(venta):
    # Lógica para generar el ticket con los detalles de la venta
    ticket_content = f"Cliente: {venta.customer_name}\n"
    ticket_content += f"Fecha: {venta.fecha_venta.strftime('%Y-%m-%d %H:%M')}\n"
    ticket_content += "Productos:\n"
    for vp in venta.ventaproducto_set.all():
        ticket_content += f"{vp.producto.nombre} x {vp.cantidad}\n"
    ticket_content += f"Total: {venta.total()}\n"

    # Crear el directorio si no existe
    ticket_dir = 'tickets'
    os.makedirs(ticket_dir, exist_ok=True)

    # Guardar el ticket en un archivo de texto
    ticket_filename = f"ticket_{venta.id}.txt"
    ticket_filepath = os.path.join(ticket_dir, ticket_filename)
    with open(ticket_filepath, 'w') as ticket_file:
        ticket_file.write(ticket_content)

    print(f"Ticket generado: {ticket_filepath}")  # Mensaje de confirmación para depuración

def kitchen_orders(request):
    orders = Venta.objects.filter(estado_pedido='pendiente')
    return render(request, 'ventas/kitchen_orders.html', {'orders': orders})

def update_order_status(request, pk):
    pedido = get_object_or_404(Venta, pk=pk)
    pedido.estado_pedido = 'completado'
    pedido.save()
    messages.success(request, 'El pedido ha sido marcado como completado.')
    return redirect('ventas:kitchen_orders')

def editar_venta(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    productos = Producto.objects.all()
    carrito = {
        str(vp.producto.id): {
            'nombre': vp.producto.nombre,
            'cantidad': vp.cantidad,
            'precio': float(vp.producto.precio),
            'total': float(vp.producto.precio) * vp.cantidad
        } for vp in venta.ventaproducto_set.all()
    }
    total_carrito = sum(detalles['total'] for detalles in carrito.values())

    if request.method == 'POST':
        producto_id = request.POST.get('producto')
        cantidad = int(request.POST.get('cantidad', 1))
        metodo_pago = request.POST.get('metodo_pago', venta.tipo_pago)

        if 'añadir_al_carrito' in request.POST and producto_id:
            producto = get_object_or_404(Producto, id=producto_id)
            if producto.stock >= cantidad:
                carrito[producto_id] = carrito.get(producto_id, {'nombre': producto.nombre, 'cantidad': 0, 'precio': float(producto.precio)})
                carrito[producto_id]['cantidad'] += cantidad
                carrito[producto_id]['total'] = float(producto.precio) * carrito[producto_id]['cantidad']
                request.session['carrito'] = carrito
                messages.success(request, 'Producto añadido al carrito.')
            else:
                messages.error(request, 'Stock insuficiente para este producto.')

        elif 'borrar_producto' in request.POST:
            producto_id = request.POST.get('producto_id')
            if producto_id in carrito:
                del carrito[producto_id]
                request.session['carrito'] = carrito
                messages.success(request, 'Producto borrado del carrito.')

        elif 'actualizar_venta' in request.POST:
            venta.tipo_pago = metodo_pago
            venta.save()
            VentaProducto.objects.filter(venta=venta).delete()
            for producto_id, detalles in carrito.items():
                producto = get_object_or_404(Producto, id=producto_id)
                VentaProducto.objects.create(venta=venta, producto=producto, cantidad=detalles['cantidad'])
            messages.success(request, 'Venta actualizada con éxito.')

            # Regenerar el ticket después de actualizar la venta
            generar_ticket(venta)
            
            return redirect('ventas:lista_ventas')

    efectivo_selected = venta.tipo_pago == 'efectivo'
    transferencia_selected = venta.tipo_pago == 'transferencia'

    return render(request, 'ventas/editar_venta.html', {
        'productos': productos,
        'carrito': carrito,
        'total_carrito': total_carrito,
        'venta': venta,
        'efectivo_selected': efectivo_selected,
        'transferencia_selected': transferencia_selected,
    })

@login_required
def eliminar_venta(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    if request.method == 'POST':
        with transaction.atomic():
            for vp in venta.ventaproducto_set.all():
                producto = vp.producto
                producto.stock += vp.cantidad
                producto.save()
            venta.delete()
            messages.success(request, 'La venta ha sido borrada y el stock ha sido actualizado correctamente.')
        return redirect('ventas:lista_ventas')
    return render(request, 'ventas/eliminar_venta.html', {'venta': venta})

@login_required
def marcar_pagado(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    if request.method == 'POST':
        if venta.estado_pedido == 'completado':
            if venta.estado_facturacion == 'Sin facturar':
                venta.estado_facturacion = 'Facturado'
                venta.save()

                if venta.caja:
                    payment_type = venta.tipo_pago  # Usar el tipo de pago de la venta
                    registrar_venta(venta.caja, request.user, venta.total(), payment_type)
                    messages.success(request, 'La venta ha sido facturada correctamente y la transacción registrada.')
                else:
                    messages.error(request, 'No hay caja asociada a esta venta.')
            else:
                messages.warning(request, 'La venta ya ha sido facturada.')
        else:
            messages.warning(request, 'El pedido debe estar marcado como completado antes de poder facturarlo.')
    return redirect('ventas:lista_ventas')

@login_required
def ingresar_dinero(request):
    if request.method == 'POST':
        form = TransaccionForm(request.POST)
        if form.is_valid():
            transaccion = form.save(commit=False)
            if transaccion.amount < 0:
                messages.error(request, 'El monto del ingreso no puede ser negativo.')
                return render(request, 'ventas/ingresar_dinero.html', {'form': form})

            registrar_ingreso(transaccion.caja, request.user, transaccion.amount)
            transaccion.user = request.user  # Asigna el usuario actual
            transaccion.save()

            messages.success(request, 'Ingreso registrado con éxito.')
            return redirect('ventas:lista_ventas')
    else:
        form = TransaccionForm()
    return render(request, 'ventas/ingresar_dinero.html', {'form': form})

@login_required
def sacar_dinero(request):
    if request.method == 'POST':
        form = TransaccionForm(request.POST)
        if form.is_valid():
            transaccion = form.save(commit=False)
            if transaccion.amount <= 0:
                messages.error(request, 'El monto del egreso debe ser mayor a 0.')
                return render(request, 'ventas/sacar_dinero.html', {'form': form})
            
            caja = transaccion.caja

            # Asegúrate de usar el related_name correcto para calcular los subtotales y saldo final
            ingresos = caja.ventas_transaction_set.filter(transaction_type='ingreso').aggregate(total=models.Sum('amount'))['total'] or 0
            egresos = caja.ventas_transaction_set.filter(transaction_type='egreso').aggregate(total=models.Sum('amount'))['total'] or 0
            ventas_efectivo = caja.ventas_transaction_set.filter(transaction_type='Venta', payment_type='efectivo').aggregate(total=models.Sum('amount'))['total'] or 0
            saldo_actual = caja.saldo_inicial + ventas_efectivo + ingresos - egresos

            if transaccion.amount > saldo_actual:
                messages.error(request, 'No hay suficiente saldo en la caja para realizar este egreso.')
                return render(request, 'ventas/sacar_dinero.html', {'form': form})
            
            registrar_egreso(transaccion.caja, request.user, transaccion.amount)
            transaccion.user = request.user  # Asigna el usuario actual
            transaccion.save()

            messages.success(request, 'Egreso registrado con éxito.')
            return redirect('ventas:lista_ventas')
    else:
        form = TransaccionForm()
    return render(request, 'ventas/sacar_dinero.html', {'form': form})

@login_required
def estadisticas(request):
    # Obtener las fechas desde los parámetros GET
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    # Filtrar las ventas por rango de fechas si se proporcionan
    ventas = Venta.objects.all()
    if fecha_inicio and fecha_fin:
        ventas = ventas.filter(fecha_venta__date__range=[fecha_inicio, fecha_fin])
    elif fecha_inicio:
        ventas = ventas.filter(fecha_venta__date__gte=fecha_inicio)
    elif fecha_fin:
        ventas = ventas.filter(fecha_venta__date__lte=fecha_fin)

    # Datos para gráficos de ingresos (usando TruncDate para evitar .extra())
    ingresos_por_fecha = ventas.annotate(fecha=TruncDate('fecha_venta')).values('fecha').annotate(total=Sum('ventaproducto__cantidad')).order_by('fecha')
    ingresos_por_fecha_labels = json.dumps([entry['fecha'].strftime('%Y-%m-%d') for entry in ingresos_por_fecha])
    ingresos_por_fecha_data = json.dumps([entry['total'] for entry in ingresos_por_fecha])

    # Datos para gráficos de métodos de pago
    metodos_de_pago = ventas.values('tipo_pago').annotate(total=Sum('ventaproducto__cantidad')).order_by('tipo_pago')
    metodos_de_pago_labels = json.dumps([entry['tipo_pago'] for entry in metodos_de_pago])
    metodos_de_pago_data = json.dumps([entry['total'] for entry in metodos_de_pago])

    return render(request, 'ventas/estadisticas.html', {
        'ingresos_por_fecha_labels': ingresos_por_fecha_labels,
        'ingresos_por_fecha_data': ingresos_por_fecha_data,
        'metodos_de_pago_labels': metodos_de_pago_labels,
        'metodos_de_pago_data': metodos_de_pago_data,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    })