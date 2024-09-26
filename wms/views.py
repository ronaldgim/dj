from django.shortcuts import render, redirect

# Datos de importaciones
from datos.views import (
    importaciones_llegadas_odbc,
    importaciones_en_transito_odbc,
    importaciones_en_transito_detalle_odbc,
    productos_odbc_and_django,
    de_dataframe_a_template,
    importaciones_llegadas_ocompra_odbc,
    wms_reservas_lotes_datos,
    wms_reservas_lote_consulta,

    # DATOS
    wms_detalle_factura,
    clientes_warehouse,
    wms_reserva_por_contratoid,
    quitar_puntos,
    wms_stock_lote_cerezos_by_product,
    wms_stock_lote_products,
    wms_datos_nota_entrega,
    importaciones_en_transito_odbc_insert_warehouse,

    # Trasnferencia
    doc_transferencia_odbc,
    
    # Ajuste Datos
    wms_ajuste_query_odbc,
    
    # Permisos costum @decorador
    permisos,
    
    # Fecuencia de ventas
    frecuancia_ventas
    )

# Pedidos por clientes
from etiquetado.views import pedido_por_cliente, reservas_table

# Http
from django.http import HttpResponse,JsonResponse, HttpResponseRedirect

# Json
import json

# Pyodbc
import pyodbc 

# Datetime
from datetime import datetime

# DB
from django.db import connections

# Models
from django.db.models import Sum, Count
from wms.models import (
    InventarioIngresoBodega, 
    Ubicacion, Movimiento, 
    Existencias, 
    Transferencia, 
    LiberacionCuarentena,
    NotaEntrega,
    AnulacionPicking,
    TransferenciaStatus,
    AjusteLiberacion,
    NotaEntregaStatus,
    DespachoCarton
    )

from django.core.exceptions import ObjectDoesNotExist

# excel 
from openpyxl.styles import Font, Alignment


# Pandas y Numpy
import pandas as pd
import numpy as np

# Forms
from wms.forms import MovimientosForm, DespachoCartonForm

# Messages
from django.contrib import messages

# Query's
from django.db.models import Q

# Models
from users.models import User, UserPerfil
from etiquetado.models import EstadoPicking

# Transactions INTEGRITY OF DATA
from django.db import transaction

# Login
from django.contrib.auth.decorators import login_required, permission_required

# Email
from django.core.mail import send_mail
from django.conf import settings


# Pyodbc
import pyodbc

# Paginado
from django.core.paginator import Paginator


"""
    LISTAS DE INGRESOS
    - LISTA DE IMPORTACIONES
    - LISTA DE BODEGA DE INVENTARIO INICIAL
"""

"""
# def kpi_tiempo():
    
#     list_picking = Movimiento.objects.filter(referencia='Picking').values_list('n_referencia', flat=True).distinct()
    
#     picking_len_0_a_5   = []
#     picking_len_5_a_10  = []
#     picking_len_10_a_20 = []
#     picking_len_mas_20  = []
    
#     for i in list_picking:
#         mov = Movimiento.objects.filter(n_referencia=i).order_by('fecha_hora')
#         n_items = len(mov)
#         mov_first = mov.first()
#         mov_last  = mov.last()
        
#         tiempo =  (mov_last.fecha_hora-mov_first.fecha_hora)
#         print(i, n_items, tiempo)
        
#         if n_items <= 5:
#             picking_len_0_a_5.append(tiempo)
#         elif 5 < n_items <= 10:
#             picking_len_5_a_10.append(tiempo)
#         elif 10 < n_items <= 20:
#             picking_len_10_a_20.append(tiempo)
#         elif n_items > 20:
#             picking_len_mas_20.append(tiempo)
    
#     # from datetime import timedelta
#     # sum_0_a_5 = sum(picking_len_0_a_5, timedelta(0))
#     # mean_0_a_5 = sum_0_a_5/len(picking_len_0_a_5)
#     # print(sum_0_a_5, mean_0_a_5)

#     print('Tiempo promedio picking de 0 a 5 items: ', sum(picking_len_0_a_5, timedelta(0)))
#     print('Tiempo promedio picking de 5 a 10 items: ', sum(picking_len_5_a_10, timedelta(0)))
#     print('Tiempo promedio picking de 10 a 20 items: ', sum(picking_len_10_a_20, timedelta(0)))
#     print('Tiempo promedio picking de mas de 20items: ', sum(picking_len_mas_20, timedelta(0)))
    
#     # suma_total = sum(lista_timedelta, timedelta(0))
#     # promedio = suma_total / len(lista_timedelta)
#     return 


# def kpi_cliclo_pedido():
    
#     # DataFrame Tiempo de picking
#     picking = pd.DataFrame(Movimiento.objects.filter(referencia='Picking').values())
    
#     t_picking_picking = []
#     t_picking_items = []
#     t_picking_tiempo = []
    
#     for i in picking['n_referencia'].unique():
#         picking_i = picking[picking['n_referencia' ]==i]
#         picking_i = picking_i.sort_values(by='fecha_hora')
        
#         len_picking = len(picking_i)
        
#         if len_picking > 1:
#             primero = picking_i['fecha_hora'].iloc[0]
#             ultimo = picking_i['fecha_hora'].iloc[-1]    
#             tiempo = ultimo - primero
#             tiempo = tiempo.total_seconds()
#         elif len_picking == 1:
#             tiempo = pd.Timedelta(seconds=0).total_seconds()
#             #tiempo = pd.Timedelta(days=0)
        
#         t_picking_picking.append(i)
#         t_picking_items.append(len_picking)
#         t_picking_tiempo.append(tiempo)
        
#     df_tiempo_picking = pd.DataFrame({
#         't_picking_picking':t_picking_picking,
#         't_picking_items':t_picking_items,
#         't_picking_tiempo':t_picking_tiempo
#         })
#     df_tiempo_picking.to_excel('df_tiempo_picking.xlsx')
#     #tiempo_promedio_picking = round((df_tiempo_picking['t_picking_tiempo'].dt.seconds).mean() / 3600, 1)
#     print(df_tiempo_picking)
    
#     # # DataFrame Tiempo Facturado - Despachado    
#     mov_facturas_list = Movimiento.objects.filter(referencia='Picking').filter(estado_picking='Despachado').exclude(n_factura='').values_list('n_factura', flat=True)
    
    ###### CREAR UNA NUEVA QUERY CON LA TABLA CORRECTA ######
#     facturas = ventas_facturas_odbc()[['CODIGO_FACTURA','FECHA','HORA_FACTURA']]
#     facturas = facturas[facturas.CODIGO_FACTURA.isin(mov_facturas_list)].drop_duplicates(subset='CODIGO_FACTURA')
#     facturas = facturas.rename(columns={'CODIGO_FACTURA':'n_factura'})
#     facturas['fecha_hora_factura'] = pd.to_datetime(facturas['FECHA'] + ' ' + facturas['HORA_FACTURA']);print(facturas)
    
#     movimientos = pd.DataFrame(Movimiento.objects.filter(referencia='Picking').filter(estado_picking='Despachado').exclude(n_factura='').values(
#         'n_referencia','n_factura','fecha_hora','actualizado')).sort_values(by='fecha_hora')
#     movimientos = movimientos[movimientos.n_factura.isin(mov_facturas_list)].drop_duplicates(subset='n_factura', keep='last')
    
#     df_tiempo_facturado_despacho = facturas.merge(movimientos, on="n_factura", how="left")
#     df_tiempo_facturado_despacho['tiempo_pickingfinalizado_facturado'] = (df_tiempo_facturado_despacho['fecha_hora_factura'] - df_tiempo_facturado_despacho['fecha_hora']).dt.seconds
#     df_tiempo_facturado_despacho['tiempo_facturado_despachado'] = (df_tiempo_facturado_despacho['fecha_hora_factura'] - df_tiempo_facturado_despacho['actualizado']).dt.seconds
    
#     tiempo_pickingfinalizado_facturado = round(df_tiempo_facturado_despacho['tiempo_pickingfinalizado_facturado'].mean() / 3600, 1)
#     #tiempo_facturado_despachado = round(df_tiempo_facturado_despacho['tiempo_facturado_despachado'].mean() / 3600, 1)
#     #print(tiempo_pickingfinalizado_facturado)
    



# def kpi_ciclo_pedido():
    
#     # 1 PICKING (desde inicio hasta fin de picking)
#     t_picking = pd.DataFrame(Movimiento.objects
#         .filter(referencia='Picking')
#         .filter(estado_picking='Despachado')
#         .values('referencia','n_referencia','fecha_hora','actualizado','n_factura')
#     ).sort_values(by='fecha_hora').reset_index()
    
#     t_picking_list = []
#     for i in t_picking['n_referencia'].unique():
#         t_picking_i = t_picking[t_picking['n_referencia']==i]
#         n_items = len(t_picking_i)
#         inicio = t_picking_i.iloc[0]['fecha_hora']
#         final  = t_picking_i.iloc[-1]['fecha_hora']
#         despachado = t_picking_i.iloc[-1]['actualizado']
#         factura =  t_picking_i.iloc[0]['n_factura']
        
#         row = (i, n_items, inicio, final, despachado, factura)
#         t_picking_list.append(row)
    
#     df_t_picking = pd.DataFrame(t_picking_list, columns=['CONTRATO_ID','N_ITEMS','INICIO_PICKING','FIN_PICKING','DESPACHADO','CODIGO_FACTURA'])
#     df_t_picking['TIEMPO_PICKING'] = df_t_picking['FIN_PICKING'] - df_t_picking['INICIO_PICKING']
#     df_t_picking['TIEMPO_PICKING_s'] = df_t_picking['TIEMPO_PICKING'].dt.total_seconds()
#     # df_t_picking['INICIO_PICKING'] = df_t_picking['INICIO_PICKING'].astype('str')
#     # df_t_picking['FIN_PICKING'] = df_t_picking['FIN_PICKING'].astype('str')
#     # df_t_picking['TIEMPO_PICKING'] = df_t_picking['TIEMPO_PICKING'].astype('str')
#     # df_t_picking['DESPACHADO'] = df_t_picking['DESPACHADO'].astype('str')
    
#     # df_t_picking.to_excel('df_t_picking.xlsx')
#     # print(df_t_picking)


#     # 2 FACTURADO (desde fin de picking hasta facturado)
#     facturas_wms_list = Movimiento.objects.exclude(n_factura='').values_list('n_factura', flat=True)
#     facturas = ventas_facturas_odbc()[['CODIGO_CLIENTE', 'CODIGO_FACTURA', 'FECHA', 'HORA_FACTURA']]
#     facturas = facturas[facturas.CODIGO_FACTURA.isin(facturas_wms_list)].drop_duplicates(subset='CODIGO_FACTURA')
#     facturas['FACTURADO'] = pd.to_datetime(facturas['FECHA'] + ' ' + facturas['HORA_FACTURA']) 
#     facturas = facturas[['CODIGO_CLIENTE','CODIGO_FACTURA','FACTURADO']]
#     facturas = facturas.merge(df_t_picking[['CODIGO_FACTURA','FIN_PICKING','DESPACHADO']], on='CODIGO_FACTURA', how='left')
#     facturas['TIEMPO_FACTURADO'] = facturas['FACTURADO'] - facturas['FIN_PICKING']
#     facturas['TIEMPO_FACTURADO_s'] = facturas['TIEMPO_FACTURADO'].dt.total_seconds()
#     facturas = facturas[facturas['TIEMPO_FACTURADO_s']>0]

#     # 3 PEDIDOS (desde que recibe el pedido hasta que inicia el picking)
#     p_cerrados = pedidos_cerrados_bct()[['CONTRATO_ID','FECHA_PEDIDO','HORA_LLEGADA']].drop_duplicates(subset='CONTRATO_ID')
#     p_cerrados['FECHA_PEDIDO'] = p_cerrados['FECHA_PEDIDO'].astype('str')
#     p_cerrados['HORA_LLEGADA'] = p_cerrados['HORA_LLEGADA'].astype('str')
#     p_cerrados['CONTRATO_ID'] = p_cerrados['CONTRATO_ID'].astype('str')
#     p_cerrados['PEDIDO'] = pd.to_datetime(p_cerrados['FECHA_PEDIDO'] + ' ' + p_cerrados['HORA_LLEGADA'])
#     p_cerrados = p_cerrados.merge(df_t_picking[['CONTRATO_ID','INICIO_PICKING']], on='CONTRATO_ID', how='right')
#     p_cerrados['TIEMPO_PEDIDO'] = p_cerrados['INICIO_PICKING'] - p_cerrados['PEDIDO']
#     p_cerrados['TIEMPO_PEDIDO_s'] = p_cerrados['TIEMPO_PEDIDO'].dt.total_seconds()
#     p_cerrados = p_cerrados[p_cerrados['TIEMPO_PEDIDO_s']>0]
    
    
#     # PROMEDIOS PARA GRAFICO
#     # 1 PICKING
#     tiempo_promedio_picking = round(df_t_picking['TIEMPO_PICKING_s'].mean() / 3600, 1)
#     # 2 FACTURADO
#     tiempo_promedio_facturado = round(facturas['TIEMPO_FACTURADO_s'].mean() / 3600, 1 )
#     # 3 PEDIDOS
#     tiempo_promedio_pedido = round(p_cerrados['TIEMPO_PEDIDO_s'].mean() / 3600, 1)
    
#     t_ciclo = {
#         'labels':['T.P.Pedido (h)','T.P.Picking (h)','T.P.Facturado (h)'],
#         'data': [tiempo_promedio_pedido, tiempo_promedio_picking, tiempo_promedio_facturado],
#         't_p_pedido':tiempo_promedio_pedido,
#         't_p_picking':tiempo_promedio_picking,
#         't_p_facturado':tiempo_promedio_facturado,
#         't_p_total':sum([tiempo_promedio_pedido,tiempo_promedio_picking,tiempo_promedio_facturado])
#     }

#     return t_ciclo

"""


def capacidad_de_bodegas_df():
    
    # DATA
    ubicaciones = pd.DataFrame(Ubicacion.objects.all().values()).rename(columns={'id':'ubicacion_id'})
    existencias = pd.DataFrame(Existencias.objects.all().values())
    productos   = productos_odbc_and_django()[['product_id', 'Unidad_Empaque','Volumen']]
    
    # CALCULOS EXISTENCIAS
    existencias = existencias.merge(productos, on='product_id', how='left')
    existencias['cartones'] = existencias['unidades'] / existencias['Unidad_Empaque']
    existencias['ocupacion_posicion_m3'] = existencias['cartones'] * (existencias['Volumen'] / 1000000)
    existencias = existencias.groupby(by=['ubicacion_id']).sum().reset_index()    
    
    # MERGE CALCULO CON UBICACIÓN
    capacidad = ubicaciones.merge(existencias, on='ubicacion_id', how='left').fillna(0)
    capacidad = capacidad.rename(columns={'capacidad_m3':'capacidad_posicion_m3'})
    
    # SORT LIST BY UBICAION
    capacidad = capacidad.sort_values(by=['bodega','pasillo','modulo','nivel'])[[
        'ubicacion_id','bodega','pasillo','modulo','nivel','distancia_puerta','disponible','capacidad_posicion_m3','ocupacion_posicion_m3'
    ]]
    
    # CAPACIDAD TOMANDO EN CUENTA UBICACIONES DISPONIBLES
    capacidad['ocupacion_posicion_m3'] = capacidad.apply(lambda x: x['capacidad_posicion_m3'] if x['disponible']==False else x['ocupacion_posicion_m3'], axis=1)
    
    # DISPONIBLE m3
    capacidad['disponible_posicion_m3'] = capacidad['capacidad_posicion_m3'] - capacidad['ocupacion_posicion_m3']
    
    # % OCUPACIÓN
    capacidad['ocupacion_porcentaje'] = (capacidad['ocupacion_posicion_m3'] / capacidad['capacidad_posicion_m3']) * 100
    
    return capacidad


