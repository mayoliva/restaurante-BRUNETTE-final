from django.shortcuts import render, redirect, get_object_or_404
from .forms import RegistroUsuarioForm
from django.contrib.auth.models import Group, User
from django.contrib.auth.decorators import login_required, user_passes_test
from caja.models import Caja
from .models import Usuario
from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm
from django.contrib.auth import logout  # Importar la función de logout
from django.contrib import messages  # Importar mensajes

# Función para verificar si el usuario es administrador
def es_admin(user):
    return user.is_superuser

# Vista para el registro de usuarios
def registro(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            grupo, creado = Group.objects.get_or_create(name='Cajero')
            usuario.groups.add(grupo)
            return redirect('login')
    else:
        form = RegistroUsuarioForm()

    return render(request, 'usuarios/registro.html', {'form': form})

# Vista para asignar roles, solo accesible para administradores
@login_required
@user_passes_test(es_admin)
def asignar_rol(request):
    if request.method == 'POST':
        usuario_id = request.POST.get('usuario_id')
        rol = request.POST.get('rol')
        usuario = User.objects.get(id=usuario_id)

        grupo, creado = Group.objects.get_or_create(name=rol)
        usuario.groups.clear()
        usuario.groups.add(grupo)

        return redirect('asignar_rol')

    usuarios = User.objects.all()
    grupos = Group.objects.all()
    grupos = Group.objects.filter(name__in=['Administrador', 'Cajero', 'Cliente', 'Cocinero'])  # Incluye el nuevo rol
    return render(request, 'usuarios/asignar_rol.html', {'usuarios': usuarios, 'grupos': grupos})


@login_required
def menu_principal(request):
    # Obtener la caja abierta actualmente
    caja_abierta = Caja.objects.filter(abierta=True).first()
    context = {
        'caja_abierta': caja_abierta
    }
    return render(request, 'usuarios/menu_principal.html', context)

@login_required
def user_list(request):
    usuarios = Usuario.objects.all()  # Mostrar todos (activos e inactivos)
    return render(request, 'usuarios/user_list.html', {'usuarios': usuarios})


@login_required
@user_passes_test(es_admin)
def edit_user(request, user_id):
    usuario = get_object_or_404(Usuario, id=user_id)
    if request.method == 'POST':
        form = UserChangeForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            return redirect('usuarios:user_list')
    else:
        form = UserChangeForm(instance=usuario)
    return render(request, 'usuarios/edit_user.html', {'form': form})

@login_required
@user_passes_test(es_admin)
def delete_user(request, user_id):
    usuario = get_object_or_404(Usuario, id=user_id)
    usuario.is_active = False  # Marcar como inactivo
    usuario.save()
    return redirect('usuarios:user_list')

# Vista para cerrar sesión
@login_required
def cerrar_sesion(request):
    # Verificar si el usuario actual tiene una caja abierta
    caja_abierta_usuario = Caja.objects.filter(abierta=True, usuario=request.user).first()
    
    if caja_abierta_usuario:
        messages.error(request, 'No puedes cerrar sesión mientras tengas una caja abierta. Por favor, cierra la caja primero.')
        return redirect('caja:detalle_caja', caja_id=caja_abierta_usuario.id)
    
    logout(request)
    return redirect('login')

class UserChangeForm(BaseUserChangeForm):
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'first_name', 'last_name', 'rol']
        
@login_required
@user_passes_test(es_admin)
def activar_usuario(request, user_id):
    usuario = get_object_or_404(Usuario, id=user_id)
    usuario.is_active = True  # Marcar como activo
    usuario.save()
    return redirect('usuarios:user_list')

