from django.shortcuts import render, redirect

# Datos de importaciones
from datos.views import (
    importaciones_llegadas_odbc, 
    productos_odbc_and_django, 
    de_dataframe_a_template, 
    importaciones_llegadas_ocompra_odbc,
    wms_reservas_lotes_datos,
    wms_reservas_lote_consulta,
    
    # DATOS
    wms_datos_doc_liberaciones,
    wms_datos_liberacion_cuc,
    wms_datos_liberacion_bct,
    wms_detalle_factura,
    clientes_warehouse,
    wms_stock_lote_cerezos,
    wms_picking_realizados_warehouse_list,
    wms_reserva_por_contratoid,
    quitar_puntos,
    wms_stock_lote_cerezos_by_product,
    wms_stock_lote_products,
    
    # Trasnferencia
    doc_transferencia_odbc
    )

# Pedidos por clientes
from etiquetado.views import pedido_por_cliente, reservas_table

# Http
from django.http import HttpResponse,JsonResponse, HttpResponseRedirect

# Json
import json

# Datetime
from datetime import datetime

# DB
from django.db import connections

# Models
from django.db.models import Sum, Count
from wms.models import InventarioIngresoBodega, Ubicacion, Movimiento, Existencias, Transferencia
from etiquetado.models import EstadoPicking

# Pandas
import pandas as pd

# Forms
from wms.forms import MovimientosForm

# Messages
from django.contrib import messages

# Query's
from django.db.models import Q

# Models
from users.models import User, UserPerfil
from etiquetado.models import EstadoPicking

# Transactions INTEGRITY OF DATA
from django.db import transaction
from django.db.utils import IntegrityError

# Login
from django.contrib.auth.decorators import login_required, permission_required

# Email
from django.core.mail import send_mail
from django.conf import settings


"""
    LISTAS DE INGRESOS 
    - LISTA DE IMPORTACIONES
    - LISTA DE BODEGA DE INVENTARIO INICIAL
"""

# Lista de importaciones por llegar
# url: importaciones/list
@login_required(login_url='login')
def wms_importaciones_list(request): #OK
    """ Lista de importaciones llegadas """
    
    imp = importaciones_llegadas_odbc()#[['MEMO','DOC_ID_CORP', 'ENTRADA_FECHA', 'WARE_COD_CORP', 'product_id']];print(imp).
    #imp['ENTRADA_FECHA'] = pd.to_datetime(imp['ENTRADA_FECHA']).dt.strftime('%d-%m-%Y')
    imp = imp[imp['ENTRADA_FECHA']>'2023-12-31']
    imp = imp.sort_values(by=['ENTRADA_FECHA'], ascending=[False])
    imp = imp.drop_duplicates(subset=['DOC_ID_CORP'])
    
    pro = productos_odbc_and_django()[['product_id', 'Marca']]  
    imp = imp.merge(pro, on='product_id', how='left')
    
    # imp = imp.sort_values(by=['ENTRADA_FECHA'], ascending=[False])
    
    imp_doc = pd.DataFrame(InventarioIngresoBodega.objects.all().values()).empty

    if not imp_doc:
        imp_doc = pd.DataFrame(InventarioIngresoBodega.objects.all().values())[['n_referencia', 'bodega']]
        imp_doc = imp_doc.drop_duplicates(subset='n_referencia')
        imp_doc = imp_doc.rename(columns={'n_referencia':'DOC_ID_CORP'})
        imp = imp.merge(imp_doc, on='DOC_ID_CORP', how='left').fillna(0)
        imp = imp[imp['bodega']==0]
    
    imp = de_dataframe_a_template(imp)

    context = {
        'imp':imp
    }
    
    return render(request, 'wms/importaciones_list.html', context)



# Lista de importaciones ingresadas
# url: importaciones/ingresadas
@login_required(login_url='login')
def wms_imp_ingresadas(request): #OK
    """ Lista de importaciones ingresadas """
    
    prod = productos_odbc_and_django()[['product_id','Marca']]
    imps = pd.DataFrame(InventarioIngresoBodega.objects.filter(referencia='Ingreso Importación').values()).sort_values(by='fecha_hora',ascending=False)

    imps_llegadas = importaciones_llegadas_odbc()[['DOC_ID_CORP','MEMO']]
    imps_llegadas = imps_llegadas.rename(columns={'DOC_ID_CORP':'n_referencia'}).drop_duplicates(subset='n_referencia')
    
    imps = imps.merge(imps_llegadas, on='n_referencia', how='left')

    if not imps.empty:
        imps = imps.merge(prod, on='product_id', how='left')
        imps = imps.drop_duplicates(subset='n_referencia')
        imps = de_dataframe_a_template(imps)

    context = {
        'imp':imps
    }
    
    return render(request, 'wms/importaciones_ingresadas_list.html', context)


# Detalle de importación
# url: importacion/<str:o_compra>
@login_required(login_url='login')
def wms_detalle_imp(request, o_compra): #OK
    """ Ver detalle de importaciones
        Seleccionar bodega 
        Guardar datos en la tabla "inventario_ingreso_bodega"
        Una vez ingresada la importación desaparece de la lista de importaciones por llegar
        y aparece en la lista de importaciones ingresadas
    """
    
    # imv_inicial_ing = pd.DataFrame(InventarioIngresoBodega.objects.filter(n_referencia=o_compra).values())
    # print(imv_inicial_ing)
    
    detalle = importaciones_llegadas_ocompra_odbc(o_compra) 
    pro     = productos_odbc_and_django()[['product_id', 'Nombre', 'marca','marca2']]
    detalle = detalle.merge(pro, on='product_id', how='left')
    detalle = detalle[detalle['product_id']!='70114-3LHS']
    
    marca = detalle['marca2'].iloc[0]
    orden = detalle['DOC_ID_CORP'].iloc[0]

    detalle = de_dataframe_a_template(detalle)

    if request.method == 'POST':
        bodega = request.POST['bodega']
        d = importaciones_llegadas_ocompra_odbc(o_compra) 
        d['bodega'] = bodega
        
        imp_ing = []
        for i in de_dataframe_a_template(d):
            imp = InventarioIngresoBodega(
                product_id          = i['product_id'],
                lote_id             = i['LOTE_ID'],
                fecha_caducidad     = i['FECHA_CADUCIDAD'],
                bodega              = i['bodega'],
                unidades_ingresadas = i['OH'],
                n_referencia        = i['DOC_ID_CORP'],
                referencia          = 'Ingreso Importación'
            )
            
            imp_ing.append(imp)
        
        imp_exist = InventarioIngresoBodega.objects.filter(n_referencia=o_compra).exists()
        
        if imp_exist:
            messages.add_message(request, messages.INFO, f'La imprtación {o_compra} ya fue ingresada !!!')
        else:    
            InventarioIngresoBodega.objects.bulk_create(imp_ing)
            return redirect(f'/wms/importacion/bodega/{o_compra}')

    context = {
        'imp':detalle,
        'marca':marca,
        'orden':orden,
    }

    return render(request, 'wms/detalle_importacion.html', context)


# Lista de productos de importación
# url: importacion/bodega/<str:o_compra>
@login_required(login_url='login')
def wms_bodega_imp(request, o_compra): #OK
    """ Detalle de la importación 
        Botón para ingresar y asignar ubicación dentro de la bodega previamente selecionada
        Si el color de la fila unidades es amarillo el ingreso esta incompleto
    """
    
    prod = productos_odbc_and_django()[['product_id','Nombre','Marca']]
    
    imp = pd.DataFrame(
    InventarioIngresoBodega.objects
        .filter(referencia='Ingreso Importación')
        .filter(n_referencia=o_compra).values()
    )
        
    movs = pd.DataFrame(
    Movimiento.objects
        .filter(referencia='Ingreso Importación')
        .filter(n_referencia=o_compra)
        #.values('item__product_id', 'item__lote_id', 'unidades'))
        .values('product_id', 'lote_id', 'unidades'))
    
    
    if not movs.empty:
        movs = movs.pivot_table(index=['product_id','lote_id'], values=['unidades'], aggfunc='sum').reset_index()
        imp = imp.merge(movs, on=['product_id','lote_id'], how='left').fillna(0)
    
    
    imp = imp.merge(prod, on='product_id', how='left')
    imp['fecha_caducidad'] = imp['fecha_caducidad'].astype(str)
    
    
    imp = de_dataframe_a_template(imp)
    
    marca  = imp[0]['Marca']
    ref    = imp[0]['n_referencia']
    bodega = imp[0]['bodega']
    context = {
        'imp'  :imp,
        'marca':marca,
        'ref'  : ref,
        'bod'  :bodega,
    }


    return render(request, 'wms/detalle_bodega.html', context)


