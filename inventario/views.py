# Shorcuts
from django.shortcuts import render, redirect

# BD
from django.db import connections
from django.db.models import Sum, F, Value, Q
from django.db.models.functions import Concat


# Pandas
import pandas as pd
import numpy as np

# JSON
import json

# Models
from datos.models import Product
from .models import Inventario, InventarioTotale, InventarioCerezos, InventarioCerezosTotale, Arqueo, ArqueoFisico, ArqueosCreados
from users.models import User, UserPerfil

# models WMS
from wms.models import Existencias, Ubicacion

# Forms
from .forms import InventarioForm, InventarioAgregarForm, InventarioTotalesForm,  InventarioCerezosForm, InventarioCerezosAgregarForm, InventarioCerezosTotalesForm, ArqueoForm

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

from django.views.decorators.csrf import csrf_exempt
from django.forms.models import model_to_dict
from etiquetado.models import ProductoUbicacion


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
        connections['gimpromed_sql'].close()
    return stock_lote 


### INVENTARIO ANDAGOYA
def stock_lote_inventario_andagoya(): #request
    ''' Colusta de stock '''
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute("SELECT * FROM warehouse.stock_lote WHERE WARE_CODE = 'BAN' OR WARE_CODE = 'CUA'")
        columns = [col[0] for col in cursor.description]
        stock = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
        
        stock_lote = pd.DataFrame(stock)
        productos = productos_odbc_and_django()[['product_id','Unidad_Empaque']]
        productos = productos.rename(columns={'product_id':'PRODUCT_ID'})
        stock_lote = stock_lote.merge(productos, on='PRODUCT_ID', how='left')
        connections['gimpromed_sql'].close()
    return stock_lote 


def stock_lote_inventario_andagoya_agrupado():

    stock_mba = stock_lote_inventario_andagoya()

    stock_mba['LOTE_ID'] = stock_mba['LOTE_ID'].str.replace('.','',regex=False)
    stock_mba['LOTE_ID'] = stock_mba['LOTE_ID'].str.strip()    
    
    stock_mba_group = stock_mba.copy()
    stock_mba_group = stock_mba_group.groupby(by=[
        'PRODUCT_ID',
        'LOTE_ID',
        'WARE_CODE',
        'LOCATION',
        'Fecha_elaboracion_lote',
        'FECHA_CADUCIDAD',
    ])[['OH2','OH','COMMITED','QUANTITY']].sum().reset_index()
    
    stock_mba_str = stock_mba.copy()
    stock_mba_str = stock_mba_str[[
            'PRODUCT_ID',
            'PRODUCT_NAME',
            'GROUP_CODE',
            'UM',
            'Unidad_Empaque',
            'LOTE_ID',
            # 'Fecha_elaboracion_lote',
            # 'FECHA_CADUCIDAD',
            'WARE_CODE',
            'LOCATION',
    ]]
    stock_mba_str = stock_mba_str.drop_duplicates(subset=[
            'PRODUCT_ID',
            'PRODUCT_NAME',
            'GROUP_CODE',
            'UM',
            'Unidad_Empaque',
            'LOTE_ID',
            # 'Fecha_elaboracion_lote',
            # 'FECHA_CADUCIDAD',
            'WARE_CODE',
            'LOCATION',
        ], 
        keep='first')
    
    stock_mba_final = stock_mba_group.merge(stock_mba_str, on=[
        'PRODUCT_ID',
        'LOTE_ID',
        'WARE_CODE',
        'LOCATION',
    ], how='left')
    stock_mba_final = stock_mba_final[[
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
        'LOCATION',
        'Unidad_Empaque',
    ]]
    
    return stock_mba_final


def stock_lote_tupla():

    stock_mba_final = stock_lote_inventario_andagoya_agrupado()
    stock_mba_final = stock_mba_final.to_dict('records')
    
    lista_stock_mba = []
    pk = 0
    for i in stock_mba_final:
        
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
        # lote_id     = i.get('LOTE_ID').replace('.', '') if '.' in i.get('LOTE_ID') else i.get('LOTE_ID')
        fecha_elab  = i.get('Fecha_elaboracion_lote')
        fecha_cadu  = i.get('FECHA_CADUCIDAD')
        ware_code   = i.get('WARE_CODE')
        location    = i.get('LOCATION').replace('/','') if '/' in i.get('LOCATION') else i.get('LOCATION')
        unidades_caja = i.get('Unidad_Empaque')
        
        numero_cajas = 0 
        unidades_sueltas = 0 
        unidades_estanteria = 0
        total_unidades = 0 
        diferencia = 0 
        
        observaciones = ''
        llenado = False
        agregado = False
        user_id = None
        llenado_estanteria = False

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
            unidades_estanteria,
            llenado_estanteria
        )

        lista_stock_mba.append(s_lote)

    return lista_stock_mba


def inventario_home(request):
    
    inventario_andagoya = Inventario.objects.all().count()
    inventario_andagoya_llenado = Inventario.objects.filter(llenado=True).count()
    andagoya = 0 if inventario_andagoya == 0 else round(inventario_andagoya_llenado / inventario_andagoya, 0)
    
    inventario_cerezos = InventarioCerezos.objects.all().count()
    inventario_cerezos_llenado = InventarioCerezos.objects.filter(llenado=True).count()
    cerezos = 0 if inventario_cerezos == 0 else round(inventario_cerezos_llenado / inventario_cerezos, 0)
    
    context = {
        'andagoya':inventario_andagoya,
        'andagoya_llenado':inventario_andagoya_llenado,
        'avance_andagoya':andagoya,
        
        'cerezos':inventario_cerezos,
        'cerezos_llenado':inventario_cerezos_llenado,
        'avance_cerezos':cerezos,
    }
    
    return render(request, 'inventario/toma_fisica/home.html', context)