def en_despacho_df():
    
    mov_en_despacho = Movimiento.objects.filter(estado_picking='En Despacho')
    picking_list = mov_en_despacho.values_list('n_referencia', flat=True)

    en_despacho = pd.DataFrame(mov_en_despacho.values())
    pickings    = pd.DataFrame(EstadoPicking.objects.filter(n_pedido__in=picking_list).values())[[
        'n_pedido','tipo_cliente','cliente'
        ]]
    pickings = pickings.rename(columns={'n_pedido':'n_referencia'})
    
    if not en_despacho.empty:
        en_despacho = en_despacho[['product_id','n_referencia','unidades','ubicacion_id']]
        en_despacho['unidades'] = en_despacho['unidades'] * -1
        
        # Merge products
        productos   = productos_odbc_and_django()[['product_id','Unidad_Empaque','Volumen']]
        en_despacho = en_despacho.merge(productos, on='product_id',how='left')
        en_despacho = en_despacho.merge(pickings, on='n_referencia', how='left')
        
        # Calculo
        en_despacho['cartones'] = en_despacho['unidades'] / en_despacho['Unidad_Empaque']
        en_despacho['ocupacion_m3']  = en_despacho['cartones'] * (en_despacho['Volumen'] / 1000000)
        
        en_despacho = en_despacho.groupby(by='tipo_cliente').sum().reset_index()

        return en_despacho
    
    else:
        return None
    

def kpi_capacidad():
    
    capacidad = capacidad_de_bodegas_df()
    
    # QUITAR UBICACIÓN 607 - JAULA
    capacidad = capacidad[capacidad['ubicacion_id']!=607]
    
    # SI DISPONIBLE FALSO 
    
    # AGRUPAR POR BODEGA
    capacidad = capacidad.groupby(by='bodega').sum().reset_index()[[
        'bodega','capacidad_posicion_m3','ocupacion_posicion_m3','disponible_posicion_m3'
        ]]
    # capacidad['ocupacion_posicion_m3_dif'] = capacidad['ocupacion_posicion_m3'] * 0.025
    
    # PORCENTAJE DE OCUPACIÓN
    capacidad['porcentaje_ocupacion'] = round((capacidad['ocupacion_posicion_m3'] / capacidad['capacidad_posicion_m3'])*100, 1)
    
    # CALCULO DE PRODUCTOS EN DESPACHO
    en_despacho = en_despacho_df()[['tipo_cliente','ocupacion_m3']]
    en_despacho = en_despacho[en_despacho['tipo_cliente']=='HOSPU']
    
    if not en_despacho.empty:
        en_despacho['bodega'] = 'CN7'
        capacidad = capacidad.merge(en_despacho, on='bodega', how='left').fillna(0)
        capacidad['ocupacion_posicion_m3'] = capacidad['ocupacion_posicion_m3'] + capacidad['ocupacion_m3']
        capacidad['disponible_posicion_m3'] = capacidad['capacidad_posicion_m3'] - capacidad['ocupacion_posicion_m3']
        capacidad['porcentaje_ocupacion'] = round((capacidad['ocupacion_posicion_m3'] / capacidad['capacidad_posicion_m3'])*100, 0)
    
        return capacidad

    else:
        return capacidad


def capacidad_data_grafico():
    
    data = kpi_capacidad()[['bodega','capacidad_posicion_m3','ocupacion_posicion_m3','ocupacion_m3']]
    data = data.rename(columns={
        'capacidad_posicion_m3':'capacidad_total',
        'ocupacion_posicion_m3':'ocupacion_alamacenamiento',
        'ocupacion_m3':'ocupacion_despacho'
        })
    data['ocupacion_alamacenamiento'] = data['ocupacion_alamacenamiento'] - data['ocupacion_despacho']
    
    # Porcentajes
    data['porcentaje_ocupacion'] = round((data['ocupacion_alamacenamiento'] / data['capacidad_total'])*100, 0)
    data['porcentaje_despacho']  = round((data['ocupacion_despacho'] / data['capacidad_total'])*100, 0)
    data['porcentaje_disponible'] = 100 - data['porcentaje_ocupacion'] 
    
    bodegas    = list(data['bodega'])
    ocupacion  = list(data['porcentaje_ocupacion'])
    despacho   = list(data['porcentaje_despacho'])
    disponible = list(data['porcentaje_disponible'])

    d = {
        'bodega': bodegas,
        'ocupacion': ocupacion,
        'despacho': despacho,
        'disponible': disponible
    }
    
    return  d


def kpi_tiempo_de_almacenamiento():
    
    prod = productos_odbc_and_django()[['product_id','Nombre','Marca']]
    
    existencias = pd.DataFrame(Existencias.objects.all().values(
        'product_id',
        'lote_id',
        'unidades',
        'ubicacion__bodega','ubicacion__pasillo','ubicacion__modulo','ubicacion__nivel'
        ))
    movimientos = pd.DataFrame(Movimiento.objects.values(
        'product_id',
        'lote_id',
        #'ubicacion__bodega',
        #'ubicacion__pasillo',
        'fecha_hora'
        )).sort_values(by='fecha_hora')
    movimientos = movimientos.drop_duplicates(subset=['product_id','lote_id'], keep='first')
    
    df = existencias.merge(movimientos, on=['product_id','lote_id'], how='left')
    
    hoy = datetime.now()
    df['hoy'] = hoy
    df['tiempo'] =  (df['hoy'] - df['fecha_hora']) #/timedelta(days=1)
    df['tiempo_dias'] =  (df['hoy'] - df['fecha_hora']).dt.days #/timedelta(days=1)
    
    df = df.sort_values(
        by=['tiempo_dias','product_id','ubicacion__bodega','ubicacion__pasillo','ubicacion__modulo','ubicacion__nivel'], 
        ascending=[False,True,True,True,True,True])
    df = df.merge(prod, on='product_id', how='left')
    
    df = de_dataframe_a_template(df)
    return df


# UBICACIONES DISPONIBLES BODEGA 6
def wms_ubicaciones_disponibles_cn6():
    
    ubicaciones_existencias = Existencias.objects.filter(ubicacion__bodega='CN6').values_list('ubicacion_id', flat=True)
    ubicaciones = Ubicacion.objects.filter(disponible=True).filter(bodega='CN6').values_list('id', flat=True)
    
    ubicaciones_existencias = set(ubicaciones_existencias)
    ubicaciones = set(ubicaciones)
    ubicaciones_disponibles = ubicaciones.difference(ubicaciones_existencias)
    
    ubi_list = Ubicacion.objects.filter(id__in=ubicaciones_disponibles)
    
    return sorted(ubi_list, key=lambda x: (x.pasillo, x.columna))


def wms_ubicaciones_disponibles_rows():
    
    # Obtener las ubicaciones ocupadas y disponibles
    ubicaciones_existencias = Existencias.objects.filter(
        Q(ubicacion__bodega='CN6') & Q(ubicacion__disponible=True)
    ).values_list('ubicacion_id', flat=True).distinct()

    # Crear un DataFrame para las ubicaciones ocupadas
    ubicaciones_existencias_df = pd.DataFrame(Ubicacion.objects.filter(id__in=ubicaciones_existencias).values('id'))
    ubicaciones_existencias_df['ocupada'] = 'si'
    
    # Crear un DataFrame para todas las ubicaciones disponibles en la bodega CN6
    ubicaciones_totales_df = pd.DataFrame(Ubicacion.objects.filter(
        Q(bodega='CN6') & Q(disponible=True)).values())
    
    # Unir los DataFrames para indicar si cada ubicación está ocupada o no
    ubicaciones_df = ubicaciones_totales_df.merge(ubicaciones_existencias_df, on='id', how='left').fillna('no')
    
    # Agrupar por pasillo y nivel para contar las ubicaciones disponibles (ocupada == 'no')
    ubicaciones_resumen = ubicaciones_df[ubicaciones_df['ocupada'] == 'no'].groupby(['pasillo', 'nivel']).size().unstack(fill_value=0)
    
    # Asegurarnos de que tenemos columnas para cada nivel (1, 2, 3, 4)
    niveles = ['1', '2', '3', '4']
    ubicaciones_resumen = ubicaciones_resumen.reindex(columns=niveles, fill_value=0)
    
    # Calcular totales por pasillo y nivel
    ubicaciones_resumen['TOTAL'] = ubicaciones_resumen.sum(axis=1)
    ubicaciones_resumen.loc['TOTAL'] = ubicaciones_resumen.sum()

    # Convertir los resultados a una tabla HTML
    ubicaciones_resumen = ubicaciones_resumen.reset_index().T.reset_index()
    
    ubi_list = ubicaciones_resumen.to_html(
        float_format='{:,.0f}'.format,
        classes='table table-responsive table-bordered m-0 p-0', 
        na_rep='0',
        table_id='ubicaciones_rows',
        index=False,
        justify='end',
    )
    
    return ubi_list


# WMS HOME
@login_required(login_url='login')
def wms_home(request):
    
    tiempo_de_almacenamiento = kpi_tiempo_de_almacenamiento()
    capacidad_tabla = de_dataframe_a_template(kpi_capacidad()) 
    data_grafico = capacidad_data_grafico()
    
    context = {
        # DATA GRAFICO
        'bodegas': data_grafico['bodega'],
        'ocupacion': data_grafico['ocupacion'],
        'despacho': data_grafico['despacho'],
        'disponible': data_grafico['disponible'],
        
        # DATA TABLAS
        'capacidad':capacidad_tabla,
        'tiempo_de_almacenamiento':tiempo_de_almacenamiento,
        
        # DATA MODALES
        'ubicaciones_disponibles':wms_ubicaciones_disponibles_cn6(),
        'len_ubicaciones_disponibles':len(wms_ubicaciones_disponibles_cn6()),
        'ubicaciones_disponibles_row':wms_ubicaciones_disponibles_rows()
    }
    
    return render(request, 'wms/home.html', context)


# Lista de importaciones por llegar
# url: importaciones/list
@login_required(login_url='login')
@permisos(['ADMINISTRADOR','OPERACIONES'], '/wms/home', 'Importaciones llegadas')
def wms_importaciones_list(request): #OK
    """ Lista de importaciones llegadas """

    imp = importaciones_llegadas_odbc()
    imp = imp[imp['WARE_COD_CORP']=='CUC']
    imp['ENTRADA_FECHA'] = pd.to_datetime(imp['ENTRADA_FECHA'])
    imp = imp[imp['ENTRADA_FECHA']>datetime(year=2023, month=12, day=31)]
    imp['ENTRADA_FECHA'] = imp['ENTRADA_FECHA'].astype('str')
    imp = imp.sort_values(by=['ENTRADA_FECHA'], ascending=[False])
    
    pro = productos_odbc_and_django()[['product_id', 'Marca']]
    imp = imp.merge(pro, on='product_id', how='left')
    imp = imp.sort_values(by=['ENTRADA_FECHA'], ascending=[False])
    imp = imp.rename(columns={
        'LOTE_ID':'lote_id',
        'OH':'unidades_ingresadas',
        })
    # print(imp)
    imp_wms = pd.DataFrame(InventarioIngresoBodega.objects.filter(referencia='Ingreso Importación').values(
        'product_id','lote_id','unidades_ingresadas','n_referencia'
    ))
    
    imp_wms = imp_wms.rename(columns={'n_referencia':'DOC_ID_CORP'})
    imp_wms['ingresado'] = 'si'
    
    imp = imp.merge(imp_wms, on=['product_id','lote_id','unidades_ingresadas','DOC_ID_CORP'], how='left').fillna('no')
    
    imp = imp[imp['ingresado']=='no']
    imp = imp.drop_duplicates(subset=['DOC_ID_CORP'])
    imp = de_dataframe_a_template(imp)

    context = {
        'imp':imp
    }

    return render(request, 'wms/importaciones_list.html', context)


# Lista de importaciones ingresadas
# url: importaciones/ingresadas
@login_required(login_url='login')
@permisos(['ADMINISTRADOR','OPERACIONES'], '/wms/home', 'Importaciones ingresadas')
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
@permisos(['ADMINISTRADOR','OPERACIONES'], '/wms/home', 'Detalle de importación')
def wms_detalle_imp(request, o_compra): #OK
    """ Ver detalle de importaciones
        Seleccionar bodega
        Guardar datos en la tabla "inventario_ingreso_bodega"
        Una vez ingresada la importación desaparece de la lista de importaciones por llegar
        y aparece en la lista de importaciones ingresadas
    """

    imp = importaciones_llegadas_ocompra_odbc(o_compra)
    pro = productos_odbc_and_django()[['product_id', 'Nombre', 'marca','marca2']]
    imp = imp.merge(pro, on='product_id', how='left')
    imp = imp.sort_values(by='marca2', ascending=True)
    
    marca = imp['marca2'].iloc[0]
    orden = imp['DOC_ID_CORP'].iloc[0]
    
    imp_wms = pd.DataFrame(InventarioIngresoBodega.objects
        .filter(referencia='Ingreso Importación')
        .filter(n_referencia=o_compra)
        .values('product_id','lote_id','unidades_ingresadas','n_referencia')
        )
    
    imp_wms = imp_wms.rename(columns={
        'lote_id':'LOTE_ID',
        'unidades_ingresadas':'OH',
        'n_referencia':'DOC_ID_CORP'
        })
    
    imp_wms['ingresado'] = 'si'
    
    if not imp_wms.empty:
        imp = imp.merge(imp_wms, on=['product_id','LOTE_ID','OH','DOC_ID_CORP'], how='left').fillna('no')
        imp = imp[imp['ingresado']=='no']   
    
    imp_template = de_dataframe_a_template(imp)

    if request.method == 'POST':
        bodega = request.POST['bodega']
        d = imp
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
            
        InventarioIngresoBodega.objects.bulk_create(imp_ing)
        return redirect(f'/wms/importacion/bodega/{o_compra}')

    context = {
        'imp':imp_template,
        'marca':marca,
        'orden':orden,
    }

    return render(request, 'wms/detalle_importacion.html', context)



