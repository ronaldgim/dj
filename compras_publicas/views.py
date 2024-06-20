from django.shortcuts import render

# BD
from django.db import connections, transaction

# Datetime
from datetime import datetime, timedelta

# # Tabla productos DJANGO
# from datos.models import Product

# Pandas
import pandas as pd
import numpy as np

# Json
import json

# Pyodbc
import pyodbc
import mysql.connector

# Paginado
from django.core.paginator import Paginator

# Model
from compras_publicas.models import ProcesosSercop, Anexo, Producto
from wms.models import Movimiento

# Forms
from compras_publicas.forms import ProcesosSercopForm, ProductoForm

# Messages
from django.contrib import messages

# Django shortcuts
from django.shortcuts import render, redirect

# Login
from django.contrib.auth.decorators import login_required

# Clientes
from datos.views import (
    clientes_warehouse, 
    productos_odbc_and_django,
    
    # Permisos costum @decorador
    permisos,
    
    # pedidos
    #pedidos_cerrados_bct
    datos_anexo,
    datos_anexo_product_list

    )

# http response
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404

# PDF
from django_xhtml2pdf.utils import pdf_decorator

# Calculos
from django.db.models import Sum, Count


# Funcios para pasar de dataframe a registros para el template
def de_dataframe_a_template(dataframe):

    json_records = dataframe.reset_index().to_json(orient='records') # reset_index().
    dataframe = json.loads(json_records)

    return dataframe


# Create your views here.
# tabla de facturas
def tabla_facturas(cliente):
    ''' Colusta de clientes por ruc a la base de datos '''
    with connections['gimpromed_sql'].cursor() as cursor:
        #cursor.execute("SELECT * FROM venta_facturas")
        cursor.execute(
            f"SELECT * FROM warehouse.venta_facturas WHERE CODIGO_CLIENTE = '{cliente}' AND FECHA > '2021-01-01'"
        )

        columns = [col[0] for col in cursor.description]
        facturas = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        facturas = pd.DataFrame(facturas)
    return facturas