# Wms andagoya 
def producto_ubicacion_wms_andagoya():
    
    producto_ubicacion = ProductoUbicacion.objects.all() 
    
    data_list = []
    for i in producto_ubicacion:
        product_id = i.product_id
        ubicaciones_len = len(i.ubicaciones.all())
        
        if ubicaciones_len > 1:
            data = {
                'product_id':product_id,
                'doble_ubicacion':'SI'
            }
            
            data_list.append(data)
            
    data_df = pd.DataFrame(data_list)
    data_df = data_df.drop_duplicates(subset='product_id')
    
    if not data_df.empty:
        return data_df
    
    return pd.DataFrame()


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
        'unidades_estanteria',
        'total_unidades',
        'diferencia',
        'observaciones',
        'llenado',
        'llenado_estanteria',
        'agregado',
        'user__username',
    )
    
    doble_ubicacion = producto_ubicacion_wms_andagoya()
    inventario_df = pd.DataFrame(inventario)
    
    if not doble_ubicacion.empty:
        inventario_df = inventario_df.merge(doble_ubicacion, on='product_id', how='left')
        inventario_df['doble_ubicacion'] = inventario_df['doble_ubicacion'].fillna('NO')
    elif doble_ubicacion.empty:
        inventario_df['doble_ubicacion'] = 'NO'
    
    inventario_df['fecha_elab_lote'] = inventario_df['fecha_elab_lote'].astype('str')
    inventario_df['fecha_cadu_lote'] = inventario_df['fecha_cadu_lote'].astype('str')
    inventario_df['llenado_ok'] = inventario_df['llenado'] | inventario_df['llenado_estanteria']
    
    total      = len(inventario) 
    procesados = len(inventario.filter(llenado=True)) 
    estanteria = len(inventario.filter(llenado_estanteria=True)) 
    procesados_bod_est = len(inventario_df[inventario_df['llenado_ok']==True]) 
    
    # porcentaje_avance = 0 if total == 0 else round((procesados / total) * 100, 0)
    porcentaje_avance = 0 if total == 0 else round((procesados_bod_est / total) * 100, 0)
    procentaje_falta  = 100 - porcentaje_avance
    
    
    lista_ubicaciones = sorted(list(inventario.filter(ware_code='BAN').values_list('location', flat=True).distinct()))
    # lista_avance = [round((inventario.filter(location=i, llenado=True).count()/inventario.filter(location=i).count())*100,1) for i in lista_ubicaciones]
    lista_avance = [round((inventario.filter(location=i).filter(Q(llenado=True) | Q(llenado_estanteria=True)).count()/inventario.filter(location=i).count())*100,1) for i in lista_ubicaciones]    
    
    lista_totales = [porcentaje_avance, procentaje_falta]    
    
    return JsonResponse({
        #'inventario': list(inventario),
        'inventario':de_dataframe_a_template(inventario_df),
        'total':total,
        'procesados':procesados,
        'estanteria':estanteria,
        'procesados_bod_est':procesados_bod_est,
        'ubicaciones': lista_ubicaciones,
        'avances': lista_avance,
        'totales': lista_totales
    })


