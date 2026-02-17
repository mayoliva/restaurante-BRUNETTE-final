from django.shortcuts import render, redirect, get_object_or_404
from .models import Producto, Categoria
from .forms import ProductoForm

# Vista para listar productos
def lista_productos(request):
    productos = Producto.objects.all()  # No se filtra por is_active, se muestran todos
    
    nombre = request.GET.get('nombre', '')
    categoria_id = request.GET.get('categoria', '')
    
    if nombre:
        productos = productos.filter(nombre__icontains=nombre)
    if categoria_id:
        productos = productos.filter(categoria__id=categoria_id)
    
    categorias = Categoria.objects.all()

    for categoria in categorias:
        if str(categoria.id) == str(categoria_id):
            categoria.selected = True
        else:
            categoria.selected = False
    
    return render(request, 'productos/lista_producto.html', {
        'productos': productos,
        'categorias': categorias,
        'nombre': nombre,
    })

# Vista para crear producto
def crear_producto(request):
    # Filtramos solo las categorías "Alimento" y "Bebida"
    categorias = Categoria.objects.filter(nombre__in=['Alimento', 'Bebida'])
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        # Asignamos al campo 'categoria' el queryset filtrado
        form.fields['categoria'].queryset = categorias
        if form.is_valid():
            form.save()
            return redirect('productos:lista_productos')
    else:
        form = ProductoForm()
        form.fields['categoria'].queryset = categorias  # Asignamos también en GET
    return render(request, 'productos/crear_producto.html', {
        'form': form,
        'categorias': categorias,
    })

# Vista para editar producto
def editar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            return redirect('productos:lista_productos')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'productos/editar_producto.html', {'form': form})

# Vista para eliminar producto
def eliminar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    producto.is_active = False  # Marcar como inactivo
    producto.save()
    return redirect('productos:lista_productos')

def activar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    producto.is_active = True  # Marcar como activo
    producto.save()
    return redirect('productos:lista_productos')