# Lista de bodega de inventari inicial
# url: inventario/inicial/list_bodega
@login_required(login_url='login')
def wms_inventario_inicial_list_bodega(request): #OK
    
    prod = productos_odbc_and_django()[['product_id','Marca']]
    inv = pd.DataFrame(InventarioIngresoBodega.objects.filter(referencia='Inventario Inicial').values())
    inv = inv.merge(prod, on='product_id', how='left').sort_values(by='bodega')
    inv = inv.drop_duplicates(subset=['bodega'])
    inv = de_dataframe_a_template(inv)

    context = {
        'inv':inv
    }
    
    return render(request, 'wms/inventario_inicial/list_bodegas.html', context)


# Lista de productos de inventario inicial por bodega
# url: inventario/inicial/<str:bodega>
@login_required(login_url='login')
def wms_inventario_inicial_bodega(request, bodega): #OK
    
    prod = productos_odbc_and_django()[['product_id','Nombre','Marca']]
    inv = pd.DataFrame(
    InventarioIngresoBodega.objects
        .filter(referencia='Inventario Inicial')
        #.filter(n_referencia='inv_in_1') # PONER EN VARIABLE
        .filter(bodega=bodega)
        .values())
    
    inv = inv.merge(prod, on='product_id', how='left').sort_values(by='bodega')
    inv['fecha_caducidad'] = inv['fecha_caducidad'].astype(str)
    
    movs = pd.DataFrame(
    Movimiento.objects
        .filter(referencia='Inventario Inicial')
        #.filter(n_referencia='inv_in_1')
        .filter(ubicacion__bodega=bodega)
        .values('product_id','lote_id','unidades'))
    
    #ubi_list = (Movimiento.objects
        #.filter(referencia='Inventario Inicial'))
        #.filter(n_referencia='inv_in_1'))
        #.filter(ubicacion__bodega=bodega))
    #print(ubi_list.values())
    
    if not movs.empty:
        movs = movs.pivot_table(index=['product_id','lote_id'], values=['unidades'], aggfunc='sum').reset_index()
        inv = inv.merge(movs, on=['product_id','lote_id'], how='left').fillna(0)
    
    inv = de_dataframe_a_template(inv)
    
    context = {
        #'ubi_list':ubi_list,
        'bod':bodega,
        'inv':inv
    }
    
    return render(request, 'wms/inventario_inicial/bodega.html', context)



    ####   QUERY DE EXISTENCIAS   ####



### QUERY DE EXISTENCIAS EN TABLA MOVIEMIENTOS ###
    #### ACTUALIZACIÓN DE TABLA EXISTENCIAS ####
@transaction.atomic
def wms_existencias_query(): #OK
    
    exitencias = Movimiento.objects.all().values(
        # 'id',
        'product_id',
        'lote_id',
        'fecha_caducidad',
        # 'item__product_id',
        # 'item__nombre',
        # 'item__marca2',
        # 'item__lote_id',
        # 'item__fecha_caducidad',
        'ubicacion'        ,
        'ubicacion__bodega',
        'ubicacion__pasillo',
        'ubicacion__modulo',
        'ubicacion__nivel',
        'estado'
    ).annotate(total_unidades=Sum('unidades')).order_by(
        # 'item__product_id',
        # 'item__marca2',
        # 'item__fecha_caducidad',
        'ubicacion__bodega',
        'ubicacion__pasillo',
        'ubicacion__modulo',
        'ubicacion__nivel',
    ).exclude(total_unidades = 0) 
        
    existencias_list = []
    for i in exitencias:
        prod = i['product_id']
        lote = i['lote_id']
        fcad = i['fecha_caducidad']
        ubi  = i['ubicacion']
        und  = i['total_unidades']
        est  = i['estado']
        
        ex = Existencias(
            product_id      = prod,
            lote_id         = lote,
            fecha_caducidad = fcad,
            ubicacion_id    = ubi,
            unidades        = und,
            estado          = est
        )
        
        existencias_list.append(ex)   
    
    with connections['default'].cursor() as cursor:
        cursor.execute("TRUNCATE wms_existencias")
        
    Existencias.objects.bulk_create(existencias_list)

    return exitencias


# Actualizar existencias por item y lote
def wms_existencias_query_product_lote(product_id, lote_id):
    
    exitencias = Movimiento.objects.filter(
        product_id=product_id, 
        lote_id=lote_id
    ).values(
        # 'id',
        'product_id',
        'lote_id',
        'fecha_caducidad',
        # 'item__product_id',
        # 'item__nombre',
        # 'item__marca2',
        # 'item__lote_id',
        # 'item__fecha_caducidad',
        'ubicacion'        ,
        'ubicacion__bodega',
        'ubicacion__pasillo',
        'ubicacion__modulo',
        'ubicacion__nivel',
        'estado'
    ).annotate(total_unidades=Sum('unidades')).order_by(
        # 'item__product_id',
        # 'item__marca2',
        # 'item__fecha_caducidad',
        'ubicacion__bodega',
        'ubicacion__pasillo',
        'ubicacion__modulo',
        'ubicacion__nivel',
    ).exclude(total_unidades = 0)
    
    existencias_list = []
    for i in exitencias:
        prod = i['product_id']
        lote = i['lote_id']
        fcad = i['fecha_caducidad']
        ubi  = i['ubicacion']
        und  = i['total_unidades']
        est  = i['estado']
        
        ex = Existencias(
            product_id      = prod,
            lote_id         = lote,
            fecha_caducidad = fcad,
            ubicacion_id    = ubi,
            unidades        = und,
            estado          = est
        )
        
        existencias_list.append(ex)
    
    Existencias.objects.filter(product_id=product_id, lote_id=lote_id).delete()
    Existencias.objects.bulk_create(existencias_list)
    
    return exitencias



# Actualizar toda la tabla existencias
def wms_btn_actualizar_todas_existencias(request):
    wms_existencias_query()
    return redirect('/wms/inventario')



# def cuadre_inventario(request):
    
#     # Stock MBA - Cerezos
#     stock_cerezos = wms_stock_lote_cerezos()[[
#         'PRODUCT_ID', 
#         'PRODUCT_NAME',
#         'GROUP_CODE',
#         'LOTE_ID',
#         'FECHA_CADUCIDAD',
#         'LOCATION',
#         'OH2',
#         ]]
#     stock_cerezos = stock_cerezos.rename(columns={
#         'PRODUCT_ID':'product_id',
#         'LOTE_ID':'lote_id'
#     })    
    
#     # Existencias WMS
#     exitencias = Movimiento.objects.all().values(
#         'product_id',
#         'lote_id',
#         'fecha_caducidad',
#         'ubicacion__bodega',
        
#     ).annotate(total_unidades=Sum('unidades')).exclude(total_unidades=0) 
    
#     exitencias = pd.DataFrame(exitencias)
#     exitencias = exitencias.rename(columns={'total_unidades':'unidades_wms'})
    
#     inv = stock_cerezos.merge(exitencias, on=['product_id','lote_id'])
#     #print(inv)
    
#     # from inventario.models import Inventario
#     # inventario_fisico = pd.DataFrame(Inventario.objects.filter(ware_code='BCT').values(
#     #     'product_id', 'lote_id', 'fecha_cadu_lote', 'total_unidades'
#     # ))
#     # inventario_fisico = inventario_fisico.rename(columns={'total_unidades':'unidades_inv'})
    
    
#     # inv = inventario_fisico.merge(
#     #     exitencias, on=['product_id','lote_id'],
#     #     how='left')
    
#     # inv['dif'] = inv['unidades_inv'] - inv['unidades_wms']
    
