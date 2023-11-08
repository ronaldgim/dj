from django.shortcuts import render, redirect

# Datos de importaciones
from datos.views import (
    importaciones_llegadas_odbc, 
    productos_odbc_and_django, 
    de_dataframe_a_template, 
    importaciones_llegadas_ocompra_odbc,
    reservas_lote)

# Pedidos por clientes
from etiquetado.views import pedido_por_cliente, reservas_table

# Http
from django.http import HttpResponse,JsonResponse, HttpResponseRedirect

# Json
import json

# DB
from django.db import connections

# Models
from django.db.models import Sum, Count
from wms.models import InventarioIngresoBodega, Ubicacion, Movimiento

# Pandas
import pandas as pd

# Forms
from wms.forms import MovimientosForm

# Messages
from django.contrib import messages

# Query's
from django.db.models import Q

# Models
from users.models import User


"""
    LISTAS DE INGRESOS 
    - LISTA DE IMPORTACIONES
    - LISTA DE BODEGA DE INVENTARIO INICIAL
"""
# Lista de importaciones por llegar
# url: importaciones/list
def wms_importaciones_list(request):
    """ Lista de importaciones llegadas """

    imp = importaciones_llegadas_odbc()[['DOC_ID_CORP', 'ENTRADA_FECHA', 'WARE_COD_CORP', 'product_id']]
    imp = imp.drop_duplicates(subset=['DOC_ID_CORP'])
    
    pro = productos_odbc_and_django()[['product_id', 'marca2']]  

    imp = imp.merge(pro, on='product_id', how='left')
    imp = imp.sort_values(by=['ENTRADA_FECHA'], ascending=[False])
    
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


# Detalle de importación
# url: importacion/<str:o_compra>
def wms_detalle_imp(request, o_compra):
    """ Ver detalle de importaciones
        Seleccionar bodega 
        Guardar datos en la tabla "inventario_ingreso_bodega"
        Una vez ingresada la importación desaparece de la lista de importaciones por llegar
        y aparece en la lista de importaciones ingresadas
    """
    
    detalle = importaciones_llegadas_ocompra_odbc(o_compra) 
    pro     = productos_odbc_and_django()[['product_id', 'Nombre', 'marca','marca2']]
    detalle = detalle.merge(pro, on='product_id', how='left')

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
def wms_bodega_imp(request, o_compra):
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
def wms_inventario_inicial_list_bodega(request):
    
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
def wms_inventario_inicial_bodega(request, bodega):
    

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



"""
    FUNCIONES DE MOVIMIENTO
    - INGRESOS
"""

# FUNCIÓN MOVIMIENTO
# INGRESOS DE INVENTARIO INICIAL & IMPORTACIONES
# url: wms/ingreso/<int:int>
def wms_movimientos_ingreso(request, id):
# def wms_movimientos_ingreso(request):
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
            #form = MovimientosForm(request.POST)
            if form.is_valid():
                form.save()
                # regresar a la lista de productos en importacion
                url_redirect
                #return redirect(f'/wms/importacion/bodega/{item.n_referencia}')
                #return redirect(f'/wms/importacion/bodega/{url_redirect}')
                return redirect(url_redirect)
            
        elif und > ingresados_ubicaciones or und > ubicaciones_und:
            # No se puede ingresar un cantidad mayor a la existente
            messages.error(request, 'No se puede ingresar una cantidad mayor a la exitente !!!')
            return redirect(f'/wms/ingreso/{item.id}')
        

        elif und < ingresados_ubicaciones :
            # guardar
            #form = MovimientosForm(request.POST)
            if form.is_valid():
                form.save()
                # retornar a la misma view
                return redirect(f'/wms/ingreso/{item.id}')

        elif ubicaciones_und == total_ingresado :
            # guardar
            #form = MovimientosForm(request.POST)
            if form.is_valid():
                form.save()
                # retornar a la misma view
                #return redirect(f'/wms/importacion/bodega/{item.n_referencia}')
                #return redirect(f'/wms/importacion/bodega/{url_redirect}')
                return redirect(url_redirect)


    context = {
        'form'             :form,
        'item'             :item,
        'ubi_list'         :ubi_list,
        'mov_list'         :mov_list,
        'total_ubicaciones':total_ubicaciones
    }

    return render(request, 'wms/detalle_ubicaciones.html', context)