# Lista de importaciones en transito
@login_required(login_url='login')
@permisos(['ADMINISTRADOR','OPERACIONES','BODEGA'], '/wms/home', 'Importaciones en tránsito')
def wms_importaciones_transito_list(request):
    
    prod = productos_odbc_and_django()[['product_id','UnidadesPorPallet']]
    prod = prod.rename(columns={'product_id':'PRODUCT_ID'}) 
    
    imp_transito = importaciones_en_transito_odbc() 
    imp_transito['FECHA_ENTREGA'] = pd.to_datetime(imp_transito['FECHA_ENTREGA']).dt.strftime('%Y-%m-%d')
    imp_transito = imp_transito.sort_values(by='FECHA_ENTREGA', ascending=True)
    
    imps_contratos = []
    imps_total_pallets = []
    imps_incompleto = []
    for i in imp_transito['CONTRATO_ID'].unique():
        imp_contrato = imp_transito[imp_transito['CONTRATO_ID']==i]
        imp_contrato = imp_contrato.merge(prod, on='PRODUCT_ID',how='left')
        imp_contrato['pallets'] = imp_contrato['QUANTITY'] / imp_contrato['UnidadesPorPallet']
        imp_contrato = imp_contrato.replace(np.inf, 0)
        
        total_pallets = round(imp_contrato['pallets'].sum(), 2)
        incompleto = 0 in list(imp_contrato['pallets'])

        imps_contratos.append(i)
        imps_total_pallets.append(total_pallets)
        imps_incompleto.append(incompleto)
        
    imp_total_pallets = pd.DataFrame()
    imp_total_pallets['CONTRATO_ID'] = imps_contratos
    imp_total_pallets['total_pallets'] = imps_total_pallets
    imp_total_pallets['incompleto'] = imps_incompleto
    imp_transito = imp_transito.drop_duplicates(subset='CONTRATO_ID')
    imp_transito = imp_transito.merge(imp_total_pallets, on='CONTRATO_ID', how='left')
    
    imp_transito = de_dataframe_a_template(imp_transito)
    
    if request.method == 'POST':
        importaciones_en_transito_odbc_insert_warehouse()
        return redirect('wms_importaciones_transito_list')
        
    context = {
        'imp_transito':imp_transito
    }
    
    return render(request, 'wms/importaciones_transito_list.html', context)


# Detalle de importación en transito
@login_required(login_url='login')
@permisos(['ADMINISTRADOR','OPERACIONES','BODEGA'], '/wms/home', 'Importaciones en tránsito')
def wms_importaciones_transito_detalle(request, contrato_id):
    
    prod = productos_odbc_and_django()[['product_id','Nombre','Marca','Unidad_Empaque','UnidadesPorPallet']]
    prod = prod.fillna(0)
    
    imp_transito = importaciones_en_transito_detalle_odbc(contrato_id)   
    imp_transito = imp_transito.rename(columns={'PRODUCT_ID':'product_id'})
    
    imp_transito =  imp_transito.merge(prod, on='product_id', how='left')
    
    imp_transito['cartones'] = imp_transito['QUANTITY'] / imp_transito['Unidad_Empaque']
    imp_transito['pallets'] = imp_transito['QUANTITY'] / imp_transito['UnidadesPorPallet']
    imp_transito = imp_transito.replace(np.inf, 0)
    
    unidades_total = imp_transito['QUANTITY'].sum()
    cartones_total = imp_transito['cartones'].sum()
    pallets_total  = imp_transito['pallets'].sum()
    
    proveedor = imp_transito.loc[0]['VENDOR_NAME']
    importacion = imp_transito.loc[0]['MEMO']
    
    imp_transito = de_dataframe_a_template(imp_transito)
    
    context = {
        'proveedor':proveedor,
        'importacion':importacion,
        'imp_transito':imp_transito,
        
        'unidades_total':unidades_total,
        'cartones_total':cartones_total,
        'pallets_total':pallets_total
    }
    
    return render(request, 'wms/importaciones_transito_detalle.html', context)


@login_required(login_url='login')
def wms_excel_importacion_transito(request, contrato_id):
    
    prod = productos_odbc_and_django()[['product_id','Nombre','Marca','Unidad_Empaque','UnidadesPorPallet']]
    prod = prod.fillna(0)
    
    imp_transito = importaciones_en_transito_detalle_odbc(contrato_id)   
    imp_transito = imp_transito.rename(columns={'PRODUCT_ID':'product_id'})
    imp_transito =  imp_transito.merge(prod, on='product_id', how='left')
    imp_transito['Cartones'] = imp_transito['QUANTITY'] / imp_transito['Unidad_Empaque']
    imp_transito = imp_transito.replace(np.inf, 0)
    
    # CABECERA
    proveedor = imp_transito.loc[0]['VENDOR_NAME']
    fecha_entrega = str(imp_transito.loc[0]['FECHA_ENTREGA'])
    memo = imp_transito.loc[0]['MEMO']
    
    imp_transito = imp_transito[['product_id','Nombre','Marca','Unidad_Empaque','QUANTITY','Cartones']]
    imp_transito = imp_transito.rename(columns={
        'product_id':'Código',
        'Unidad_Empaque':'Unidades por empaque',
        'QUANTITY':'Unidades',
    })

    # TOTALES
    totales = imp_transito[['Unidades','Cartones']].sum()
    totals_row = pd.DataFrame(totales).T
    totals_row['Código'] = 'Totales'

    # DF FINAL
    imp_transito = pd.concat([imp_transito, totals_row], ignore_index=True).fillna('')
    
    # Generar respuesta HTTP
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{proveedor} - {memo}.xlsx"'
    
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        # Añadir el DataFrame al archivo Excel
        imp_transito.to_excel(writer, sheet_name=f'{memo}', startrow=5, index=False)

        # Acceder al workbook y worksheet
        workbook = writer.book
        worksheet = writer.sheets[f'{memo}']

        # Insertar el título en la fila 1, combinando 6 columnas
        worksheet.merge_cells('A1:F1')
        title_cell = worksheet['A1']
        title_cell.value = proveedor
        title_cell.font = Font(size=14, bold=True)
        title_cell.alignment = Alignment(horizontal='center')

        # Fila 2: Vacía

        # Fila 3: Subtítulo 2 (Importación)
        worksheet['A3'] = 'Importación'
        worksheet['A3'].font = Font(bold=True)
        worksheet['B3'] = memo

        # Fila 4: Subtítulo 3 (Fecha entrega)
        worksheet['A4'] = 'Fecha entrega'
        worksheet['A4'].font = Font(bold=True)
        worksheet['B4'] = fecha_entrega
        
        # Ajustar el ancho de las columnas con openpyxl
        worksheet.column_dimensions['A'].width = 20
        worksheet.column_dimensions['B'].width = 35
        worksheet.column_dimensions['C'].width = 15
        worksheet.column_dimensions['D'].width = 25
        worksheet.column_dimensions['E'].width = 15
        worksheet.column_dimensions['F'].width = 15
        
        response
    
    return response



# Lista de productos de importación
# url: importacion/bodega/<str:o_compra>
@login_required(login_url='login')
@permisos(['ADMINISTRADOR','OPERACIONES','BODEGA'], '/wms/home', 'detalle de productos')
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
@permisos(['ADMINISTRADOR','OPERACIONES','BODEGA'], '/wms/home', 'Inventario inicial')
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
@permisos(['ADMINISTRADOR','OPERACIONES','BODEGA'], '/wms/home', 'Inventario inicial')
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

    # e = pd.DataFrame(Movimiento.objects.all().values())
    # e.to_excel('mm.xlsx')
    

    # for i in exitencias:
    #     if i['total_unidades'] < 0:
    #         print(i['product_id'], i['lote_id'], i['ubicacion'], i['total_unidades'] )
    
    
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
@transaction.atomic
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
    
    # for i in existencias_list:
    #     print(i.product_id, i.lote_id, i.unidades)
    
    Existencias.objects.filter(product_id=product_id, lote_id=lote_id).delete()
    Existencias.objects.bulk_create(existencias_list)

    return exitencias


# Actualizar toda la tabla existencias
def wms_btn_actualizar_todas_existencias(request):
    wms_existencias_query()
    return redirect('/wms/inventario')



# Inventario - Lista de productos Existencias
# url: wms/inventario
@login_required(login_url='login')
@permisos(['ADMINISTRADOR','OPERACIONES','BODEGA'], '/wms/home', 'ingrear a Inventario')
def wms_inventario(request): #OK
    """ Inventario
        Suma de ingresos y egresos que dan el total de todo el inventario
    """
    # wms_existencias_query_product_lote("A3065F","260624")
    
    prod = productos_odbc_and_django()[['product_id','Nombre','Marca']]
    productos = pd.DataFrame(Existencias.objects.all().values('product_id'))
    productos = productos.merge(prod, on='product_id', how='left').sort_values('product_id')
    productos = productos.drop_duplicates('product_id')
    productos = de_dataframe_a_template(productos)
    
    # Todos los productos 
    inv = pd.DataFrame(Existencias.objects.all().values(
        'id',
        'product_id', 'lote_id', 'fecha_caducidad', 'unidades', 'fecha_hora',
        'ubicacion', 'ubicacion__bodega', 'ubicacion__pasillo', 'ubicacion__modulo', 'ubicacion__nivel',
        'estado'
    ))
    inv = inv.merge(prod, on='product_id', how='left')
    inv['fecha_caducidad'] = pd.to_datetime(inv['fecha_caducidad'])
    inv = inv.sort_values(
        by        = ['estado', 'product_id', 'fecha_caducidad', 'lote_id', 'ubicacion__bodega', 'ubicacion__nivel', 'unidades'],
        ascending = [False,    True,         True,              True,      True,                True,               True]    
    )
    inv['fecha_caducidad'] = inv['fecha_caducidad'].dt.strftime('%d-%m-%Y')
    
    inv = de_dataframe_a_template(inv)
    
    if request.method == 'POST':
        
        ex = Existencias.objects.filter(product_id=request.POST['codigo']).values('id',
            'product_id', 'lote_id', 'fecha_caducidad', 'unidades', 'fecha_hora',
            'ubicacion', 'ubicacion__bodega', 'ubicacion__pasillo', 'ubicacion__modulo', 'ubicacion__nivel',
            'estado')
        
        inv = pd.DataFrame(ex).merge(prod, on='product_id', how='left')
        inv['fecha_caducidad'] = pd.to_datetime(inv['fecha_caducidad'])
        inv = inv.sort_values(
            by        = ['estado', 'product_id', 'fecha_caducidad', 'lote_id', 'ubicacion__bodega', 'ubicacion__nivel', 'unidades'],
            ascending = [False,    True,         True,              True,      True,                True,               True]    
        )
        inv['fecha_caducidad'] = inv['fecha_caducidad'].dt.strftime('%d-%m-%Y')
        inv = de_dataframe_a_template(inv)
        
        # INV DETALLE
        products = productos_odbc_and_django()[['product_id','Unidad_Empaque','UnidadesPorPallet','Volumen']]
        
        inv_detalle = pd.DataFrame(ex).groupby(by=['estado','product_id','lote_id','fecha_caducidad']).sum().reset_index().sort_values(by='fecha_caducidad')
        inv_detalle = inv_detalle.merge(products, on='product_id', how='left')
        inv_detalle['cartones'] = inv_detalle['unidades'] / inv_detalle['Unidad_Empaque']
        inv_detalle['volumen']  = inv_detalle['cartones'] * (inv_detalle['Volumen'] / 1000000)
        inv_detalle['pallets']  = inv_detalle['unidades'] / inv_detalle['UnidadesPorPallet'] 
        inv_detalle['fecha_caducidad'] = pd.to_datetime(inv_detalle['fecha_caducidad']).dt.strftime('%d-%m-%Y')
        inv_detalle = inv_detalle.replace(to_replace=np.inf, value=0)
        
        # INV ESTADO
        inv_estado = pd.DataFrame(inv_detalle).groupby(by="estado").sum().sort_values(by='estado',ascending=False).reset_index()
        
        # TOTALES
        total_unidades = inv_detalle['unidades'].sum()
        total_cartones = inv_detalle['cartones'].sum()
        total_volumen  = inv_detalle['volumen'].sum()
        total_pallets  = inv_detalle['pallets'].sum()
        
        inv_detalle = de_dataframe_a_template(inv_detalle)
        inv_estado = de_dataframe_a_template(inv_estado)
        
        en_despacho = (Movimiento.objects
            .filter(product_id=request.POST['codigo'])
            .filter(referencia='Picking')
            .filter(estado_picking='En Despacho')
            .values('product_id','lote_id','fecha_caducidad','estado_picking','unidades'))
        
        en_despacho_df = pd.DataFrame(en_despacho)
        
        if not en_despacho_df.empty:
            en_despacho_df['unidades'] = en_despacho_df['unidades'] * -1
            en_despacho_df = en_despacho_df.merge(products, on='product_id', how='left')
            en_despacho_df['cartones'] = en_despacho_df['unidades'] / en_despacho_df['Unidad_Empaque']
            en_despacho_df['volumen']  = en_despacho_df['cartones'] * (en_despacho_df['Volumen'] / 1000000)
            en_despacho_df['pallets']  = en_despacho_df['unidades'] / en_despacho_df['UnidadesPorPallet'] 
            en_despacho_df['fecha_caducidad'] = pd.to_datetime(en_despacho_df['fecha_caducidad']).dt.strftime('%d-%m-%Y')
            en_despacho_df = en_despacho_df.replace(to_replace=np.inf, value=0)
            
            total_unidades_despacho = en_despacho_df['unidades'].sum()
            total_cartones_despacho = en_despacho_df['cartones'].sum()
            total_volumen_despacho  = en_despacho_df['volumen'].sum()
            total_pallets_despacho  = en_despacho_df['pallets'].sum()
            
            en_despacho = de_dataframe_a_template(en_despacho_df)
        else:
            
            total_unidades_despacho = 0
            total_cartones_despacho = 0
            total_volumen_despacho  = 0
            total_pallets_despacho  = 0
            
            en_despacho = de_dataframe_a_template(en_despacho_df)
        
        context = {
            'productos':productos,
            'inv':inv,
            
            'codigo':request.POST['codigo'],
            'inv_detalle':inv_detalle,
            'inv_estado':inv_estado,
            'en_despacho':en_despacho,
            
            'total_unidades':total_unidades,
            'total_cartones':total_cartones,
            'total_volumen':total_volumen,
            'total_pallets':total_pallets,
            
            'total_unidades_despacho':total_unidades_despacho,
            'total_cartones_despacho':total_cartones_despacho,
            'total_volumen_despacho':total_volumen_despacho,
            'total_pallets_despacho':total_pallets_despacho,
        }
    
        return render(request, 'wms/inventario.html', context)

    context = {
        'productos':productos,
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
@permisos(['ADMINISTRADOR','OPERACIONES'], '/wms/home', 'de ingrear a movimiento de ingreso')
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
    ubi_list = Ubicacion.objects.filter(bodega=item.bodega).filter(disponible=True)

    # Movimientos ingresado
    mov_list = (Movimiento.objects
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

        if und == total_ingresado:
            # guardar
            if form.is_valid():
                form.save()
                wms_existencias_query_product_lote(product_id=request.POST['product_id'], lote_id=request.POST['lote_id'])
                
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
                
                return redirect(f'/wms/ingreso/{item.id}')
            else:
                messages.error(request, form.errors)

        elif ubicaciones_und == total_ingresado :
            # guardar
            if form.is_valid():
                form.save()
                wms_existencias_query_product_lote(product_id=request.POST['product_id'], lote_id=request.POST['lote_id'])
                
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
        recipient_list = ['dreyes@gimpromed.com','jgualotuna@gimpromed.com','ncaisapanta@gimpromed.com'],
        fail_silently  = False
        )

    return JsonResponse({'msg':'Correo enviado'}, status=200)



# Movimiento interno
# url: inventario/mov-interno-<int:id>
@login_required(login_url='login')
@permisos(['BODEGA'], '/wms/inventario', 'ingrear a Movimiento interno')
def wms_movimiento_interno(request, id): #OK
    
    item = Existencias.objects.get(id=id)
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
                    usuario     = request.user.id
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
    }

    return render(request, 'wms/movimiento_interno.html', context)