#     # inv = inv[['product_id','lote_id','fecha_cadu_lote','fecha_caducidad',
#     #             'unidades_inv','unidades_wms','dif']]
    
    
#     response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
#     response['Content-Disposition'] = 'Rep.xlsx'

#     inv.to_excel(response)
    
#     return response 
#     # return HttpResponse(exitencias)



# Inventario - Lista de productos Existencias
# url: wms/inventario
@login_required(login_url='login')
def wms_inventario(request): #OK
    """ Inventario 
        Suma de ingresos y egresos que dan el total de todo el inventario
    """
    
    #wms_existencias_query()
    prod = productos_odbc_and_django()[['product_id','Nombre','Marca']]
    
    #inv = wms_existencias_query()
    inv = pd.DataFrame(Existencias.objects.all().values(
        'id',
        'product_id', 'lote_id', 'fecha_caducidad', 'unidades', 'fecha_hora', 
        'ubicacion', 'ubicacion__bodega', 'ubicacion__pasillo', 'ubicacion__modulo', 'ubicacion__nivel', 
        'estado'
    ).order_by('product_id','fecha_caducidad', 'ubicacion__distancia_puerta'))
    inv = inv.merge(prod, on='product_id', how='left')
    #inv['fecha_caducidad'] = inv['fecha_caducidad'].astype(str)
    inv['fecha_caducidad'] = pd.to_datetime(inv['fecha_caducidad'])
    inv['fecha_caducidad'] = inv['fecha_caducidad'].dt.strftime('%d-%m-%Y')
    inv = de_dataframe_a_template(inv)

    context = {
        'inv':inv,
    }

    return render(request, 'wms/inventario.html', context)



"""
    FUNCIONES DE MOVIMIENTO
    - INGRESOS
"""

# FUNCIÓN MOVIMIENTO
# INGRESOS DE INVENTARIO INICIAL & IMPORTACIONES
# url: wms/ingreso/<int:int>
@login_required(login_url='login')
def wms_movimientos_ingreso(request, id): #OK
    """ Esta función asigna una ubiación a los items intresados por la importación
        Esta asiganación de ubicación se permite solo dentro de la bodega preselecionada
        Pasa el objecto solo para tomar sus valores 
    """
    
    item = InventarioIngresoBodega.objects.get(id=id)
    
    if item.n_referencia == 'inv_in_1':
        url_redirect = f'/wms/inventario/inicial/{item.bodega}'
    else:
        url_redirect = f'/wms/importacion/bodega/{item.n_referencia}' 
    
    
    # Lista de ubicaciones por bodega para seleccionar
    ubi_list = Ubicacion.objects.filter(bodega=item.bodega)
    
    # Movimientos ingresado 
    mov_list = (Movimiento.objects
        #.filter(item=item.id)
        .filter(product_id=item.product_id)
        .filter(lote_id=item.lote_id)
        .filter(referencia=item.referencia)
        .filter(n_referencia=item.n_referencia)
        )
    
    
    total_ubicaciones = mov_list.aggregate(Sum('unidades'))['unidades__sum']
    if total_ubicaciones == None:
        total_ubicaciones = 0
    
    total_ingresado = item.unidades_ingresadas
    ingresados_ubicaciones = total_ingresado - total_ubicaciones


    form = MovimientosForm()
    if request.method == 'POST':
        und = int(request.POST['unidades'])
        ubicaciones_und = und + total_ubicaciones

        form = MovimientosForm(request.POST)
        #if form.is_valid():
        if und == total_ingresado:
            # guardar
            if form.is_valid():
                form.save()
                wms_existencias_query_product_lote(product_id=request.POST['product_id'], lote_id=request.POST['lote_id'])
                #wms_existencias_query()
                # regresar a la lista de productos en importacion
                url_redirect
                #return redirect(f'/wms/importacion/bodega/{item.n_referencia}')
                #return redirect(f'/wms/importacion/bodega/{url_redirect}')
                return redirect(url_redirect)
            else:
                messages.error(request, form.errors)
            
        elif und > ingresados_ubicaciones or und > ubicaciones_und:
            # No se puede ingresar un cantidad mayor a la existente
            messages.error(request, 'No se puede ingresar una cantidad mayor a la exitente !!!')
            return redirect(f'/wms/ingreso/{item.id}')
        

        elif und < ingresados_ubicaciones :
            # guardar
            if form.is_valid():
                form.save()
                wms_existencias_query_product_lote(product_id=request.POST['product_id'], lote_id=request.POST['lote_id'])
                #wms_existencias_query()
                # retornar a la misma view
                return redirect(f'/wms/ingreso/{item.id}')
            else:
                messages.error(request, form.errors)

        elif ubicaciones_und == total_ingresado :
            # guardar
            if form.is_valid():
                form.save()
                wms_existencias_query_product_lote(product_id=request.POST['product_id'], lote_id=request.POST['lote_id'])
                #wms_existencias_query()
                return redirect(url_redirect)
            else:
                messages.error(request, form.errors)

    context = {
        'form'             :form,
        'item'             :item,
        'ubi_list'         :ubi_list,
        'mov_list'         :mov_list,
        'total_ubicaciones':total_ubicaciones
    }

    return render(request, 'wms/movimientos/ingreso_ubicacion_importacion.html', context)


# Enviar correo en movimiento interno, en caso de que el 
# movimiento se realice entre dos bodegas
def wms_movimiento_entre_bodegas_email(product_id, lote_id, ubi_egreso, ubi_ingreso, unidades, usuario):
    
    ubi_eg = Ubicacion.objects.get(id=ubi_egreso)
    ubi_in = Ubicacion.objects.get(id=ubi_ingreso)
    user   = User.objects.get(id=usuario)

    send_mail(
        subject='WMS-Movimiento entre bodegas',
        message=f'''
Se ha realizado un movimiento entre bodegas:\n
Código: {product_id}\n
Lote: {lote_id}\n
Sale de la ubicación: {ubi_eg} - unidades: {unidades}\n
Entra a la ubicación: {ubi_in} - unidades: {unidades}

Realizado por: {user.first_name} {user.last_name}\n

***Este mensaje fue enviado automaticamente mediante WMS***
''',
        from_email     = settings.EMAIL_HOST_USER,
        recipient_list = ['carcosh@gimpromed.com','dreyes@gimpromed.com','jgualotuna@gimpromed.com','ncaisapanta@gimpromed.com'],
        fail_silently  = False
        )

    return JsonResponse({'msg':'Correo enviado'}, status=200)



# Movimiento interno
# url: inventario/mov-interno-<int:id>
@login_required(login_url='login')
def wms_movimiento_interno(request, id): #OK
    
    item = Existencias.objects.get(id=id)
    #ubicaciones = Ubicacion.objects.exclude(id=item.ubicacion.id)
    und_existentes = item.unidades    

    if request.method == 'POST':

        # Control
        und_post = int(request.POST['unidades'])
        ubi_post = int(request.POST['ubicacion'])
        und_egreso = und_post * (-1)

        if und_post > 0 and und_post <= und_existentes:
            # Crear registro de Egreso
            mov_egreso = Movimiento(
                tipo            = 'Egreso',
                unidades        = und_egreso,
                ubicacion_id    = item.ubicacion.id,
                descripcion     = 'N/A',
                n_referencia    = '',
                referencia      = 'Movimiento Interno',
                usuario_id      = request.user.id,
                fecha_caducidad = item.fecha_caducidad,
                lote_id         = item.lote_id,
                product_id      = item.product_id,
                estado          = item.estado
            )
            mov_egreso.save()
            
            # Crear registro de Inreso
            mov_ingreso = Movimiento(
                tipo            = 'Ingreso',
                unidades        = und_post,
                ubicacion_id    = ubi_post,
                descripcion     = 'N/A',
                n_referencia    = '',
                referencia      = 'Movimiento Interno',
                usuario_id      = request.user.id,
                fecha_caducidad = item.fecha_caducidad,
                lote_id         = item.lote_id,
                product_id      = item.product_id,
                estado          = item.estado
            )
            mov_ingreso.save()
            
            # Actualizar inventario
            wms_existencias_query_product_lote(product_id=item.product_id, lote_id=item.lote_id)
            
            # Enviar correo si el movimiento es de una bodega a otra
            if item.ubicacion.bodega != Ubicacion.objects.get(id=ubi_post).bodega:
                wms_movimiento_entre_bodegas_email(
                    product_id  = item.product_id, 
                    lote_id     = item.lote_id, 
                    ubi_egreso  = item.ubicacion.id, 
                    ubi_ingreso = ubi_post, 
                    unidades    = und_post,
                    usuario=request.user.id
                )
            
            messages.success(request, 'Movimiento realizado con exito !!!')
            return redirect('/wms/inventario')
        
        elif und_post > und_existentes:
            messages.error(request, 'No se puede retirar una cantidad mayor a la exitente !!!')
            return redirect(f'/wms/inventario/mov-interno/{id}')

        else: 
            messages.error(request, 'Error en el movimiento !!!')
            return redirect(f'/wms/inventario/mov-interno/{id}')

    context = {
        'item':item,
        #'ubi':ubicaciones,
    }

    return render(request, 'wms/movimiento_interno.html', context)