# Tabla infimas
def tabla_infimas():

    one_year = datetime.now().date()
    days = 365
    one_year_ago = one_year - timedelta(days=days)

    with connections['infimas_sql'].cursor() as cursor:
        cursor.execute(
            # """SELECT infimas.Fecha, entidad.Nombre, infimas.Proveedor,
            # infimas.Objeto_Compra, infimas.Cantidad, infimas.Costo, infimas.Valor, infimas.Tipo_Compra, entidad.Nombre
            # FROM entidad, infimas
            # WHERE infimas.Codigo_Entidad = entidad.Codigo"""

            f"""SELECT infimas.Fecha, entidad.Nombre, infimas.Proveedor,
            infimas.Objeto_Compra, infimas.Cantidad, infimas.Costo, infimas.Valor,
            infimas.Tipo_Compra, entidad.Nombre

            FROM entidad, infimas
            WHERE infimas.Codigo_Entidad = entidad.Codigo
            AND infimas.Fecha > '{one_year_ago}'
            AND infimas.Tipo_Compra = 'Otros Bienes'
            """
        )
        columns = [col[0] for col in cursor.description]
        infimas = [ # Lista de diccionarios
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
    infimas = pd.DataFrame(infimas)
    infimas['Fecha'] = infimas['Fecha'].astype(str)
    # infimas = infimas[infimas['Fecha']>'2023-01-01']
    infimas = infimas.sort_values(by=['Fecha'], ascending=[False])
    # infimas = infimas[infimas['Tipo_Compra']=='Otros Bienes']
    infimas = infimas.reset_index()

    return infimas



def clientes_hospitales_publicos():

    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(
        "SELECT CODIGO_CLIENTE, NOMBRE_CLIENTE, CLIENT_TYPE FROM warehouse.clientes WHERE CLIENT_TYPE = 'HOSPU'"
    )

        columns = [col[0] for col in cursor.description]
        hpublicos = [ # Lista de diccionarios
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

    return hpublicos


def facturas_por_product(producto):

    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(
        f"SELECT * FROM warehouse.venta_facturas WHERE PRODUCT_ID = '{producto}' AND FECHA > '2021-01-01'"
    )

        columns = [col[0] for col in cursor.description]
        producto = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
        
        producto = pd.DataFrame(producto)
        prod = productos_odbc_and_django()[['product_id','Nombre','Marca']]
        prod = prod.rename(columns={'product_id':'PRODUCT_ID'})
        cli  = clientes_warehouse()[['CODIGO_CLIENTE','NOMBRE_CLIENTE']]
        
        producto = producto.merge(prod, on='PRODUCT_ID', how='left')
        producto = producto.merge(cli, on='CODIGO_CLIENTE', how='left')
        
        producto = producto.rename(columns={
            'PRODUCT_ID':'Código',
            'FECHA':'Fecha',
            'QUANTITY':'Cantidad',
            'UNIT_PRICE':'Precio Unitario',
            'NOMBRE_CLIENTE':'Cliente'
        })
        
        producto = producto[['Código','Nombre','Marca','Cliente','Fecha','Cantidad','Precio Unitario']]

    return producto


def facturas_por_product_ajax(request):
    
    product_id = request.POST['producto']
    ventas = facturas_por_product(product_id)
    ventas['Precio Unitario'] = ventas['Precio Unitario'].astype(float)
    ventas['Cantidad'] = ventas['Cantidad'].apply(lambda x:'{:,.0f}'.format(x))
    ventas['Precio Unitario'] = ventas['Precio Unitario'].apply(lambda x:'$ {:,.2f}'.format(x))
    ventas = ventas.sort_values(by='Fecha', ascending=False)
    
    ventas = ventas.to_html(
        #classes='table', 
        table_id='v_table',
        index=False,
        justify='start',
        border=0
    )
    
    return HttpResponse(ventas)

    


# precios historicos
@login_required(login_url='login')
@permisos(['COMPRAS PUBLICAS'], '/', 'ingresar a Compras Públicas')
def precios_historicos(request):

    hospitales = clientes_hospitales_publicos()
    
    context = {
        'hospitales':hospitales,
    }
    
    if request.method == 'POST':
        try:        
            hospitales = clientes_hospitales_publicos()
            prod = productos_odbc_and_django()
            prod = prod.rename(columns={'product_id':'PRODUCT_ID'})
            
            hospital = request.POST['hospital']
            
            facturas = tabla_facturas(hospital)
            clientes = clientes_warehouse()[['CODIGO_CLIENTE', 'NOMBRE_CLIENTE']]
            
            precios_filtrado = facturas.merge(clientes, on='CODIGO_CLIENTE', how='left')
            precios_filtrado = precios_filtrado.merge(prod, on='PRODUCT_ID', how='left')
            precios_filtrado = precios_filtrado.sort_values(by=['FECHA'], ascending=[False])
            
            h = precios_filtrado['NOMBRE_CLIENTE'].iloc[0]
            
            precios_filtrado = de_dataframe_a_template(precios_filtrado)        

            context = {
                'h':h,
                'precios_filtrado':precios_filtrado,
                'hospitales':hospitales,
                }
        except:
            messages.error(request, 'Error, intente nuevamente !!!')
            
        return render(request, 'compras_publicas/precios.html', context)

    return render(request, 'compras_publicas/precios.html', context)



from django.http import JsonResponse

def my_ajax_view(request):
    data = {
        "key1": "value1",
        "key2": "value2",
    }

    # data = tabla_infimas()
    # data = data.to_json(orient='table')
    # data = json.loads(data)

    # print(data)
    return JsonResponse(data)


# Infimas
def infimas(request):

    infimas = tabla_infimas() #[:10] # Tabla infimas
    infimas = de_dataframe_a_template(infimas)

    paginator   = Paginator(infimas, 50)
    page_number = request.GET.get('page')

    if page_number == None:
        page_number = 1

    infimas = paginator.get_page(page_number)

    if request.method == 'POST':
        busqueda = request.POST['busqueda']
        infimas_df = tabla_infimas()
        infimas_df['Objeto_Compra'] = infimas_df['Objeto_Compra'].astype(str)
        infimas_df['Objeto_Compra'] = infimas_df.Objeto_Compra.str.lower()
        infimas_df = infimas_df[infimas_df['Objeto_Compra'].str.contains(busqueda)] #contains(busqueda)
        resultados = len(infimas_df)
        infimas_df = de_dataframe_a_template(infimas_df)

        # paginator = Paginator(infimas_df, 200)
        # page_number = 1 #request.POST.get('page')
        # infimas_df = paginator.get_page(page_number)

        context = {
            'infimas':infimas_df,
            'busqueda':busqueda,
            'resultados':resultados,
            }

        return render(request, 'compras_publicas/infimas.html', context)

    context = {
        'infimas':infimas
        }

    return render(request, 'compras_publicas/infimas.html', context)


def procesos_sercop_sql():
    with connections['procesos_sercop'].cursor() as cursor:
        cursor.execute("""
            SELECT * 
            FROM procesos_sercop.procesos
            LEFT JOIN procesos_sercop.fechas
            ON procesos_sercop.procesos.Codigo = procesos_sercop.fechas.Codigo
            """)

        columns  = [col[0] for col in cursor.description]
        procesos = [dict(zip(columns, row)) for row in cursor.fetchall()]

        procesos = pd.DataFrame(procesos)

        return procesos



def procesos_sercop(request):

    procesos = pd.DataFrame(ProcesosSercop.objects.all().order_by('-fecha_hora').values())
    procesos_sql = procesos_sercop_sql()
    procesos_sql = procesos_sql.rename(columns={'Codigo':'proceso'})

    procesos = procesos.merge(procesos_sql, on='proceso', how='left')
    procesos = procesos.sort_values(by=['fecha_hora','Fecha_Puja','Hora_Puja'], ascending=[False,False,True])
    
    procesos = de_dataframe_a_template(procesos)

    form = ProcesosSercopForm()

    if request.method == 'POST':
        form = ProcesosSercopForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'El proceso se agrego correctamente !!!')
            return redirect('/compras-publicas/procesos-sercop')

        else:
            messages.error(request, form.errors)
            return redirect('/compras-publicas/procesos-sercop')

    context = {
        'procesos':procesos,
        'form':form
    }

    return render(request, 'compras_publicas/procesos_sercop.html', context)





### ANEXOS
@login_required(login_url='login')
def anexos_list(request):
    
    anexos = Anexo.objects.all().order_by('-id')   
    context = {
        'anexos':anexos
    }
    
    return render(request, 'compras_publicas/anexos_list.html', context)


@transaction.atomic
def add_datos_anexo_ajax(request):
    
    try:
        contrato_id = request.POST.get('contrato_id')
        
        anexo_data = datos_anexo(contrato_id)    
        anexo_product_data = datos_anexo_product_list(contrato_id)
        
        anexo = Anexo(
            n_pedido  = anexo_data['CONTRATO_ID'],
            fecha     = anexo_data['FECHA_PEDIDO'],
            cliente   = anexo_data['NOMBRE_CLIENTE'],
            ruc       = anexo_data['IDENTIFICACION_FISCAL'],
            direccion = anexo_data['DIRECCION'],
        )
        
        anexo.save()
        
        if anexo.id:
            
            prod_list = []
            for i in anexo_product_data:
                product = Producto(
                    product_id      = i['PRODUCT_ID'],
                    nombre          = i['Nombre'],
                    presentacion    = i['Unidad'],
                    marca           = i['Marca'],
                    procedencia     = i['Procedencia'],
                    r_sanitario     = i['Reg_San'],
                    lote_id         = i['LOTE_ID'],
                    f_elaboracion   = i['Fecha_elaboracion_lote'],
                    f_caducidad     = i['FECHA_CADUCIDAD'],
                    cantidad        = i['EGRESO_TEMP'],
                    cantidad_total  = i['EGRESO_TEMP'],
                    precio_unitario = i['Price'],
                ) 
                
                product.save()
                prod_list.append(product)
            
            anexo.product_list.add(*prod_list)
            
            return JsonResponse({
                'type':'ok',
                'redirect_url':f'/compras-publicas/anexos/{anexo.id}'
                })
        
    except Exception as e:    
        
        return JsonResponse({
            'type':'error',
            'msg':str(e)
        })


@login_required(login_url='login')
def anexo_detail(request, anexo_id):
    
    anexo = Anexo.objects.get(id=anexo_id)
    products = anexo.product_list.all().order_by('product_id')
    
    context = {
        'anexo':anexo,
        'products':products
    }
    
    return render(request, 'compras_publicas/anexo_detail.html', context)


@login_required(login_url='login')
@require_POST
def anexo_cabecera_edit_ajax(request):
    anexo_id = int(request.POST.get('id', 0))
    anexo_field = request.POST.get('name')
    anexo_value = request.POST.get('value')
    
    # Validar entrada
    if not anexo_id or not anexo_field or anexo_value is None:
        return JsonResponse({'msg': 'fail', 'error': 'Invalid input'})

    # Obtener el anexo o retornar 404
    anexo = get_object_or_404(Anexo, id=anexo_id)
    
    # Diccionario para mapear campos
    valid_fields = {
        'fecha':'fecha',
        'cliente': 'cliente',
        'ruc': 'ruc',
        'direccion': 'direccion',
        'orden_compra': 'orden_compra',
        'n_factura':'n_factura',
        'observaciones': 'observaciones'
    }

    # Verificar si el campo es válido
    if anexo_field in valid_fields:
        # Actualizar el campo del modelo dinámicamente
        setattr(anexo, valid_fields[anexo_field], anexo_value)
        anexo.save()
        
        # Verificar si el campo se actualizó correctamente
        if getattr(anexo, valid_fields[anexo_field]) == anexo_value:
            return JsonResponse({'msg': 'ok'})
        else:
            return JsonResponse({'msg': 'fail'})
    
    return JsonResponse({'msg': 'fail', 'error': 'Invalid field'})


@login_required(login_url='login')
def anexo_edit_product_ajax(request):
    
    if request.method=='GET':
        producto = Producto.objects.get(id=int(request.GET.get('product_id', 0)))    
        return HttpResponse(
        f"""
            <input type="hidden" name="id_prod" value="{producto.id}">
            <div class="modal-body">
                <div class="row g-3 align-items-center">
                    <div class="col-4">
                        <label for="product_id" class="col-form-label fw-bold">Código:</label>
                    </div>
                    <div class="col-8">
                        <input type="text" name="product_id" class="form-control form-control-sm" value="{producto.product_id}"  aria-describedby="passwordHelpInline">
                    </div>
                </div>
            
                <div class="row g-3 align-items-center">
                    <div class="col-4">
                        <label for="nombre" class="col-form-label fw-bold">Nombre:</label>
                    </div>
                    <div class="col-8">
                        <input type="text" name="nombre" class="form-control form-control-sm" value="{producto.nombre}" aria-describedby="passwordHelpInline">
                    </div>
                </div>

                <div class="row g-3 align-items-center">
                    <div class="col-4">
                        <label for="nombre_generico" class="col-form-label fw-bold">Nombre Generico:</label>
                    </div>
                    <div class="col-8">
                        <input type="text" name="nombre_generico" class="form-control form-control-sm" value="{producto.nombre_generico}" aria-describedby="passwordHelpInline">
                    </div>
                </div>
            
                <div class="row g-3 align-items-center">
                    <div class="col-4">
                        <label for="presentacion" class="col-form-label fw-bold">Presentación:</label>
                    </div>
                    <div class="col-8">
                        <input type="text" name="presentacion" class="form-control form-control-sm" value="{producto.presentacion}" aria-describedby="passwordHelpInline">
                    </div>
                </div>

                <div class="row g-3 align-items-center">
                    <div class="col-4">
                        <label for="marca" class="col-form-label fw-bold">Marca:</label>
                    </div>
                    <div class="col-8">
                        <input type="text" name="marca" class="form-control form-control-sm" value="{producto.marca}"  aria-describedby="passwordHelpInline">
                    </div>
                </div>
            
                <div class="row g-3 align-items-center">
                    <div class="col-4">
                        <label for="procedencia" class="col-form-label fw-bold">Procedencia:</label>
                    </div>
                    <div class="col-8">
                        <input type="text" name="procedencia" class="form-control form-control-sm" value="{producto.procedencia}" aria-describedby="passwordHelpInline">
                    </div>
                </div>

                <div class="row g-3 align-items-center">
                    <div class="col-4">
                        <label for="r_sanitario" class="col-form-label fw-bold">Registro Sanitario:</label>
                    </div>
                    <div class="col-8">
                        <input type="text" name="r_sanitario" class="form-control form-control-sm" value="{producto.r_sanitario}" aria-describedby="passwordHelpInline">
                    </div>
                </div>

                <div class="row g-3 align-items-center">
                    <div class="col-4">
                        <label for="lote" class="col-form-label fw-bold">Lote:</label>
                    </div>
                    <div class="col-8">
                        <input type="text" name="lote_id" class="form-control form-control-sm" value="{producto.lote_id}" aria-describedby="passwordHelpInline">
                    </div>
                </div>

                <div class="row g-3 align-items-center">
                    <div class="col-4">
                        <label for="f_elaboracion" class="col-form-label fw-bold">F.Elaboración:</label>
                    </div>
                    <div class="col-8">
                        <input type="date" name="f_elaboracion" class="form-control form-control-sm" value="{producto.f_elaboracion}" aria-describedby="passwordHelpInline">
                    </div>
                </div>

                <div class="row g-3 align-items-center">
                    <div class="col-4">
                        <label for="f_caducidad" class="col-form-label fw-bold">F.Caducidad:</label>
                    </div>
                    <div class="col-8">
                        <input type="date" name="f_caducidad" class="form-control form-control-sm" value="{producto.f_caducidad}" aria-describedby="passwordHelpInline">
                    </div>
                </div>

                <div class="row g-3 align-items-center">
                    <div class="col-4">
                        <label for="cantidad" class="col-form-label fw-bold">Cantidad:</label>
                    </div>
                    <div class="col-8">
                        <input type="number" name="cantidad" class="form-control form-control-sm" value="{producto.cantidad}" aria-describedby="passwordHelpInline">
                    </div>
                </div>
                
                <div class="row g-3 align-items-center">
                    <div class="col-4">
                        <label for="cantidad_total" class="col-form-label fw-bold">Cantidad total:</label>
                    </div>
                    <div class="col-8">
                        <input type="number" name="cantidad_total" class="form-control form-control-sm" value="{producto.cantidad_total}" aria-describedby="passwordHelpInline">
                    </div>
                </div>
                
                <div class="row g-3 align-items-center">
                    <div class="col-4">
                        <label for="precio_unitario" class="col-form-label fw-bold">Precio Unitario:</label>
                    </div>
                    <div class="col-8">
                        <input type="number" step="0.001" name="precio_unitario" class="form-control form-control-sm" value="{producto.precio_unitario}" aria-describedby="passwordHelpInline">
                    </div>
                </div>
            </div>
        """
        )
    
    if request.method == 'POST':
        
        anexo = Anexo.objects.get(id=int(request.POST.get('id_anexo')))
        
        producto = Producto.objects.get(id=int(request.POST.get('id_prod')))
        form = ProductoForm(request.POST, instance=producto)
    
        if form.is_valid():
            form.save()
            return redirect('anexo_detail', anexo.id)


@pdf_decorator(pdfname='anexo_formato_general.pdf')
@login_required(login_url='login')
def anexo_formato_general(request, anexo_id):
    
    anexo = Anexo.objects.get(id=anexo_id)
    products = anexo.product_list.all().order_by('product_id')
    subtotal = products.aggregate(p_total=Sum('precio_total'))['p_total']
    mas_iva = subtotal * 0.15
    total = subtotal + mas_iva
    
    context = {
        'anexo':anexo,
        'products':products,
        'subtotal':subtotal,
        'mas_iva':mas_iva,
        'total':total
    }

    return render(request, 'compras_publicas/anexo_formato_general.html', context)


@pdf_decorator(pdfname='anexo_formato_hbo.pdf')
@login_required(login_url='login')
def anexo_formato_hbo(request, anexo_id):
    
    anexo = Anexo.objects.get(id=anexo_id)
    anexo_prod_list = anexo.product_list.all()
    
    prods_list =[]
    
    for i in anexo.product_list.all().values_list('product_id', flat=True).distinct():
        prods = {}
        prods['product_id'] = i
        prods['products'] = anexo_prod_list.filter(product_id=i) 
        prods['nombre'] = anexo_prod_list.filter(product_id=i).first().nombre
        prods['nombre_generico'] = anexo_prod_list.filter(product_id=i).first().nombre_generico
        prods['marca'] = anexo_prod_list.filter(product_id=i).first().marca
        prods['r_sanitario'] = anexo_prod_list.filter(product_id=i).first().r_sanitario
        prods['prods_len'] = len(anexo_prod_list.filter(product_id=i))
        prods['cantidad_total_2'] = anexo_prod_list.filter(product_id=i).aggregate(cantidad_total_2=Sum('cantidad'))['cantidad_total_2']
        
        prods_list.append(prods)
    
    context = {
        'anexo':anexo,
        'prods_list':prods_list,
    }

    return render(request, 'compras_publicas/anexo_formato_hbo.html', context)


@pdf_decorator(pdfname='anexo_formato_hcam.pdf')
@login_required(login_url='login')
def anexo_formato_hcam(request, anexo_id):
    
    anexo = Anexo.objects.get(id=anexo_id)
    products = anexo.product_list.all().order_by('product_id')
    subtotal = products.aggregate(p_total=Sum('precio_total'))['p_total']
    mas_iva = subtotal * 0.15
    total = subtotal + mas_iva
    
    context = {
        'anexo':anexo,
        'products':products,
        'subtotal':subtotal,
        'mas_iva':mas_iva,
        'total':total
    }

    return render(request, 'compras_publicas/anexo_formato_hcam.html', context)


from num2words import num2words

@pdf_decorator(pdfname='anexo_formato_hpas.pdf')
@login_required(login_url='login')
def anexo_formato_hpas(request, anexo_id):
    
    anexo = Anexo.objects.get(id=anexo_id)
    products = anexo.product_list.all().order_by('product_id')
    subtotal = products.aggregate(p_total=Sum('precio_total'))['p_total']
    mas_iva = subtotal * 0.15
    total = subtotal + mas_iva
    
    total_str = num2words(total, lang='es', to='currency')
    total_str = total_str.replace('euros', 'dolares')
    total_str = total_str.replace('céntimos', 'centavos')
    
    context = {
        'anexo':anexo,
        'products':products,
        'subtotal':subtotal,
        'mas_iva':mas_iva,
        'total':total,
        'total_str':total_str
    }

    return render(request, 'compras_publicas/anexo_formato_hpas.html', context)