from django.shortcuts import render

from metro.models import Product, Inventario, TomaFisica
from metro.forms import ProductForm, InventarioForm, TomaFisicaForm
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.forms.models import model_to_dict
import json
from django.views.decorators.http import require_POST
import datetime


from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie



### PRODUCTOS
@login_required(login_url='login')
def metro_products_list(request):
    
    products = Product.objects.all().order_by('codigo_gim', 'marca')
    products_data = {
        'total':products.count(),
        'activos':products.filter(activo=True).count(),
        'inactivos':products.filter(activo=False).count(),
    }
    
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.usuario = request.user
            product.save()
            messages.success(request, f"Producto {form.clean_codigo_gim()} creado exitosamente")
            form = ProductForm()
    else:
        form = ProductForm()
    
    context = {
        'products':products,
        'products_data':products_data,
        'form':form
    }
    
    return render(request, 'metro/products-list.html', context)


@login_required(login_url='login')
def metro_product_edit(request, id):
    """
    Vista para manejar la edición de productos en un modal.
    GET: Devuelve el formulario HTML para mostrar en el modal
    POST: Procesa el formulario enviado y devuelve respuesta JSON
    """
    # Obtener el producto o devolver 404 si no existe
    product = get_object_or_404(Product, id=id)
    
    if request.method == 'POST':
        # Procesar el formulario enviado
        form = ProductForm(request.POST, instance=product, user=request.user) 
        if form.is_valid():
            form.save()
            messages.success(request, f'Producto {form.clean_codigo_gim()} editado correctamente !!!')
            return JsonResponse({
                'success': True,
                'message': f'Producto actualizado {form.clean_codigo_gim()} correctamente.',
                # Datos actualizados para refrescar la tabla sin recargar
                'product': {
                    'id': product.id,
                    'codigo_gim': product.codigo_gim,
                    'nombre_gim': product.nombre_gim,
                    'marca': product.marca,
                    # Incluir otros campos necesarios para actualizar la UI
                }
            })
        else:
            # Devolver errores si el formulario no es válido
            errors = form.get_formatted_errors() if hasattr(form, 'get_formatted_errors') else str(form.errors)
            return JsonResponse({
                'success': False,
                'errors': errors
            }, status=400)
    else:
        # Para solicitudes GET, crear el formulario con el producto existente
        form = ProductForm(instance=product, user=request.user)
        return HttpResponse(form.as_p())


@login_required(login_url='login')
def metro_product_eliminar(request):
    pass


### INVENTARIOS
@login_required(login_url='login')
def metro_inventarios_list(request):
    
    inventarios = Inventario.objects.all().order_by('-id')
    
    if request.method == 'POST':
        form = InventarioForm(request.POST)
        if form.is_valid():
            inventario = form.save(commit=False)
            inventario.usuario = request.user
            inventario.save()
            
            # crear productos en toma fisica
            for i in Product.objects.filter(activo=True):
                toma_fisica = TomaFisica(
                    inventario_id = inventario.id,
                    product_id = i.id
                )
                
                toma_fisica.save() 
            
            messages.success(request, f"Inventario {inventario.nombre} creado exitosamente")
            form = InventarioForm()
    else:
        form = InventarioForm()
    
    context = {
        'inventarios':inventarios,
        'form':form
    }
    
    return render(request, 'metro/inventarios-list.html', context)


@ensure_csrf_cookie  # Asegura que se envíe el token CSRF
@require_http_methods(["PATCH"])
def metro_inventario_patch(request, id):
    try:
        # Obtener el producto
        inventario = Inventario.objects.get(id=id)
        
        # Parsear los datos recibidos
        datos = json.loads(request.body)
        
        # Actualizar solo los campos recibidos
        if 'nombre' in datos:
            inventario.nombre = datos['nombre']
        
        if 'estado_inv' in datos:
            inventario.estado_inv = datos['estado_inv']
            
        if 'estado_tf' in datos:
            if inventario.estado_tf == 'CREADO' and datos['estado_tf'] == 'EN PROCESO':
                inventario.estado_tf = datos['estado_tf']
                inventario.inicio_tf = datetime.datetime.now()
            elif datos['estado_tf'] == 'FINALIZADO':
                inventario.estado_tf = datos['estado_tf']
                inventario.fin_tf = datetime.datetime.now()
            else:
                inventario.estado_tf = datos['estado_tf']
        
        # Guardar los cambios
        inventario.save()
        
        # Devolver respuesta exitosa
        return JsonResponse({
            'status': 'success',
            'data':model_to_dict(inventario)
            # 'data': {
            #     'id': producto.id,
            #     'nombre': producto.nombre,
            #     'precio': float(producto.precio),
            #     'stock': producto.stock,
            #     'descripcion': producto.descripcion,
            #     'activo': producto.activo
            # }
        })
    except Inventario.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Producto no encontrado'
        }, status=404)
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'JSON inválido'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required(login_url='login')
def metro_inventario_eliminar(request):
    pass