def wms_movimiento_interno_get_ubi_list_ajax(request):
    
    bodega  = request.POST['bodega']
    pasillo = request.POST['pasillo']
    ubi_salida = int(request.POST['ubi_salida'])
    
    ubi_list = pd.DataFrame(Ubicacion.objects
        .filter(bodega=bodega)
        .filter(pasillo=pasillo)
        .exclude(id=ubi_salida)
        .values()
        ).sort_values(by=['bodega','pasillo','modulo','nivel'])
    
    ubi_list = de_dataframe_a_template(ubi_list)
    
    return JsonResponse({'ubi_list':ubi_list}, status=200)



# Si el movimiento se va a realizar dentro de bodega 6
# disparar un modal que indique el producto que se encuntra 
# en la ubicación seleccionada y el volumen ocupado
def wms_verificar_ubicacion_destino_ajax(request):
    
    ubi_destino = int(request.POST['ubi_destino'])
    
    ubi = Ubicacion.objects.get(id=ubi_destino)
    existencia_ubi_destino = pd.DataFrame(Existencias.objects.filter(ubicacion_id=ubi_destino).values())
    
    if not existencia_ubi_destino.empty:
        product_data = productos_odbc_and_django()[['product_id','Unidad_Empaque','Volumen']]
        product_data['vol_m3'] = product_data['Volumen'] / 1000000
        
        existencia_ubi_destino = existencia_ubi_destino.merge(product_data, on='product_id', how='left')
        existencia_ubi_destino['cartones'] = existencia_ubi_destino['unidades'] / existencia_ubi_destino['Unidad_Empaque']
        existencia_ubi_destino = existencia_ubi_destino[['product_id','lote_id','unidades','cartones']]
        
        existencia_ubi_destino['unidades'] = existencia_ubi_destino['unidades'].astype('str')
        existencia_ubi_destino.loc['total'] = existencia_ubi_destino.sum(numeric_only=True, axis=0)
        
        existencia_ubi_destino_html = existencia_ubi_destino.to_html(
            float_format='{:,.2f}'.format,
            classes='table table-responsive table-bordered m-0 p-0',
            table_id= 'existencias',
            index=False,
            justify='start',
            na_rep='',
        )
        
        return JsonResponse({
            'exitencias':existencia_ubi_destino_html,
            'msg':f'⚠ Posición {ubi} con mercaderia !!!',
            'type':'warning'
            })
    
    else:
        return JsonResponse({
            'msg':f'✅ Posición {ubi} vacia !!!',
            'type':'success'
        })



# Comprobar si existe para realizar el egreso
def comprobar_ajuste_egreso(codigo, lote, fecha_cadu, ubicacion, und_egreso): #OK
    
    ext = (
    Existencias.objects
        .filter(product_id=codigo)
        .filter(lote_id=lote)
        .filter(fecha_caducidad=fecha_cadu)
        .filter(ubicacion_id=ubicacion)
        )
    
    if ext.exists():
        total = ext.last().unidades - und_egreso
        
        if total >=0:
            return True
        else:
            return 'No se puede retirar más uniades de las existentes'
    else:
        return 'No hay existencias del código y lote seleccionados, ó no coincide la fecha o ubicación. \n No se puede realizar el egreso!!!'



# Ajuste de inventario
# movimiento de ingreso o egreso
# url: inventario/mov-ajuste
@transaction.atomic
@login_required(login_url='login')
def wms_movimiento_ajuste(request): #OK
    
    # prod = productos_odbc_and_django()[['product_id','Nombre','Marca']]
    # prod = de_dataframe_a_template(prod)
    # ubi  = Ubicacion.objects.all()
    
    if request.method == 'POST':
        tipo = request.POST['tipo']
        
        if tipo == 'Ingreso':   
            
            mov = Movimiento(
                tipo            = tipo,
                unidades        = int(request.POST['unidades']),
                ubicacion_id    = int(request.POST['ubicacion']),
                descripcion     = request.POST['descripcion'],
                n_referencia    = request.POST['n_referencia'],
                referencia      = 'Ajuste',
                usuario_id      = request.user.id,
                fecha_caducidad = request.POST['fecha_caducidad'],
                lote_id         = request.POST['lote_id'],
                product_id      = request.POST['product_id'],
                estado          = request.POST['estado']
            )
            
            mov.save()
            wms_existencias_query_product_lote(product_id=request.POST['product_id'], lote_id=request.POST['lote_id'])
            messages.success(request, 'Ajuste realizado exitosamente !!!')
            return redirect('/wms/inventario')
                    
        elif tipo == 'Egreso':
            
            mov = Movimiento(
                tipo            = tipo,
                unidades        = int(request.POST['unidades'])*-1,
                ubicacion_id    = int(request.POST['ubicacion']),
                descripcion     = request.POST['descripcion'],
                n_referencia    = request.POST['n_referencia'],
                referencia      = 'Ajuste',
                usuario_id      = request.user.id,
                fecha_caducidad = request.POST['fecha_caducidad'],
                lote_id         = request.POST['lote_id'],
                product_id      = request.POST['product_id'],
                estado          = request.POST['estado']
            )
            
            comprobar = comprobar_ajuste_egreso(
                codigo     = request.POST['product_id'],
                lote       = request.POST['lote_id'],
                ubicacion  = int(request.POST['ubicacion']),
                fecha_cadu = request.POST['fecha_caducidad'],
                und_egreso = int(request.POST['unidades'])
            )
            
            if comprobar == True:
                mov.save()
                wms_existencias_query_product_lote(product_id=request.POST['product_id'], lote_id=request.POST['lote_id'])
                messages.success(request, 'Ajuste realizado exitosamente !!!')
                return redirect('/wms/inventario')
            else:
                messages.error(request, comprobar)
                return HttpResponseRedirect('/wms/inventario/mov-ajuste')

        return redirect('/wms/inventario')
    
    context = {
        #'productos':prod,
        #'ubi':ubi
    }

    return render(request, 'wms/movimientos/movimiento_ajuste.html', context)


# Llamar los productos para ajuste de acuerdo a tipo de movimiento
def wms_ajuste_product_ajax(request):
    
    tipo = request.POST['tipo']
    
    if tipo == 'Ingreso':
        # Buscar en Existencias MBA
        productos = wms_stock_lote_products()
        return JsonResponse({'productos':productos})
        
    elif tipo == 'Egreso':
        # Buscar en Existencias WMS
        productos = pd.DataFrame(Existencias.objects.all().values('product_id'))
        prod = productos_odbc_and_django()[['product_id','Nombre','Marca']]
        productos = productos.merge(prod, on='product_id', how='left').sort_values(by=['Marca','product_id'], ascending=[True, True])
        productos = productos.drop_duplicates(subset='product_id')
        productos = de_dataframe_a_template(productos)
    
        return JsonResponse({'productos':productos})
    return JsonResponse({'productos':None})
    
    