def wms_movimiento_interno_get_ubi_list_ajax(request):

    bodega  = request.POST['bodega']
    pasillo = request.POST['pasillo']
    ubi_salida = int(request.POST['ubi_salida'])

    ubi_list = pd.DataFrame(Ubicacion.objects
        .filter(disponible=True)
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
@permisos(['ADMINISTRADOR','OPERACIONES'], '/wms/home', 'ingresar a Ajustes')
def wms_movimiento_ajuste(request): #OK

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
            .filter(disponible=True)
            #.all()
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
            .filter(disponible=True)
            #.all()
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
@permisos(['ADMINISTRADOR','OPERACIONES','BODEGA'], '/wms/home', 'ingresar a Movimientos')
def wms_movimientos_list(request): #OK
    """ Lista de movimientos """

    mov = Movimiento.objects.all().order_by('-fecha_hora', '-id')
    
    paginator = Paginator(mov, 50)
    page_number = request.GET.get('page')
    
    if page_number == None: page_number = 1
    
    mov = paginator.get_page(page_number)
    
    if request.method == 'POST':
        
        product_id = request.POST.get('product_id')
        n_referencia = request.POST.get('n_referencia')
        n_factura = request.POST.get('n_factura')
        
        filtro = {}
        if product_id:
            tipo = 'Código'
            valor= product_id
            filtro['product_id'] = product_id
        elif n_referencia:
            tipo = 'Referencia'
            valor=n_referencia
            filtro['n_referencia__icontains'] = n_referencia
        elif n_factura:
            tipo = 'Factura'
            valor= n_factura
            filtro['n_factura__icontains'] = n_factura
        
        mov = Movimiento.objects.filter(**filtro).order_by('-fecha_hora','-id')
        
        context = {
            'mov':mov,
            'len':len(mov),
            'tipo':tipo,
            'valor':valor
        }
        
        return render(request, 'wms/movimientos_list.html', context)
        
    context = {
        'mov':mov
    }

    return render(request, 'wms/movimientos_list.html', context)



### PICKDING
# Lista de pedidos
# url: picking/list
@login_required(login_url='login')
@permisos(['ADMINISTRADOR','OPERACIONES','BODEGA'], '/wms/home', 'ingrear a Listado de Pedidos')
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
@permisos(['ADMINISTRADOR','OPERACIONES','BODEGA'], '/picking/list', 'ingresar a Detalle de Pedido')
def wms_egreso_picking(request, n_pedido): #OK
    
    estado_picking = EstadoPicking.objects.filter(n_pedido=n_pedido).exists()
    if estado_picking:
        est = EstadoPicking.objects.get(n_pedido=n_pedido)
        estado = est.estado
        estado_id = est.id
    else:
        estado = 'SIN ESTADO'
        estado_id = ''

    prod   = productos_odbc_and_django()[['product_id','Nombre','Marca','Unidad_Empaque']]
    prod   = prod.rename(columns={'product_id':'PRODUCT_ID'})
    
    pedido = pedido_por_cliente(n_pedido).sort_values('PRODUCT_ID')
    pedido = pedido.groupby(by=['CONTRATO_ID','CODIGO_CLIENTE','NOMBRE_CLIENTE','FECHA_PEDIDO','HORA_LLEGADA','PRODUCT_ID','PRODUCT_NAME']).sum().reset_index()
    pedido = pedido.merge(prod, on='PRODUCT_ID',how='left')
    
    cli    = clientes_warehouse()[['CODIGO_CLIENTE','CIUDAD_PRINCIPAL']]
    pedido = pedido.merge(cli, on='CODIGO_CLIENTE', how='left')

    prod_list = list(pedido['PRODUCT_ID'].unique())
    
    n_ped = pedido['CONTRATO_ID'].iloc[0]
    cli   = pedido['NOMBRE_CLIENTE'].iloc[0]
    ciu   = pedido['CIUDAD_PRINCIPAL'].iloc[0]
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

    # Inventario
    inv = Existencias.objects.filter(product_id__in=prod_list).values(
        'product_id','lote_id','fecha_caducidad','unidades',
        'ubicacion_id','ubicacion__bodega','ubicacion__pasillo','ubicacion__modulo','ubicacion__nivel',
        'ubicacion__distancia_puerta',
        'unidades',
        'estado'
    )

    mov_bodega_df = pd.DataFrame(movimientos.order_by('fecha_caducidad').values('product_id', 'ubicacion__bodega'))
    mov_bodega_df = mov_bodega_df.rename(columns={'ubicacion__bodega':'bodega_mov'})
    mov_bodega_df = mov_bodega_df.drop_duplicates(subset='product_id', keep='first').fillna('')
    
    exi_bodega_df = pd.DataFrame(inv.order_by('fecha_caducidad'))#[['product_id','ubicacion__bodega']]
    exi_bodega_df = exi_bodega_df.rename(columns={'ubicacion__bodega':'bodega_exi'})
    exi_bodega_df = exi_bodega_df.drop_duplicates(subset='product_id', keep='first').fillna('')
    
    if not mov_bodega_df.empty and not exi_bodega_df.empty:
        bodega_df = exi_bodega_df.merge(mov_bodega_df, on='product_id', how='left').fillna('')
    elif not mov_bodega_df.empty and exi_bodega_df.empty:
        bodega_df = mov_bodega_df
    else:
        bodega_df = exi_bodega_df
        bodega_df['bodega_mov'] = ''
    
    bodega_df['primera_bodega'] = bodega_df.apply(lambda x: x['bodega_exi'] if not x['bodega_mov'] else x['bodega_mov'], axis=1)       
    bodega_df = bodega_df.rename(columns={'product_id':'PRODUCT_ID'})[['PRODUCT_ID','primera_bodega']]
    
    if inv.exists():
        inv = pd.DataFrame(inv).sort_values(by=['lote_id','fecha_caducidad','ubicacion__distancia_puerta'], ascending=[True,True,True])
        inv['fecha_caducidad'] = inv['fecha_caducidad'].astype(str)

        r_lote = wms_reservas_lotes_datos()
        if not r_lote.empty:
            inv = inv.merge(r_lote, on=['product_id','lote_id'], how='left')
            inv = de_dataframe_a_template(inv)
    else:
        inv = {}

    # Calculo Cartones
    pedido['cartones'] = pedido['QUANTITY'] / pedido['Unidad_Empaque']
    pedido = pedido.merge(bodega_df, on='PRODUCT_ID', how='left').sort_values(by='primera_bodega')
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
        'ciu':ciu,
        'fecha': fecha ,
        'hora':hora,
        'estado':estado,
        'estado_id':estado_id
    }

    return render(request, 'wms/picking.html', context)


# Estado Picking AJAX
@permisos(['BODEGA'], '/wms/picking/list', 'cambio de estado de picking')
def wms_estado_picking_ajax(request):

    contrato_id = request.POST['n_ped']
    estado = request.POST['estado']
    user_id = int(request.POST['user_id'])
    user_perfil_id   = UserPerfil.objects.get(user__id=user_id).id

    reserva = wms_reserva_por_contratoid(contrato_id)
    cli     = clientes_warehouse()[['CODIGO_CLIENTE','CLIENT_TYPE']]
    reserva = reserva.merge(cli, on='CODIGO_CLIENTE', how='left')
    
    cliente        = reserva['NOMBRE_CLIENTE'].iloc[0]
    fecha_pedido   = reserva['FECHA_PEDIDO'].iloc[0]
    tipo_cliente   = reserva['CLIENT_TYPE'].iloc[0]
    bodega         = reserva['WARE_CODE'].iloc[0]
    codigo_cliente = reserva['CODIGO_CLIENTE'].iloc[0]
    data           = (reserva[['PRODUCT_ID', 'QUANTITY']]).to_dict()
    data           = json.dumps(data)

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
@permisos(['BODEGA'], '/wms/picking/list', 'cambio de estado de picking')
def wms_estado_picking_actualizar_ajax(request):

    id_picking = int(request.POST['id_picking'])
    estado_post = request.POST['estado']

    estado_picking = EstadoPicking.objects.get(id=id_picking)

    if estado_post == 'FINALIZADO':

        pick = pedido_por_cliente(n_pedido=estado_picking.n_pedido)
        pick_total_unidades = pick['QUANTITY'].sum()
        movs = Movimiento.objects.filter(referencia='Picking').filter(n_referencia=estado_picking.n_pedido).values_list('unidades', flat=True)
        movs_total_unidades = sum(movs) * -1
            
        if estado_picking.bodega == 'BCT':
            
            if movs_total_unidades < pick_total_unidades:

                return JsonResponse({'msg':' ⚠ Aun no a completado el picking !!!',
                                    'alert':'warning'})

            elif pick_total_unidades == movs_total_unidades:

                estado_picking.estado = estado_post
                estado_picking.fecha_actualizado = datetime.now()

                try:
                    estado_picking.save()

                    if estado_picking.id:
                        return JsonResponse({'msg':f'✅ Estado de picking {estado_picking.estado}',
                                        'alert':'success'}, status=200)
                except:
                    return JsonResponse({'msg':'❌ Error, intente nuevamente !!!',
                                        'alert':'danger'})
        
        elif estado_picking.bodega == 'BAN':
            
            estado_picking.estado = estado_post
            estado_picking.fecha_actualizado = datetime.now()

            try:
                estado_picking.save()

                if estado_picking.id:
                    return JsonResponse({'msg':f'✅ Estado de picking {estado_picking.estado}',
                                    'alert':'success'}, status=200)
            except:
                return JsonResponse({'msg':'❌ Error, intente nuevamente !!!',
                                    'alert':'danger'})
            
    else:
            estado_picking.estado = estado_post
            estado_picking.fecha_actualizado = datetime.now()

            try:
                estado_picking.save()

                if estado_picking.id:
                    return JsonResponse({'msg':f'✅ Estado de picking {estado_picking.estado}',
                                    'alert':'success'}, status=200)
            except:
                return JsonResponse({'msg':'❌ Error, intente nuevamente !!!',
                                    'alert':'danger'})


# Crear egreso en tabla movimientos
@login_required(login_url='login')
@permisos(['BODEGA'], '/wms/picking/list', 'retirar productos de inventario')
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

            return JsonResponse({'msg':f'✅ Producto {prod_id}, lote {lote_id} seleccionado correctamente !!!'})
        return JsonResponse({'msg':'❌ Error !!!'})
    return JsonResponse({'msg':'❌Error !!!'})


# Eliminar movimeinto de egreso AJAX
@login_required(login_url='login')
@permisos(['BODEGA'], '/wms/picking/list', 'retirar productos de inventario')
def wms_eliminar_movimiento(request): #OK

    mov_id = request.POST['mov']
    mov_id = int(mov_id)
    mov = Movimiento.objects.get(id=mov_id)
    m = mov

    mov.delete()

    wms_existencias_query_product_lote(product_id=m.product_id, lote_id=m.lote_id)

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
@permisos(['ADMINISTRADOR','OPERACIONES','BODEGA'], '/wms/home', 'ingresar a productos en despacho')
def wms_productos_en_despacho_list(request): #OK

    anulados = pd.DataFrame(AnulacionPicking.objects.filter(estado=True).values(
        'picking_nuevo','picking_anulado'))
    anulados = anulados.rename(columns={'picking_nuevo':'n_referencia'})
    anulados['n_referencia'] = anulados['n_referencia'].astype('float')
    anulados['n_referencia'] = anulados['n_referencia'].astype('int')
    
    mov      = Movimiento.objects.filter(estado_picking='En Despacho')
    mov_list = mov.values_list('n_referencia', flat=True).distinct()
    pik      = EstadoPicking.objects.filter(n_pedido__in=mov_list)

    en_despacho = pd.DataFrame(mov.values(
        'product_id','lote_id','fecha_caducidad','referencia','n_referencia',
        'ubicacion__bodega','ubicacion__pasillo','ubicacion__modulo','ubicacion__nivel',
        'fecha_hora','unidades','usuario__first_name','usuario__last_name'
    ))
    contexto_picking = pd.DataFrame(pik.values())[['n_pedido','cliente']]
    contexto_picking = contexto_picking.rename(columns={'n_pedido':'n_referencia'})

    en_despacho = en_despacho.merge(contexto_picking, on='n_referencia', how='left')
    en_despacho['unidades'] = en_despacho['unidades']*-1
    en_despacho['n_referencia'] = en_despacho['n_referencia'].astype('float')
    en_despacho['n_referencia'] = en_despacho['n_referencia'].astype('int')
    en_despacho['fecha_caducidad'] = en_despacho['fecha_caducidad'].astype('str')
    en_despacho['fecha_hora'] = pd.to_datetime(en_despacho['fecha_hora']).dt.strftime('%Y-%m-%d %H:%M')

    en_despacho = en_despacho.sort_values(by='n_referencia')
    en_despacho = en_despacho.merge(anulados, on='n_referencia', how='left')
    en_despacho = de_dataframe_a_template(en_despacho)

    context = {
        'mov':en_despacho
    }

    return render(request, 'wms/productos_en_despacho_list.html', context)



