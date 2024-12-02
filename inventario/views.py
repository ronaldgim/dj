# Shorcuts
from django.shortcuts import render, redirect

# BD
from django.db import connections
from django.db.models import Sum

# Pandas
import pandas as pd
import numpy as np

# JSON
import json

# Models
from datos.models import Product
from .models import Inventario, InventarioTotale, Arqueo, ArqueoFisico, ArqueosCreados
from users.models import User, UserPerfil

# Forms
from .forms import InventarioForm, InventarioAgregarForm, InventarioTotalesForm, ArqueoForm

# Messages
from django.contrib import messages

# Django http
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse

# Datetime
from datetime import datetime, date, timedelta

# Login required
from django.contrib.auth.decorators import login_required, permission_required

# Shorcuts
from django.shortcuts import redirect

# Datos
from datos.views import (
    permisos,
    de_dataframe_a_template, 
    reservas_lote_product_id, 
    productos_odbc_and_django,
    trazabilidad_odbc)


# WMS
from wms.models import InventarioIngresoBodega, Movimiento

# HTTPS
from django.views.decorators.http import require_GET, require_POST


def stock_lote(): #request
    ''' Colusta de stock '''
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute("SELECT * FROM stock_lote")
        columns = [col[0] for col in cursor.description]
        stock = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
        
        stock_lote = pd.DataFrame(stock)
        
    return stock_lote 


### INVENTARIO ANDAGOYA
def stock_lote_inventario_andagoya(): #request
    ''' Colusta de stock '''
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute("SELECT * FROM warehouse.stock_lote WHERE WARE_CODE = 'BAN' OR WARE_CODE = 'CUA'")
        columns = [col[0] for col in cursor.description]
        clientes = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
        
        stock_lote = pd.DataFrame(clientes)
        productos = productos_odbc_and_django()[['product_id','Unidad_Empaque']]
        productos = productos.rename(columns={'product_id':'PRODUCT_ID'})
        stock_lote = stock_lote.merge(productos, on='PRODUCT_ID', how='left')
        
    return stock_lote 


def stock_lote_tupla():

    stock_mba = stock_lote_inventario_andagoya()
    stock_mba = stock_mba.to_dict('records')
    
    lista_stock_mba = []
    pk = 0

    for i in stock_mba:
        
        pk += 1
        prod_id     = i.get('PRODUCT_ID')
        prod_name   = i.get('PRODUCT_NAME')
        group_code  = i.get('GROUP_CODE')
        um          = i.get('UM')
        oh          = i.get('OH')
        oh2         = i.get('OH2')
        commited    = i.get('COMMITED')
        quantity    = i.get('QUANTITY')
        lote_id     = i.get('LOTE_ID')
        fecha_elab  = i.get('Fecha_elaboracion_lote')
        fecha_cadu  = i.get('FECHA_CADUCIDAD')
        ware_code   = i.get('WARE_CODE')
        location    = i.get('LOCATION').replace('/','') if '/' in i.get('LOCATION') else i.get('LOCATION')
        unidades_caja = i.get('Unidad_Empaque')
        
        numero_cajas = 0
        unidades_sueltas = 0
        total_unidades = 0
        diferencia = 0
        observaciones = ''
        llenado = False
        agregado = False
        user_id = None

        s_lote = (
            pk,
            prod_id,     
            prod_name,   
            group_code,  
            um,          
            oh,          
            oh2,         
            commited,    
            quantity,    
            lote_id,     
            fecha_elab,  
            fecha_cadu,  
            ware_code,   
            location,

            unidades_caja,
            numero_cajas,
            unidades_sueltas,
            total_unidades,
            diferencia,
            observaciones,
            llenado,
            agregado,
            user_id,
        )

        lista_stock_mba.append(s_lote)

    return lista_stock_mba


## GET REPORTE
@require_GET
def inventario_andagoya_get_stock(request):
    
    inventario = Inventario.objects.all().values(
        'product_id',
        'product_name',
        'group_code',
        'um',
        'oh',
        'oh2',
        'commited',
        'quantity',
        'lote_id',
        'fecha_elab_lote',
        'fecha_cadu_lote',
        'ware_code',
        'location',
        'unidades_caja',
        'numero_cajas',
        'unidades_sueltas',
        'total_unidades',
        'diferencia',
        'observaciones',
        'llenado',
        'agregado',
        'user__username',
    )
    
    total      = len(inventario)
    procesados = len(inventario.filter(llenado=True))
    
    porcentaje_avance = round((procesados / total) * 100, 0)
    procentaje_falta  = 100 - porcentaje_avance
    
    lista_ubicaciones = sorted(list(inventario.filter(ware_code='BAN').values_list('location', flat=True).distinct()))
    lista_avance = [round((inventario.filter(location=i, llenado=True).count()/inventario.filter(location=i).count())*100,1) for i in lista_ubicaciones]
    
    lista_totales = [porcentaje_avance, procentaje_falta]    
    
    return JsonResponse({
        'inventario': list(inventario),
        'total':total,
        'procesados':procesados,
        'ubicaciones': lista_ubicaciones,
        'avances': lista_avance,
        'totales': lista_totales
    })