# Llamar los valores para ajuste de acuerdo a tipo de movimiento
def wms_ajuste_lote_ajax(request):
    
    tipo = request.POST['tipo']
    prod = request.POST['product_id']
    
    if tipo == 'Ingreso':
        # Buscar en Existencias MBA
        if not prod:
            lotes = []
        else:
            lotes = wms_stock_lote_cerezos_by_product(product_id=prod)[['LOTE_ID']]
            lotes = lotes.drop_duplicates(subset='LOTE_ID')
            lotes = lotes.rename(columns={'LOTE_ID':'lote_id'})
            lotes = de_dataframe_a_template(lotes)
        
        return JsonResponse({'lotes':lotes})
        
    elif tipo == 'Egreso':
        # Buscar en Existencias WMS
        lotes = pd.DataFrame(Existencias.objects.filter(product_id=prod)
            .values('lote_id').distinct())
        lotes = de_dataframe_a_template(lotes)
        
        return JsonResponse({'lotes':lotes})
    return JsonResponse({'lotes':None})


# Llamar los valores para ajuste de acuerdo a tipo de movimiento
def wms_ajuste_fecha_ajax(request):
    
    tipo = request.POST['tipo']
    prod = request.POST['product_id']
    lote = request.POST['lote_id']
    
    if tipo == 'Ingreso':
        existencias = wms_stock_lote_cerezos_by_product(product_id=prod)
        existencias = existencias.drop_duplicates(subset='LOTE_ID')
        
        if not lote:
            fecha = ''
        else:
            existencias = existencias[existencias['LOTE_ID']==lote]
            existencias['FECHA_CADUCIDAD'] = existencias['FECHA_CADUCIDAD'].astype('str')
            
            fecha = de_dataframe_a_template(existencias)[0] 
            fecha = fecha['FECHA_CADUCIDAD']
        
        ubi = de_dataframe_a_template(existencias)[0]
        ubi = ubi['LOCATION']
        ubicaciones = pd.DataFrame(Ubicacion.objects
            #.filter(bodega=ubi)
            .all()
            .values(
            'id', 
            'bodega', 
            'pasillo', 
            'modulo',
            'nivel'))
        ubicaciones = ubicaciones.rename(
            columns={
                'id':'ubicacion_id', 
                'bodega':'ubicacion__bodega', 
                'pasillo':'ubicacion__pasillo', 
                'modulo':'ubicacion__modulo',
                'nivel':'ubicacion__nivel'
            }
        )
        ubicaciones = de_dataframe_a_template(ubicaciones)
        
        estado = [
            {'index':0, 'estado':'Disponible'},
            {'index':1, 'estado':'Cuarentena'},
        ]
        
        referencia = [
            {'index':0, 'referencia':'Inventario Inicial'},
            {'index':1, 'referencia':'Ingreso Importación'},
            {'index':2, 'referencia':'Liberación'},
            {'index':3, 'referencia':'Ajuste'},
        ]
        return JsonResponse({
            'fecha':fecha,
            'ubicaciones':ubicaciones,
            'estado':estado,
            'referencia':referencia
        })
        
    elif tipo == 'Egreso':
        # Buscar en Existencias WMS        
        existencias = Existencias.objects.filter(product_id=prod, lote_id=lote) 
        if not lote:
            fecha = ''
        else:
            fecha = existencias.first().fecha_caducidad
            
        ubicaciones = pd.DataFrame(existencias.values(
            'ubicacion_id', 'ubicacion__bodega', 
            'ubicacion__pasillo', 'ubicacion__modulo',
            'ubicacion__nivel').distinct())
        ubicaciones = de_dataframe_a_template(ubicaciones)
        
        estado = pd.DataFrame(existencias.values('estado').distinct())
        estado = de_dataframe_a_template(estado)
        
        referencia = [
            {'index':0, 'referencia':'Liberación'},
            {'index':1, 'referencia':'Ajuste'},
            {'index':2, 'referencia':'Picking'},
            {'index':3, 'referencia':'Transferencia'},
        ]
        
        return JsonResponse({
            'fecha':fecha,
            'ubicaciones':ubicaciones,
            'estado':estado,
            'referencia':referencia
        })
            
    return JsonResponse({
            'fecha':None,
            'ubicaciones':None,
            'estado':None,
            'referencia':None
        })



# lista de movimientos
# url: 'movimientos/list'
@login_required(login_url='login')
def wms_movimientos_list(request): #OK
    """ Lista de movimientos """
    
    mov = Movimiento.objects.all().order_by('-fecha_hora')
    
    context = {
        'mov':mov
    }

    return render(request, 'wms/movimientos_list.html', context)



### PICKDING
# Lista de pedidos
# url: picking/list
@login_required(login_url='login')
def wms_listado_pedidos(request): #OK
    """ Listado de pedidos (picking) """

    pedidos = pd.DataFrame(reservas_table())
    pedidos = pedidos[pedidos['WARE_CODE']=='BCT']
    pedidos['FECHA_PEDIDO'] = pedidos['FECHA_PEDIDO'].astype(str)
    pedidos = pedidos.drop_duplicates(subset='CONTRATO_ID')

    estados = pd.DataFrame(EstadoPicking.objects.all().values('n_pedido','estado','user__user__first_name','user__user__last_name'))
    estados = estados.rename(columns={'n_pedido':'CONTRATO_ID'})   
    pedidos = pedidos.merge(estados, on='CONTRATO_ID', how='left')
    
    pedidos = de_dataframe_a_template(pedidos)

    context = {
        'reservas':pedidos
    }

    return render(request, 'wms/listado_pedidos.html', context)


# Detalle de pedido
# url: picking/<n_pedido>
@login_required(login_url='login')
def wms_egreso_picking(request, n_pedido): #OK
    
    estado_picking = EstadoPicking.objects.filter(n_pedido=n_pedido).exists()
    if estado_picking:
        est = EstadoPicking.objects.get(n_pedido=n_pedido)
        estado = est.estado
        estado_id = est.id
    else: 
        estado = 'SIN ESTADO'
        estado_id = ''
    
    prod   = productos_odbc_and_django()[['product_id','Nombre','Marca']]
    prod   = prod.rename(columns={'product_id':'PRODUCT_ID'})
    
    pedido = pedido_por_cliente(n_pedido).sort_values('PRODUCT_ID') #;print(pedido.keys())
    pedido = pedido.groupby(by=['CONTRATO_ID','NOMBRE_CLIENTE','FECHA_PEDIDO','HORA_LLEGADA','PRODUCT_ID','PRODUCT_NAME']).sum().reset_index() 
    pedido = pedido.merge(prod, on='PRODUCT_ID',how='left')
        
    prod_list = list(pedido['PRODUCT_ID'].unique())
    
    n_ped = pedido['CONTRATO_ID'].iloc[0]
    cli   = pedido['NOMBRE_CLIENTE'].iloc[0]
    fecha = pedido['FECHA_PEDIDO'].iloc[0]
    hora  = pedido['HORA_LLEGADA'].iloc[0]

    movimientos = Movimiento.objects.filter(referencia='Picking').filter(n_referencia=n_pedido)
    
    if movimientos.exists():
        mov = pd.DataFrame(movimientos.values(
            'id','product_id','lote_id','fecha_caducidad','tipo','unidades',
            'ubicacion_id','ubicacion__bodega','ubicacion__pasillo','ubicacion__modulo','ubicacion__nivel'
        ))

        mov['fecha_caducidad'] = mov['fecha_caducidad'].astype(str)
        mov['unidades'] = pd.Series.abs(mov['unidades'])
        
        unds_pickeadas = mov[['product_id','unidades']].groupby(by='product_id').sum().reset_index()
        unds_pickeadas = unds_pickeadas.rename(columns={'product_id':'PRODUCT_ID'})
        pedido = pedido.merge(unds_pickeadas, on='PRODUCT_ID', how='left')
        
        mov = de_dataframe_a_template(mov)
        
    else:
        mov = {}


    inv = Existencias.objects.filter(product_id__in=prod_list).values(
        'product_id','lote_id','fecha_caducidad','unidades',
        'ubicacion_id','ubicacion__bodega','ubicacion__pasillo','ubicacion__modulo','ubicacion__nivel',
        'ubicacion__distancia_puerta',
        'unidades',
        'estado'
    )
    
    if inv.exists():
        inv = pd.DataFrame(inv).sort_values(by=['lote_id','fecha_caducidad','ubicacion__distancia_puerta'], ascending=[True,True,True])
        inv['fecha_caducidad'] = inv['fecha_caducidad'].astype(str)
        
        r_lote = wms_reservas_lotes_datos()
        if not r_lote.empty:
            inv = inv.merge(r_lote, on=['product_id','lote_id'], how='left')
            inv = de_dataframe_a_template(inv)
    else:
        inv = {}
    
    ped = de_dataframe_a_template(pedido)
    
    for i in prod_list:
        for j in ped:
            if j['PRODUCT_ID'] == i:
                j['ubi'] = ubi_list = []
                j['pik'] = pik_list = []
                for k in inv:
                    if k['product_id'] == i:
                        ubi_list.append(k)
                for m in mov:
                    if m['product_id'] == i:
                        pik_list.append(m)
    
    context = {
        'pedido':ped,
        'n_ped':n_ped,
        'cli':cli,
        'fecha': fecha ,
        'hora':hora,
        'estado':estado,
        'estado_id':estado_id
    }
    
    return render(request, 'wms/picking.html', context)


