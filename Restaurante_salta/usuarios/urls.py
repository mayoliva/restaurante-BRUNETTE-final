from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('registro/', views.registro, name='registro'),
    path('asignar_rol/', views.asignar_rol, name='asignar_rol'),
    path('menu/', views.menu_principal, name='menu_principal'),
    path('user_list/', views.user_list, name='user_list'),
    path('edit_user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('delete_user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('cerrar_sesion/', views.cerrar_sesion, name='cerrar_sesion'),  # Ruta para cerrar sesión
    path('activar_usuario/<int:user_id>/', views.activar_usuario, name='activar_usuario'),
]