# Lista de picking en despacho
@login_required(login_url='login')
@permisos(['ADMINISTRADOR','OPERACIONES','BODEGA'], '/wms/home', 'ingresar a picking en despacho')
def wms_picking_en_despacho_list(request): #OK
    
    anulados = pd.DataFrame(AnulacionPicking.objects.filter(estado=True).values('picking_nuevo','picking_anulado'))
    anulados = anulados.rename(columns={'picking_nuevo':'n_referencia'})
    anulados['n_referencia'] = anulados['n_referencia'].astype('float')
    anulados['n_referencia'] = anulados['n_referencia'].astype('int') 

    mov      = Movimiento.objects.filter(estado_picking='En Despacho')
    mov_list = mov.values_list('n_referencia', flat=True).distinct()
    pik      = EstadoPicking.objects.filter(n_pedido__in=mov_list) 

    en_despacho = pd.DataFrame(mov.values('product_id','referencia','n_referencia','fecha_hora')) 
    contexto_picking = pd.DataFrame(pik.values())[['n_pedido','cliente']] 
    contexto_picking = contexto_picking.rename(columns={'n_pedido':'n_referencia'})

    en_despacho = en_despacho.merge(contexto_picking, on='n_referencia', how='left')
    en_despacho['n_referencia'] = en_despacho['n_referencia'].astype('float')
    en_despacho['n_referencia'] = en_despacho['n_referencia'].astype('int')
    en_despacho['fecha_hora'] = pd.to_datetime(en_despacho['fecha_hora']).dt.strftime('%Y-%m-%d %H:%M')
    
    en_despacho = en_despacho.sort_values(by='fecha_hora', ascending=True)
    en_despacho = en_despacho.drop_duplicates(subset='n_referencia', keep='last') #; print(en_despacho)
    en_despacho = en_despacho.merge(anulados, on='n_referencia', how='left')
    
    en_despacho = de_dataframe_a_template(en_despacho)

    context = {
        'mov':en_despacho
    }

    return render(request, 'wms/picking_en_despacho_list.html', context)



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
        # calculo cartones
        productos = productos_odbc_and_django()[['product_id','Unidad_Empaque']]
        factura = factura.merge(productos, on='product_id', how='left')
        factura['cartones'] = factura['EGRESO_TEMP'] / factura['Unidad_Empaque']
        
        total_cartones = round(factura['cartones'].sum(), 2)
        
        fn_pedido = de_dataframe_a_template(factura)[0]['NUMERO_PEDIDO_SISTEMA']

        try:
            picking = pd.DataFrame(Movimiento.objects.filter(n_referencia = fn_pedido).values())
            picking['lote_wms'] = picking['lote_id']
            picking['lote_id'] = quitar_puntos(picking['lote_id'])
            picking = picking.groupby(by=['product_id','lote_id','estado_picking','lote_wms']).sum().reset_index()
            
            factura = factura.merge(picking, on=['product_id','lote_id'], how='left').fillna(0)
            factura['unidades'] = factura['unidades'].abs()
            factura['diferencia'] = factura['unidades'] - factura['EGRESO_TEMP']
            factura['n_factura_format'] = factura['CODIGO_FACTURA'].apply(lambda x: int(x.split('-')[1][4:]))

            factura = {
                'factura':de_dataframe_a_template(factura),
                'cabecera':de_dataframe_a_template(factura)[0],
                'total_cartones':total_cartones
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
@permisos(['BODEGA'], '/wms/home', 'ingresar a cruce de picking-factura')
def wms_cruce_picking_factura(request):

    if request.method=="POST":
        n_factura = request.POST['n_factura']
        factura = wms_armar_codigo_factura(n_factura)
        try:
            cartones = DespachoCarton.objects.get(picking=factura.get('cabecera').get('NUMERO_PEDIDO_SISTEMA')).cartones_fisicos
        except:
            cartones = 00.0
        
        context={
            'factura':factura,
            'cartones':cartones
        }
        return render(request, 'wms/cruce_picking_factura.html', context)
    context = {}
    return render(request, 'wms/cruce_picking_factura.html', context)


# Cartones despacho
def wms_despacho_cartones(request):
    if request.method == "POST":
        picking = request.POST.get('picking')
        registro = DespachoCarton.objects.filter(picking=picking)
        if not registro.exists():
            form = DespachoCartonForm(request.POST)
            if form.is_valid():
                form.save()
                return JsonResponse({
                    'tipo':'success',
                    'msg':'Registro de cartones exitoso !!!'})
            else:
                return JsonResponse({
                    'tipo':'danger',
                    'msg':f'{form.errors}'})
        elif registro.exists():
            form = DespachoCartonForm(request.POST, instance=registro.first())
            if form.is_valid():
                form.save()
                return JsonResponse({
                    'tipo':'success',
                    'msg':'Actulización de registro de cartones exitoso !!!'})
            else:
                return JsonResponse({
                    'tipo':'danger',
                    'msg':f'{form.errors}'})



@permisos(['BODEGA'], '/wms/home/', 'ingresar a cruce de picking-factura')
def wms_cruce_check_despacho(request):

    n_pick    = request.POST['n_picking']
    prod_id   = request.POST['prod_id']
    lote_id   = request.POST['lote_id']
    n_factura = request.POST['n_factura']

    items = (Movimiento.objects
        .filter(n_referencia=n_pick)
        .filter(product_id=prod_id)
        .filter(lote_id=lote_id)
        )

    if items.exists():
        items.update(estado_picking='Despachado', n_factura=n_factura)

        return JsonResponse({
            'msg':'OK',
            })

    else:
        return JsonResponse({
            'msg':'FAIL',
            })



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
@permisos(['ADMINISTRADOR','OPERACIONES'], '/wms/home', 'ingresar a revisión de transferencia')
def wms_revision_transferencia(request):
    return render(request, 'wms/revision_trasferencia.html', {})


# # Transferencias estatus
# def wms_transferencias_estatus_all():
    
#     transf_list = NotaEntrega.objects.values_list('doc_id', flat=True).distinct()
    
#     for i in transf_list:
        
#         transf_mba = NotaEntrega.objects.filter(doc_id=i)
#         mba_total  = sum(transf_mba.values_list('unidades', flat=True))
        
#         transf_wms = Movimiento.objects.filter(referencia='Nota de entrega').filter(n_referencia=i)
#         wms_total  = sum(transf_wms.values_list('unidades', flat=True))*-1
        
#         avance_i = round(((wms_total / mba_total) * 100), 1)
        
#         if wms_total == 0 or wms_total == None:
#             estado_i = 'CREADO'
#         elif wms_total < mba_total:
#             estado_i = 'EN PROCESO'
#         elif mba_total == wms_total or wms_total > mba_total:
#             estado_i = 'FINALIZADO'        
        
#         NotaEntregaStatus.objects.update_or_create(
#             nota_entrega    = i,
#             unidades_mba    = mba_total,
#             unidades_wms    = wms_total,
#             avance          = avance_i,
#             estado          = estado_i
#         )
        
#     return JsonResponse({
#         'msg':{
#             'tipo':'success',
#             'texto':'✅ Estado de transferencia actualizado !!!'
#         }
#     })



def wms_transferencias_estatus_transf(n_transf):
    
    transf_mba = Transferencia.objects.filter(n_transferencia=n_transf)
    mba_total  = sum(transf_mba.values_list('unidades', flat=True))
    
    transf_wms = Movimiento.objects.filter(referencia='Transferencia').filter(n_referencia=n_transf)
    wms_total  = sum(transf_wms.values_list('unidades', flat=True))*-1
    
    avance_i = round(((wms_total / mba_total) * 100), 1)
    
    if wms_total == 0 or wms_total == None:
        estado_i = 'CREADO'
    elif wms_total < mba_total:
        estado_i = 'EN PROCESO'
    elif mba_total == wms_total or wms_total > mba_total:
        estado_i = 'FINALIZADO'    

    transf_status = TransferenciaStatus.objects.get(n_transferencia=n_transf)
    transf_status.estado       = estado_i
    transf_status.unidades_mba = mba_total
    transf_status.unidades_wms = wms_total
    transf_status.avance       = avance_i
    
    transf_status.save()

    return JsonResponse({
        'msg':{
            'tipo':'success',
            'texto':f'✅ Transferencia {n_transf} actualizado !!!'
        }
    })


# Agregar transferencia para realizar picking de transferencia 
@login_required(login_url='login')
def wms_transferencia_input_ajax(request):
    
    n_trasf = request.POST['n_trasf']
    
    trans_mba  = doc_transferencia_odbc(n_trasf)

    new_transf = Transferencia.objects.filter(n_transferencia=n_trasf)
    if not new_transf.exists():

        trans_mba['n_transferencia'] = n_trasf
        trans_mba = trans_mba.groupby(by=['doc','n_transferencia','product_id','lote_id','f_cadu','bodega_salida','UBICACION']).sum().reset_index()
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
                unidades        = i['unidades'],
                ubicacion       = i['UBICACION']
            )

            tr_list.append(tr)
            
        Transferencia.objects.bulk_create(tr_list)
        
        if len(tr_list) > 0 and tr.bodega_salida == 'BCT' or tr.bodega_salida == 'CUC':
            TransferenciaStatus.objects.create(
                n_transferencia = n_trasf,
                estado          = 'CREADO',
                unidades_mba    = 0,
                unidades_wms    = 0,
                avance          = 0.0
            )

        return JsonResponse({
            'msg':f'La Transferencia {n_trasf} fue añadida exitosamente !!!',
            'alert':'success'
        })

    else:
    #elif new_transf.exists():
        return JsonResponse({
            'msg':f'La Transferencia {n_trasf} ya fue añadida anteriormente !!!',
            'alert':'danger'
        })


@login_required(login_url='login')
@permisos(['BODEGA'], '/wms/home', 'ingresar una transferencia nueva')
def wms_transferencias_list(request):
    
    transf_wms = pd.DataFrame(Transferencia.objects.all().values()).drop_duplicates(subset='n_transferencia')
    # transf_wms = transf_wms[transf_wms['bodega_salida']=='BCT']
    transf_wms = transf_wms[(transf_wms['bodega_salida']=='BCT') | (transf_wms['bodega_salida']=='CUC')]
    
    transf_status = pd.DataFrame(TransferenciaStatus.objects.all().values())[['n_transferencia','estado','avance']]
    
    if not transf_wms.empty:
        transf_wms = transf_wms.sort_values(by='fecha_hora', ascending=False)
        transf_wms['fecha_hora'] = pd.to_datetime(transf_wms['fecha_hora']).dt.strftime('%d-%m-%Y - %r').astype(str)
        
    if not transf_status.empty:
        transf_wms = transf_wms.merge(transf_status, on='n_transferencia', how='left')
    
    transf_wms = de_dataframe_a_template(transf_wms)
    context = {
        'transf_wms':transf_wms
    }

    return render(request, 'wms/transferencias_list.html', context)



@login_required(login_url='login')
def wms_transferencia_picking(request, n_transf):
    
    estado = TransferenciaStatus.objects.get(n_transferencia=n_transf)
    
    prod   = productos_odbc_and_django()[['product_id','Nombre','Marca','Unidad_Empaque','Volumen']]
    
    # Trasferencia
    transf = pd.DataFrame(Transferencia.objects.filter(n_transferencia=n_transf).values())
    transf = transf.merge(prod, on='product_id', how='left')
    transf['fecha_caducidad'] = pd.to_datetime(transf['fecha_caducidad']).dt.strftime('%d-%m-%Y').astype(str)
    transf['cartones'] = transf['unidades'] / transf['Unidad_Empaque']
    transf['vol'] = transf['cartones'] * (transf['Volumen']/1000000)
    transf['id_max'] = ''
    transf.at[transf['vol'].idxmax(), 'id_max'] = 'max'
    # transf = transf.sort_values('ubicacion')
    
    # Productos y cantidades egresados de WMS por Picking Transferencia
    mov = pd.DataFrame(Movimiento.objects.filter(n_referencia=n_transf).values(
        'id',
        'product_id','lote_id','fecha_caducidad',
        'unidades','ubicacion__bodega','ubicacion__pasillo','ubicacion__modulo','ubicacion__nivel',
        'ubicacion__distancia_puerta'))

    if not mov.empty:
        mov['fecha_caducidad'] = pd.to_datetime(mov['fecha_caducidad']).dt.strftime('%d-%m-%Y')
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
        ).order_by('ubicacion__bodega')
        if ext.exists():
            for j in ext:
                ext_id.append(j)

    prod = list(transf['product_id'].unique())
    
    
    # df existencias bodega
    existencias_bodega_df = pd.DataFrame(Existencias.objects.filter(product_id__in=prod).values(
        'product_id','lote_id','ubicacion__bodega').order_by('fecha_caducidad'))

    # Merge transf
    if not transf.empty and not mov.empty and not existencias_bodega_df.empty:
        existencias_bodega_df = existencias_bodega_df.rename(columns={'ubicacion__bodega':'bodega_exi'})        
        transf = transf.merge(existencias_bodega_df, on=['product_id','lote_id'], how='left').fillna('')
        
        mov_bodega_df = mov[['product_id','lote_id','ubicacion__bodega']].rename(columns={'ubicacion__bodega':'bodega_mov'})
        transf = transf.merge(mov_bodega_df, on=['product_id','lote_id'], how='left').fillna('')
        
        transf['primera_bodega'] = transf.apply(lambda x: x['bodega_exi'] if not x['bodega_mov'] else x['bodega_mov'], axis=1)
        transf = transf.sort_values(by='primera_bodega')
        
    transf_template = de_dataframe_a_template(transf)
    
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
    
    context = {
        'transf':transf_template,
        'n_transf':n_transf,
        'estado':estado.estado,
        'avance':estado.avance,
        'vol_max':transf['vol'].max()
    }
    return render(request, 'wms/transferencia_picking.html', context)



# Ingreso de transferencias a bodega Cerezos List
@login_required(login_url='login')
@permisos(['ADMINISTRADOR','OPERACIONES'], '/wms/home', 'ingresar una transferencia a Cerezos')
def wms_transferencia_ingreso_cerezos_list(request):
    
    transf_wms = pd.DataFrame(Transferencia.objects.all().values()).drop_duplicates(subset='n_transferencia')
    transf_wms = transf_wms[transf_wms['bodega_salida']!='BCT']
    if not transf_wms.empty:
        transf_wms = transf_wms.sort_values(by='fecha_hora', ascending=False)
        transf_wms['fecha_hora'] = pd.to_datetime(transf_wms['fecha_hora']).dt.strftime('%d-%m-%Y - %r').astype(str)
        #transf_wms = transf_wms.sort_values(by=['fecha_hora'], ascending=[False])

    transf_wms = de_dataframe_a_template(transf_wms)

    context = {
        'transf_wms':transf_wms
    }

    return render(request, 'wms/transferencia_ingreso_cerezos_list.html', context)


# Detalle de transferencia de ingreso a cerezos
@permisos(['ADMINISTRADOR','OPERACIONES'], '/wms/home', 'ingresar una transferencia a Cerezos')
def wms_transferencia_ingreso_cerezos_detalle(request, n_transferencia):
    
    transf = pd.DataFrame(Transferencia.objects.filter(n_transferencia=n_transferencia).values())
    prod = productos_odbc_and_django()[['product_id','Nombre','Marca']]
    transf = transf.merge(prod, on='product_id', how='left')
    transf['fecha_caducidad'] = transf['fecha_caducidad'].astype('str')
    transf = de_dataframe_a_template(transf)
    
    movs = Movimiento.objects.filter(n_referencia=n_transferencia)
    
    if movs.exists():
        estado = movs.last().estado

    else:
        estado = 'Sin estado'
    
    context={
        'transf':transf,
        'n_transferencia':n_transferencia,
        'estado':estado
    }
    return render(request, 'wms/transferencia_ingreso_cerezos_detalle.html', context)


def wms_transferencia_ingreso_cerezos_input_ajax(request):
    
    n_transf = request.POST['n_trasf']
    user     = int(request.POST['usuario'])
    
    transf  = Transferencia.objects.filter(n_transferencia=n_transf)
    
    for i in transf:
        
        ing = Movimiento(
            tipo            = 'Ingreso',
            unidades        = i.unidades,
            descripcion     = 'N/A',
            n_referencia    = i.n_transferencia,
            referencia      = 'Transferencia',
            usuario_id      = user,
            fecha_caducidad = i.fecha_caducidad,
            lote_id         = i.lote_id,
            product_id      = i.product_id,
            estado          = 'Cuarentena',
            ubicacion_id    = 606,
        )
        
        ing.save()
        wms_existencias_query_product_lote(product_id=ing.product_id, lote_id=ing.lote_id)
        
    if ing:
        
        return JsonResponse({
            'msg':{
                'tipo':'success',
                'texto':'Se agrego todos los productos al Inventario con estado Cuarentena !!!'
            }
        })
    
    else:
        return JsonResponse({
            'msg':{
                'tipo':'danger',
                'texto':'Error, intente nuevamente !!!'
            }
        })


# Liberar transferencia de cuarentena a disponible
def wms_transferencia_ingreso_cerezos_liberacion_ajax(request):
    
    n_transf = request.POST['n_trasf']
    user     = int(request.POST['usuario'])
    
    movs = Movimiento.objects.filter(n_referencia=n_transf).filter(estado='Cuarentena')
    estado = movs.last().estado
    
    if estado == 'Cuarentena': 
        
        for i in movs:
            lib_egreso = Movimiento(
                tipo            = 'Egreso',
                unidades        = i.unidades*-1,
                descripcion     = 'N/A',
                n_referencia    = i.n_referencia,
                referencia      = 'Liberación',
                usuario_id      = user,
                fecha_caducidad = i.fecha_caducidad,
                lote_id         = i.lote_id,
                product_id      = i.product_id,
                estado          = 'Cuarentena',
                ubicacion_id    = i.ubicacion.id,
            )
            
            lib_egreso.save()
            
            lib_ingreso = Movimiento(
                tipo            = 'Ingreso',
                unidades        = i.unidades,
                descripcion     = 'N/A',
                n_referencia    = i.n_referencia,
                referencia      = 'Liberación',
                usuario_id      = user,
                fecha_caducidad = i.fecha_caducidad,
                lote_id         = i.lote_id,
                product_id      = i.product_id,
                estado          = 'Disponible',
                ubicacion_id    = i.ubicacion.id,
            )
            
            lib_ingreso.save()
            wms_existencias_query_product_lote(product_id=lib_ingreso.product_id, lote_id=lib_ingreso.lote_id)
        
        if lib_ingreso:
            return JsonResponse({
            'msg':{
                'tipo':'success',
                'texto':'Transferencia Liberada !!!'
            }
        })
        
    else:
        return JsonResponse({
            'msg':{
                'tipo':'danger',
                'texto':'Producto en ya Disponible !!!'
            }
        })
    
    return JsonResponse({
            'msg':{
                'tipo':'danger',
                'texto':'Error !!!'
            }
        })


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
    est       = request.POST['estado']

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
                estado          = est, #'Disponible',
                estado_picking  = 'Despachado',
                usuario_id      = request.user.id,
            )

            transferencia.save()

            wms_existencias_query_product_lote(product_id=prod_id, lote_id=lote_id)
            wms_transferencias_estatus_transf(transferencia.n_referencia)

            return JsonResponse({'msg':f'✅ Producto {prod_id}, lote {lote_id} seleccionado correctamente !!!'})
        return JsonResponse({'msg':'❌ Error !!!'})
    return JsonResponse({'msg':'❌Error !!!'})