# Estado Picking AJAX
def wms_estado_picking_ajax(request):
    
    contrato_id = request.POST['n_ped']
    estado = request.POST['estado']
    user_id = int(request.POST['user_id'])
    user_perfil_id   = UserPerfil.objects.get(user__id=user_id).id
        
    reserva = wms_reserva_por_contratoid(contrato_id)
    cli     = clientes_warehouse()[['NOMBRE_CLIENTE','CODIGO_CLIENTE','CLIENT_TYPE']]
    reserva = reserva.merge(cli, on='NOMBRE_CLIENTE', how='left')
    
    cliente = reserva['NOMBRE_CLIENTE'].iloc[0]
    fecha_pedido = reserva['FECHA_PEDIDO'].iloc[0]
    tipo_cliente = reserva['CLIENT_TYPE'].iloc[0]
    bodega = reserva['WARE_CODE'].iloc[0]
    codigo_cliente = reserva['CODIGO_CLIENTE'].iloc[0]
    data = (reserva[['PRODUCT_ID', 'QUANTITY']]).to_dict()
    data = json.dumps(data)
    
    estado_picking = EstadoPicking(
        user_id        = user_perfil_id,
        n_pedido       = contrato_id,
        estado         = estado,
        fecha_pedido   = fecha_pedido,
        tipo_cliente   = tipo_cliente,
        cliente        = cliente,
        codigo_cliente = codigo_cliente,
        detalle        = data,
        bodega         = bodega,
    )
    
    try:
        estado_picking.save()
    
        if estado_picking.id:
            return JsonResponse({'msg':f'✅ Estado de picking {estado_picking.estado}',
                            'alert':'success'})
    except:
        return JsonResponse({'msg':'❌ Error, intente nuevamente !!!',
                            'alert':'danger'})



# Actualizar Estado Picking AJAX
def wms_estado_picking_actualizar_ajax(request):
    
    id_picking = int(request.POST['id_picking'])
    estado = request.POST['estado']
    
    estado_picking = EstadoPicking.objects.get(id=id_picking) 
    estado_picking.estado = estado
    estado_picking.fecha_actualizado = datetime.now()
    
    try:
        estado_picking.save()
    
        if estado_picking.id:
            return JsonResponse({'msg':f'✅ Estado de picking {estado_picking.estado}',
                            'alert':'success'})
    except:
        return JsonResponse({'msg':'❌ Error, intente nuevamente !!!',
                            'alert':'danger'})



# Crear egreso en tabla movimientos
def wms_movimiento_egreso_picking(request): #OK
    
    # Egreso
    unds_egreso = request.POST['unds']
    if not unds_egreso:
        #messages.error(request, 'Error, ingrese una cantidad !!!')
        unds_egreso = 0
        return JsonResponse({'msg':'❌ Error, ingrese una cantidad !!!'})
    else:
        unds_egreso = int(unds_egreso)
        
    n_picking = request.POST['n_picking']
    
    # Item busqueda Existencias
    prod_id   = request.POST['prod_id']
    lote_id   = request.POST['lote_id']
    caducidad = request.POST['caducidad']
    ubi       = int(request.POST['ubi'])
    
    existencia = (Existencias.objects
        .filter(product_id=prod_id,)
        .filter(lote_id=lote_id)
        .filter(fecha_caducidad=caducidad)
        .filter(ubicacion_id=ubi)
        )
    
    movimientos = Movimiento.objects.filter(product_id=prod_id).filter(referencia='Picking').filter(n_referencia=n_picking)
    
    if movimientos.exists():
        mov = pd.DataFrame(movimientos.values('product_id','unidades'))
        mov['unidades'] = pd.Series.abs(mov['unidades'])
        mov = mov[['product_id','unidades']].groupby(by='product_id').sum()
        mov = de_dataframe_a_template(mov)[0]
        total_mov = mov['unidades'] + int(unds_egreso)
    else:
        total_mov = int(unds_egreso)
    
    pedido = pedido_por_cliente(n_picking)
    pedido = pedido[pedido['PRODUCT_ID']==prod_id][['PRODUCT_ID','QUANTITY']]#.reset_index()
    pedido = pedido.groupby(by='PRODUCT_ID').sum().to_dict('records')[0]
    total_pedido = pedido['QUANTITY']   
    
    if not existencia.exists():
        return JsonResponse({'msg':'❌ Error, revise las existencias o refresque la pagina !!!'})
    elif existencia.exists():
        if unds_egreso > existencia.last().unidades:
            return JsonResponse({'msg':'❌ No puede retirar más unidades de las existentes !!!'})
        elif unds_egreso == 0 or unds_egreso < 0:
            return JsonResponse({'msg':'❌ La cantidad debe ser mayor 0 !!!'})
        elif total_mov > total_pedido:
            return JsonResponse({'msg':'❌ No puede retirar más unidades de las solicitadas en el Picking !!!'})
        elif total_mov <= total_pedido:
            
            picking = Movimiento(
                product_id      = prod_id,
                lote_id         = lote_id,
                fecha_caducidad = caducidad,
                tipo            = 'Egreso',
                descripcion     = 'N/A',
                referencia      = 'Picking',
                n_referencia    = n_picking,
                ubicacion_id    = ubi,
                unidades        = unds_egreso*-1,
                estado          = 'Disponible',
                estado_picking  = 'En Despacho',
                usuario_id      = request.user.id,
            )
            
            picking.save()
            wms_existencias_query_product_lote(product_id=prod_id, lote_id=lote_id)
            #wms_existencias_query()
            
            return JsonResponse({'msg':f'✅ Producto {prod_id}, lote {lote_id} seleccionado correctamente !!!'})
        return JsonResponse({'msg':'❌ Error !!!'})
    return JsonResponse({'msg':'❌Error !!!'})


#def wms_movimiento_reverso_picking()

# Eliminar movimeinto de egreso AJAX
def wms_eliminar_movimiento(request): #OK

    mov_id = request.POST['mov']
    mov_id = int(mov_id)
    mov = Movimiento.objects.get(id=mov_id)
    m = mov
    
    mov.delete()
    
    wms_existencias_query_product_lote(product_id=m.product_id, lote_id=m.lote_id)
    #wms_existencias_query()

    return JsonResponse({'msg':'Egreso eliminado ✔!!!'})


# Tabla de reservas AJAX
def wms_reservas_lote_consulta_ajax(request):
    
    
    prod = request.POST['prod_id']
    lote = request.POST['lote_id']
    
    r_lote = wms_reservas_lote_consulta(prod, lote)
    
    return HttpResponse(r_lote)


