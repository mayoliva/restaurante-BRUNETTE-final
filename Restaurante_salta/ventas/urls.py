from django.urls import path
from . import views

app_name = 'ventas'

urlpatterns = [
    path('', views.lista_ventas, name='lista_ventas'),
    path('crear/', views.crear_venta, name='crear_venta'),
    path('editar/<int:pk>/', views.editar_venta, name='editar_venta'),
    path('eliminar/<int:pk>/', views.eliminar_venta, name='eliminar_venta'),
    path('pagado/<int:pk>/', views.marcar_pagado, name='marcar_pagado'),
    path('kitchen-orders/', views.kitchen_orders, name='kitchen_orders'),  # Nueva ruta para la vista de cocina
    path('update-order-status/<int:pk>/', views.update_order_status, name='update_order_status'),  # Nueva ruta para actualizar el estado del pedido
    path('ingresar-dinero/', views.ingresar_dinero, name='ingresar_dinero'),  # Nueva ruta para ingresar dinero
    path('sacar-dinero/', views.sacar_dinero, name='sacar_dinero'),  # Nueva ruta para sacar dinero
    path('estadisticas/', views.estadisticas, name='estadisticas'),
    path('caja/<int:caja_id>/', views.lista_ventas, name='lista_ventas_por_caja'),  # Nueva ruta para ventas por caja
]