@require_GET
def inventario_andagoya_actualizar_db(request):
    
    try:
        with connections['default'].cursor() as cursor:
            cursor.execute("TRUNCATE TABLE inventario_inventario")
            connections['default'].close()
        
        
        with connections['default'].cursor() as cursor:
            cursor.execute("TRUNCATE TABLE inventario_inventariototale")
            connections['default'].close()
        
        with connections['default'].cursor() as cursor:
            stock_mba = stock_lote_tupla()
            cursor.executemany("""
                INSERT INTO inventario_inventario 
                (id, product_id, product_name, group_code, um, oh, oh2, commited, quantity, lote_id, fecha_elab_lote, fecha_cadu_lote, ware_code, location, unidades_caja, numero_cajas, unidades_sueltas, total_unidades, diferencia, observaciones, llenado, agregado, user_id, unidades_estanteria, llenado_estanteria) 
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", 
                stock_mba)
            connections['default'].close()
        
        return JsonResponse({'msg':'ok'})
    except Exception as e:
        return JsonResponse({'msg': str(e)})


def inventario_andagoya_reportes(request):
    return render(request, 'inventario/toma_fisica/andagoya/reportes_andagoya.html')


### ANDAGOYA ###
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
    bodega = de_dataframe_a_template(bodega)
    
    context = {
        'bodega':bodega,
        'general':Inventario.objects.all().count()
    }

    return render(request, 'inventario/toma_fisica/andagoya/home.html', context)


@login_required(login_url='login')
def inventario_por_bodega(request, bodega, ubicacion): 
    
    inv = (
    Inventario.objects.filter(
        Q(ware_code=bodega) &
        Q(location=ubicacion)
        )
        .order_by('group_code', 'product_id')
        .annotate(total_unidades_ok=F('total_unidades') - F('unidades_estanteria'))
    )
    
    inv_df = pd.DataFrame(inv.values())
    
    inventario = de_dataframe_a_template(inv_df)

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


@login_required(login_url='login')
def inventario_toma_fisica_andagoya_vue(request, bodega, location):
    return render(request, 'inventario/toma_fisica/andagoya/toma_fisica.html')


# from etiquetado.views import productos_ubicacion_lista_template
from etiquetado.models import ProductoUbicacion

@login_required(login_url='login')
def inventario_general(request): 

    n_inventario = Inventario.objects.all().count()
    n_inventario_llenado = Inventario.objects.filter(llenado_estanteria=True).count()  # Inventario.objects.filter(llenado=True).count()
    n_inventario_nollenado = Inventario.objects.filter(llenado_estanteria=False).count()  # Inventario.objects.filter(llenado=False).count()

    producto_ubicacion = ProductoUbicacion.objects.all() 
    ubicaciones = []
    for i in producto_ubicacion:
        data = {
            'id':i.id,
            'product_id': i.product_id,
            # 'ware_code':i.ubicaciones.bodega if i.ubicaciones.exists() else '',
            'ubicaciones': list([{'estanteria': j.estanteria ,'nombre': j.nombre} for j in i.ubicaciones.all()])
        }
        ubicaciones.append(data)

    inventario_data = []
    for i in Inventario.objects.all():
        for j in ubicaciones:
            if i.product_id == j['product_id']:
                data = {
                    'id':i.id,
                    'product_id': i.product_id,
                    'product_name':i.product_name,
                    'group_code':i.group_code,
                    'um':i.um,
                    'lote_id':i.lote_id,
                    'unidades_estanteria':i.unidades_estanteria,
                    'ware_code':i.ware_code,
                    'location':j['ubicaciones'],
                }
                inventario_data.append(data)

    context = {
        'inventario':inventario_data,
        'n_inventario':n_inventario,
        'n_inventario_llenado':n_inventario_llenado,
        'n_inventario_nollenado':n_inventario_nollenado,
    }

    return JsonResponse(context)


@login_required(login_url='login')
def inventario_general_toma_fisica_andagoya_vue(request):
    return render(request, 'inventario/toma_fisica/andagoya/toma_fisica_general.html')


@csrf_exempt
def inventario_toma_fisica_item(request, item_id):
    
    if request.method == 'GET':
        
        # item
        item = Inventario.objects.get(id=item_id)
        item_dict = model_to_dict(item)
        
        # item totales
        item_totales = InventarioTotale.objects.filter(
            Q(product_id_t=item.product_id) &
            Q(ware_code_t=item.ware_code) &
            Q(location_t=item.location)
        )
        
        lotes = Inventario.objects.filter(
            Q(product_id=item.product_id) &
            Q(ware_code=item.ware_code) &
            Q(location=item.location)
        ).annotate(unidades_ok=F('total_unidades') - F('unidades_estanteria'))
        
        # print(lotes.values('total_unidades','unidades_estanteria','unidades_ok'))
        # .values('lote_id', 'total_unidades', 'unidades_estanteria', 'unidades_ok')
        
        total_lotes = lotes.aggregate(unidades=Sum('unidades_ok'))
        total_agrupado = item_totales.aggregate(unidades=Sum('total_unidades_t')) if item_totales.exists() else {'unidades':0}
        diferencia = total_lotes['unidades'] - total_agrupado['unidades']
        
        # print('T.Lotes', total_lotes['unidades'])
        # print('T.Agrupado', total_agrupado['unidades'])
        # print('Diferencia', diferencia)    
        
        return JsonResponse({
            'item': item_dict,
            'item_totales': model_to_dict(item_totales.first()) if item_totales.first() else None,
            'lotes':list(lotes.values('product_id', 'lote_id', 'unidades_ok')),
            'total_lotes':total_lotes['unidades'],
            'total_agrupado':total_agrupado['unidades'],
            'diferencia':diferencia
            })
    
    elif request.method == 'POST':
        
        data = json.loads(request.body)
        data['user'] = User.objects.get(id=data.get('user_id'))
        my_instance = Inventario.objects.get(id=item_id)
        form = InventarioForm(data, instance = my_instance)
        
        if form.is_valid():
            form.save()
            return JsonResponse({
                'type':'success',
                'msg':'Registrado Correctamiente'})
        else:
            return JsonResponse({'type':'danger','msg':form.errors})


@csrf_exempt
def inventario_toma_fisica_estanteria_item(request, item_id):
    
    if request.method == 'GET':
        
        # item
        item = Inventario.objects.get(id=item_id)
        item_dict = model_to_dict(item)
        
        # # item totales
        # item_totales = (InventarioTotale.objects
        #     .filter(product_id_t=item.product_id)
        #     .filter(ware_code_t=item.ware_code)
        #     .filter(location_t=item.location)
        # )
        
        return JsonResponse({
            'item': item_dict,
            # 'item_totales': model_to_dict(item_totales.first()) if item_totales.first() else None,
            })
    
    elif request.method == 'POST':
        from .forms import InventarioEstanteriaForm
        
        data = json.loads(request.body)
        # data['user'] = User.objects.get(id=data.get('user_id'))
        my_instance = Inventario.objects.get(id=item_id)
        form = InventarioEstanteriaForm(data, instance = my_instance)
        
        if form.is_valid():
            form.save()
            return JsonResponse({
                'type':'success',
                'msg':'Registrado Correctamiente'})
        else:
            return JsonResponse({'type':'danger','msg':form.errors})


@csrf_exempt
def inventario_toma_fisica_total_agrupado(request):
    
    if request.method == 'POST':
        data = json.loads(request.body)
        data['user'] = User.objects.get(id=data.get('user_id'))
        
        # actualizar registro
        if data.get('id'):
            item_totales = InventarioTotale.objects.get(id=data.get('id'))            
            form = InventarioTotalesForm(data, instance=item_totales)
            if form.is_valid():                
                item = form.save()
                return JsonResponse({
                    'type':'success','msg':'Actualizado Correctamiente',
                    'unidades':item.total_unidades_t
                    })
            else:
                return JsonResponse({'type':'danger','msg':form.errors})
        
        # crear registro
        else:
            form = form = InventarioTotalesForm(data)
            if form.is_valid():
                item = form.save()
                return JsonResponse({
                    'type':'success', 'msg':'Registrado Correctamente',
                    'unidades':item.total_unidades_t})
            else:
                return JsonResponse({'type':'danger','msg':form.errors})


@csrf_exempt
def inventario_toma_fisica_buscar_producto(request):
    
    if request.method == 'POST':
        data = json.loads(request.body) 
        product_id = data.get('product_id').get('codigo')
        product = productos_odbc_and_django()
        product = product[product['product_id']==product_id][[
            'product_id','Nombre','Marca','Unidad','Unidad_Empaque'
        ]]
        
        data_lotes = Inventario.objects.filter(product_id=product_id).values('lote_id','fecha_elab_lote','fecha_cadu_lote').distinct()
        
        if not product.empty:
            return JsonResponse({
                'type':'success', 
                'msg':'Producto encontrado !!!', 
                'product':product.to_dict(orient='records')[0],
                'data_lotes':list(data_lotes)
                })
        else:
            return JsonResponse({
                'type':'danger',
                'msg':f'No se encuentra resultados para {product_id}'
                })


@csrf_exempt
def inventario_toma_fisica_agregar_producto(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        data['user'] = User.objects.get(id=data.get('user_id'))
        
        form = InventarioAgregarForm(data)
        if form.is_valid():
            form.save()
            return JsonResponse({'type':'success','msg':'Producto agregado correctamente'})
        else:
            return JsonResponse({'type':'danger','msg':form.errors})


## Reporte completo excel ###
@login_required(login_url='login')
def reporte_completo_excel(request):

    doble_ubicacion = producto_ubicacion_wms_andagoya()

    reporte_completo_excel = pd.DataFrame(Inventario.objects.all().values(
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
        'unidades_estanteria',
        'total_unidades',
        'diferencia',
        'observaciones',
        'llenado',
        'llenado_estanteria',
        'agregado',
        'user__username'
    ).order_by('group_code', 'product_id', 'fecha_cadu_lote'))

    reporte_completo_excel['diferencia_ok'] = reporte_completo_excel['total_unidades'] - reporte_completo_excel['oh2']

    reporte_completo_excel['fecha_elab_lote'] = reporte_completo_excel['fecha_elab_lote'].astype(str)
    reporte_completo_excel['fecha_cadu_lote'] = reporte_completo_excel['fecha_cadu_lote'].astype(str)
    
    if not doble_ubicacion.empty:
        reporte_completo_excel = reporte_completo_excel.merge(doble_ubicacion, on='product_id', how='left')
        reporte_completo_excel['doble_ubicacion'] = reporte_completo_excel['doble_ubicacion'].fillna('NO')
    elif doble_ubicacion.empty:
        reporte_completo_excel['doble_ubicacion'] = 'NO'
    
    reporte_completo_excel = reporte_completo_excel[[
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
        'unidades_estanteria',
        'total_unidades',
        'diferencia_ok',
        # 'diferencia',
        'doble_ubicacion',
        'observaciones',
        'llenado',
        'llenado_estanteria',
        'agregado',
        'user__username'
        ]]

    date_time = str(datetime.now())
    date_time = date_time[0:16]
    n = 'Reporte Inventario Completo_' + date_time + '_.xlsx'
    nombre = 'attachment; filename=' + '"' + n + '"'

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = nombre

    reporte_completo_excel.to_excel(response, index=False)

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


@login_required(login_url='login')
def reporte_andagoya_bpa(request):
    
    inv = Inventario.objects.all().values(
        'product_id',
        'product_name',
        'group_code',
        'um',
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
        'unidades_estanteria',
        'total_unidades',
        'diferencia',
        'observaciones',
        'user__username'
    )

    inv_df = pd.DataFrame(inv).sort_values(by=['ware_code','location','product_id','lote_id','fecha_elab_lote'])
    inv_df['fecha_elab_lote']   = inv_df['fecha_elab_lote'].astype('str')
    inv_df['fecha_cadu_lote']   = inv_df['fecha_cadu_lote'].astype('str')
    inv_df['subtotal_unidades'] = inv_df['numero_cajas'] * inv_df['unidades_caja'].astype(int) + inv_df['unidades_sueltas']
    inv_df['unidades_caja']     = inv_df['unidades_caja'].astype('str')
    
    df_list = []
    for i in inv_df['product_id'].unique():
        
        df_product = inv_df[inv_df['product_id']==i]#.fillna('')      
        df_product = df_product[[
            'product_id',
            'product_name',
            'group_code',
            'um',
            'oh2',
            'lote_id',
            'fecha_elab_lote',
            'fecha_cadu_lote',
            'ware_code',
            'location',
            'unidades_caja',
            'numero_cajas',
            'unidades_sueltas',
            'unidades_estanteria',
            'subtotal_unidades',
            'total_unidades',
            'diferencia',
            'observaciones',
            'user__username'
        ]]
                
        df_totales = df_product.select_dtypes(include='number').sum()
        df_totales['product_id'] = f'Total: {i}'
        df_totales = pd.DataFrame([df_totales])
        
        df_product_final = pd.concat([df_product, df_totales], ignore_index=True).fillna('')
        
        df_list.append(df_product_final)
        
    df_final = pd.concat(df_list, ignore_index=True)
    
    date_time = str(datetime.now())
    date_time = date_time[0:16]
    n = 'inventario_andagoya_bpa_' + date_time + '_.xlsx'
    nombre = 'attachment; filename=' + '"' + n + '"'

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = nombre
    
    df_final.to_excel(response, index=False)

    return response



### INVENTARIO CEREZOS
def stock_lote_inventario_cerezos(): #request
    ''' Colusta de stock '''
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute("SELECT * FROM warehouse.stock_lote WHERE WARE_CODE = 'BCT' OR WARE_CODE = 'CUC'")
        columns = [col[0] for col in cursor.description]
        stock = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
        
        stock_lote = pd.DataFrame(stock)
        productos = productos_odbc_and_django()[['product_id','Unidad_Empaque']]
        productos = productos.rename(columns={'product_id':'PRODUCT_ID'})
        stock_lote = stock_lote.merge(productos, on='PRODUCT_ID', how='left')
        
    return stock_lote 


def inventario_cerezos_actualizar_db(request):
    
    productos = productos_odbc_and_django()[['product_id','Nombre','Marca','Unidad','Unidad_Empaque']]
    productos = productos.drop_duplicates(subset=['product_id','Nombre','Marca','Unidad','Unidad_Empaque'], keep='first')
    
    stock_bct = stock_lote()[['PRODUCT_ID','LOTE_ID','Fecha_elaboracion_lote']]
    stock_bct['LOTE_ID'] = stock_bct['LOTE_ID'].str.replace('.','',regex=False)
    stock_bct['LOTE_ID'] = stock_bct['LOTE_ID'].str.strip()
    stock_bct = stock_bct.drop_duplicates(subset=['PRODUCT_ID','LOTE_ID','Fecha_elaboracion_lote'], keep='first')
    stock_bct['Fecha_elaboracion_lote'] = pd.to_datetime(stock_bct['Fecha_elaboracion_lote'], errors='coerce')
    stock_bct = stock_bct.rename(columns={'PRODUCT_ID':'product_id','LOTE_ID':'lote_id', 'Fecha_elaboracion_lote':'fecha_elab_lote'})
    
    existencias = Existencias.objects.all().values()
    existencias_df = pd.DataFrame(existencias)
    existencias_df['lote_id'] = existencias_df['lote_id'].astype(str).str.replace('.','', regex=False)
    existencias_df['lote_id'] = existencias_df['lote_id'].str.strip()
    
    existencias_df_agrupado = existencias_df.copy()
    existencias_df_agrupado = existencias_df_agrupado.groupby(by=[
        'product_id',
        'lote_id',
        'fecha_caducidad',
        'ubicacion_id',
        'estado'
    ])[['unidades']].sum().reset_index()
    
    existencias_df_agrupado = existencias_df_agrupado.merge(stock_bct, on=[
        'product_id',
        'lote_id'
    ], how='left')
    
    existencias_df_agrupado = existencias_df_agrupado.merge(productos, on='product_id', how='left')    
    
    # Filtrar registros sin fecha de elaboración (ya que la columna no acepta NULL)
    existencias_df_error_fecha_elab_lote = existencias_df_agrupado[~existencias_df_agrupado['fecha_elab_lote'].notna()]
    print(len(existencias_df_error_fecha_elab_lote))
    print(existencias_df_error_fecha_elab_lote)
    print(f"Registros antes de filtrar: {len(existencias_df_agrupado)}")
    existencias_df_agrupado = existencias_df_agrupado[existencias_df_agrupado['fecha_elab_lote'].notna()]
    print(f"Registros después de filtrar: {len(existencias_df_agrupado)}")
    existencias_df_error_fecha_elab_lote = existencias_df_agrupado[existencias_df_agrupado['fecha_elab_lote'].notna()]
    
    # Si no hay registros válidos, retornar
    if len(existencias_df_agrupado) == 0:
        return JsonResponse({'msg':'No hay registros con fecha de elaboración válida', 'status': 'warning'})
    
    existencias_df_agrupado['id'] = range(1, len(existencias_df_agrupado) + 1)
    existencias_df_agrupado['numero_cajas'] = 0
    existencias_df_agrupado['unidades_sueltas'] = 0
    existencias_df_agrupado['total_unidades'] = 0
    existencias_df_agrupado['diferencia'] = 0
    existencias_df_agrupado['observaciones'] = ''
    existencias_df_agrupado['llenado'] = False
    existencias_df_agrupado['agregado'] = False
    existencias_df_agrupado['user_id'] = None
    
    existencias_df_agrupado = existencias_df_agrupado[[
        'id',
        'product_id','Nombre','Marca','Unidad','estado','unidades','lote_id',
        'fecha_elab_lote','fecha_caducidad','Unidad_Empaque',
        'numero_cajas','unidades_sueltas','total_unidades','diferencia',
        'observaciones','llenado','agregado','ubicacion_id','user_id',
    ]]
    
    # Convertir fechas a formato compatible con la base de datos
    existencias_df_agrupado['fecha_elab_lote'] = existencias_df_agrupado['fecha_elab_lote'].apply(
        lambda x: x.date() if pd.notna(x) and hasattr(x, 'date') else None
    )
    existencias_df_agrupado['fecha_caducidad'] = pd.to_datetime(existencias_df_agrupado['fecha_caducidad'], errors='coerce').apply(
        lambda x: x.date() if pd.notna(x) and hasattr(x, 'date') else None
    )
    
    existencias_df_agrupado = existencias_df_agrupado.where(pd.notna(existencias_df_agrupado), None)    
    data = list(existencias_df_agrupado.itertuples(index=False, name=None)) 
    
    with connections['default'].cursor() as cursor:
        cursor.execute("TRUNCATE TABLE inventario_inventariocerezos")
        
    with connections['default'].cursor() as cursor:
        cursor.execute("TRUNCATE TABLE inventario_inventariocerezostotale")
        
    with connections['default'].cursor() as cursor:
        cursor.executemany("""
            INSERT INTO inventario_inventariocerezos
            (id, product_id, product_name, group_code, um, estado, oh2, lote_id, 
            fecha_elab_lote, fecha_cadu_lote, unidades_caja, 
            numero_cajas, unidades_sueltas, total_unidades, diferencia, 
            observaciones, llenado, agregado, ubicacion_id, user_id) 
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", 
            data)
    
    return JsonResponse({'msg':'ok'})