# Lista de productos en despahco
# url: picking/producto-despacho/list
@login_required(login_url='login')
def wms_productos_en_despacho_list(request): #OK
    
    mov = Movimiento.objects.filter(estado_picking='En Despacho')
    mov_list = mov.values_list('n_referencia', flat=True).distinct()
    pik = EstadoPicking.objects.filter(n_pedido__in=mov_list)
    
    en_despacho = pd.DataFrame(mov.values(
        'product_id','lote_id','fecha_caducidad','referencia','n_referencia',
        'ubicacion__bodega','ubicacion__pasillo','ubicacion__modulo','ubicacion__nivel',
        'fecha_hora','unidades',
        'usuario__first_name','usuario__last_name'
    ))
    contexto_picking = pd.DataFrame(pik.values())[['n_pedido','cliente']]
    contexto_picking = contexto_picking.rename(columns={'n_pedido':'n_referencia'})
    
    en_despacho = en_despacho.merge(contexto_picking, on='n_referencia', how='left')
    en_despacho['unidades'] = en_despacho['unidades']*-1
    en_despacho['n_referencia'] = en_despacho['n_referencia'].astype('float')
    en_despacho['n_referencia'] = en_despacho['n_referencia'].astype('int')
    # en_despacho['fecha_caducidad'] = en_despacho['fecha_caducidad'].astype('str')
    en_despacho['fecha_hora'] = pd.to_datetime(en_despacho['fecha_hora']).dt.strftime('%Y-%m-%d %H:%M')
    
    en_despacho = en_despacho.sort_values(by='n_referencia')
    en_despacho = de_dataframe_a_template(en_despacho)

    context = {
        'mov':en_despacho
    }
    
    return render(request, 'wms/productos_en_despacho_list.html', context)



def wms_armar_codigo_factura(n_factura):
    
    # FACSI-1001000077438-GIMPR
    # 000077438 -> 9
    
    len_codigo  = 9
    len_input   = len(n_factura)
    len_ceros   = len_codigo - len_input
    input_ceros = '0' * len_ceros
    
    n_f = 'FCSRI-1001' + input_ceros + n_factura + '-GIMPR'
    factura = wms_detalle_factura(n_f)
    factura['lote_id'] = quitar_puntos(factura['lote_id'])
    factura = factura.groupby(by=[
        'CODIGO_FACTURA','CODIGO_CLIENTE','FECHA_FACTURA','product_id','PRODUCT_NAME',
        'GROUP_CODE','lote_id','FECHA_CADUCIDAD','NUMERO_PEDIDO_SISTEMA',
        'NOMBRE_CLIENTE','IDENTIFICACION_FISCAL']).sum().reset_index()

    if not factura.empty:

        fn_pedido = de_dataframe_a_template(factura)[0]['NUMERO_PEDIDO_SISTEMA']
        
        try:
            picking = pd.DataFrame(Movimiento.objects.filter(n_referencia = fn_pedido).values())
            picking['lote_wms'] = picking['lote_id']
            picking['lote_id'] = quitar_puntos(picking['lote_id'])
            picking = picking.groupby(by=['product_id','lote_id','estado_picking','lote_wms']).sum().reset_index()
            
            factura = factura.merge(picking, on=['product_id','lote_id'], how='left').fillna(0)
            factura['unidades'] = factura['unidades'].abs()
            factura['diferencia'] = factura['unidades'] - factura['EGRESO_TEMP']
            
            factura = {
                'factura':de_dataframe_a_template(factura),
                'cabecera':de_dataframe_a_template(factura)[0]
            }
        except:
            factura = {
                'cabecera':de_dataframe_a_template(factura)[0]
            }
        
        return factura

    else:
        return JsonResponse({'msg':'Factura no encontrada !!!'})


# Cruce de picking y factura 
# url: 'wms/cruce/picking/facturas'
@login_required(login_url='login')
def wms_cruce_picking_factura(request):
    
    if request.method=="POST":
        n_factura = request.POST['n_factura']
        factura = wms_armar_codigo_factura(n_factura)        
        
        context={
            'factura':factura,
        }
        return render(request, 'wms/cruce_picking_factura.html', context)
    context = {}
    return render(request, 'wms/cruce_picking_factura.html', context)



def wms_cruce_check_despacho(request):
    
    n_pick  = request.POST['n_picking']
    prod_id = request.POST['prod_id']
    lote_id = request.POST['lote_id']
    
    items = (Movimiento.objects
        .filter(n_referencia=n_pick)
        .filter(product_id=prod_id)
        .filter(lote_id=lote_id)
        )
    
    if items.exists():
        items.update(estado_picking='Despachado')
        
        return JsonResponse({
            'msg':'OK',
            })
        
    else:
        return JsonResponse({
            'msg':'FAIL',
            })    
        
        
        
def wms_picking_realizados(request):
    
    picking = list(Movimiento.objects.filter(referencia='Picking').values_list('n_referencia',flat=True).distinct())
    picking = tuple(map(lambda x: int(float(x)), picking))
    
    query = wms_picking_realizados_warehouse_list()
    # print(query)
    
    return HttpResponse('ok')


# Liberaciones Cuarentena
def wms_liberaciones_cuarentena(request):
    liberacion_mba3 = wms_datos_liberacion_cuc()
    #print(liberacion_mba3)
    return HttpResponse('ok')



# Revisicón de transferencias
def wms_revision_transferencia_ajax(request):
    
    try:
        n_trasf = request.POST['n_trasf'] 
        prod = productos_odbc_and_django()[['product_id','Nombre','Marca']]
        
        trasf_mba = doc_transferencia_odbc(n_trasf) 
        trasf_mba = trasf_mba.groupby(by=['doc','product_id','lote_id','bodega_salida','f_cadu']).sum().reset_index()
        trasf_mba = trasf_mba.rename(columns={'unidades':'unidades_mba'})
        trasf_mba = trasf_mba.merge(prod, on='product_id', how='left')    
        
        trasf_mov = pd.DataFrame(Movimiento.objects.filter(n_referencia=n_trasf).values('product_id','lote_id','unidades'))
        
        if not trasf_mov.empty:
        
            trasf_mov['unidades'] = trasf_mov['unidades'] * -1
            trasf_mov = trasf_mov.rename(columns={'unidades':'unidades_wms'})
            trasf_mov = trasf_mov.groupby(by=['product_id','lote_id']).sum().reset_index()
            
            trasf_rev = trasf_mba.merge(trasf_mov, on=['product_id','lote_id'], how='left').fillna(0)
            trasf_rev['diferencia'] = trasf_rev['unidades_mba'] - trasf_rev['unidades_wms']
            trasf_rev = trasf_rev[['product_id','Nombre','Marca','lote_id','unidades_mba','unidades_wms','diferencia']]
            trasf_rev = trasf_rev.rename(columns={'product_id':'Código','lote_id':'Lote'}).sort_values('diferencia',ascending=False)
            
            trasf_rev = trasf_rev.to_html(
                classes='table table-responsive table-bordered m-0 p-0', 
                float_format='{:.0f}'.format,
                index=False,
                justify='start'
            )
            
            return HttpResponse(trasf_rev)
        
        else:
            trasf_mba = trasf_mba[['product_id','Nombre','Marca','lote_id','unidades_mba']]
            trasf_mba['unidades_wms'] = 'no existen !!!'
            trasf_mba['diferencia'] = 'no existen !!!'
            
            trasf_mba = trasf_mba.rename(columns={'product_id':'Código','lote_id':'Lote'})
            trasf_rev = trasf_mba.to_html(
                classes='table table-responsive table-bordered m-0 p-0', 
                float_format='{:.0f}'.format,
                index=False,
                justify='start'
            )
            return HttpResponse(trasf_rev)
            
    except:
        return HttpResponse('El número de trasferencia es incorrecto !!!')



@login_required(login_url='login')
def wms_revision_transferencia(request):
    return render(request, 'wms/revision_trasferencia.html', {})



def wms_transferencia_input_ajax(request):
    
    n_trasf = request.POST['n_trasf']
    trans_mba  = doc_transferencia_odbc(n_trasf)
    
    new_transf = Transferencia.objects.filter(n_transferencia=n_trasf)
    if not new_transf.exists():

        trans_mba['n_transferencia'] = n_trasf
        trans_mba = trans_mba.groupby(by=['doc','n_transferencia','product_id','lote_id','f_cadu','bodega_salida']).sum().reset_index()
        trans_mba['f_cadu'] = trans_mba['f_cadu'].astype(str)
        trans_mba = de_dataframe_a_template(trans_mba)
        
        tr_list = []
        for i in trans_mba:        
            tr = Transferencia(
                doc_gimp        = i['doc'],
                n_transferencia = i['n_transferencia'],
                product_id      = i['product_id'],
                lote_id         = i['lote_id'],
                fecha_caducidad = i['f_cadu'],
                bodega_salida   = i['bodega_salida'],
                unidades        = i['unidades']
            )
        
            tr_list.append(tr)
            
        Transferencia.objects.bulk_create(tr_list)
        
        messages.success(request, f'La Transferencia {n_trasf} fue añadida exitosamente !!!')
        return redirect('/wms/transferencias/list') 
    
    elif new_transf.exists():
        return HttpResponse(f'La Transferencia {n_trasf} ya fue añadida')
    
    
    
