# Utils
import json
import datetime
import pandas as pd

# Django
from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.forms.models import model_to_dict
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db.models import Func, F, Value, IntegerField, CharField
from django.db.models.functions import Cast
from django.views.decorators.csrf import csrf_exempt

# Models
from metro.models import Product, Inventario, TomaFisica, Kardex
from metro.forms import ProductForm, InventarioForm, TomaFisicaForm, KardexForm

### PRODUCTOS
@login_required(login_url='login')
def metro_products_list(request):
    
    products = Product.objects.all().order_by('orden', 'codigo_gim', 'marca')
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


@csrf_exempt
def metro_cambiar_orden_productos_ajax(request):
    if request.method == 'POST':
        data = json.loads(request.body)["n_orden"]
        
        for i in data:
            prod = Product.objects.get(id=i['id'])
            prod.orden = i['n_orden']
            prod.save()
            
        return JsonResponse({
            'msg':'ok'
        })

# @login_required(login_url='login')
# def metro_product_eliminar(request):
#     pass


### INVENTARIOS
@login_required(login_url='login')
def metro_inventarios_list(request):
    
    inventarios = Inventario.objects.all().order_by('-id').exclude(id__in=[15,16,17,26])
    
    if request.method == 'POST':
        form = InventarioForm(request.POST)
        if form.is_valid():
            inventario = form.save(commit=False)
            inventario.usuario = request.user
            inventario.save()
            
            # crear productos en toma fisica
            for i in Product.objects.filter(activo=True):
                toma_fisica = TomaFisica(
                    orden = i.orden,
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
@csrf_exempt
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


# @login_required(login_url='login')
# def metro_inventario_eliminar(request):
#     pass


@login_required(login_url='login')
def metro_inventario_informe(request, id):
    
    inventario = Inventario.objects.get(id=id)
    products = TomaFisica.objects.filter(inventario=id).order_by('orden', 'product__codigo_gim', 'product__marca')
    
    context = {
        'inventario':inventario,
        'products':products
    }
    return render(request, 'metro/inventario-informe.html', context)


@login_required(login_url='login')
def metro_inventario_informe_excel(request, id):
    inventario = Inventario.objects.get(id=id)
    products = TomaFisica.objects.filter(inventario=id).values(
        'product__codigo_gim',
        'product__codigo_hm',
        'product__nombre_gim',
        'product__nombre_hm',
        'product__marca',
        'product__unidad',
        'product__u_empaque',
        'product__consignacion',
        'product__ubicacion',
        'cantidad_estanteria',
        'cantidad_suministro',
        'cantidad_bulto',
        'cantidad_total',
        'observaciones',
        'llenado',
        # 'agregado',
        'revisado',
        'usuario__username'
    )
    
    reporte = pd.DataFrame(products)
    reporte = reporte.rename(columns={
        'product__codigo_gim':'Código GIM',
        'product__codigo_hm':'Código HM',
        'product__nombre_gim':'Nombre GIM',
        'product__nombre_hm':'Nombre HM',
        'product__marca':'Marca',
        'product__unidad':'UM',
        'product__u_empaque':'U.Empaque',
        'product__consignacion':'Und.Consignación',
        'product__ubicacion':'Ubicación',
        'cantidad_estanteria':'Und.Estantería',
        'cantidad_bulto':'Und.Bulto',
        'cantidad_suministro':'Und.Suministro',
        'cantidad_total':'Und.Total',
        'observaciones':'Observaciones',
        'llenado':'Llenado',
        # 'agregado':'Agregado',
        'revisado':'Revisado',
        'usuario__username':'Usuario'
    })
    
    if not reporte.empty:
        # hoy = datetime.today().strftime('%Y-%m-%d_%H-%M-%S')
        nombre_archivo = f'Reporte-{inventario.nombre}_{inventario.creado}.xlsx'
        content_disposition = f'attachment; filename="{nombre_archivo}"'

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = content_disposition

        with pd.ExcelWriter(response, engine='openpyxl') as writer:
            
            reporte.to_excel(writer, sheet_name='Reporte-Reservas', index=False)
            
            workbook = writer.book
            worksheet = writer.sheets['Reporte-Reservas']
            
            worksheet.column_dimensions['A'].width = 16 # Código GIM
            worksheet.column_dimensions['B'].width = 16 # Código HM
            worksheet.column_dimensions['C'].width = 50 # Nombre GIM
            worksheet.column_dimensions['D'].width = 60 # Nombre HM
            worksheet.column_dimensions['E'].width = 12 # Marca
            worksheet.column_dimensions['F'].width = 5 # UM
            worksheet.column_dimensions['G'].width = 12 # U.Empaque
            worksheet.column_dimensions['H'].width = 16 # Und.Consignación
            worksheet.column_dimensions['I'].width = 10 # Ubicación
            worksheet.column_dimensions['J'].width = 13 # Und.Estantería
            worksheet.column_dimensions['K'].width = 13 # Und.Bulto
            worksheet.column_dimensions['L'].width = 13 # Und.Suministro
            worksheet.column_dimensions['M'].width = 13 # Und.Total
            worksheet.column_dimensions['N'].width = 25 # Observaciones
            worksheet.column_dimensions['O'].width = 11 # Llenado
            worksheet.column_dimensions['P'].width = 11 # Agregado
            worksheet.column_dimensions['Q'].width = 20 # Usuario
            
        return response

    else:
        messages.success(request, 'Reservas actualizadas, no hay items que mover !!!')
        return HttpResponseRedirect(f'/metro/inventario-informe/{inventario.id}')


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
    # products = TomaFisica.objects.filter(inventario=inventario_id).order_by('product__ubicacion')

    try:
        class SubstringIndex(Func):
            function = 'SUBSTRING_INDEX'
            arity = 3

            def __init__(self, expression, delimiter, count, **extra):
                super().__init__(expression, delimiter, count, output_field=CharField(), **extra)

        products = TomaFisica.objects.filter(inventario=inventario_id).annotate(
            n_order=Cast(
                SubstringIndex(F('product__ubicacion'), Value('-'), Value(1)),
                output_field=IntegerField()
            ),
            l_order=SubstringIndex(
                SubstringIndex(F('product__ubicacion'), Value('-'), Value(2)),
                Value('-'),
                Value(-1)
            )
        ).order_by('n_order', 'l_order')
    except:
        products = TomaFisica.objects.filter(inventario=inventario_id).order_by('product__ubicacion')
    
    context = {
        'inventario':inventario,
        'products':products
    }
    return render(request, 'metro/toma-fisica.html', context)


@csrf_exempt
@login_required(login_url='login')
def metro_toma_fisica_edit(request, id):
    
    # Obtener el producto o devolver 404 si no existe
    toma_fisica = get_object_or_404(TomaFisica, id=id)
    
    if request.method == 'GET':
        # Para solicitudes GET, crear el formulario con el producto existente
        form = TomaFisicaForm(
            instance=toma_fisica, 
            user=request.user, 
            initial = {
                'cantidad_estanteria': '' if toma_fisica.cantidad_estanteria == 0 else toma_fisica.cantidad_estanteria,
                'cantidad_bulto': '' if toma_fisica.cantidad_bulto == 0 else toma_fisica.cantidad_bulto,
                'cantidad_suministro': '' if toma_fisica.cantidad_suministro == 0 else toma_fisica.cantidad_suministro
                }
            )
        
        return JsonResponse({
            'form':form.as_div(),
            'product':model_to_dict(toma_fisica.product)
        })
    
    if request.method == 'POST':
        
        if toma_fisica.inventario.estado_inv == 'CERRADO':
            return JsonResponse({
                'cerrado':True,
            })
        
        # Procesar el formulario enviado
        form = TomaFisicaForm(request.POST, instance=toma_fisica) 
        if form.is_valid():
            toma = form.save(commit=False)
            toma.usuario = request.user
            toma.llenado = True
            toma.save()
            # messages.success(request, f'Toma física exitosa !!!')
            return JsonResponse({
                'success': True,
                'message': 'Toma física exitosa.',
                'toma_fisica':model_to_dict(toma_fisica)
            })
        else:
            # Devolver errores si el formulario no es válido
            errors = form.get_formatted_errors() if hasattr(form, 'get_formatted_errors') else str(form.errors)
            return JsonResponse({
                'success': False,
                'errors': errors
            }, status=400)


# Revisión inventario
@login_required(login_url='login')
def metro_inventario_revision(request, id):
    
    inventario = Inventario.objects.get(id=id)
    products = TomaFisica.objects.filter(inventario=id).order_by('orden', 'product__codigo_gim', 'product__marca')
    
    context = {
        'inventario':inventario,
        'products':products
    }
    return render(request, 'metro/inventario-revision.html', context)


@csrf_exempt
def metro_cambiar_orden_revision_ajax(request):
    if request.method == 'POST':
        data = json.loads(request.body)["n_orden"]
        
        for i in data:
            prod = TomaFisica.objects.get(id=i['id'])
            prod.orden = i['n_orden']
            prod.save()
            
        return JsonResponse({
            'msg':'ok'
        })


@csrf_exempt
@login_required(login_url='login')
def revision_check(request, id):
    
    # Obtener el producto o devolver 404 si no existe
    toma_fisica = get_object_or_404(TomaFisica, id=id)
    
    if request.method == 'POST':
        
        if toma_fisica.inventario.estado_inv == 'CERRADO':
            return JsonResponse({
                'cerrado':True,
            })
        
        toma_fisica.revisado = True
        toma_fisica.save()
        
        return JsonResponse({
                'success': True,
                'message': 'Toma física exitosa.',
                'toma_fisica':model_to_dict(toma_fisica)
            })


@csrf_exempt
@login_required(login_url='login')
def metro_consignacion(request):
    
    products = Product.objects.filter(activo=True).order_by('orden') #.filter(saldo=14)
    # products = [ i for i in Product.objects.filter(activo=True) if i.saldo > 0]
    
    # # Kardex.objects.all().delete()
    # for i in products:
    #     # print(i.id)
    #     # if i.codigo_gim != '70055':
    #         # print(i)
    #     k = Kardex(
    #         product = i,
    #         tipo = 'Ingreso',
    #         description = 'Saldo inicial',
    #         cantidad = i.consignacion,
    #         usuario_id = 1,
    #     )
    #     k.save()
    
    context = {
        'products':products
    }
    
    return render(request, 'metro/consignacion.html', context)


@csrf_exempt
@login_required(login_url='login')
def metro_kardex(request, product_id):
    
    product = Product.objects.get(id=product_id)
    kardex = Kardex.objects.filter(product__id=product_id)
    form = KardexForm()
    
    if request.method == 'POST':
        form = KardexForm(request.POST)
        if form.is_valid():
            form.save()
        else:
            print(form.errors)
    
    context = {
        'product':product,
        'kardex':kardex,
        'form':form
    }
    
    return render(request, 'metro/kardex.html', context)


@csrf_exempt
@login_required(login_url='login')
def metro_movimiento_edit(request, id):
    """
    Vista para manejar la edición de productos en un modal.
    GET: Devuelve el formulario HTML para mostrar en el modal
    POST: Procesa el formulario enviado y devuelve respuesta JSON
    """
    # Obtener el producto o devolver 404 si no existe
    product = get_object_or_404(Kardex, id=id)
    
    if request.method == 'POST':
        # Procesar el formulario enviado
        form = KardexForm(request.POST, instance=product, user=request.user) 
        if form.is_valid():
            form.save()
            messages.success(request, f'Movimiento editado correctamente !!!')
            return JsonResponse({
                'success': True,
                'message': f'Movimiento editado correctamente !!!',
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
        form = KardexForm(instance=product, user=request.user)
        return HttpResponse(form.as_p())

@csrf_exempt
@login_required(login_url='login')
def metro_movimiento_delete(request, id):
    try:
        mov = Kardex.objects.get(id=id)
        mov.delete()
        return JsonResponse({'success':True})
    except:
        return JsonResponse({'success':False})


def descargar_kardex(request, product_id):
    
    product = Product.objects.get(id=product_id)
    kardex = Kardex.objects.filter(product__id=product_id)
    
    data = []
    for i in kardex:
        data_row = {
            'Código HM': i.product.codigo_hm,
            'Código GIM': i.product.codigo_gim,
            'Nombre HM': i.product.nombre_hm,
            'Nombre GIM' : i.product.nombre_gim,
            'Marca': i.product.marca,
            'Cantidad en consig.': i.cantidad,
            'Precio unitario': i.product.precio_unitario_gim,
            'Factor': i.product.factor,
            'Precio unitario HM': i.product.precio_unitario_hm
        }
        
        data.append(data_row)
    reporte = pd.DataFrame(data)
    
    nombre_archivo = f'Kardex-{product.codigo_gim}_{datetime.datetime.now()}.xlsx'
    content_disposition = f'attachment; filename="{nombre_archivo}"'

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = content_disposition

    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        
        sheet_name = f'Kardex-{product.codigo_gim}'
        
        reporte.to_excel(writer, sheet_name=sheet_name, index=False)
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]
        
        worksheet.column_dimensions['A'].width = 12 # Código GIM
        worksheet.column_dimensions['B'].width = 12 # Código HM
        worksheet.column_dimensions['C'].width = 37 # Nombre GIM
        worksheet.column_dimensions['D'].width = 37 # Nombre HM
        worksheet.column_dimensions['E'].width = 10 # Marca
        worksheet.column_dimensions['F'].width = 17 # Consiganción
        worksheet.column_dimensions['G'].width = 17 # Precio unitario
        worksheet.column_dimensions['H'].width = 10 # Factor
        worksheet.column_dimensions['I'].width = 17 # Precio unitario hm
        
    return response