@require_GET
def inventario_cerezos_get_stock(request):
    
    inventario = InventarioCerezos.objects.all().values(
        'product_id',
        'product_name',
        'group_code',
        'um',
        'estado',
        
        'oh2',
        
        'lote_id',
        'fecha_elab_lote',
        'fecha_cadu_lote',
        
        'ubicacion__id',
        'ubicacion__bodega',
        'ubicacion__pasillo',
        'ubicacion__modulo',
        'ubicacion__nivel',
        
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
    
    porcentaje_avance = 0 if total == 0 else round((procesados / total) * 100, 0)
    procentaje_falta  = 100 - porcentaje_avance
    
    lista_ubicaciones = sorted(list(inventario.values_list('ubicacion__bodega', flat=True).distinct()))
    lista_avance = [round((inventario.filter(ubicacion__bodega=i, llenado=True).count()/inventario.filter(ubicacion__bodega=i).count())*100,1) for i in lista_ubicaciones]
    
    lista_totales = [porcentaje_avance, procentaje_falta]    
    
    return JsonResponse({
        'inventario': list(inventario),
        'total':total,
        'procesados':procesados,
        'ubicaciones': lista_ubicaciones,
        'avances': lista_avance,
        'totales': lista_totales
    })


def inventario_cerezos_reportes(request):
    return render(request, 'inventario/toma_fisica/cerezos/reportes_cerezos.html')


@login_required(login_url='login')
def inventario_cerezos_home(request):
    
    bodegas = InventarioCerezos.objects.values_list('ubicacion__bodega', flat=True).distinct()
    
    lista_por_bodega = []
    for bodega in bodegas:
        pasillos = InventarioCerezos.objects.filter(ubicacion__bodega=bodega).values_list('ubicacion__pasillo', flat=True).distinct()
        for pasillo in pasillos:
            items = InventarioCerezos.objects.filter(
                ubicacion__bodega=bodega, ubicacion__pasillo=pasillo
            ).count()
        
            d = {
                'bodega': bodega,
                'pasillo': pasillo,
                'items': items
            }
            
            lista_por_bodega.append(d)
    
    context = {
        'bodega': lista_por_bodega,
    }
    
    return render(request, 'inventario/toma_fisica/cerezos/home.html', context)


@login_required(login_url='login')
def inventario_por_bodega_cerezos(request, bodega, ubicacion): 
    
    inventario = InventarioCerezos.objects.filter(ubicacion__bodega=bodega, ubicacion__pasillo=ubicacion).order_by('group_code', 'product_id').values(
        'id',
        'product_id',
        'product_name',
        'group_code',
        'um',
        'estado',
        
        'oh2',
        
        'lote_id',
        'fecha_elab_lote',
        'fecha_cadu_lote',
        
        'ubicacion__id',
        'ubicacion__bodega',
        'ubicacion__pasillo',
        'ubicacion__modulo',
        'ubicacion__nivel',
        
        'unidades_caja',
        'numero_cajas',
        'unidades_sueltas',
        'total_unidades',
        'diferencia',
        'observaciones',
        
        'llenado',
        'agregado',
        'user__username',
    ).order_by(
        'ubicacion__bodega',
        'ubicacion__pasillo',
        'ubicacion__modulo',
        'ubicacion__nivel',
        'product_id'
    ).annotate(
        ubi_full_name=
            Concat(F('ubicacion__bodega'),
            Value('-'),
            F('ubicacion__pasillo'),
            Value('-'),
            F('ubicacion__modulo'),
            Value('-'),
            F('ubicacion__nivel'))
    )

    n_inventario =len(inventario)
    n_inventario_llenado = len(InventarioCerezos.objects.filter(ubicacion__bodega=bodega).filter(ubicacion__pasillo=ubicacion).filter(llenado=True))
    n_inventario_nollenado = len(InventarioCerezos.objects.filter(ubicacion__bodega=bodega).filter(ubicacion__pasillo=ubicacion).filter(llenado=False))

    context = {
        'inventario':list(inventario),
        'mi_bodega':bodega,
        'mi_ubicacion':ubicacion,
        'n_inventario':n_inventario,
        'n_inventario_llenado':n_inventario_llenado,
        'n_inventario_nollenado':n_inventario_nollenado,
    }

    return JsonResponse(context)


@login_required(login_url='login')
def inventario_toma_fisica_cerezos_vue(request, bodega, location):
    return render(request, 'inventario/toma_fisica/cerezos/toma_fisica.html')


def inventario_ubicaciones_wms(request):
    
    ubicaciones = Ubicacion.objects.all().annotate(
        full_name=Concat(F('bodega'),Value('-'),F('pasillo'),Value('-'),F('modulo'),Value('-'),F('nivel'))
    ).values()
    
    return JsonResponse({
        'ubicaciones': list(ubicaciones) 
    })


@csrf_exempt
def inventario_cerezos_toma_fisica_item(request, item_id):
    
    if request.method == 'GET':
        
        # item
        item = InventarioCerezos.objects.get(id=item_id) 
        item_dict = model_to_dict(item)
        item_dict['ubi'] = model_to_dict(item.ubicacion)
                
        # item totales
        item_totales = (InventarioCerezosTotale.objects
            .filter(product_id_t=item.product_id)
            .filter(ubicacion=item.ubicacion)
        )
        
        return JsonResponse({
            'item': item_dict,
            'item_totales': model_to_dict(item_totales.first()) if item_totales.first() else None,
            })
    
    elif request.method == 'POST':
        
        data = json.loads(request.body)
        data['user'] = User.objects.get(id=data.get('user_id'))
        my_instance = InventarioCerezos.objects.get(id=item_id)
        form = InventarioCerezosForm(data, instance = my_instance)
        
        if form.is_valid():
            form.save()
            return JsonResponse({
                'type':'success',
                'msg':'Registrado Correctamiente'})
        else:
            return JsonResponse({'type':'danger','msg':form.errors})


@csrf_exempt
def inventario_cerezos_toma_fisica_total_agrupado(request):
    
    if request.method == 'POST':
        data = json.loads(request.body)
        data['user'] = User.objects.get(id=data.get('user_id')) 
        data['ubicacion'] = Ubicacion.objects.get(id=data.get('ubicacion_id'))
        
        # actualizar registro
        if data.get('id'):
            item_totales = InventarioCerezosTotale.objects.get(id=data.get('id'))            
            form = InventarioCerezosTotalesForm(data, instance=item_totales)
            if form.is_valid():                
                form.save()
                return JsonResponse({'type':'success','msg':'Actualizado Correctamiente'})
            else:
                return JsonResponse({'type':'danger','msg':form.errors})
        
        # crear registro
        else:
            form = form = InventarioCerezosTotalesForm(data)
            if form.is_valid():
                form.save()
                return JsonResponse({'type':'success', 'msg':'Registrado Correctamente'})
            else:
                return JsonResponse({'type':'danger','msg':form.errors})


@csrf_exempt
def inventario_cerezos_toma_fisica_buscar_producto(request):
    
    if request.method == 'POST':
        data = json.loads(request.body)
        product_id = data.get('product_id').get('codigo') 
        product = productos_odbc_and_django()
        product = product[product['product_id']==product_id][[
            'product_id','Nombre','Marca','Unidad','Unidad_Empaque'
        ]]
        
        data_lotes = InventarioCerezos.objects.filter(product_id=product_id).values('lote_id','fecha_elab_lote','fecha_cadu_lote').distinct()
        if not product.empty:
            return JsonResponse({
                'type':'success', 
                'msg':'Producto encontrado !!!', 
                'product':product.to_dict(orient='records')[0],
                'data_lotes':list(data_lotes)
                })
        else:
            return JsonResponse({
                'type':'danger',
                'msg':f'No se encuentra resultados para {product_id}'
                })


@csrf_exempt
def inventario_cerezos_toma_fisica_agregar_producto(request):
    if request.method == 'POST':
        data = json.loads(request.body) 
        data['user'] = User.objects.get(id=data.get('user_id'))
        data['ubicacion'] = Ubicacion.objects.get(id=data.get('ubicacion_id').get('id'))
        
        form = InventarioCerezosAgregarForm(data)
        if form.is_valid():
            form.save()
            return JsonResponse({'type':'success','msg':'Producto agregado correctamente'})
        else:
            return JsonResponse({'type':'danger','msg':form.errors})


@csrf_exempt
def inventario_cerezos_eliminar_item_agregado(request):
    
    if request.method == 'POST':

        data = json.loads(request.body)
        
        item_id = data.get('item_id')
        item = InventarioCerezos.objects.get(id=item_id)
        item.delete()
        
        return JsonResponse({'type':'success','msg':'Item eliminado correctamente'})
    else:
        return JsonResponse({'type':'danger','msg':'Error al eliminar item'})


@login_required(login_url='login')
def reporte_cerezos_completo(request):
    
    inv = InventarioCerezos.objects.all().values(
        'product_id',
        'product_name',
        'group_code',
        'um',
        'estado',
        'oh2',
        'lote_id',
        'fecha_elab_lote',
        'fecha_cadu_lote',        
        'ubicacion__bodega',
        'ubicacion__pasillo',
        'ubicacion__modulo',
        'ubicacion__nivel',
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
    
    inv_df = pd.DataFrame(inv)
    
    inv_df['ubicacion'] = inv_df['ubicacion__bodega'] + '-' + inv_df['ubicacion__pasillo'] + '-' + inv_df['ubicacion__modulo'] + '-' + inv_df['ubicacion__nivel']
    inv_df['fecha_elab_lote'] = inv_df['fecha_elab_lote'].astype('str')
    inv_df['fecha_cadu_lote'] = inv_df['fecha_cadu_lote'].astype('str')
    
    inv_df['#'] = inv_df.reset_index().index + 1
    
    inv_df = inv_df[[
        '#',
        'product_id',
        'product_name',
        'group_code',
        'um',
        'estado',
        'oh2',
        'lote_id',
        'fecha_elab_lote',
        'fecha_cadu_lote',
        'ubicacion',
        'unidades_caja',
        'numero_cajas',
        'unidades_sueltas',
        'total_unidades',
        'diferencia',
        'observaciones',
        'llenado',
        'agregado',
        'user__username',
    ]]
    
    date_time = str(datetime.now())
    date_time = date_time[0:16]
    n = 'inventario_cerezos_completo' + date_time + '_.xlsx'
    nombre = 'attachment; filename=' + '"' + n + '"'

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = nombre
    
    inv_df.to_excel(response, index=False)
    
    return response


@login_required(login_url='login')
def reporte_cerezos_agrupado(request):
    
    inv = InventarioCerezos.objects.all().values(
        'product_id',
        # 'product_name',
        # 'group_code',
        # 'um',
        # 'estado',
        'oh2',
        'lote_id',
        # 'fecha_elab_lote',
        # 'fecha_cadu_lote',        
        'ubicacion__bodega',
        # 'ubicacion__pasillo',
        # 'ubicacion__modulo',
        # 'ubicacion__nivel',
        # 'unidades_caja',
        # 'numero_cajas',
        # 'unidades_sueltas',
        'total_unidades',
        # 'diferencia',
        # 'observaciones',
        # 'llenado',
        # 'agregado',
        # 'user__username',
    )
    
    inv_df = pd.DataFrame(inv)
    
    inv_df = inv_df.groupby(by=[
        'product_id',
        'lote_id',
        'ubicacion__bodega',
    ]).sum().reset_index()
    
    inv_df['diferencia'] = inv_df['total_unidades'] - inv_df['oh2']
    
    date_time = str(datetime.now())
    date_time = date_time[0:16]
    n = 'inventario_cerezos_agrupado_' + date_time + '_.xlsx'
    nombre = 'attachment; filename=' + '"' + n + '"'

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = nombre
    
    inv_df.to_excel(response, index=False)
    
    return response


@login_required(login_url='login')
def reporte_cerezos_tf_mba(request):
    
    # INV TOMA FISICA
    inv = InventarioCerezos.objects.all().values(
        'product_id',
        'estado',
        'oh2',
        'lote_id',       
        'ubicacion__bodega',
        'total_unidades',
    )
    
    inv_df = pd.DataFrame(inv)
    
    inv_df['lote_id'] = inv_df['lote_id'].str.replace(pat='.', repl='', regex=False)
    inv_df['lote_id'] = inv_df['lote_id'].str.strip()
    inv_df = inv_df.groupby(by=[
        'product_id',
        'estado',
        'lote_id',
        'ubicacion__bodega',
    ]).sum().reset_index()
    inv_df['WARE_CODE'] = inv_df.apply(lambda x: 'BCT' if x['estado'] == 'Disponible' else 'CUC', axis=1)
    inv_df = inv_df.rename(columns={
        'product_id': 'PRODUCT_ID',
        'lote_id': 'LOTE_ID',
        'ubicacion__bodega': 'LOCATION',
        'oh2': 'UNDS-WMS',
        'total_unidades': 'UNDS-TF',
    })


    # INV STOCK
    stock = stock_lote_inventario_cerezos()[['PRODUCT_ID','LOTE_ID','OH2','WARE_CODE','LOCATION']]
    stock['LOTE_ID'] = stock['LOTE_ID'].str.replace(pat='.', repl='', regex=False)
    stock['LOTE_ID'] = stock['LOTE_ID'].str.strip()

    stock = stock.groupby(by=[
        'PRODUCT_ID',
        'LOTE_ID',
        'WARE_CODE',
        'LOCATION',
    ]).sum().reset_index()

    inv_df = inv_df.merge(stock, on=[
        'PRODUCT_ID',
        'LOTE_ID',
        'WARE_CODE',
        # 'LOCATION'
    #], how='left')
    ], how='outer')
    
    inv_df = inv_df.rename(columns={
        'LOCATION_x':'LOCATION_WMS',
        'LOCATION_y':'LOCATION_MBA',
        'OH2':'UNDS-MBA'
    })
    
    inv_df['DIFERENCIA (WMS-TF)'] = inv_df['UNDS-WMS'] - inv_df['UNDS-TF']
    inv_df['DIFERENCIA (MBA-TF)'] = inv_df['UNDS-MBA'] - inv_df['UNDS-TF']
    inv_df['DIFERENCIA (WMS-MBA)'] = inv_df['UNDS-WMS'] - inv_df['UNDS-MBA']
    
    inv_df['#'] = inv_df.reset_index().index + 1
    
    inv_df = inv_df[[
        '#',
        'PRODUCT_ID',
        'LOTE_ID',
        'WARE_CODE',
        'LOCATION_WMS',
        'LOCATION_MBA',
        'UNDS-WMS',
        'UNDS-MBA',
        'UNDS-TF',
        'DIFERENCIA (WMS-TF)',
        'DIFERENCIA (MBA-TF)',
        'DIFERENCIA (WMS-MBA)'
    ]]


    date_time = str(datetime.now())
    date_time = date_time[0:16]
    n = 'inventario_cerezos_agrupado_' + date_time + '_.xlsx'
    nombre = 'attachment; filename=' + '"' + n + '"'

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = nombre
    
    inv_df.to_excel(response, index=False)
    
    return response


@login_required(login_url='login')
def reporte_cerezos_bpa(request):
    
    # INV TOMA FISICA
    inv = InventarioCerezos.objects.all().values(
        'product_id',
        'product_name',
        'group_code',
        'um',
        'estado',
        'oh2',
        'lote_id',
        'fecha_elab_lote',
        'fecha_cadu_lote',
        'ubicacion__bodega',
        'unidades_caja',
        'numero_cajas',
        'unidades_sueltas',
        'total_unidades',
        'diferencia',
        'observaciones',
        'user__username',
    )
    
    inv_df = pd.DataFrame(inv)
    
    inv_unidades_df = inv_df.copy()
    inv_unidades_df['ware_code'] = inv_unidades_df.apply(lambda x: 'BCT' if x['estado'] == 'Disponible' else 'CUC', axis=1)
    inv_unidades_df = inv_unidades_df.pivot_table(
        index=[        
            'product_id',
            'product_name',
            'group_code',
            'um',
            'ware_code',
            'unidades_caja',
            'lote_id',
            'fecha_elab_lote',
            'fecha_cadu_lote',
            'ubicacion__bodega',
        ],
        values=[
            'oh2',
            'numero_cajas',
            'unidades_sueltas',
            'total_unidades',
            'diferencia'
        ],
        aggfunc='sum'
    ).reset_index()
    
    # USER
    df_str_users = inv_df.copy()
    df_str_users = df_str_users[[
        'product_id',
        'lote_id',
        'estado',
        'fecha_elab_lote',
        'fecha_cadu_lote',
        'ubicacion__bodega',
        'user__username'
    ]]    
    df_str_users['user__username'] = df_str_users['user__username'].fillna('')
    df_str_users['ware_code'] = df_str_users.apply(lambda x: 'BCT' if x['estado'] == 'Disponible' else 'CUC', axis=1)
    df_str_users = df_str_users.pivot_table(
        index=[
            'product_id',
            'ware_code',
            'lote_id',
            'fecha_elab_lote',
            'fecha_cadu_lote',
            'ubicacion__bodega',
            'user__username'
        ],
        values=['user__username'],
        aggfunc=lambda x: ', '.join(set(x))
    ).reset_index()

    # OBS
    df_str_obs = inv_df.copy()
    df_str_obs = df_str_obs[[
        'product_id',
        'lote_id',
        'estado',
        'fecha_elab_lote',
        'fecha_cadu_lote',
        'ubicacion__bodega',
        'observaciones'
    ]]    
    df_str_obs['observaciones'] = df_str_obs['observaciones'].fillna('')
    df_str_obs['ware_code'] = df_str_obs.apply(lambda x: 'BCT' if x['estado'] == 'Disponible' else 'CUC', axis=1)
    df_str_obs = df_str_obs.pivot_table(
        index=[
            'product_id',
            'ware_code',
            'lote_id',
            'fecha_elab_lote',
            'fecha_cadu_lote',
            'ubicacion__bodega',
            'observaciones'
        ],
        values=['observaciones'],
        aggfunc=lambda x: ', '.join(set(x))
    ).reset_index()
    
    # STR FINAL
    df_str = df_str_users.merge(df_str_obs, on=[
        'product_id',
        'lote_id',
        'estado',
        'ware_code',
        'fecha_elab_lote',
        'fecha_cadu_lote',
        'ubicacion__bodega',
    ], how='left')
    
    # DF UNIDO
    df_unido = inv_unidades_df.merge(df_str, on=[
        'product_id',
        'ware_code',
        'lote_id',
        'fecha_elab_lote',
        'fecha_cadu_lote',
        'ubicacion__bodega',
    ], how='left').sort_values(by=['ware_code','ubicacion__bodega','product_id','lote_id','fecha_elab_lote'])
    
    # DF FINAL
    df_list = []
    for i in inv_df['product_id'].unique():
        
        df_by_product = df_unido[df_unido['product_id']==i]
        
        df_by_product = df_by_product.pivot_table(
            index=[        
                'product_id',
                'product_name',
                'group_code',
                'um',
                'ware_code',
                'unidades_caja',
                'lote_id',
                'fecha_elab_lote',
                'fecha_cadu_lote',
                'ubicacion__bodega',
                'observaciones',
                'user__username'
            ],
            values=[
                'oh2',
                'numero_cajas',
                'unidades_sueltas',
                'total_unidades',
                'diferencia'
            ],
            aggfunc='sum',
            margins = True,
            margins_name = f'Total: {i}',
            ).reset_index()
        
        df_by_product['fecha_elab_lote']   = df_by_product['fecha_elab_lote'].astype('str')
        df_by_product['fecha_cadu_lote']   = df_by_product['fecha_cadu_lote'].astype('str')
        df_by_product['subtotal_unidades'] = (
            df_by_product['numero_cajas'].replace('', '0').astype('int') * 
            df_by_product['unidades_caja'].replace('', '0').astype('int') + 
            df_by_product['unidades_sueltas'].replace('', '0').astype('int')
        )

        df_by_product = df_by_product[[
                'product_id',
                'product_name',
                'group_code',
                'um',
                'oh2',
                'lote_id',
                'fecha_elab_lote',
                'fecha_cadu_lote',
                'ware_code',
                'ubicacion__bodega',
                'unidades_caja',
                'numero_cajas',
                'unidades_sueltas',
                'subtotal_unidades',
                'total_unidades',
                'diferencia',
                'observaciones',
                'user__username'
        ]]
        
        df_list.append(df_by_product)
    
    df_final = pd.concat(df_list).fillna('')
    
    date_time = str(datetime.now())
    date_time = date_time[0:16]
    n = 'inventario_cerezos_bpa_' + date_time + '_.xlsx'
    nombre = 'attachment; filename=' + '"' + n + '"'

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = nombre
    
    df_final.to_excel(response, index=False)

    return response


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
    