@login_required(login_url='login')
def wms_transferencias_list(request):
    
    transf_wms = pd.DataFrame(Transferencia.objects.all().values()).drop_duplicates(subset='n_transferencia')
    if not transf_wms.empty:
        transf_wms['fecha_hora'] = pd.to_datetime(transf_wms['fecha_hora']).dt.strftime('%d-%m-%Y - %r').astype(str)
        transf_wms = transf_wms.sort_values(by='fecha_hora', ascending=False)
        
    transf_wms = de_dataframe_a_template(transf_wms)
    
    context = {
        'transf_wms':transf_wms
    }
    
    return render(request, 'wms/transferencias_list.html', context)



@login_required(login_url='login')
def wms_transferencia_picking(request, n_transf):
    
    prod   = productos_odbc_and_django()[['product_id','Nombre','Marca']]
    
    # Trasferencia
    transf = pd.DataFrame(Transferencia.objects.filter(n_transferencia=n_transf).values())
    transf = transf.merge(prod, on='product_id', how='left')
    transf['fecha_caducidad'] = pd.to_datetime(transf['fecha_caducidad']).dt.strftime('%d-%m-%Y').astype(str)
    
    # Productos y cantidades egresados de WMS por Picking Transferencia
    mov = pd.DataFrame(Movimiento.objects.filter(n_referencia=n_transf).values(
        'id',
        'product_id','lote_id','unidades','ubicacion__bodega','ubicacion__pasillo','ubicacion__modulo','ubicacion__nivel',
        'ubicacion__distancia_puerta'))
    
    if not mov.empty:
        mov['unidades'] = mov['unidades']*-1
        
    # Lista de movimientos
    mov_list = de_dataframe_a_template(mov)
    
    # Si existen movimiento añadir al pedido la suma
    if not mov.empty:
        mov_group = mov.groupby(by=['product_id','lote_id']).sum().reset_index()
        mov_group = mov_group.rename(columns={'unidades':'unidades_wms'})
        transf = transf.merge(mov_group, on=['product_id','lote_id'], how='left').fillna(0)
        
    # Ubicaciones de productos en transferencia
    prod_lote = transf[['product_id','lote_id']].to_dict('records')
    ext_id = []
    for i in prod_lote:
        ext = Existencias.objects.filter(product_id=i['product_id'], lote_id=i['lote_id']).values(
            'product_id','lote_id','fecha_caducidad','unidades','estado',
            'ubicacion__id',
            'ubicacion__bodega','ubicacion__pasillo','ubicacion__modulo','ubicacion__nivel',
            'ubicacion__distancia_puerta'
        )
        if ext.exists():
            for j in ext:
                ext_id.append(j)
    
    transf_template = de_dataframe_a_template(transf)
    
    prod = list(transf['product_id'].unique())
    for i in prod:
        for j in transf_template:
            if j['product_id'] == i:
                j['ubi'] = ubi_list = []
                j['pik'] = pik_list = []
                for k in ext_id:
                    if k['product_id'] == i:
                        ubi_list.append(k)
                for m in mov_list:
                    if m['product_id'] == i:
                        pik_list.append(m)
    
    # print(transf_template)
    # transf_template = sorted(transf_template, key= lambda x: x['ubi'][0['ubicacion__bodega']])
    
    context = {
        'transf':transf_template,
        'n_transf':n_transf
    }
    return render(request, 'wms/transferencia_picking.html', context)



# Crear egreso en tabla movimientos
def wms_movimiento_egreso_transferencia(request): #OK
    
    # Egreso
    unds_egreso = request.POST['unds']
    if not unds_egreso:
        #messages.error(request, 'Error, ingrese una cantidad !!!')
        unds_egreso = 0
        return JsonResponse({'msg':'❌ Error, ingrese una cantidad !!!'})
    else:
        unds_egreso = int(unds_egreso)
        
    n_transf = request.POST['n_transf']
    
    # Item busqueda Existencias
    prod_id   = request.POST['prod_id']
    lote_id   = request.POST['lote_id']
    caducidad = request.POST['caducidad']
    ubi       = int(request.POST['ubi'])
    
    existencia = (Existencias.objects
        .filter(product_id=prod_id,)
        .filter(lote_id=lote_id)
        .filter(fecha_caducidad=caducidad)
        .filter(ubicacion_id=ubi)
        )
    
    movimientos = Movimiento.objects.filter(product_id=prod_id).filter(n_referencia=n_transf)
    
    if movimientos.exists():
        mov = pd.DataFrame(movimientos.values('product_id','unidades'))
        mov['unidades'] = pd.Series.abs(mov['unidades'])
        mov = mov[['product_id','unidades']].groupby(by='product_id').sum()
        mov = de_dataframe_a_template(mov)[0]
        total_mov = mov['unidades'] + int(unds_egreso)
    else:
        total_mov = int(unds_egreso)
    
    total_transf = sum(Transferencia.objects
        .filter(n_transferencia=n_transf)
        .filter(product_id=prod_id).values_list('unidades',flat=True))
    
    if not existencia.exists():
        return JsonResponse({'msg':'❌ Error, revise las existencias o refresque la pagina !!!'})
    elif existencia.exists():
        if unds_egreso > existencia.last().unidades:
            return JsonResponse({'msg':'❌ No puede retirar más unidades de las existentes !!!'})
        elif unds_egreso == 0 or unds_egreso < 0:
            return JsonResponse({'msg':'❌ La cantidad debe ser mayor 0 !!!'})
        elif total_mov > total_transf:
            return JsonResponse({'msg':'❌ No puede retirar más unidades de las solicitadas en el Picking !!!'})
        elif total_mov <= total_transf:
            
            transferencia = Movimiento(
                product_id      = prod_id,
                lote_id         = lote_id,
                fecha_caducidad = caducidad,
                tipo            = 'Egreso',
                descripcion     = 'Transferencia',
                referencia      = 'Transferencia',
                n_referencia    = n_transf,
                ubicacion_id    = ubi,
                unidades        = unds_egreso*-1,
                estado          = 'Disponible',
                estado_picking  = 'Despachado',
                usuario_id      = request.user.id,
            )
            
            transferencia.save()
            
            wms_existencias_query_product_lote(product_id=prod_id, lote_id=lote_id)
            #wms_existencias_query()
            
            return JsonResponse({'msg':f'✅ Producto {prod_id}, lote {lote_id} seleccionado correctamente !!!'})
        return JsonResponse({'msg':'❌ Error !!!'})
    return JsonResponse({'msg':'❌Error !!!'})



## FUNCIONES PENDIENTES POR DESARROLLAR
# Listado de liberaciones
# url: wms/liberaciones
# def wms_lista_liberaciones(request):

#     lista_liberaciones = wms_datos_doc_liberaciones()
#     #inv_cuc = Movimiento.objects.filter(cuarentena=True)
#     #print(lista_liberaciones)
#     context = {
#         'liberaciones':de_dataframe_a_template(lista_liberaciones),
#         #'inv_cuc':inv_cuc
#     }

#     return render(request, 'wms/movimientos/liberaciones_list.html', context)


# def wms_liberacion(request):

#     doc = request.POST['doc']
#     liberacion_query = wms_datos_liberacion_cuc(doc)
#     liberaciones_list = wms_datos_doc_liberaciones()[['DOC_ID_CORP','MEMO','ENTERED_DATE']]
#     liberaciones_list = liberaciones_list[liberaciones_list['DOC_ID_CORP']==doc]

#     liberacion = liberacion_query.merge(liberaciones_list, on='DOC_ID_CORP', how='left')
#     liberacion['product_id'] = list(map(lambda x:x[:-6], liberacion['PRODUCT_ID_CORP']))

#     # print(liberacion_query)
#     # print(liberaciones_list)
#     # print(liberacion)

#     return HttpResponse(liberacion_query)