# LIBERACIONES JUAN
def wms_ingreso_ajuste(request):
    return render(request, 'wms/ingreso_ajuste.html', {'elementos': ''})



def wms_busqueda_ajuste(request, n_ajuste):

    user = request.user.id
    
    cnxn = pyodbc.connect('DSN=mba3;PWD=API')
    cursorOdbc = cnxn.cursor()
    

    # La variable 'n' no está siendo usada en la consulta. Asegúrate de que sea necesario.
    n = 'A-00000' + str(n_ajuste) + '-GIMPR'
    
    #Transferencia Egreso
    try:
        cursorOdbc.execute(
            "SELECT INVT_Producto_Lotes_Bodegas.Doc_id_Corp, "
            "INVT_Producto_Lotes_Bodegas.PRODUCT_ID_CORP, "
            "INVT_Producto_Lotes_Bodegas.LOTE_ID, "
            "INVT_Producto_Lotes_Bodegas.WARE_CODE, "
            "INVT_Producto_Lotes_Bodegas.LOCATION "
            "FROM INVT_Producto_Lotes_Bodegas "
            f"WHERE (INVT_Producto_Lotes_Bodegas.Doc_id_Corp='{n}') "
        )
        
        ajuste = [tuple(row) for row in cursorOdbc.fetchall()]

        ajuste_df = pd.DataFrame(ajuste, columns=['DOC_ID_CORP', 'PRODUCT_ID_CORP', 'LOTE_ID', 'WARE_CODE', 'LOCATION']) if ajuste else pd.DataFrame()
        print(ajuste_df)
        # Segunda consulta
        cursorOdbc.execute(
            "SELECT INVT_Lotes_Ubicacion.DOC_ID_CORP, INVT_Lotes_Ubicacion.PRODUCT_ID_CORP, INVT_Lotes_Ubicacion.LOTE_ID, "
            "INVT_Lotes_Ubicacion.EGRESO_TEMP, INVT_Lotes_Ubicacion.COMMITED, INVT_Lotes_Ubicacion.WARE_CODE_CORP, "
            "INVT_Lotes_Ubicacion.UBICACION, INVT_Producto_Lotes.Fecha_elaboracion_lote, INVT_Producto_Lotes.FECHA_CADUCIDAD "
            "FROM INVT_Lotes_Ubicacion, INVT_Producto_Lotes "
            "WHERE INVT_Lotes_Ubicacion.PRODUCT_ID_CORP = INVT_Producto_Lotes.PRODUCT_ID_CORP "
            "AND INVT_Producto_Lotes.LOTE_ID = INVT_Lotes_Ubicacion.LOTE_ID "
            f"AND ((INVT_Lotes_Ubicacion.DOC_ID_CORP='{n}') AND (INVT_Producto_Lotes.ENTRADA_TIPO='OC')) "
        )
        inventario = [tuple(row) for row in cursorOdbc.fetchall()]
        inventario_df = pd.DataFrame(inventario, columns=['DOC_ID_CORP', 'PRODUCT_ID_CORP', 'LOTE_ID', 'EGRESO_TEMP', 'COMMITED', 'WARE_CODE_CORP', 'UBICACION', 'Fecha_elaboracion_lote', 'FECHA_CADUCIDAD']) if inventario else pd.DataFrame()
        print(inventario_df)
        # Unión (merge) de los DataFrames en los campos comunes
        if not ajuste_df.empty and not inventario_df.empty:
            resultado_df = pd.merge(ajuste_df, inventario_df, on=['DOC_ID_CORP', 'PRODUCT_ID_CORP', 'LOTE_ID'], how='inner')
            resultado_df = resultado_df.drop_duplicates(subset=['DOC_ID_CORP', 'PRODUCT_ID_CORP', 'LOTE_ID'])
            
            if 'Fecha_elaboracion_lote' in resultado_df.columns:
                resultado_df['Fecha_elaboracion_lote'] = resultado_df['Fecha_elaboracion_lote'].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notnull(x) else x)
            if 'FECHA_CADUCIDAD' in resultado_df.columns:
                resultado_df['FECHA_CADUCIDAD'] = resultado_df['FECHA_CADUCIDAD'].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notnull(x) else x)
            print(resultado_df)
            #eliminar por DOC_ID_CORP
            LiberacionCuarentena.objects.filter(doc_id_corp = n ).delete(),
            

            #si ya existe un registro con los mismos datos en doc_id_corp, product_id_corp ,lote_id que lo actualize o cree
            #sino que lo cree
            
            for index, row in resultado_df.iterrows():
                #busca si existe el registro
                existe = LiberacionCuarentena.objects.filter(doc_id_corp = row['DOC_ID_CORP']).filter(product_id_corp = row['PRODUCT_ID_CORP']).filter(lote_id = row['LOTE_ID']).exists()
                if existe==False:
                    LiberacionCuarentena.objects.update_or_create(
                    #replace string
                    doc_id = n_ajuste,
                    doc_id_corp = row['DOC_ID_CORP'],
                    product_id_corp = row['PRODUCT_ID_CORP'],
                    product_id= row['PRODUCT_ID_CORP'].replace('-GIMPR',''),
                    lote_id = row['LOTE_ID'],
                    ware_code = row['WARE_CODE'],
                    location = row['LOCATION'],
                    egreso_temp = row['EGRESO_TEMP'],
                    commited = row['COMMITED'],
                    ware_code_corp = row['WARE_CODE_CORP'],
                    ubicacion = row['UBICACION'],
                    fecha_elaboracion_lote = row['Fecha_elaboracion_lote'],
                    fecha_caducidad = row['FECHA_CADUCIDAD'],
                    estado=0
                    )
                    #wms_get_existencias(row,n_ajuste,user)
                else:
                    if(existe.estado==0):
                        pass
                        #wms_get_existencias(row,n_ajuste,user)
                    
            # LiberacionCuarentena.objects.bulk_create(liberacion_cuarentena_objects)

            # Asegúrate de que las columnas de fecha estén en un formato de fecha reconocible
            # Si las columnas ya están en formato de fecha, no necesitas hacer nada más.
            # Si necesitas ajustar el formato, puedes hacerlo aquí.

            # Convertir DataFrame a JSON, asegurándose de que las fechas se formateen correctamente
            resultado_json = resultado_df.to_json(orient='records', force_ascii=False, date_format='iso')
        
            return HttpResponse(resultado_json, content_type='application/json')
        else:
            return JsonResponse({'error': 'No se encontraron datos para realizar la unión.'}, status=404)

    except Exception as e:
        print(e)
        return JsonResponse({'error': str(e)}, status=500)      



def wms_get_existencias(row,n_ajuste,user):
    try:
        existencia = Existencias.objects.filter(
            estado='Cuarentena',
            product_id=row['PRODUCT_ID_CORP'].replace('-GIMPR', ''),
            lote_id=row['LOTE_ID'],
            unidades__lte=row['COMMITED']
        ).get()

        print(existencia)
        #si tiene estado 0 
        wms_liberacion_cuarentena(existencia, n_ajuste, user ,row['COMMITED'])
    except ObjectDoesNotExist:
        print('no existe')
        # Maneja el caso de no existencia aquí
    except Exception as e:
        print(e)
        return JsonResponse({'error': str(e)}, status=500)
    
    
    
def wms_liberacion_cuarentena(existencia,n_referencia,user,cantidad):
    try:
        #crea un egreso en la tabla movimientos ejmpl: 
        Movimiento.objects.create(
            tipo='Egreso',
            unidades=cantidad * -1,
            descripcion='N/A',
            n_referencia=n_referencia,
            referencia='Liberación',
            product_id=existencia.product_id,
            lote_id=existencia.lote_id,
            fecha_caducidad=existencia.fecha_caducidad,
            estado='Cuarentena',
            estado_picking='',
            ubicacion_id=existencia.ubicacion.id,
            usuario_id=user,
            fecha_hora=datetime.now(),
            actualizado=datetime.now()
        )
        
        #crear un ingreso
        Movimiento.objects.create(
            tipo='Ingreso',
            unidades=cantidad,
            descripcion='N/A',
            n_referencia=n_referencia,
            referencia='Liberación',
            product_id=existencia.product_id,
            lote_id=existencia.lote_id,
            fecha_caducidad=existencia.fecha_caducidad,
            estado='Disponible',
            estado_picking='',
            #ubicacion_id=606,
            ubicacion_id=existencia.ubicacion.id,
            usuario_id=user,
            fecha_hora=datetime.now(),
            actualizado=datetime.now()
        )
        
        # #actualizar estado de LiberacionCuarentena a 1
        # Existencias.objects.filter(
        #     product_id=existencia.product_id,
        #     lote_id=existencia.lote_id,
        #     doc_id=n_referencia
        # ).update(estado=1)
        
        LiberacionCuarentena.objects.filter(
            product_id=existencia.product_id,
            lote_id=existencia.lote_id,
            doc_id=n_referencia
        ).update(estado=1)
        
        #actualizar wms_existencias_query_product_lote
        wms_existencias_query_product_lote(product_id=existencia.product_id, lote_id=existencia.lote_id)
        
    except ObjectDoesNotExist:
        print('no existe')
        # Maneja el caso de no existencia aquí
    except Exception as e:
        print(e)
        return JsonResponse({'error': str(e)}, status=500)


# Reporte de reposición
@login_required(login_url='login')
@permisos(['ADMINISTRADOR','OPERACIONES','BODEGA'],'/wms/home', 'ingresar a reporte repocición')
def wms_resposicion_rm(request):

    try:
        with connections['default'].cursor() as cursor:
            cursor.execute(
            "SELECT DISTINCT wms_existencias.product_id, count(wms_existencias.unidades) as count "
            "FROM wms_existencias left join wms_ubicacion on wms_existencias.ubicacion_id=wms_ubicacion.id "
            "where wms_ubicacion.bodega = 'CN6' AND wms_ubicacion.nivel>'1' group by wms_existencias.product_id;"
            )
            columns =  [col[0] for col in cursor.description]
            query5  = [dict(zip(columns, row)) for row in cursor.fetchall()]
            df_greater  = pd.DataFrame(query5)
            
        with connections['default'].cursor() as cursor:
            cursor.execute(        
            # "SELECT DISTINCT wms_existencias.product_id, count(wms_existencias.unidades) as count "    
            # "FROM wms_existencias left join wms_ubicacion on wms_existencias.ubicacion_id=wms_ubicacion.id " 
            # "where wms_ubicacion.bodega = 'CN6' AND wms_ubicacion.nivel='1' group by wms_existencias.product_id;"
            
            
            "Select T.product_id, T.lote_id, T.count from (SELECT * FROM wms_existencias as S JOIN "
            "(SELECT product_id as pro_id, MIN(fecha_caducidad) as min_fecha_caducidad, count(unidades) as count  from "
            "wms_existencias group by product_id) as U "
            "ON S.product_id=U.pro_id and S.fecha_caducidad=U.min_fecha_caducidad "
            "group by S.product_id order by S.product_id) as T "
            "LEFT JOIN wms_ubicacion as W on T.ubicacion_id=W.id WHERE W.bodega <>'CN6' "
            "UNION "
            "SELECT  wms_existencias.product_id, wms_existencias.lote_id, count(wms_existencias.unidades) as count "
            "FROM wms_existencias left join wms_ubicacion on wms_existencias.ubicacion_id=wms_ubicacion.id "
            "where wms_ubicacion.bodega = 'CN6' AND wms_ubicacion.nivel=1 group by wms_existencias.product_id;"
            )
            columns = [col[0] for col in cursor.description]
            query6  = [dict(zip(columns, row)) for row in cursor.fetchall()]
            df_equal  = pd.DataFrame(query6)
            
            df_non_match = pd.merge(df_greater, df_equal, how='outer', indicator=True, on='product_id')
            df_non_match = df_non_match[(df_non_match._merge == 'left_only')]
            df_non_match = de_dataframe_a_template(df_non_match)
            
            context = {
                'data': df_non_match,
            }
            
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        
    return render(request, 'wms/reporte_rm.html', context)


# Reporte de nivel uno vacio rm
@permisos(['ADMINISTRADOR','OPERACIONES','BODEGA'],'/wms/home', 'ingresar a reporte repocición')
def wms_reporte_nivelunovacio_rm(request):
    try:
        with connections['default'].cursor() as cursor:
            cursor.execute(
            "SELECT bodega, pasillo, modulo, nivel, count(nivel) as count " 
            "FROM wms_ubicacion left join wms_existencias on wms_ubicacion.id=wms_existencias.ubicacion_id " 
            "where wms_existencias.unidades IS null AND bodega='CN6' GROUP BY bodega, pasillo, modulo, nivel;" 
            )
            columns =  [col[0] for col in cursor.description]
            query   = [dict(zip(columns, row)) for row in cursor.fetchall()]
            df_free = pd.DataFrame(query)
            df_free = df_free[df_free['nivel'] == "1"]
            df_free_template = de_dataframe_a_template(df_free)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        context = {'reporte':df_free_template}
    return render(request, 'wms/reporte_nivelunovacio.html', context)


# Ingresar nota de entrega AJAX
def wms_nota_entrega_input_ajax(request):
    
    n_entrega = int(request.POST['nota_entrega'])
    
    ne_existente = NotaEntrega.objects.filter(doc_id=n_entrega)
    
    if ne_existente.exists():
        return JsonResponse({
                'msg':{
                    'type': 'warning',
                    'texto':'⚠ Nota de entrega ya añadida !!!'
                }
            })
        
    elif not ne_existente.exists():

        ne_datos = wms_datos_nota_entrega(n_entrega)
        try:
            for i in ne_datos:
                
                ne = NotaEntrega(
                    doc_id_corp     = i['doc_id_corp'],
                    doc_id          = i['doc_id'],
                    product_id      = i['product_id'],
                    lote_id         = i['lote_id'],
                    fecha_caducidad = i['fecha_caducidad'],
                    unidades        = i['unidades']
                )
            
                ne.save()
            
            if ne.id:
                NotaEntregaStatus.objects.create(
                    nota_entrega = ne.doc_id,
                    unidades_mba = 0,
                    unidades_wms = 0,
                    avance       = 0.0,
                    estado       = 'CREADO'
                )
                return JsonResponse({
                    'msg':{
                        'type': 'success',
                        'texto': f'✅ Nota de entrega {ne.doc_id} añadida exitosamente !!!'
                    }
                })
        except:
            return JsonResponse({
                'msg':{
                    'type': 'danger',
                    'texto':'❌ Error !!!'
                }
            })
    
    else:
        return JsonResponse({
                'msg':{
                    'type': 'danger',
                    'texto':'❌ Error !!!'
                }
            })


