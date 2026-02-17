from django.shortcuts import redirect

def redirect_to_menu(request):
    return redirect('usuarios:menu_principal')