# RECIBE EL TIPO (INGRESO-EGRESO) Y CREA EL REGISTRO
def movimiento(tipo, mov_dic):
    
    if tipo == 'Ingreso':
        und = int(mov_dic['unidades'][0])
    elif tipo == 'Egreso':
        und = int(mov_dic['unidades'][0]) * -1
    #ubicación
    mov = Movimiento(
        tipo            = tipo,     
        unidades        = und,                      
        descripcion     = mov_dic['descripcion'][0],
        n_referencia    = mov_dic['n_referencia'][0],
        referencia      = mov_dic['referencia'][0],
        usuario_id      = int(mov_dic['usuario'][0]),
        ubicacion_id    = int(mov_dic['ubicacion'][0]),
        fecha_caducidad = mov_dic['fecha_caducidad'][0],
        lote_id         = mov_dic['lote_id'][0],
        product_id      = mov_dic['product_id'][0],        
    )
    
    mov.save()
    if mov.id:
        return HttpResponse(mov.id)


def wms_ubicaciones_list_ingreso(request):
    data = dict(request.POST)
    
    movs = (
        Movimiento.objects
        .filter(referencia=data['referencia'][0])
        .filter(n_referencia=data['n_referencia'][0])
        .filter(product_id=data['producto'][0])
        .filter(lote_id=data['lote'][0])
    ).values()
    
    movs = pd.DataFrame(movs).to_html()
    
    return HttpResponse(movs)


def wms_ing(request):
    print(request.POST, type(request.POST))
    #data = dict(request.POST)
    
    # d = movimiento('Ingreso', data)
    # d.status_code
    
    # return HttpResponse(d.status_code)
    return 'OK'


def wms_prueba_ing(request):
    d = {
        'product_id':'60152',
        'lote_id':'A123',
        'fecha_caducidad':'2030-12-31',
        'descripcion':'',
        'referencia':'Inventario Inicial',
        'n_referencia':'inv_in_1',
        'ubicacion':1,
        'unidades':1000,
        'usuario':1,       
    }
    
    i = movimiento('Egreso', d)
    print(i.status_code)
    return i



#
# url: importaciones/ingresadas
def wms_imp_ingresadas(request):
    """ Lista de importaciones ingresadas """

    prod = productos_odbc_and_django()[['product_id','Marca']]
    imps = pd.DataFrame(InventarioIngresoBodega.objects.filter(referencia='Ingreso Importación').values())
    imps = imps.merge(prod, on='product_id', how='left')
    imps = imps.drop_duplicates(subset='n_referencia')
    imps = de_dataframe_a_template(imps)

    context = {
        'imp':imps
    }
    
    return render(request, 'wms/importaciones_ingresadas_list.html', context)










from datos.models import Product
def wms_movimientos_list(request):
    """ Lista de movimientos """

    mov = Movimiento.objects.all().order_by('-fecha_hora')

    context = {
        'mov':mov
    }

    return render(request, 'wms/movimientos_list.html', context)


def wms_inventario(request):
    """ Inventario 
        Suma de ingresos y egresos que dan el total de todo el inventario
    """
    prod = productos_odbc_and_django()[['product_id','Nombre','Marca']]
    prod = prod.rename(columns={'product_id':'item__product_id'})

    inv = Movimiento.objects.all().values(
        # 'id',
        'item__product_id',
        # 'item__nombre',
        # 'item__marca2',
        'item__lote_id',
        'item__fecha_caducidad',
        'ubicacion'        ,
        'ubicacion__bodega',
        'ubicacion__pasillo',
        'ubicacion__modulo',
        'ubicacion__nivel'
    ).annotate(total_unidades=Sum('unidades')).order_by(
        'item__product_id',
        # 'item__marca2',
        'item__fecha_caducidad',
        
        'ubicacion__bodega',
        'ubicacion__pasillo',
        'ubicacion__modulo',
        'ubicacion__nivel'
        ).exclude(total_unidades__lte=0)

    

    inv_df = pd.DataFrame(inv);print(inv_df)
    inv_df = inv_df.merge(prod, on='item__product_id', how='left')
    inv_df['item__fecha_caducidad'] = inv_df['item__fecha_caducidad'].astype(str)
    inv_df = de_dataframe_a_template(inv_df)

    context = {
        # 'inv':inv,
        'inv':inv_df
    }

    return render(request, 'wms/inventario.html', context)