# # Toma física template
# from django.contrib.auth.mixins import LoginRequiredMixin
# from django.views.generic import TemplateView


# class TomaFisicaView(LoginRequiredMixin, TemplateView):
#     template_name = 'metro/toma_fisica.html'


# # Toma Física
# @login_required(login_url='login')
# def metro_toma_fisica_data(request, inventario_id):
#     print(inventario)
#     inventario = Inventario.objects.get(id=inventario_id)
#     products = TomaFisica.objects.filter(inventario = inventario_id)
    
#     return JsonResponse({
#         # 'inventario':inventario,
#         'inventario': model_to_dict(inventario),
#         # 'products':products
#         'products':list(products.values())
#     })

#     # context = {
#     #     'inventario':inventario,
#     #     'products':products
#     # }
#     # return render(request, 'metro/toma-fisica.html', context)




# Estado inventario toma fisica
@require_POST  # Asegura que solo se acepten solicitudes POST
@login_required(login_url='login')
def metro_inventario_estado_tf(request, id):

    try:
        # Decodificar el JSON recibido
        data = json.loads(request.body) 
        nuevo_estado = data.get('estado_tf')
        
        # Validar que se recibió el estado
        if not nuevo_estado:
            return JsonResponse({'error': 'No se proporcionó el estado'}, status=400)
        
        # Obtener y actualizar el inventario
        inventario = Inventario.objects.get(id=id) 
        
        if inventario.estado_tf == 'CREADO' and nuevo_estado == 'EN PROCESO':
            inventario.inicio_tf = datetime.datetime.now()
            
        if nuevo_estado == 'FINALIZADO':
            inventario.fin_tf = datetime.datetime.now()
        
        inventario.estado_tf = nuevo_estado  # Asumiendo que el campo se llama "estado"
        inventario.save()
        
        # Devolver respuesta exitosa con datos serializados manualmente
        return JsonResponse({
            'success': True,
            'inventario': {
                'id': inventario.id,
                'estado': inventario.estado_tf,
            }
        })
    except Inventario.DoesNotExist:
        return JsonResponse({'error': 'Inventario no encontrado'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



### TOMA FISICA
# Toma Física Lista
@login_required(login_url='login')
def metro_toma_fisica_list(request):
    
    inventarios = Inventario.objects.all().order_by('-id')
    context = {
        'inventarios':inventarios
    }
    return render(request, 'metro/toma-fisica-list.html', context)


# Toma Física
@login_required(login_url='login')
def metro_toma_fisica(request, inventario_id):
    
    inventario = Inventario.objects.get(id=inventario_id)
    products = TomaFisica.objects.filter(inventario = inventario_id)
    
    context = {
        'inventario':inventario,
        'products':products
    }
    return render(request, 'metro/toma-fisica.html', context)


@login_required(login_url='login')
def metro_toma_fisica_edit(request, id):
    """
    Vista para manejar la edición de productos en un modal.
    GET: Devuelve el formulario HTML para mostrar en el modal
    POST: Procesa el formulario enviado y devuelve respuesta JSON
    """
    # Obtener el producto o devolver 404 si no existe
    toma_fisica = get_object_or_404(TomaFisica, id=id)
    
    
    if request.method == 'GET':
        # Para solicitudes GET, crear el formulario con el producto existente
        form = TomaFisicaForm(
            instance=toma_fisica, 
            user=request.user, 
            initial = {
                'cantidad_estanteria': '' if toma_fisica.cantidad_estanteria == 0 else toma_fisica.cantidad_estanteria,
                'cantidad_bulto': '' if toma_fisica.cantidad_bulto == 0 else toma_fisica.cantidad_bulto
                }
            )
        
        return JsonResponse({
            'form':form.as_p(),
            'product':model_to_dict(toma_fisica.product)
        })
    
    if request.method == 'POST':
        # Procesar el formulario enviado
        form = TomaFisicaForm(request.POST, instance=toma_fisica)
        if form.is_valid():
            toma = form.save(commit=False)
            toma.usuario = request.user
            toma.llenado = True
            toma.save()
            
            messages.success(request, f'Toma física exitosa !!!')
            return JsonResponse({
                'success': True,
                'message': 'Toma física exitosa.',
                # Datos actualizados para refrescar la tabla sin recargar
                'toma_fisica': {
                    'cantidad_total': toma_fisica.cantidad_total,
                    'llenado':toma_fisica.llenado
                }
            })
        else:
            # Devolver errores si el formulario no es válido
            errors = form.get_formatted_errors() if hasattr(form, 'get_formatted_errors') else str(form.errors)
            return JsonResponse({
                'success': False,
                'errors': errors
            }, status=400)
    