# Lisata de Notas de entrega 
@login_required(login_url='login')
@permisos(['OPERACIONES','BODEGA'], '/wms/home', 'ingresar notas de entrega')
def wms_nota_entrega_list(request):
    
    ne_list = pd.DataFrame(NotaEntrega.objects.all().values()).drop_duplicates(subset='doc_id', keep='last')
    ne_status = pd.DataFrame(NotaEntregaStatus.objects.all().values())
    ne_status = ne_status.rename(columns={'nota_entrega':'doc_id'})
    
    ne_list = ne_list.merge(ne_status, on='doc_id', how='left')
    
    if not ne_list.empty:
        ne_list = ne_list.sort_values(by='fecha_hora', ascending=False)
        ne_list['fecha_hora'] = pd.to_datetime(ne_list['fecha_hora']).dt.strftime('%d-%m-%Y - %r').astype(str)
        
        ne_list = de_dataframe_a_template(ne_list)
    
    context= {'ne_list':ne_list,}
    
    return render(request, 'wms/nota_entrega_list.html', context)


def wms_nota_entrega_estatus(nota_entrega):
    
    nentrega_mba = NotaEntrega.objects.filter(doc_id=nota_entrega)
    mba_total  = sum(nentrega_mba.values_list('unidades', flat=True))
    
    transf_wms = Movimiento.objects.filter(referencia='Nota de entrega').filter(n_referencia=nota_entrega)
    wms_total  = sum(transf_wms.values_list('unidades', flat=True))*-1
    
    avance_i = round(((wms_total / mba_total) * 100), 1)
    
    if wms_total == 0 or wms_total == None:
        estado_i = 'CREADO'
    elif wms_total < mba_total:
        estado_i = 'EN PROCESO'
    elif mba_total == wms_total or wms_total > mba_total:
        estado_i = 'FINALIZADO'    

    n_entrega_status = NotaEntregaStatus.objects.get(nota_entrega=nota_entrega)
    n_entrega_status.estado       = estado_i
    n_entrega_status.unidades_mba = mba_total
    n_entrega_status.unidades_wms = wms_total
    n_entrega_status.avance       = avance_i
    
    n_entrega_status.save()

    return JsonResponse({
        'msg':{
            'tipo':'success',
            'texto':f'✅ Transferencia {nota_entrega} actualizado !!!'
        }
    })
    
    
# Picking de nota de entrega
@login_required(login_url='login')
@permisos(['BODEGA'], '/wms/home', 'ingresar nota de entrega')
def wms_nota_entrega_picking(request, n_entrega):
    
    estado = NotaEntregaStatus.objects.get(nota_entrega=n_entrega)
    
    prod = productos_odbc_and_django()[['product_id','Nombre','Marca']]
    
    # Nota Entrega
    nota_entrega = pd.DataFrame(NotaEntrega.objects.filter(doc_id=n_entrega).values())
    nota_entrega = nota_entrega.merge(prod, on='product_id', how='left')
    nota_entrega['fecha_caducidad'] = pd.to_datetime(nota_entrega['fecha_caducidad']).dt.strftime('%d-%m-%Y').astype(str)
    
    # Movimientos
    mov = pd.DataFrame(Movimiento.objects.filter(n_referencia=n_entrega).values(
        'id',
        'product_id','lote_id','fecha_caducidad',
        'unidades','ubicacion__bodega','ubicacion__pasillo','ubicacion__modulo','ubicacion__nivel',
        'ubicacion__distancia_puerta'))
    
    if not mov.empty:
        mov['fecha_caducidad'] = pd.to_datetime(mov['fecha_caducidad']).dt.strftime('%d-%m-%Y')
        mov['unidades'] = mov['unidades'] * -1
        
    mov_list = de_dataframe_a_template(mov)
    
    # Si existe movimiento añadir al pedido
    if not mov.empty:
        mov_group = mov.groupby(by=['product_id','lote_id']).sum().reset_index()
        mov_group = mov_group.rename(columns={'unidades':'unidades_wms'})
        nota_entrega = nota_entrega.merge(mov_group, on=['product_id','lote_id'], how='left').fillna(0)
    
    # Ubicaciones de productos en nota entrega
    prod_lote = nota_entrega[['product_id','lote_id']].to_dict('records')
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
                
    nota_entrega_template = de_dataframe_a_template(nota_entrega)
    
    prod = list(nota_entrega['product_id'].unique())
    for i in prod:
        for j in nota_entrega_template:
            if j['product_id'] == i:
                j['ubi'] = ubi_list = []
                j['pik'] = pik_list = []
                for k in ext_id:
                    if k['product_id'] == i:
                        ubi_list.append(k)
                for m in mov_list:
                    if m['product_id'] == i:
                        pik_list.append(m)
    
    context = {
        'nota_entrega':nota_entrega_template,
        'n_entrega':n_entrega,
        'estado':estado.estado,
        'avance':estado.avance
    }
    
    return render(request, 'wms/nota_entrega_picking.html', context)


# Movimiento de egreso de Nota de entrega
def wms_movimiento_egreso_nota_entrega(request): #OK

    # Egreso
    unds_egreso = request.POST['unds']
    if not unds_egreso:
        unds_egreso = 0
        return JsonResponse({'msg':'❌ Error, ingrese una cantidad !!!'})
    else:
        unds_egreso = int(unds_egreso)
    
    n_entrega = request.POST['n_entrega']

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

    movimientos = Movimiento.objects.filter(product_id=prod_id).filter(n_referencia=n_entrega)

    if movimientos.exists():
        mov = pd.DataFrame(movimientos.values('product_id','unidades'))
        mov['unidades'] = pd.Series.abs(mov['unidades'])
        mov = mov[['product_id','unidades']].groupby(by='product_id').sum()
        mov = de_dataframe_a_template(mov)[0]
        total_mov = mov['unidades'] + unds_egreso
    else:
        total_mov = unds_egreso

    total_nota_entrega = sum(NotaEntrega.objects
        .filter(doc_id=n_entrega)
        .filter(product_id=prod_id).values_list('unidades',flat=True))

    if not existencia.exists():
        return JsonResponse({'msg':'❌ Error, revise las existencias o refresque la pagina !!!'})
    elif existencia.exists():
        if unds_egreso > existencia.last().unidades:
            return JsonResponse({'msg':'❌ No puede retirar más unidades de las existentes !!!'})
        elif unds_egreso == 0 or unds_egreso < 0:
            return JsonResponse({'msg':'❌ La cantidad debe ser mayor 0 !!!'})
        elif total_mov > total_nota_entrega:
            return JsonResponse({'msg':'❌ No puede retirar más unidades de las solicitadas en el Picking !!!'})
        elif total_mov <= total_nota_entrega:

            nota_entrega = Movimiento(
                product_id      = prod_id,
                lote_id         = lote_id,
                fecha_caducidad = caducidad,
                tipo            = 'Egreso',
                descripcion     = 'Nota de entrega',
                referencia      = 'Nota de entrega',
                n_referencia    = n_entrega,
                ubicacion_id    = ubi,
                unidades        = unds_egreso*-1,
                estado          = 'Disponible',
                estado_picking  = 'Despachado',
                usuario_id      = request.user.id,
            )

            nota_entrega.save()
            wms_existencias_query_product_lote(product_id=prod_id, lote_id=lote_id)
            wms_nota_entrega_estatus(nota_entrega.n_referencia)
            
            return JsonResponse({'msg':f'✅ Producto {prod_id}, lote {lote_id} seleccionado correctamente !!!'})
        return JsonResponse({'msg':'❌ Error !!!'})
    return JsonResponse({'msg':'❌Error !!!'})



## Anulación picking
@login_required(login_url='login')
@permisos(['ADMINISTRADOR','OPERACIONES','BODEGA'],'/wms/home', 'ingresar a anulación de picking')
def wms_anulacion_picking_list(request):
    
    anuladas = AnulacionPicking.objects.all().order_by('-fecha_hora')
    
    if request.method == 'POST':
        
        p_anulado = request.POST['p_anulado'] + '.0'
        p_nuevo   = request.POST['p_nuevo']   + '.0'
        
        try:
        
            pn = AnulacionPicking(
                picking_anulado = p_anulado,
                picking_nuevo   = p_nuevo,
                usuario_id      = request.user.id
            )
            
            pn.save()
            
            messages.success(request, f'Se añadio la anulación del picking {p_anulado}')
            
            return redirect('wms_anulacion_picking_list')
            
        except Exception as e:
            messages.error(request, e)
            
    context = {
        'anuladas':anuladas
    }
    
    return render(request, 'wms/anulacion_picking_crear.html', context)


# Anulación de picking detalle
@login_required(login_url='login')
@permisos(['ADMINISTRADOR','OPERACIONES','BODEGA'],'/wms/home', 'ingresar a anulación de picking')
def wms_anulacion_picking_detalle(request, id_anulacion):
    
    prod      = productos_odbc_and_django()[['product_id','Nombre','Marca']]
    anulacion = AnulacionPicking.objects.get(id=id_anulacion)
    
    try:
        cabecera  = EstadoPicking.objects.get(n_pedido=anulacion.picking_anulado)
    except:
        cabecera = EstadoPicking.objects.get(n_pedido=anulacion.picking_nuevo)
    
    if anulacion.estado == True:
        picking = anulacion.picking_nuevo
    else:
        picking = anulacion.picking_anulado
    
    
    movs = pd.DataFrame(Movimiento.objects.filter(n_referencia=picking)
                    .values('n_referencia','product_id','lote_id', 'unidades'))
    movs['Picking nuevo'] = anulacion.picking_nuevo
    movs['estado']        = anulacion.estado
    movs['unidades']      = movs['unidades'] *-1
    
    movs = movs.merge(prod, on='product_id', how='left')
    movs = de_dataframe_a_template(movs)
    
    context = {
        'cabecera':cabecera,
        'anulacion':anulacion,
        'movs':movs,
    }

    return render(request, 'wms/anulacion_picking_detalle.html', context)


## Anulación picking
def wms_anulacion_picking_ajax(request):
    
    id_anulacion = int(request.POST['id_anulacion'])
    anulacion = AnulacionPicking.objects.get(id=id_anulacion)
    
    movs = Movimiento.objects.filter(n_referencia=anulacion.picking_anulado)
    
    if movs.exists():
        
        # ACTUALIZAR NÚMERO DE PICKING EN TABLA ESTADO PICKING ETIQUETADO
        estado_picking = EstadoPicking.objects.get(n_pedido=anulacion.picking_anulado) 
        estado_picking.n_pedido = anulacion.picking_nuevo
        estado_picking.save()
        
        # ACTUALIZAR NÚMERO DE PICKING TABLA MOVIMIENTOS WMS
        movs.update(n_referencia=anulacion.picking_nuevo)
        anulacion.estado = True
        anulacion.save()
    
        return JsonResponse({
            'msg':{
                'tipo': 'success',
                'texto': f'✅ Se ha cambiado el picking {anulacion.picking_anulado} por {anulacion.picking_nuevo} !!!'
            }
        })
        
    else:
        return JsonResponse({
            'msg':{
                'tipo': 'error',
                'texto': f'❌ Error, intenta nuevamente !!!'
            }
        })



### Ajuste Liberación ERIK
@login_required(login_url='login')
@permisos(['ADMINISTRADOR','OPERACIONES'],'/wms/home', 'ingresar a ajuste liberaciones')
def wms_ajuste_liberacion_list(request):
    
    ajuste_liberacion = pd.DataFrame(AjusteLiberacion.objects.all().values().order_by('-doc_id')).drop_duplicates(subset=['doc_id'])
    ajuste_liberacion = de_dataframe_a_template(ajuste_liberacion)
    
    context = {
        'ajuste_liberacion':ajuste_liberacion
        }
    
    return render(request, 'wms/ajuste_liberacion_list.html', context)


def wms_ajuste_liberacion_input_ajax(request):
    
    tipo_liberacion = request.POST['tipo']
    n_liberacion = request.POST['n_liberacion']
    
    liberacion_data = wms_ajuste_query_odbc(n_liberacion)
    liberacion_data = liberacion_data[liberacion_data['EGRESO_TEMP']!=0]
    
    liberacion_data['doc_id'] = n_liberacion
    liberacion_data['tipo'] = tipo_liberacion
    liberacion_data['FECHA_CADUCIDAD'] = liberacion_data['FECHA_CADUCIDAD'].astype('str')
    liberacion_data = liberacion_data.rename(columns={'LOTE_ID':'lote_id'})
    
    existencias = pd.DataFrame(Existencias.objects.filter(estado='Cuarentena').values(
        'product_id', 'lote_id','unidades','ubicacion_id','estado'
    ))
    
    liberacion_data = liberacion_data.merge(existencias, on=['product_id','lote_id'], how='left')
    
    if liberacion_data['unidades'].isna().any():
        return JsonResponse({
            'msg':{
                'tipo': 'danger', 
                'texto': f'La liberación {n_liberacion} no hay productos en Cuarentena !!!'
            }
        })
    
    else:
    
        lib_data_list = []
        for i in de_dataframe_a_template(liberacion_data):
            
            lib_data = AjusteLiberacion(
                doc_id_corp     = i['DOC_ID_CORP'],
                doc_id          = i['doc_id'],
                tipo            = i['tipo'],
                product_id      = i['product_id'],
                lote_id         = i['lote_id'],
                ware_code       = i['WARE_CODE_CORP'],
                location        = i['UBICACION'],
                egreso_temp     = i['EGRESO_TEMP'],
                commited        = i['COMMITED'],
                fecha_caducidad = i['FECHA_CADUCIDAD'],
                
                unidades_cuc    = i['unidades'],
                ubicacion_id    = i['ubicacion_id'], 
                estado          = i['estado']
            )
            
            lib_data_list.append(lib_data)
        
        lib_data_exist = AjusteLiberacion.objects.filter(doc_id=n_liberacion).exists()
        
        if lib_data_exist:
        
            return JsonResponse({
                'msg':{
                    'tipo': 'danger', 
                    'texto': f'La liberación {n_liberacion} ya fue ingresada !!!'
                }
            })
        
        else:
            # Add liberación
            AjusteLiberacion.objects.bulk_create(lib_data_list)
            return JsonResponse({
                'msg':{
                    'tipo': 'success', 
                    'texto': f'La liberación {n_liberacion} ingresada exitosamente !!!'
                }
            })