#def wms_movimiento_interno(request , prod, lote, bod, pas, mod, niv):
def wms_movimiento_interno(request):
    """ Filtra los movimientos por producto, lote, bodega, pasillo, modulo, nivel
        *** Los productos que tiene '/' en el codigo va a dar error ***
        *** cambiar esta vista por ajax para pasar los datos por 'request' ***
    """
    req = dict(request.GET)
    print(req, type(req))
    # prod = request.GET.get('prod')
    # lote = request.GET.get('lote')
    # u    = request.GET['ubi']
    # u   = u.split('.')

    prod = req['product_id'][0]
    lote = req['lote_id'][0]
    u    = req['ubicacion'][0]
    u    = u.split('.')
    bod = u[0]
    pas = u[1]
    mod = u[2]
    niv = u[3]


    print(u, type(u))
    print(prod, lote)#, bod, pas, mod, niv)
    
    # mov = Movimiento.objects.get(id=id)
    mov_q = (Movimiento.objects
            .filter(Q(item__product_id=prod) & Q(item__lote_id=lote))
            .filter(ubicacion__bodega=bod)
            .filter(ubicacion__pasillo=pas)
            .filter(ubicacion__modulo=mod)
            .filter(ubicacion__nivel=niv)
        ) #.order_by('id').last()
    
    # Objeto
    mov = mov_q.order_by('id').last()
    und_existentes = mov_q.aggregate(total_unidades=Sum('unidades'))['total_unidades'] 

    item_id            = InventarioIngresoBodega.objects.get(id=mov.item.id) 
    ubicacion_saliente = Ubicacion.objects.get(id=mov.ubicacion.id) 
    ubicaciones        = Ubicacion.objects.exclude(id=ubicacion_saliente.id)

    # if request.method == 'POST':

    #     # Control
    #     und_post = int(request.POST['unidades'])
    #     ubi_post = int(request.POST['ubicacion'])
    #     user     = request.POST['usuario']
    #     user     = User.objects.get(username=user)
    #     und_egreso = und_post * (-1)
    #     ubicacion_ingresante = Ubicacion.objects.get(id=ubi_post) 

    #     if und_post > 0 and und_post <= und_existentes:
    #         # Crear registro de Egreso
    #         mov_egreso = Movimiento.objects.create(
    #             item = item_id,
    #             tipo = 'Egreso',
    #             descripcion = 'Movimiento Interno',
    #             ubicacion = ubicacion_saliente,
    #             unidades = und_egreso,
    #             usuario =  user
    #         )
    #         mov_egreso.save()

    #         # Crear registro de Inreso
    #         mov_ingreso = Movimiento.objects.create(
    #             item = item_id,
    #             tipo = 'Ingreso',
    #             descripcion = 'Movimiento Interno',
    #             ubicacion = ubicacion_ingresante,
    #             unidades = und_post ,
    #             usuario =  user
    #         )
    #         mov_ingreso.save()
            
    #         messages.success(request, 'Movimiento realizado con exito !!!')
    #         return redirect(f'/wms/inventario')
        
    #     elif und_post > und_existentes:
    #         messages.error(request, 'No se puede retirar una cantidad mayor a la exitente !!!')
    #         return redirect(f'/wms/inventario/mov-interno/{prod}/{lote}/{bod}/{pas}/{mod}/{niv}')

    #     else: 
    #         messages.error(request, 'Error en el movimiento !!!')
    #         return redirect(f'/wms/inventario/mov-interno/{prod}/{lote}/{bod}/{pas}/{mod}/{niv}')

    
    context = {
        'mov':mov,
        'ubi':ubicaciones,
        'und_existentes':und_existentes
    }

    return render(request, 'wms/movimiento_interno.html', context)



def wms_listado_pedidos(request):
    """ Listado de pedidos (picking) """

    pedidos = pd.DataFrame(reservas_table())
    pedidos['FECHA_PEDIDO'] = pedidos['FECHA_PEDIDO'].astype(str)
    pedidos = pedidos.drop_duplicates(subset='CONTRATO_ID')

    pedidos = de_dataframe_a_template(pedidos)

    context = {
        'reservas':pedidos
    }

    return render(request, 'wms/listado_pedidos.html', context)



