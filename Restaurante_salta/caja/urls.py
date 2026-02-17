from django.urls import path
from . import views

app_name = 'caja'

urlpatterns = [
    path('apertura/', views.apertura_caja, name='apertura_caja'),
    path('detalle/<int:caja_id>/', views.detalle_caja, name='detalle_caja'),
    path('cierre/<int:caja_id>/', views.cierre_caja, name='cierre_caja'),
    path('transacciones/', views.lista_transacciones, name='lista_transacciones'),  # Nueva ruta
    path('transaccion/<int:transaccion_id>/', views.detalle_transaccion, name='detalle_transaccion'),  # Nueva ruta
    path('cajas-cerradas/', views.lista_cajas_cerradas, name='lista_cajas_cerradas'),
]