@permisos(['ADMINISTRADOR','OPERACIONES'],'/wms/home', 'ingresar a ajuste liberaciones')
def wms_ajuste_liberacion_detalle(request, n_liberacion):
    
    prod = productos_odbc_and_django()[['product_id','Nombre','Marca']]
    ubi  = pd.DataFrame(Ubicacion.objects.filter(disponible=True).values())
    ubi  = ubi.rename(columns={'id':'ubicacion_id'})
    
    ajuste = pd.DataFrame(AjusteLiberacion.objects.filter(doc_id=n_liberacion).values())
    ajuste['fecha_caducidad'] = ajuste['fecha_caducidad'].astype('str')
    ajuste = ajuste.merge(prod, on='product_id', how='left')[[
        'tipo','product_id','lote_id','fecha_caducidad','egreso_temp','estado','ubicacion_id', 'unidades_cuc',
    ]]
    
    ajuste = ajuste.merge(prod, on='product_id', how='left')
    ajuste = ajuste.merge(ubi, on='ubicacion_id', how='left')

    ajuste['ubicacion_liberacion'] = ajuste.apply(
        lambda x: '606' if x['tipo'] == 'Liberación Acondicionamiento' else x['ubicacion_id'], axis=1
    )
    
    ajuste['unidades_cuc'] = ajuste.apply(
        lambda x: x['egreso_temp'] if x['tipo'] == 'Liberación Acondicionamiento' else x['unidades_cuc'], axis=1
    )
    
    tipo = ajuste.iloc[0]['tipo']
    estado = ajuste.iloc[0]['estado']
    
    ajuste = de_dataframe_a_template(ajuste)
    
    if request.method == 'POST':
        for i in ajuste:
            mov_eg = Movimiento(
                tipo            = 'Egreso',
                unidades        = int(i['unidades_cuc']) *-1,
                descripcion     = 'N/A' ,
                n_referencia    = n_liberacion,
                referencia      = 'Liberación',
                usuario_id      = int(request.user.id),
                fecha_caducidad = i['fecha_caducidad'],
                lote_id         = i['lote_id'],
                product_id      = i['product_id'],
                estado          = 'Cuarentena',
                ubicacion_id    = int(i['ubicacion_id']),
            )
            mov_eg.save()
            
            mov_in = Movimiento(
                tipo            = 'Ingreso',
                unidades        = int(i['unidades_cuc']),
                descripcion     = 'N/A' ,
                n_referencia    = n_liberacion,
                referencia      = 'Liberación',
                usuario_id      = int(request.user.id),
                fecha_caducidad = i['fecha_caducidad'],
                lote_id         = i['lote_id'],
                product_id      = i['product_id'],
                estado          = 'Disponible',
                ubicacion_id    = int(i['ubicacion_liberacion']),
            )
            mov_in.save()
            
            wms_existencias_query_product_lote(product_id=mov_in.product_id, lote_id=mov_in.lote_id)
            
        AjusteLiberacion.objects.filter(doc_id=n_liberacion).update(estado='Liberado')
    
        return HttpResponseRedirect(f'/wms/ajuste-liberacion/detalle/{n_liberacion}') 
    
    context = {
        'ajuste':ajuste,
        'n_liberacion':n_liberacion,
        'tipo':tipo,
        'estado':estado
    }

    return render(request, 'wms/ajuste_liberacion_detalle.html', context)


### Regresar productos en despacho al inventario
@login_required(login_url='login')
@permisos(['ADMINISTRADOR','OPERACIONES'],'/wms/home', 'ingresar a retiro de productos en despacho')
def wms_retiro_producto_despacho(request):

    if request.method == 'POST':
        n_picking = request.POST['n_picking'] + '.0' 
        estado_picking = EstadoPicking.objects.filter(n_pedido=n_picking)
        
        if not estado_picking.exists():
            messages.error(request, f"No se encontró el Picking {request.POST['n_picking']}")
            
        elif estado_picking.exists():
            estado = estado_picking.last().estado
            bodega = estado_picking.last().bodega
            
            if bodega == 'BAN':
                messages.error(request, f"El Picking {request.POST['n_picking']} esta en bodega Andagoya")
                
            elif bodega == 'BCT':
                if estado == 'FINALIZADO':
                    picking = Movimiento.objects.filter(n_referencia=n_picking).filter(estado_picking='En Despacho')
                    
                    context = {
                        'picking':picking,
                        'cabecera':estado_picking.last()
                        }
                    
                    return render(request, 'wms/retiro_producto_despacho_list.html', context)
                
                else:
                    messages.error(request, f"El Picking {request.POST['n_picking']} su esta es {estado}")
    
    return render(request, 'wms/retiro_producto_despacho_list.html', {})


@permisos(['ADMINISTRADOR','OPERACIONES'],'/wms/home', 'ingresar a retiro de productos en despacho')
def wms_retiro_producto_despacho_ajax(request):
    
    id_mov = int(request.POST['id']) 
    
    mov = Movimiento.objects.get(id=id_mov)
    
    mov_ing = Movimiento(
        product_id      = mov.product_id,
        lote_id         = mov.lote_id,
        fecha_caducidad = mov.fecha_caducidad,
        tipo            = 'Ingreso',
        descripcion     = mov.descripcion,
        referencia      = 'Reverso de picking',
        n_referencia    = mov.n_referencia,
        n_factura       = '',
        ubicacion_id    = 605,
        unidades        = (mov.unidades)*-1,
        estado          = mov.estado,
        estado_picking  = '',
        usuario_id      = request.user.id
    )
    
    # Nuevo registro de ingreso
    mov_ing.save()
    
    # Cambio de estado al registro de egreso picking
    mov.estado_picking = 'No Despachado'
    mov.save()
    
    wms_existencias_query_product_lote(product_id=mov.product_id, lote_id=mov.lote_id)
    
    return JsonResponse({
        'tipo':'success',
        'msg':f'Las {(mov.unidades*-1)} unidades del producto {mov.product_id} - {mov.lote_id} regreso a la ubicación CN6-G-1'
        })


# MODULO UBICACIÓNES DISPONIBLES Y NO DISPONIBLES
@permisos(['ADMINISTRADOR','OPERACIONES', 'BODEGA'],'/wms/home', 'ingresar a ubicaciones')
def wms_ubicaciones_list(request):    
    
    capacidad = de_dataframe_a_template(capacidad_de_bodegas_df())
    en_despacho = de_dataframe_a_template(en_despacho_df())
    
    context = {
        'capacidad':capacidad,
        'en_despacho':en_despacho
    }
    
    return render(request, 'wms/ubicaciones_list.html', context)


# HABILITAR O DESHABILITAR UBICACIÓN
@permisos(['ADMINISTRADOR','OPERACIONES','BODEGA'],'/wms/home', 'ingresar a ubicaciones')
def wms_habilitar_deshabilitar_ubicacion_ajax(request):
    
    if request.method == 'GET':
        ubicacion_get_id = request.GET.get('ubicacion')
        ubicacion = Ubicacion.objects.get(id=int(ubicacion_get_id))
        existencias = Existencias.objects.filter(ubicacion_id=ubicacion_get_id)
        
        if existencias.exists():
            existencias_list = existencias.values_list('product_id', flat=True)
            existencias_list = ' - '.join([str(i) for i in existencias_list])
        else:
            existencias_list = ''
        
        return JsonResponse({
            'tipo':'success', 
            #'msg':'No se puede realizar esta acción por medio de',
            'ubicacion':ubicacion.__str__(),
            'disponible':ubicacion.disponible,
            'observaciones':ubicacion.observaciones,
            'existencias':existencias.exists(),
            'existencias_list':existencias_list,
            })
        
    if request.method == 'POST':
        ubicacion_post_id = request.POST.get('ubicacion_get_id')
        ubicacion = Ubicacion.objects.get(id=int(ubicacion_post_id))
        #existencias = Existencias.objects.filter(ubicacion_id=ubicacion_post_id)
        
        # Data POST
        disponible = request.POST.get('disponible')
        observaciones = request.POST.get('observaciones')
        
        # SI NO HAY EXISTENCIAS SI SE PUEDE DESHABILITAR
        if disponible:
            # Habilitar 
            time = datetime.now().strftime('%Y-%m-%d %H:%M')
            ubicacion.disponible = True
            ubicacion.observaciones = f"""---------------------\nHABILITADA\n{request.user.first_name} {request.user.last_name} - {time}\n{observaciones}"""
            ubicacion.save()
            messages.success(request, f'Habilito exitosamente la ubicación: {ubicacion}!!!')
            return redirect('wms_ubicaciones_list')
        
        else:
            # Deshabilitar
            time = datetime.now().strftime('%Y-%m-%d %H:%M')
            ubicacion.disponible = False
            ubicacion.observaciones = f"""---------------------\nDESHABILITADA\n{request.user.first_name} {request.user.last_name} - {time}\n{observaciones}"""
            ubicacion.save()
            messages.success(request, f'Deshabilito exitosamente la ubicación: {ubicacion}!!!')
            return redirect('wms_ubicaciones_list')


@permisos(['ADMINISTRADOR','OPERACIONES','BODEGA'],'/wms/home', 'ingresar a ubicaciones')
def wms_reporte_reposicion(request):
    
    existencias_query = Existencias.objects.all()
    products = existencias_query.values_list('product_id', flat=True).distinct()
    
    productos_reporte = []
    for i in products:
        existencia = existencias_query.filter(product_id=i).order_by('fecha_caducidad', 'ubicacion__nivel')
        existencia_mas_proxima = existencia.first()
        
        if existencia_mas_proxima.ubicacion.nivel != '1':
            productos_reporte.append(existencia_mas_proxima)

    context = {
        'productos_reporte':productos_reporte,
    }
    
    return render(request, 'wms/reporte_reposicion.html', context)


@permisos(['ADMINISTRADOR','OPERACIONES','BODEGA'],'/wms/home', 'ingresar a reporte')
def wms_reporte_bodegas457(request):
    
    products = Existencias.objects.all().values_list('product_id', flat=True).distinct()
    
    products_list_final = []    
    for i in products:
        existencia = Existencias.objects.filter(
            product_id=i,
            ubicacion__bodega__in = ['CN4','CN5','CN7']
        ).order_by('fecha_caducidad', 'lote_id')
        
        if existencia.exists():
            products_list_final.append(existencia.first().id)
    
    df = pd.DataFrame(Existencias.objects.filter(id__in = products_list_final).values(
        'product_id','lote_id','fecha_caducidad','ubicacion__bodega', 'unidades',
        'ubicacion__pasillo','ubicacion__modulo','ubicacion__nivel'
    ))
    
    products = productos_odbc_and_django()[['product_id','Nombre','Marca']]
    
    if not df.empty:
        df = pd.merge(df, products, on='product_id', how='left')
        df['fecha_caducidad'] = df['fecha_caducidad'].astype('str')
        productos_reporte = de_dataframe_a_template(df)

    context = {
        'productos_reporte':productos_reporte,
    }
    
    return render(request, 'wms/reporte_bod457.html', context)



@permisos(['ADMINISTRADOR','OPERACIONES','BODEGA'],'/wms/home', 'ingresar a ubicaciones')
def wms_reporte_reposicion_alertas(request):    
    
    ventas = frecuancia_ventas()
    productos_ventas = ventas['PRODUCT_ID'].unique()
    
    reporte_existencias_list = []
    for i in productos_ventas:
        existencias_by_product = Existencias.objects.filter(product_id=i).order_by('fecha_caducidad', 'lote_id', 'ubicacion__bodega', 'ubicacion__nivel')
        
        if len(existencias_by_product) > 1:
                        
            producto_uno = existencias_by_product[0]
            #producto_dos = existencias_by_product[1]            
            
            total_unidades_nivel_uno_query = existencias_by_product.filter(
                Q(ubicacion__nivel='1') & 
                Q(lote_id=producto_uno.lote_id)
                )
            
            if total_unidades_nivel_uno_query.exists():
                total_unidades_nivel_uno = total_unidades_nivel_uno_query.aggregate(unidades_nivel_uno=Sum('unidades'))['unidades_nivel_uno']
            else:
                total_unidades_nivel_uno = 0
            
            
            suma_iteracion = 0
            for j in existencias_by_product:
                suma_iteracion += j.unidades
                if suma_iteracion > total_unidades_nivel_uno:
                    producto_dos = j
                    break
            
            ventas_product_mensual = ventas.loc[ventas['PRODUCT_ID']==i, 'ANUAL'].values[0] / 12
            producto_uno_alerta_mensual = round(total_unidades_nivel_uno / ventas_product_mensual, 1)
            
            if producto_uno_alerta_mensual <= 1.5 and producto_dos.ubicacion.nivel != '1':
                
                product = {
                    'product_id':producto_uno.product_id,
                    'lote_id':producto_uno.lote_id,
                    'fecha_caducidad': producto_uno.fecha_caducidad,
                    'ubicacion':producto_uno.ubicacion.nombre_completo,
                    'total_unidades_nivel_uno':total_unidades_nivel_uno,
                    'ventas_product_mensual':ventas_product_mensual,
                    'unidades':producto_uno.unidades,
                    'meses':producto_uno_alerta_mensual,
                }
        
                reporte_existencias_list.append(product)
        
    reporte_existencias_df = pd.DataFrame(reporte_existencias_list)
    
    if not reporte_existencias_df.empty:
        productos = productos_odbc_and_django()[['product_id','Nombre','Marca']]
        reporte = reporte_existencias_df.merge(productos, on='product_id', how='left').sort_values(by='meses')
        reporte['fecha_caducidad'] = reporte['fecha_caducidad'].astype('str')
    
    context = {
        'reporte':de_dataframe_a_template(reporte),
    }
    
    return render(request, 'wms/reporte_reposicion_alertas.html', context)


def wms_movimiento_grupal(request):
    
    context = {
        
    }
    
    return render(request, 'wms/movimiento_grupal.html', context)


def wms_movimiento_grupal_get_ubi_list_ajax(request):

    bodega  = request.POST['bodega']
    pasillo = request.POST['pasillo']
    #ubi_salida = int(request.POST['ubi_salida'])

    ubi_list = pd.DataFrame(Ubicacion.objects
        .filter(disponible=True)
        .filter(bodega=bodega)
        .filter(pasillo=pasillo)
        #.exclude(id=ubi_salida)
        .values()
        ).sort_values(by=['bodega','pasillo','modulo','nivel'])

    ubi_list = de_dataframe_a_template(ubi_list)

    return JsonResponse({'ubi_list':ubi_list}, status=200)


def wms_movimiento_grupal_ubicacion_salida_ajax(request):

    ubi_salida = int(request.POST['ubi_salida'])
    ubi = Ubicacion.objects.get(id=ubi_salida)
    #ubicaciones_destino = Ubicacion.objects.exclude(id=ubi.id).values()
    existencia_ubi_salida = pd.DataFrame(Existencias.objects.filter(ubicacion_id=ubi_salida).values())

    if not existencia_ubi_salida.empty:
        existencia_ubi_salida = existencia_ubi_salida[[
            'id', 
            'product_id', 
            'lote_id', 
            'unidades',
            'ubicacion_id'
        ]]
        
        rows_html = []
        
        for index, row in existencia_ubi_salida.iterrows():
            
            row_tr = f"""
                <tr>
                    <td>{row['product_id']}</td>
                    <td>{row['lote_id']}</td>
                    <td class="text-end">{row['unidades']}</td>
                    <td class="text-center" id="tr-inputs">
                        <input id="id_mover" type="checkbox" class="form-check-input">
                        <input id="id_existencia" type="hidden" value="{row['id']}">
                        <input id="id_ubicacion" type="hidden" value="{row['ubicacion_id']}">
                    </td>
                </tr>
            """
            rows_html.append(row_tr)
        
        table = f"""
        <table border="1" style="font-size:small" class="table table-responsive table-bordered m-0 p-0" id="existencias">
            <thead>
                <tr>
                    <th>Código</th>
                    <th>Lote</th>
                    <th>Unidades</th>
                    <th>Mover</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows_html)}
            </tbody>
        </table>
        """        
        
        return JsonResponse({
            'exitencias':table,
            'msg':f'⚠ Existencias en ubicación {ubi} !!!',
            'type':'warning',
            #'ubicaciones_destino':ubicaciones_destino
            })

    else:
        return JsonResponse({
            'msg':f'✅ Posición {ubi} vacia !!!',
            'type':'success'
        })