def wms_egreso_picking(request, pedido):

    # n_picking = pedido
    
    m = Movimiento.objects.filter(referencia='Picking').filter(n_referencia=pedido)
    m = pd.DataFrame(m.values('id','item__product_id', 'item__lote_id', 'unidades'))
    m = m.rename(columns={'item__product_id':'PRODUCT_ID'})
    
    prod   = productos_odbc_and_django()[['product_id','Nombre','Marca']]
    prod   = prod.rename(columns={'product_id':'PRODUCT_ID'})
    
    pedido = pedido_por_cliente(pedido).sort_values('PRODUCT_ID')
    pedido = pedido.merge(prod, on='PRODUCT_ID',how='left')
    
    r_lote = reservas_lote()
    r_lote = r_lote.pivot_table(index=['PRODUCT_ID', 'LOTE_ID'], values=['EGRESO_TEMP'], aggfunc='sum').reset_index()
    r_lote = r_lote.rename(columns={'PRODUCT_ID':'item__product_id', 'LOTE_ID':'item__lote_id','EGRESO_TEMP':'egreso_temp'}).fillna(0)
    
    n_ped = pedido['CONTRATO_ID'].iloc[0]
    cli = pedido['NOMBRE_CLIENTE'].iloc[0]
    fecha = pedido['FECHA_PEDIDO'].iloc[0]
    hora = pedido['HORA_LLEGADA'].iloc[0]

    prod_list = list(pedido['PRODUCT_ID'])

    inv = (Movimiento.objects.filter(item__product_id__in=prod_list).values(
        # 'id',
        'item__product_id',
        # 'item__nombre',
        # 'item__marca2',
        'item__lote_id',
        'item__fecha_caducidad',
        
        'ubicacion__bodega',
        'ubicacion__pasillo',
        'ubicacion__modulo',
        'ubicacion__nivel'
    )
    .annotate(total_unidades=Sum('unidades'))
    .order_by(
        'item__fecha_caducidad',

        'ubicacion__bodega',
        'ubicacion__pasillo',
        'ubicacion__modulo',
        'ubicacion__nivel'
    ).exclude(total_unidades__lte=0))

    inv = pd.DataFrame(inv)
    inv = inv.merge(r_lote, on=['item__product_id','item__lote_id'], how='left').fillna(0)
    inv['disponible'] = inv['total_unidades'] - inv['egreso_temp']  #;print(inv)
    inv['item__fecha_caducidad'] = inv['item__fecha_caducidad'].astype(str)
    inv = inv[inv['disponible']>0]
    inv = de_dataframe_a_template(inv)
    
    if not m.empty:
        pedido = pedido.merge(m, on='PRODUCT_ID', how='left').fillna(0)
        pedido['unidades'] = pedido['unidades'].abs()

    ped = de_dataframe_a_template(pedido)
    for i in prod_list:
        for j in ped:
            if j['PRODUCT_ID'] == i:
                j['ubi'] = ubi_list = []
                for k in inv:
                    if k['item__product_id'] == i:
                        ubi_list.append(k)
    
    # Ordenar el pedido por ubicación
    ped = sorted(ped, key=lambda x: len(x['ubi']), reverse=True)

    context = {
        'pedido':ped,

        'n_ped':n_ped,
        'cli':cli,
        'fecha': fecha ,
        'hora':hora 
    }

    return render(request, 'wms/picking.html', context)


def wms_movimiento_egreso_picking(request):

    # Item
    prod_id = request.POST['prod_id']
    lote_id = request.POST['lote_id']

    # get last of inventario
    item_inventario = InventarioIngresoBodega.objects.filter(product_id=prod_id).filter(lote_id=lote_id)
    item_inventario = item_inventario.last()

    # Unidades que salen
    unds = int(request.POST['unds'])
    unds = unds * -1

    # Referencia picking
    picking = request.POST['n_picking']
    
    # Ubicación
    ubi_split = (request.POST['ubi']).split('.') 
    ubi = Ubicacion.objects.filter(bodega=ubi_split[0]).filter(pasillo=ubi_split[1]).filter(modulo=ubi_split[2]).filter(nivel=ubi_split[3])
    ubi = ubi.first()

    # Usuario
    user = request.user.username
    user = User.objects.get(username=user)

    #egreso = 
    Movimiento.objects.create(
        item         = item_inventario,
        tipo         = 'Egreso',
        descripcion  = 'Egreso Picking',
        referencia   = 'Picking',
        n_referencia = picking,
        ubicacion    = ubi,
        unidades     = unds,
        usuario      = user
    )

    return HttpResponse('ok')
    


def wms_eliminar_movimiento(request):

    mov_id = request.POST['mov']
    mov_id = mov_id[:-2]
    mov_id = int(mov_id)

    mov = Movimiento.objects.get(id=mov_id)
    mov.delete()

    return HttpResponse('ok')