@require_GET
def inventario_andagoya_actualizar_db(request):

    with connections['default'].cursor() as cursor:
        cursor.execute("TRUNCATE TABLE inventario_inventario")
    
    
    with connections['default'].cursor() as cursor:
        cursor.execute("TRUNCATE TABLE inventario_inventariototale")
    
    
    with connections['default'].cursor() as cursor:
        stock_mba = stock_lote_tupla()
        cursor.executemany("""
            INSERT INTO inventario_inventario 
            (id, product_id, product_name, group_code, um, oh, oh2, commited, quantity, lote_id, fecha_elab_lote, fecha_cadu_lote, ware_code, location, unidades_caja, numero_cajas, unidades_sueltas, total_unidades, diferencia, observaciones, llenado, agregado, user_id) 
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", 
            stock_mba)
    
    return JsonResponse({'msg':'ok'})


def inventario_andagoya_reportes(request):
    return render(request, 'inventario/toma_fisica/andagoya/reportes_andagoya.html')


### Reporte completo ###
@login_required(login_url='login')
def inventario_andagoya_home(request):
    
    inv = pd.DataFrame(Inventario.objects.all().values())
    bodega = inv[['ware_code', 'location', 'product_id']]

    bodega = bodega.groupby(['ware_code', 'location'])['product_id'].count()
    bodega = bodega.reset_index()
    
    bodega['Bodega'] = bodega.apply(lambda x: 
        'Andagoya' if x['ware_code'] == 'BAN' else 
        'Cerezos' if x['ware_code'] == 'BCT' else 
        'Cuarentena Andagoya' if x['ware_code'] == 'CUA' else
        'Cuarentena Cerezos' if x['ware_code'] == 'CUC' else 'Otras',
    axis=1)
    
    bodega = bodega.sort_values(['Bodega', 'location'])
    bodega = bodega.drop(index=0)

    bodega = de_dataframe_a_template(bodega)

    context = {
        'bodega':bodega
    }

    return render(request, 'inventario/toma_fisica/andagoya/home.html', context)


## Reporte completo excel ###
@login_required(login_url='login')
def reporte_completo_excel(request):
    
    # Conf Usuario
    users    = pd.DataFrame(User.objects.all().values())
    users = users.rename(columns={'id':'user_id'})
    users = users[['user_id', 'first_name', 'last_name']]
    users['usuario'] = users['first_name'] + ' ' + users['last_name']
    users = users[['user_id', 'usuario']]
    users['user_id'] = users['user_id'].astype(int)

    # Reporte 
    reporte_completo_excel = pd.DataFrame(Inventario.objects.all().values().order_by('group_code', 'product_id', 'fecha_cadu_lote'))
    reporte_completo_excel = reporte_completo_excel.fillna(0)
    reporte_completo_excel['user_id'] = reporte_completo_excel['user_id'].astype(int)
    reporte_completo_excel = reporte_completo_excel.merge(users, on='user_id', how='left')
    reporte_completo_excel = reporte_completo_excel.drop(['id', 'user_id'], axis=1)
    reporte_completo_excel = reporte_completo_excel.set_index('product_id')

    reporte_completo_excel['diferencia_ok'] = reporte_completo_excel['total_unidades'] - reporte_completo_excel['oh2']

    reporte_completo_excel = reporte_completo_excel[[
        'product_name', 'group_code', 'um', 'oh', 'oh2', 'commited', 
        'quantity', 
        'lote_id', 'fecha_elab_lote','fecha_cadu_lote', 'ware_code', 'location', 'unidades_caja', 'numero_cajas', 'unidades_sueltas', 'total_unidades',
        'diferencia_ok', 'observaciones', 'llenado', 'agregado', 'usuario'
    ]]

    reporte_completo_excel['fecha_elab_lote'] = reporte_completo_excel['fecha_elab_lote'].astype(str)
    reporte_completo_excel['fecha_cadu_lote'] = reporte_completo_excel['fecha_cadu_lote'].astype(str)

    date_time = str(datetime.now())
    date_time = date_time[0:16]
    n = 'Reporte Inventario Completo_' + date_time + '_.xlsx'
    nombre = 'attachment; filename=' + '"' + n + '"'

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = nombre

    reporte_completo_excel.to_excel(response)

    return response



@login_required(login_url='login')
def reporte_format_excel(request):

    reporte_completo_excel = pd.DataFrame(Inventario.objects.all().values())
    reporte_completo_excel = reporte_completo_excel[[
        'product_id', 
        'product_name', 
        'group_code', 
        'lote_id', 
        
        'fecha_cadu_lote', 
        'unidades_caja',
        'oh2'
        ]]
    
    reporte_completo_excel = reporte_completo_excel.fillna(0)
    reporte_completo_excel = reporte_completo_excel.sort_values(by=['group_code'])
    reporte_completo_excel = reporte_completo_excel.groupby([
        'product_id', 
        'product_name', 
        'group_code', 
        'lote_id', 
        
        'fecha_cadu_lote', 
        'unidades_caja',

        ])['oh2'].sum()
    
    # reporte_completo_excel.assign(total=reporte_completo_excel.sum(1).to_frame('oh2'))
    # reporte_completo_excel.stack(level='product_id')# total=reporte_completo_excel.sum(1).to_frame('oh2'))

    date_time = str(datetime.now())
    date_time = date_time[0:16]
    n = 'Reporte Format Completo_' + date_time + '_.xlsx'
    nombre = 'attachment; filename=' + '"' + n + '"'

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = nombre

    reporte_completo_excel.to_excel(response)

    return response



# Bodega
@login_required(login_url='login')
def inventario_por_bodega(request, bodega, ubicacion): 
    
    inventario = pd.DataFrame(Inventario.objects.all().order_by('group_code', 'product_id'). values())
    inventario = inventario.loc[(inventario['ware_code'] == bodega) & (inventario['location'] == ubicacion)]
    
    inventario = de_dataframe_a_template(inventario)

    n_inventario =len(inventario)
    n_inventario_llenado = len(Inventario.objects.filter(ware_code=bodega).filter(location=ubicacion).filter(llenado=True))
    n_inventario_nollenado = len(Inventario.objects.filter(ware_code=bodega).filter(location=ubicacion).filter(llenado=False))

    context = {
        'inventario':inventario,
        'mi_bodega':bodega,
        'mi_ubicacion':ubicacion,
        'n_inventario':n_inventario,
        'n_inventario_llenado':n_inventario_llenado,
        'n_inventario_nollenado':n_inventario_nollenado,
    }

    #return render(request, 'inventario/bodega_ubicacion_list.html', context)
    return JsonResponse(context)


def inventario_toma_fisica_andagoya_vue(request, bodega, location):
    return render(request, 'inventario/toma_fisica/andagoya/toma_fisica.html')


from django.forms.models import model_to_dict
def inventario_toma_fisica_item(request, item_id):
    
    if request.method == 'GET':
        
        # item
        item = Inventario.objects.get(id=item_id)
        item_dict = model_to_dict(item)
        
        # item totales
        item_totales = (InventarioTotale.objects
            .filter(product_id_t=item.product_id)
            .filter(ware_code_t=item.ware_code)
            .filter(location_t=item.location)
        )
        
        return JsonResponse({
            'item': item_dict,
            'item_totales': model_to_dict(item_totales.first()) if item_totales.first() else {},
            })


### INVENTARIO FORM UPDATE ###
@login_required(login_url='login')
def inventario_update(request, id, bodega, ubicacion):

    instancia = Inventario.objects.get(id=id)
    inventario_totales = InventarioTotalesForm(initial={
        'unidades_caja_t':0,
        # 'numero_cajas_t':0,
        # 'unidades_sueltas_t':0
    })
    
    productos_total = InventarioTotale.objects.filter(ware_code_t=bodega).filter(location_t=ubicacion).filter(product_id_t=instancia.product_id)
    total_unds = []
    for i in productos_total:
        p_t = i.total_unidades_t
        total_unds.append(p_t)
    t_unds = sum(total_unds)
    

    inventario_lotes = Inventario.objects.filter(ware_code=bodega).filter(location=ubicacion).filter(product_id=instancia.product_id)
    total_lotes = []
    for i in inventario_lotes:
        t = i.total_unidades
        total_lotes.append(t)
    t_lotes = sum(total_lotes)
    print(inventario_lotes)
    print(total_lotes)

    diferencia = t_unds - t_lotes
    
    if request.method == 'GET':

        form = InventarioForm(instance=instancia)

        context = {
        'instancia':instancia,
        'form':form,
        'inventario_totales':inventario_totales,
        'bodega':bodega,
        'ubicacion':ubicacion,

        'productos_total':productos_total,
        'inventario_lotes':inventario_lotes,

        't_lotes':t_lotes,
        'diferencia':diferencia
        }

    elif request.method == 'POST':

        if productos_total.exists(): #or instancia.agregado
            #inventario_lotes = Inventario.objects.filter(ware_code=bodega).filter(location=ubicacion).filter(product_id=instancia.product_id)
            form = InventarioForm(request.POST, instance=instancia)

            if form.is_valid():
                form.save()

                messages.success(request, 'Invenario tomado con éxito !!!')
                return redirect(f'/inventario/inv/{bodega}/{ubicacion}')
            else:
                messages.error(request, 'Error, ingrese nuevamente')
                return redirect(f'/inventario/inv/{bodega}/{ubicacion}')

        else:

            form = InventarioForm(request.POST, instance=instancia)
            form_totales = InventarioTotalesForm(request.POST)

            if form.is_valid() and form_totales.is_valid():
                form.save()
                form_totales.save()

                messages.success(request, 'Invenario tomado con éxito !!!')
                return redirect(f'/inventario/inv/{bodega}/{ubicacion}')
            else:
                messages.error(request, 'Error, ingrese nuevamente')
                return redirect(f'/inventario/inv/{bodega}/{ubicacion}')

    return render(request, 'inventario/form_inventario.html', context)


### Inventario update totales
@login_required(login_url='login')
def inventario_update_totales(request, id):
    
    inv_totales_instance = InventarioTotale.objects.get(id=id)
    form = InventarioTotalesForm(instance=inv_totales_instance)
    pro = Product.objects.get(product_id=inv_totales_instance.product_id_t)

    if request.method == 'POST':
        form_update = InventarioTotalesForm(request.POST, instance=inv_totales_instance)
        if form_update.is_valid():
            form_update.save()
            messages.success(request, 'Total de unidades editado con éxito !!!')
            return redirect(f'/inventario/inv/{inv_totales_instance.ware_code_t}/{inv_totales_instance.location_t}')
        else:
            messages.error(request, 'Error, intente nuevamente') 
            return redirect(f'/inventario/inv/{inv_totales_instance.ware_code_t}/{inv_totales_instance.location_t}')


    context = {
        'inv_totales_instance':inv_totales_instance,
        'form':form,
        'instancia':pro
    }

    return render(request, 'inventario/totales_form_update.html', context)


### INVENTARIO FORM AGREGAR ###
@login_required(login_url='login')
def inventario_agregar(request, bodega, ubicacion):

    form = InventarioAgregarForm(initial={
        'unidades_caja':0,
        'numero_cajas':0,
        'unidades_sueltas':0
    })
    prod = Product.objects.all()

    context = {
        'form':form,
        'prod':prod
    }

    try:
        if request.method == 'GET':

            prod = request.GET.get('producto')
            prod = str(prod)
            p = productos_odbc_and_django()
            p = p[p['product_id']==prod].to_dict('records')[0]
            
            if not p == '':

                context = {
                'form':form,
                'cod':p.get('product_id'), #p.product_id,
                'nom':p.get('Nombre'), #p.description,
                'mar':p.get('Marca'), #p.marca,
                'bodega':bodega,
                'ubicacion':ubicacion
                }

        elif request.method == 'POST':
            
            form_ag = InventarioAgregarForm(request.POST)

            if form_ag.is_valid():
                form_ag.save()
                messages.success(request, 'Invenario tomado con éxito !!!')
                return redirect(f'/inventario/inv/{bodega}/{ubicacion}')
            else:
                messages.error(request, 'Error, ingrese nuevamente')
                return redirect(f'/inventario/inv/{bodega}/{ubicacion}')

    except:
        context = {
            'form':form,
            'prod':prod,
            'bodega':bodega,
            'ubicacion':ubicacion
        }

    return render(request, 'inventario/form_agregar_inventario.html', context)












# # WMS ADD INVENTARIO INICIAL
# def inventario_inicial_wms(request):
    
#     id_inv = int(request.POST['id_inv'])
    
#     inv = Inventario.objects.get(id=id_inv)

#     ingreso = InventarioIngresoBodega(
#         product_id          = inv.product_id,
#         lote_id             = inv.lote_id,
#         fecha_caducidad     = inv.fecha_cadu_lote,
#         bodega              = inv.location,
#         unidades_ingresadas = inv.total_unidades,
#         n_referencia        = 'inv_in_1',
#         referencia          = 'Inventario Inicial',
#         id_ref              = id_inv
#     )
    
#     ingreso.save()
    
#     return JsonResponse({'id':ingreso.id})





#### ARQUEOS
# Nuevo Arqueo
def nuevo_arqueo(request):

    arqueo_form = ArqueoForm()

    if request.method == 'POST':
        form = ArqueoForm(request.POST)
        p = request.POST.getlist('productos')
        prod_list = [Product.objects.get(id=i).product_id for i in p]

        if form.is_valid():
            f = form.save()

            stock = stock_lote()[stock_lote().PRODUCT_ID.isin(prod_list)].sort_values(by=['PRODUCT_ID','WARE_CODE','LOCATION','FECHA_CADUCIDAD'])
            stock['id_arqueo'] = f.id
            stock = stock[[
                'id_arqueo',
                'PRODUCT_ID',
                'PRODUCT_NAME',
                'GROUP_CODE',
                'UM',
                'OH',
                'OH2',
                'COMMITED',
                'QUANTITY',
                'LOTE_ID',
                'Fecha_elaboracion_lote',
                'FECHA_CADUCIDAD',
                'WARE_CODE',
                'LOCATION'
            ]]

            stock_insert = stock.to_dict('records')

            if stock.empty:
                messages.error(request, 'No stock en bodega de estos items !!!')
            
            else:

                stock_bulck_creat = []
                for i in stock_insert:

                    pr = ArqueoFisico(
                        id_arqueo       = i['id_arqueo'],
                        product_id      = i['PRODUCT_ID'],
                        product_name    = i['PRODUCT_NAME'],
                        group_code      = i['GROUP_CODE'],
                        um              = i['UM'],
                        oh              = i['OH'],
                        oh2             = i['OH2'],
                        commited        = i['COMMITED'],
                        quantity        = i['QUANTITY'],
                        lote_id         = i['LOTE_ID'],
                        fecha_elab_lote = i['Fecha_elaboracion_lote'],
                        fecha_cadu_lote = i['FECHA_CADUCIDAD'],
                        ware_code       = i['WARE_CODE'],
                        location        = i['LOCATION']
                    )
                    
                    stock_bulck_creat.append(pr)
                    
                ArqueoFisico.objects.bulk_create(stock_bulck_creat)

            return redirect(f'view/{f.id}')

    context = {
        'arqueo_form':arqueo_form
    }
    
    return render(request, 'inventario/arqueos/nuevo_arqueo.html', context)


# Vista para ver y editar los productos antes de crear los arqueos
def arqueo_view(request, id):

    arqueo = Arqueo.objects.get(id=id)
    arqueo_d = arqueo.descripcion
    productos = ArqueoFisico.objects.filter(id_arqueo = id).order_by('ware_code','location')
    bodegas = pd.DataFrame(productos.order_by('ware_code').values('ware_code'))['ware_code']
    bodegas = list(bodegas.unique())

    prod_list = list(arqueo.productos.values_list('product_id', flat=True))
    prod = productos_odbc_and_django()
    prod = prod[prod.product_id.isin(prod_list)]
    prod = de_dataframe_a_template(prod)
    
    context = {
        'arqueo':arqueo,
        'productos': productos,
        'bod':bodegas,

        'arqueo_id':arqueo.id,
        'arqueo_enum':arqueo.enum,
        'arqueo_f_h':arqueo.fecha_hora,
        'arqueo_d':arqueo_d,

        'arqueo':id,
        'prod':prod,

    }
    
    return render(request, 'inventario/arqueos/detalle_arqueo.html', context)


# Vista para ingrear y editar los arqueos ya creados 
def arqueo_edit_view(request, id, ware_code):

    arqueo    = Arqueo.objects.get(id=id)
    arqueo_d  = arqueo.descripcion
    productos = ArqueoFisico.objects.filter(id_arqueo = id).filter(ware_code=ware_code).order_by('ware_code','location')
    bodegas   = pd.DataFrame(productos.order_by('ware_code').values('ware_code'))['ware_code']
    bodegas   = list(bodegas.unique())

    prod_list = list(arqueo.productos.values_list('product_id', flat=True))
    prod = productos_odbc_and_django()
    prod = prod[prod.product_id.isin(prod_list)]
    prod = de_dataframe_a_template(prod)
    
    context = {
        'arqueo':arqueo,
        'productos': productos,
        'bod':bodegas,

        'arqueo_id':arqueo.id,
        'arqueo_enum':arqueo.enum,
        'arqueo_f_h':arqueo.fecha_hora,
        'arqueo_d':arqueo_d,

        'arqueo':id,
        'prod':prod
    }
    
    return render(request, 'inventario/arqueos/detalle_edit_arqueo.html', context)


# Ajax para editar items
def add_item_arqueo(request):
    
    prod = request.POST['prod_id']
    p = Product.objects.get(product_id=prod)
    
    p_product_name = p.description
    p_group_code = p.marca
    
    item = ArqueoFisico.objects.create(
        id_arqueo       = int(request.POST['arqueo']),
        product_id      = prod,
        product_name    = p_product_name,
        group_code      = p_group_code,
        oh              = int(request.POST['unds']),
        lote_id         = request.POST['lote_id'],
        fecha_cadu_lote = request.POST['f_cadu'],
        ware_code       = request.POST['bode'],
        location        = request.POST['ubic'],

        oh2             = 0,
        commited        = 0,
        quantity        = 0,
        fecha_elab_lote = '2000-01-01',
    )

    item.save()

    return HttpResponse('ok')


# eliminar producto en arqueo
def eliminar_fila_arqueo(request):
    
    id_row = int(request.POST['id'])
    
    try:
        instancia = ArqueoFisico.objects.get(id=id_row)
        instancia.delete()
        return HttpResponse('ok')
    
    except:
        return HttpResponse('error')
    

def editar_fila_arqueo(request):
    
    id_row = int(request.POST['id'])
    n_mba = int(request.POST['n_mba']) 

    try:
        instancia = ArqueoFisico.objects.get(id=id_row)
        instancia.oh = n_mba
        instancia.save()

        return HttpResponse('ok')
    
    except:
        return HttpResponse('error')
    

# Crear arqueos
def arqueos_por_bodega(request):

    bodegas = request.POST['bodegas']
    arqueo_id = int(request.POST['arqueo_id'])

    arq = Arqueo.objects.get(id=arqueo_id)
    
    prod = ArqueoFisico.objects.filter(id_arqueo=arqueo_id).values_list('product_id', flat=True).distinct()
    prod_list = list(prod)

    reservas_list = {}
    reservas_list['reservas'] = reservas_lote_product_id(prod_list)
    reservas_mba = json.dumps(reservas_list)

    descripcion = request.POST['descripcion']
    bodegas = bodegas.strip('[]').split(',')

    bodegas_list = [i.strip() for i in bodegas]     

    # Enum de arqueo
    n_len = len(str(arqueo_id))
    nn = str(arqueo_id)
    if n_len == 3:
        enum = nn
    elif n_len == 2:
        enum = '0'+nn
    elif n_len == 1:
        enum = '00'+nn
    else:
        enum = nn
    

    arqueos_creados_list = []
    for i in bodegas_list:
        bod = i.replace("'", "")

        if bod == 'BAN':
            b = 'Andagoya'
        elif bod == 'BCT':
            b = 'Cerezos'
        elif bod == 'CUA':
            b = 'Cuarentena Andagoya'
        elif bod == 'CUC':
            b = 'Cuarentena Cerezos'
        else:
            b = 'Desconocida'       

        arqueo_creado = ArqueosCreados(
            arqueo       = arq,
            arqueo_enum  = enum + ' - ' + bod,
            bodega       = b,
            descripcion  = descripcion.strip(),
            estado       = 'CREADO',
            ware_code    = bod,
            reservas     = reservas_mba,
        )

        arqueos_creados_list.append(arqueo_creado)
    
    ArqueosCreados.objects.bulk_create(arqueos_creados_list)
    
    return HttpResponse('ok')


# Anular arqueo creado
def anular_arqueo_creado(request):
    
    arqueo_enum = request.POST['arqueo']
    
    arq = ArqueosCreados.objects.get(arqueo_enum=arqueo_enum)
    arq.estado = 'ANULADO'
    arq.save()
    
    return HttpResponse('ok')


# Lista de arqueos creados
def arqueos_list(request):

    arqueos_creados = ArqueosCreados.objects.all().order_by('-arqueo','ware_code')
    
    if request.method=='POST':
        d = request.POST['desde']
        h = request.POST['hasta']        
        desde = datetime.strptime(d, '%Y-%m-%d')
        hasta = datetime.strptime(h, '%Y-%m-%d')
        hasta = hasta + timedelta(hours=23) + timedelta(minutes=59)
        
        arqs = (ArqueosCreados.objects
                .filter(estado='FINALIZADO')
                .filter(fecha_hora_actualizado__range=[desde, hasta])
            )
        
        arqs_ids = arqs.values_list('arqueo_id', flat=True)
        
        arqs_df = arqs.values(
            'arqueo_id',
            'arqueo_enum',
            'fecha_hora_actualizado',
            'usuario__first_name',
            'usuario__last_name',
            'descripcion',
            'ware_code'
        )
        arqs_df = pd.DataFrame(arqs_df)
        arqs_df = arqs_df.rename(columns={'arqueo_id':'id_arqueo'})
        
        arqs_fisico_df = pd.DataFrame(ArqueoFisico.objects.filter(id_arqueo__in=arqs_ids).values(
            'id_arqueo',
            'product_id',
            'product_name',
            'group_code',
            'observaciones2',
            'diferencia'
        ))
        
        df = arqs_df.merge(arqs_fisico_df, on='id_arqueo', how='left')
        df['fecha_hora_actualizado'] = pd.to_datetime(df['fecha_hora_actualizado']).dt.date
        df['Responsable'] = df['usuario__first_name'] + ' ' + df['usuario__last_name']
        df = df.rename(columns={
            'fecha_hora_actualizado':'Fecha',
            'arqueo_enum':'No. Arqueo',
            'ware_code':'Bodega',
            'product_id':'Referencia',
            'product_name':'Descripción',
            'group_code':'Marca',
            'observaciones2':'Obs-AD',
            'diferencia':'Diferencia'
        })
        
        df = df[[
            'Responsable',
            'Fecha',
            'No. Arqueo',
            'Bodega',
            'Referencia',
            'Descripción',
            'Marca',
            'Obs-AD',
            'Diferencia'
        ]]
        
        df['Fecha'] = df['Fecha'].astype(str)
        
        hoy = str(datetime.today())
        n = 'Reporte-Arqueos_'+hoy+'.xlsx'
        nombre = 'attachment; filename=' + '"' + n + '"'
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        response['Content-Disposition'] = nombre
        df.to_excel(response, index=False)
        
        return response
        
    context = {
        'arqueos':arqueos_creados
    }

    return render(request, 'inventario/arqueos/lista.html', context)


# Lista de arqueos por crear
def arqueos_pendientes_list(request):
    
    arqueos_list_ids = Arqueo.objects.values_list('id', flat=True)
    arqueos_list_ids = set(arqueos_list_ids)

    arqueos_fisicos_list_ids = ArqueosCreados.objects.values_list('arqueo_id', flat=True)
    arqueos_fisicos_list_ids = set(arqueos_fisicos_list_ids)
    
    arqueos_pendientes = arqueos_list_ids.difference(arqueos_fisicos_list_ids)
    
    arqueos = Arqueo.objects.filter(id__in=arqueos_pendientes)
    
    context = {
        'arqueos':arqueos,
        'pendientes':1
    }
    
    return render(request, 'inventario/arqueos/pendientes_lista.html', context)


def arqueo_bodega_view(request, arqueo, ware_code):

    arqueo_creado = ArqueosCreados.objects.filter(arqueo_id=arqueo).filter(ware_code=ware_code).first() 
    reservas = json.loads(arqueo_creado.reservas)['reservas']
    
    arqueo_fisico = ArqueoFisico.objects.filter(id_arqueo=arqueo).filter(ware_code=ware_code)
    prod = arqueo_fisico.values_list('product_id', flat=True).distinct()
    
    qq = []

    for i in prod:
        prod_query        = arqueo_fisico.filter(product_id=i)
        prod_total_mba    = prod_query.aggregate(total_mba=Sum('oh'))['total_mba']
        prod_diferencia   = prod_query.aggregate(diferencia=Sum('diferencia'))['diferencia']
        prod_total_fisico = prod_query.aggregate(total_fisico=Sum('total_unidades'))['total_fisico']

        q = {}
        q['product_id']       = i
        q['prod_query']       = prod_query
        q['prod_total_mba']   = prod_total_mba
        #q['prod_diferencia']  = prod_diferencia
        q['prod_diferencia']  = prod_total_fisico - prod_total_mba 
        q['prod_total_fisico']= prod_total_fisico
        q['reservas']         = [r for r in reservas if r['PRODUCT_ID']==i if r['WARE_CODE']==ware_code] 
        
        qq.append(q)

    context = {
        'arqueo_creado':arqueo_creado,
        'arqueo_fisico':arqueo_fisico,
        'reservas':reservas,
        'qq':qq
    }

    return render(request, 'inventario/arqueos/ver_arqueo.html', context)


def arqueos_list_bodega(request, ware_code):

    arqueos_creados = ArqueosCreados.objects.filter(ware_code=ware_code).order_by('-arqueo','ware_code')

    context = {
        'arqueos':arqueos_creados
    }

    return render(request, 'inventario/arqueos/lista_bodega.html', context)


# Vista de toma fisica de inventario
def arqueo_bodega_tomafisica(request, arqueo, ware_code):

    # print(request.user)
    arqueo_creado = ArqueosCreados.objects.filter(arqueo_id=arqueo).filter(ware_code=ware_code).first() 
    arqueo_fisico = ArqueoFisico.objects.filter(id_arqueo=arqueo).filter(ware_code=ware_code)

    prod = arqueo_fisico.values_list('product_id', flat=True).distinct() 

    productos = Product.objects.filter(product_id__in = prod)
    bodega = arqueo_creado.ware_code    

    arqueo_id = arqueo_creado.arqueo_id

    if bodega == 'BAN':
        ubicacion = ['AN1', 'AN4', 'BN1', 'BN2', 'BN3','BN4']
    elif bodega == 'BCT':
        ubicacion = ['CN4','CN5','CN6','CN7']
    else:
        ubicacion = ['N/U']
        # ubicacion = ['NU']

    context = {
        'arqueo_creado':arqueo_creado,
        'arqueo_fisico':arqueo_fisico,

        'arqueo_id':arqueo_id,
        'productos':productos,
        'bodega':bodega,
        'ubicacion':ubicacion
    }

    return render(request, 'inventario/arqueos/toma_fisica.html', context)


# Ajax - Cambio de estado de inventario
def arqueo_cambiar_estado_ajax(request):
    
    arqueo_id = int(request.POST['arqueo_id'])
    est = request.POST['estado']
    u_id = int(request.POST['usuario'])
    usr = User.objects.get(id=u_id)

    arqueo = ArqueosCreados.objects.get(id=arqueo_id)
    arqueo.estado = est
    arqueo.usuario = usr
    arqueo.save()

    return HttpResponse('ok')


# Toma fisica de inventario - Ajax por registro 
def toma_fisica_inventario_ajax(request):
    
    # Variables de request Ajax
    id_arqueo          = int(request.POST['id'])
    unidades_caja_r    = int(request.POST['unidades_caja'])
    numero_cajas_r     = int(request.POST['numero_cajas'])
    unidades_sueltas_r = int(request.POST['unidades_sueltas'])
    observaciones_r    = request.POST['observaciones']
    
    # Row
    arqueo = ArqueoFisico.objects.get(id=id_arqueo)
    
    # Calculos
    total_unds = (unidades_caja_r * numero_cajas_r) + unidades_sueltas_r
    und_mba = arqueo.oh
    dif_unds = total_unds - und_mba 

    # Save method
    arqueo.unidades_caja    = unidades_caja_r
    arqueo.numero_cajas     = numero_cajas_r
    arqueo.unidades_sueltas = unidades_sueltas_r
    arqueo.total_unidades   = total_unds
    arqueo.diferencia       = dif_unds
    arqueo.observaciones    = observaciones_r
    arqueo.llenado          = True

    arqueo.save()
    
    return HttpResponse('ok')


# Añadir un registro a la toma fisica de inventario
def add_registro_tomafisica_ajax(request):

    id_arqueo_r = int(request.POST['id_arqueo'])
    bodega_r = request.POST['bodega']

    prod = request.POST['product_id']
    product = Product.objects.get(product_id=prod)
    codigo = product.product_id
    nombre = product.description
    marca  = product.marca

    ubicacion_r = request.POST['ubicacion']
    lote_r = request.POST['lote']
    fecha_elab_r = request.POST['fecha_elab']
    fecha_cadu_r = request.POST['fecha_cadu']

    unidades_caja_r = int(request.POST['unidades_caja'])
    numero_cajas_r = int(request.POST['numero_cajas'])
    unidades_sueltas_r = int(request.POST['unidades_sueltas'])

    observaciones_r = request.POST['observaciones']


    # Calculos
    total_unds = (unidades_caja_r * numero_cajas_r) + unidades_sueltas_r
    dif = 0 - total_unds

    reg = ArqueoFisico.objects.create(
        id_arqueo       = id_arqueo_r,
        product_id      = codigo,
        product_name    = nombre,
        group_code      = marca,

        oh              = 0,
        oh2             = 0,
        commited        = 0,
        quantity        = 0,

        lote_id         = lote_r,
        fecha_elab_lote = fecha_elab_r,
        fecha_cadu_lote = fecha_cadu_r,
        ware_code       = bodega_r,
        location        = ubicacion_r,

        unidades_caja   = unidades_caja_r,
        numero_cajas    = numero_cajas_r,
        unidades_sueltas = unidades_sueltas_r,
        total_unidades  = total_unds,
        diferencia      = dif,
        observaciones   = observaciones_r,

        llenado         = True,
        agregado        = True
    )

    reg.save()

    return HttpResponse('ok')


# Ajax add observación 2 en arqueos
def add_obs2_ajax(request):
    
    # Variables de request Ajax
    id_row       = int(request.POST['id'])
    obs_r        = request.POST['obs2']
    
    # Row
    arqueo = ArqueoFisico.objects.get(id=id_row)
    
    # Save method
    arqueo.observaciones2 = obs_r
    arqueo.save()
    
    return HttpResponse('ok')


#@permiso('TRAZABILIDAD', '/inventario/bodegas', 'Trazabilidad')
def trazabilidad(request):
    
    try:

        if request.method == 'POST':

            cod = request.POST['codigo']
            lot = request.POST['lote']
            
            tr = trazabilidad_odbc(cod, lot)[[
                'DOC_ID_CORP',
                'NOMBRE_CLIENTE',
                'DATE_I',
                'FECHA_FACTURA',
                'INGRESO_EGRESO',
                'EGRESO_TEMP',
                'TIPO_MOVIMIENTO',
                'WARE_COD_CORP'
            ]]
            
            tr['FECHA'] = tr.apply(lambda x: x['DATE_I'] if x['FECHA_FACTURA']==None else x['FECHA_FACTURA'] if x['DATE_I']==None else '', axis=1)
            tr['CANTIDAD'] = tr.apply(lambda x: x['EGRESO_TEMP']*-1 if x['INGRESO_EGRESO']=='-' else x['EGRESO_TEMP'], axis=1)

            tr['FECHA'] = pd.to_datetime(tr['FECHA'])
            tr = tr.sort_values(by='FECHA', ascending=True).fillna('-')
            tr['FECHA'] = tr['FECHA'].astype(str)

            bodegas = tr['WARE_COD_CORP'].unique()
            movimientos = tr['TIPO_MOVIMIENTO'].unique()

            trz_list = []

            for i in bodegas:
                t = tr[tr['WARE_COD_CORP']==i]

                t_ingreso_compras = t[t['TIPO_MOVIMIENTO']=='RP']
                t_ingreso_compras = t_ingreso_compras['CANTIDAD'].sum()

                t_transf_ingreso = t[t['TIPO_MOVIMIENTO']=='TI']
                t_transf_ingreso = t_transf_ingreso['CANTIDAD'].sum()

                t_egreso          = t[(t['TIPO_MOVIMIENTO']=='FT') | (t['TIPO_MOVIMIENTO']=='MA')]
                t_egreso          = t_egreso['CANTIDAD'].sum()

                t_transf_egreso  = t[t['TIPO_MOVIMIENTO']=='TE']
                t_transf_egreso  = t_transf_egreso ['CANTIDAD'].sum()

                otros = t_ingreso_compras + t_transf_ingreso + t_transf_egreso + t_egreso

                cantidad_actual = t['CANTIDAD'].sum()

                tabla = de_dataframe_a_template(t)

                trz = {}
                trz['bodega'] = i
                trz['ingreso_compras'] = t_ingreso_compras
                trz['transferencia_ingreso'] = t_transf_ingreso
                trz['egreso'] = t_egreso
                trz['transferencia_egreso'] = t_transf_egreso
                trz['otros'] = otros
                trz['cantidad_actual'] = cantidad_actual
                trz['tabla']  = tabla

                trz_list.append(trz)
            
            context = {
            'cod':cod,
            'lot':lot,
            'trazabilidad':trz_list,
            'bodegas':bodegas,
            'movimientos':movimientos
            }
            
            return render(request, 'inventario/trazabilidad/trazabilidad.html', context)
        
    except:
        context = {
            'cod':cod,
            'lot':lot,
            'mensaje':'No hay conisidencias entre código y lote'
            }
        
        return render(request, 'inventario/trazabilidad/trazabilidad.html', context)


    context={}

    return render(request, 'inventario/trazabilidad/trazabilidad.html', context)
    