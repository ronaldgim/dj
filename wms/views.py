from django.shortcuts import render, redirect 

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from utils.warehouse_data import get_vendedor_email_by_contrato

# PDF
from django_xhtml2pdf.utils import pdf_decorator

# Pedidos por clientes
from etiquetado.views import pedido_por_cliente, reservas_table

# Http
from django.http import HttpResponse,JsonResponse, HttpResponseRedirect

# Json
import json

# Datetime
from datetime import datetime

# DB
from django.db import connections, transaction
from django.db.models import Q, Sum, OuterRef, Subquery


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
    DespachoCarton,
    ProductoArmado,
    OrdenEmpaque,
    FacturaAnulada,
    ImportacionFotos,
    CostoImportacion,
    OrdenSalida
    )

from warehouse.models import Cliente

from django.core.exceptions import ObjectDoesNotExist

# excel 
from openpyxl.styles import Font, Alignment

# Pandas y Numpy
import pandas as pd
import numpy as np

# Forms
from wms.forms import (
    MovimientosForm, 
    DespachoCartonForm,
    ProductoNuevoArmadoForm,
    OrdenEmpaqueForm,
    OrdenEmpaqueUpdateForm,
    ComponenteArmadoForm,
    ProductoNuevoArmadoUpdateForm,
    FacturaAnuladaForm,
    ImportacionFotosForm,
    OrdenSalidaForm
    )

# Messages
from django.contrib import messages

# Models
from users.models import User, UserPerfil
from etiquetado.models import EstadoPicking, ProductoUbicacion
from datos.models import Reservas

# Login
from django.contrib.auth.decorators import login_required #, permission_required

# Email
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings

# Paginado
from django.core.paginator import Paginator
from django.core.files.base import ContentFile

# PDF
from django_xhtml2pdf.utils import pisa #pdf_decorator

# datos api_mba
from api_mba.tablas_warehouse import api_actualizar_imp_transito_warehouse

# Utils
from utils.warehouse_data import productos_mba_django

# BYTES
import io

from warehouse.models import Producto

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

    # api transferencias mba
    transferencias_mba,
    
    # Ajuste Datos
    wms_ajuste_query_api,
    
    # Permisos costum @decorador
    permisos,
    
    # Fecuencia de ventas
    frecuancia_ventas
    )

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
    #existencias = existencias.groupby(by=['ubicacion_id']).sum().reset_index()    
    
    existencias = existencias.groupby(by='ubicacion_id').agg({
        'unidades': 'sum',
        'ocupacion_posicion_m3': 'sum',
    }).reset_index()
    
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
    
    capacidad = capacidad.replace(np.inf, 0)
    
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
    capacidad = capacidad.groupby(by=['bodega']).sum().reset_index()[[
        'bodega','capacidad_posicion_m3','ocupacion_posicion_m3','disponible_posicion_m3'
        ]]
    #capacidad['ocupacion_posicion_m3_dif'] = capacidad['ocupacion_posicion_m3'] * 0.025
    #print(capacidad[capacidad['bodega']=='CN6'])
    
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
    disponible[-1] = disponible[-1] - despacho[-1] 
    
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
    ) #.exclude(n_referencia='2234-GIMPR-OC')
    )
    
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
@permisos(['ADMINISTRADOR','OPERACIONES', 'BODEGA'], '/wms/home', 'Importaciones ingresadas')
def wms_imp_ingresadas(request): #OK
    """ Lista de importaciones ingresadas """
    
    prod = productos_odbc_and_django()[['product_id','Marca', 'MarcaDet']]
    imps = pd.DataFrame(
        InventarioIngresoBodega.objects
        .filter(referencia='Ingreso Importación')
        .values()).sort_values(by='fecha_hora',ascending=False
    )
    imps['fecha_hora'] = pd.to_datetime(imps['fecha_hora']).dt.strftime('%Y-%m-%d')
    
    imps_llegadas = importaciones_llegadas_odbc()[['DOC_ID_CORP','MEMO', 'ENTRADA_FECHA']] 
    imps_llegadas = imps_llegadas.rename(columns={'DOC_ID_CORP':'n_referencia'}).drop_duplicates(subset='n_referencia')
    imps_llegadas['ENTRADA_FECHA'] = imps_llegadas['ENTRADA_FECHA'].astype('str')
    
    imps = imps.merge(imps_llegadas, on='n_referencia', how='left') 
    
    imp_fotos = pd.DataFrame(ImportacionFotos.objects.all().values()).drop_duplicates(subset='importacion')
    if not imp_fotos.empty:
        imps = pd.merge(left=imps, right=imp_fotos, left_on='MEMO', right_on='importacion', how='left')

    if not imps.empty:
        imps = imps.merge(prod, on='product_id', how='left')
        imps = imps.drop_duplicates(subset='n_referencia') 
        imps = de_dataframe_a_template(imps)
    
    # imps['ENTRADA_FECHA'] = imps['ENTRADA_FECHA'].astype('str')
    # imps['fecha_hora'] = imps['fecha_hora'].astype('str')
    
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
    imp['LOTE_ID'] = imp['LOTE_ID'].str.replace('.', '')
    
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
    
    prod = productos_odbc_and_django()[['product_id', 'Marca','UnidadesPorPallet']]
    prod = prod.rename(columns={'product_id':'PRODUCT_ID'}) 
    
    imp_transito = importaciones_en_transito_odbc() 
    imp_transito['FECHA_ENTREGA'] = pd.to_datetime(imp_transito['FECHA_ENTREGA']).dt.strftime('%Y-%m-%d')
    imp_transito = imp_transito.sort_values(by='FECHA_ENTREGA', ascending=True)
    imp_transito = imp_transito.merge(prod, on='PRODUCT_ID',how='left')
    
    imps_contratos = []
    imps_total_pallets = []
    imps_incompleto = []
    for i in imp_transito['CONTRATO_ID'].unique():
        imp_contrato = imp_transito[imp_transito['CONTRATO_ID']==i]
        # imp_contrato = imp_contrato.merge(prod, on='PRODUCT_ID',how='left')
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
    
    fotos_importacion = pd.DataFrame(ImportacionFotos.objects.all().values('importacion')).drop_duplicates()
    if not fotos_importacion.empty:
        imp_transito = imp_transito.merge(fotos_importacion, left_on='MEMO', right_on='importacion', how='left')
    imp_transito = de_dataframe_a_template(imp_transito)
    
    if request.method == 'POST':
        api_actualizar_imp_transito_warehouse()
        return redirect('wms_importaciones_transito_list')
        
    context = {
        'imp_transito':imp_transito
    }
    
    return render(request, 'wms/importaciones_transito_list.html', context)


# Detalle de importación en transito
@login_required(login_url='login')
@permisos(['ADMINISTRADOR','OPERACIONES','BODEGA'], '/wms/home', 'Importaciones en tránsito')
def wms_importaciones_transito_detalle(request, contrato_id):
    
    prod = productos_odbc_and_django()[['product_id','Nombre','Marca','Unidad_Empaque','UnidadesPorPallet','Volumen']]
    prod = prod.fillna(0)
    
    imp_transito = importaciones_en_transito_detalle_odbc(contrato_id)   
    imp_transito = imp_transito.rename(columns={'PRODUCT_ID':'product_id'})
    
    imp_transito =  imp_transito.merge(prod, on='product_id', how='left')
    
    imp_transito['cartones'] = imp_transito['QUANTITY'] / imp_transito['Unidad_Empaque']
    imp_transito['vol_m3'] = imp_transito['cartones'] * (imp_transito['Volumen'] / 1000000)
    imp_transito['pallets'] = imp_transito['QUANTITY'] / imp_transito['UnidadesPorPallet']
    imp_transito = imp_transito.replace(np.inf, 0)
    
    unidades_total = imp_transito['QUANTITY'].sum()
    cartones_total = imp_transito['cartones'].sum()
    vol_m3_total   = imp_transito['vol_m3'].sum()
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
        'vol_m3_total':vol_m3_total,
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


@login_required(login_url='login')
def wms_importacion_fotos(request, importacion:str, proveedor:str= None, marca:str= None):
    fotos = ImportacionFotos.objects.filter(importacion=importacion).order_by('-id')
    
    if request.method == 'POST':
        form = ImportacionFotosForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Foto agregada exitosamente !!!')
            return HttpResponseRedirect(f'/wms/importaciones/fotos/{importacion}/{proveedor}/{marca}')
        else:
            messages.error(request, form.errors)
        
    context = {
        'importacion': importacion,
        'proveedor':proveedor,
        'marca':marca,
        'fotos':fotos
        }
    return render(request, 'wms/importacion_fotos.html', context)


@login_required(login_url='login')
def wms_importacion_foto_delete(request, id):
    
    try:
        if request.method == 'POST':
            ImportacionFotos.objects.filter(id=id).delete()
            return JsonResponse({
                'success':True,
                'msg':'Foto eliminada correctamente !!!'
            })
    except Exception as e:
        return JsonResponse({
                'success':False,
                'msg':f'Error: {e}'
            })
        

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
    
    try:

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
        #     print(i.id, i.product_id, i.lote_id, i.fecha_caducidad, i.ubicacion_id, i.unidades, i.estado)
        
        Existencias.objects.filter(product_id=product_id, lote_id=lote_id).delete()
        Existencias.objects.bulk_create(existencias_list)
        
        return exitencias

    except Exception as e:
        print(str(e))
        for i in existencias_list:
            print(i.id, i.product_id, i.lote_id, i.fecha_caducidad, i.ubicacion_id, i.unidades, i.estado)
        return HttpResponse(f'{e}')



# def recalcular_existencias_fun():
#     existencias = Existencias.objects.all()
#     for i in existencias:
#         prod = i.product_id
#         lot  = i.lote_id
        
#         print(prod, lot)
#         wms_existencias_query_product_lote(prod, lot)


# def recalcular_existencias(request):
#     recalcular_existencias_fun()
#     return HttpResponse('recalculado')


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
    # wms_existencias_query_product_lote("10-160-24","3325224M")    
    
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
        
        # inv_detalle = pd.DataFrame(ex).groupby(by=['estado','product_id','lote_id','fecha_caducidad']).sum().reset_index().sort_values(by='fecha_caducidad')
        inv_detalle = pd.DataFrame(ex).groupby(by=['estado','product_id','lote_id','fecha_caducidad']).agg({'unidades':'sum'}).reset_index().sort_values(by='fecha_caducidad')
        
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
        recipient_list = ['dreyes@gimpromed.com','jgualotuna@gimpromed.com'],
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
        
        existencia_ubi_destino = existencia_ubi_destino.rename(columns={
            'product_id':'Código',
            'lote_id':'Lote',
            'unidades':'Unidades',
            'cartones':'Cartones'
            })
        
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
def comprobar_ajuste_egreso(codigo, lote, estado, fecha_cadu, ubicacion, und_egreso): #OK

    ext = (
    Existencias.objects
        .filter(product_id=codigo)
        .filter(lote_id=lote)
        .filter(estado=estado)
        .filter(fecha_caducidad=fecha_cadu)
        .filter(ubicacion_id=ubicacion)
        )
    
    if ext.exists():
        total = ext.last().unidades - und_egreso
        if total >= 0: 
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
                estado     = request.POST['estado'],
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
    # mov = Movimiento.objects.select_related(
    #     'ubicacion', 'usuario'
    # ).order_by('-fecha_hora', '-id')
    
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
# @login_required(login_url='login')
# @permisos(['ADMINISTRADOR','OPERACIONES','BODEGA'], '/wms/home', 'ingrear a Listado de Pedidos')
# def wms_listado_pedidos(request): #OK
#     """ Listado de pedidos (picking) """
#     pedidos = pd.DataFrame(reservas_table()) 
#     pedidos = pedidos[pedidos['WARE_CODE']=='BCT']
#     pedidos['FECHA_PEDIDO'] = pedidos['FECHA_PEDIDO'].astype(str)
#     pedidos = pedidos.drop_duplicates(subset='CONTRATO_ID')
    
#     estados = pd.DataFrame(EstadoPicking.objects.all().values('n_pedido','estado','user__user__first_name','user__user__last_name'))
#     estados = estados.rename(columns={'n_pedido':'CONTRATO_ID'})
#     pedidos = pedidos.merge(estados, on='CONTRATO_ID', how='left')

#     pedidos = de_dataframe_a_template(pedidos)

#     context = {
#         'reservas':pedidos
#     }

#     return render(request, 'wms/listado_pedidos.html', context)


@login_required(login_url='login')
@permisos(['ADMINISTRADOR','OPERACIONES','BODEGA'], '/wms/home', 'ingrear a Listado de Pedidos')
def wms_listado_pedidos(request): #OK
    """ Listado de pedidos (picking) """

    # clientes = clientes_warehouse()[['CODIGO_CLIENTE','NOMBRE_CLIENTE']]
    # clientes = clientes.rename(columns={'CODIGO_CLIENTE':'codigo_cliente'})
    
    # mis_reservas = Reservas.objects.filter(ware_code='BCT').order_by('-fecha_pedido', '-hora_llegada')
    
    # pedidos = pd.DataFrame(       
    #     mis_reservas.values('contrato_id', 'codigo_cliente', 'ware_code', 'fecha_pedido', 'hora_llegada')
    # )
    # pedidos['contrato_id'] = pedidos['contrato_id'] + '.0'
    # pedidos = pedidos.drop_duplicates(subset='contrato_id', keep='first').reset_index(drop=True)
    # pedidos['fecha_pedido'] = pedidos['fecha_pedido'].astype(str)
    # pedidos = pedidos.merge(clientes, on='codigo_cliente', how='left')
    
    # estados = pd.DataFrame(EstadoPicking.objects.all().values('n_pedido','estado','user__user__first_name','user__user__last_name'))
    # estados = estados.rename(columns={'n_pedido':'contrato_id'})
    # pedidos = pedidos.merge(estados, on='contrato_id', how='left')

    # pedidos = de_dataframe_a_template(pedidos)[:200]
    
    q_reserva = request.GET.get('n_pedido', None)    
    query = (
        Reservas.objects
        .filter(ware_code='BCT')
        .values(
            'contrato_id',
            'codigo_cliente',
            'fecha_pedido',
            'hora_llegada',
            'ware_code'
        )
        .order_by('-contrato_id')
        .distinct()
    )

    if q_reserva:
        query = query.filter(contrato_id=q_reserva)

    query = query[:150]

    reservas = list(query)
    
    contratos = [f'{r['contrato_id']}.0' for r in reservas]

    estados = (
        EstadoPicking.objects
        .filter(n_pedido__in=contratos)
        .select_related('user__user')
    )

    estado_map = {e.n_pedido: e for e in estados}
    codigos_cliente = {r['codigo_cliente'] for r in reservas}
    
    clientes = {
        c.codigo_cliente: c.nombre_cliente
        for c in Cliente.objects
            .using('gimpromed_sql')
            .filter(codigo_cliente__in=codigos_cliente)
    }

    datos_pedidos = []
    for r in reservas:
        estado = estado_map.get(f'{r['contrato_id']}.0')
        datos_pedidos.append({
            'contrato_id': r['contrato_id'],
            'cliente': clientes.get(r['codigo_cliente']),
            'bodega': 'Cerezos', #if r['ware_code'] == 'BCT' else 'Andagoya',
            'fecha_hora': f"{r['fecha_pedido']} - {r['hora_llegada']}",
            'estado': estado.estado if estado else None,
            'usuario': (
                f"{estado.user.user.first_name} {estado.user.user.last_name}"
                if estado and estado.user and estado.user.user
                else None
            ),
        })
    
    context = {
        'reservas': datos_pedidos #pedidos
    }

    return render(request, 'wms/listado_pedidos_misreservas.html', context)


def wms_picking_notificaciones(request):
    
    pickings = EstadoPicking.objects.filter(
        Q(bodega='BCT') &
        Q(estado='FINALIZADO')
    # ).order_by('-id', 'n_pedido')[:100] #.values() email_picking_fecha_hora
    ).order_by('-email_picking_fecha_hora')[:100] #.values() 
    
    
    pedidos = []
    for i in pickings:
        data = {
            'cliente':i.cliente,
            'estado':i.estado,
            'pedido':i.n_pedido.split('.')[0],
            'send_email':'<i class="bi bi-check-circle-fill" style="color:green"></i>' if i.email_picking_send else '<i class="bi bi-x-circle-fill" style="color:red"></i>',
            'fecha_email':i.email_picking_fecha_hora.strftime('%Y-%m-%d %H:%M:%S') if i.email_picking_fecha_hora else '-',
            'error_email':i.email_picking_errors if i.email_picking_errors else '-',
        }
        pedidos.append(data)
    
    return JsonResponse({
        'pedidos':pedidos
    })


@login_required(login_url='login')
@permisos(['ADMINISTRADOR','OPERACIONES'], '/picking/list', 'ingresar a Detalle de Pedido')
def wms_detalle_misreservas(request, contrato_id):
    
    estado = EstadoPicking.objects.filter(n_pedido=contrato_id)
    
    if estado.exists():
        estado = estado.first()
    else:
        estado = ''
    
    contrato_id_int = contrato_id.split('.')[0]
    reserva = Reservas.objects.filter(contrato_id=contrato_id_int)
    contrato = pd.DataFrame(reserva.values(
        'id', 'product_id','codigo_cliente','contrato_id','quantity','ware_code','confirmed',
        'fecha_pedido','hora_llegada','sec_name_cliente','alterado','usuario__first_name','usuario__last_name'
    ))
    clientes = clientes_warehouse()[['CODIGO_CLIENTE','NOMBRE_CLIENTE','CIUDAD_PRINCIPAL']]
    clientes = clientes.rename(columns={'CODIGO_CLIENTE':'codigo_cliente'})
    productos = productos_odbc_and_django()[['product_id','Nombre','Marca']]
    
    contrato = contrato.merge(clientes, on='codigo_cliente', how='left')
    contrato = contrato.merge(productos, on='product_id', how='left') 
    contrato['fecha_pedido'] = contrato['fecha_pedido'].astype('str') 
    contrato = de_dataframe_a_template(contrato)
    
    if request.method == "POST":
        codigo = request.POST.get('codigo')
        unidades = request.POST.get('quantity')
        Reservas.objects.create(
            contrato_id = reserva.first().contrato_id,
            codigo_cliente = reserva.first().codigo_cliente,
            product_id = codigo,
            quantity = int(unidades),
            ware_code = reserva.first().ware_code,
            confirmed = reserva.first().confirmed,
            fecha_pedido = reserva.first().fecha_pedido,
            hora_llegada = reserva.first().hora_llegada,
            sec_name_cliente = '',
            unique_id = None,
            alterado = True,
            usuario_id = request.user.id
        )
        return HttpResponseRedirect(f'/wms/picking/misreservas/{contrato_id_int}')
    
    context = {
        'estado':estado,
        'cabecera':contrato[0],
        'contrato':contrato,
        'productos':de_dataframe_a_template(productos)
    }
    
    return render(request, 'wms/detalle_misreservas.html', context)


@login_required(login_url='login')
def wms_detalle_misreservas_edit_ajax(request):
    
    try:
        
        unidades = request.POST.get('unidades')
        id = request.POST.get('id')
        
        row = Reservas.objects.get(id=id)
        row.quantity = int(unidades)
        row.usuario_id = request.user.id
        row.alterado = True
        row.save()
        
        return JsonResponse({
            'type':'success',
            'msg': f'Producto {row.product_id} editado exitosamente !!!'
        })
    except:
        return JsonResponse({
            'type':'danger',
            'msg': f'Error al editar el producto {row.product_id} !!!'
        })


@login_required(login_url='login')
def wms_detalle_misreservas_delete_ajax(request):
    
    try:
        id = request.POST.get('id')
        row = Reservas.objects.get(id=id)
        row.delete()
        
        return JsonResponse({
            'type':'success',
            'msg': f'Producto {row.product_id} eliminado exitosamente !!!'
        })
    except:
        return JsonResponse({
            'type':'danger',
            'msg': f'Error al eliminar el producto {row.product_id} !!!'
        })


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
        foto = est.foto_picking
        foto_2 = est.foto_picking_2
    else:
        estado = 'SIN ESTADO'
        estado_id = ''
        foto = ''
        foto_2 = ''

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
        'estado_id':estado_id,
        'foto':foto,
        'foto_2':foto_2
    }

    return render(request, 'wms/picking.html', context)


# Detalle de pedido
# url: picking/<n_pedido>
@login_required(login_url='login')
@permisos(['ADMINISTRADOR','OPERACIONES','BODEGA'], '/picking/list', 'ingresar a Detalle de Pedido')
def wms_egreso_picking_misreservas(request, n_pedido): #OK
    
    estado_picking = EstadoPicking.objects.filter(n_pedido=n_pedido).exists()
    if estado_picking:
        est = EstadoPicking.objects.get(n_pedido=n_pedido)
        estado = est.estado
        estado_id = est.id
        foto = est.foto_picking
        foto_2 = est.foto_picking_2
    else:
        estado = 'SIN ESTADO'
        estado_id = ''
        foto = ''
        foto_2 = ''

    prod   = productos_odbc_and_django()[['product_id','Nombre','Marca','Unidad_Empaque']]
    #prod   = prod.rename(columns={'product_id':'PRODUCT_ID'})
    
    # pedido = pedido_por_cliente(n_pedido).sort_values('PRODUCT_ID')
    contrato_id = n_pedido.split('.')[0]
    pedido = pd.DataFrame(Reservas.objects.filter(ware_code='BCT').filter(contrato_id=contrato_id).values())
    
    # pedido = pedido.groupby(by=['CONTRATO_ID','CODIGO_CLIENTE','NOMBRE_CLIENTE','FECHA_PEDIDO','HORA_LLEGADA','PRODUCT_ID','PRODUCT_NAME']).sum().reset_index()
    pedido = pedido.groupby(by=['contrato_id','codigo_cliente','product_id'])['quantity'].sum().reset_index()
    # pedido = pedido.merge(prod, on='PRODUCT_ID',how='left')
    pedido = pedido.merge(prod, on='product_id',how='left')
    
    
    # cli    = clientes_warehouse()[['CODIGO_CLIENTE','CIUDAD_PRINCIPAL']]
    # pedido = pedido.merge(cli, on='CODIGO_CLIENTE', how='left')

    cli    = clientes_warehouse()[['CODIGO_CLIENTE','CIUDAD_PRINCIPAL', 'NOMBRE_CLIENTE']]
    cli    = cli.rename(columns={'CODIGO_CLIENTE':'codigo_cliente'})
    # pedido = pedido.merge(cli, on='CODIGO_CLIENTE', how='left')
    pedido = pedido.merge(cli, on='codigo_cliente', how='left')
    

    # prod_list = list(pedido['PRODUCT_ID'].unique())
    prod_list = list(pedido['product_id'].unique())
    
    movimientos = Movimiento.objects.filter(referencia='Picking').filter(n_referencia=n_pedido)
    
    if movimientos.exists():
        mov = pd.DataFrame(movimientos.values(
            'id','product_id','lote_id','fecha_caducidad','tipo','unidades',
            'ubicacion_id','ubicacion__bodega','ubicacion__pasillo','ubicacion__modulo','ubicacion__nivel'
        ))

        mov['fecha_caducidad'] = mov['fecha_caducidad'].astype(str)
        mov['unidades'] = pd.Series.abs(mov['unidades'])

        unds_pickeadas = mov[['product_id','unidades']].groupby(by='product_id').sum().reset_index()
        # unds_pickeadas = unds_pickeadas.rename(columns={'product_id':'PRODUCT_ID'})
        # pedido = pedido.merge(unds_pickeadas, on='PRODUCT_ID', how='left')
        pedido = pedido.merge(unds_pickeadas, on='product_id', how='left')
        mov = de_dataframe_a_template(mov)

    else:
        mov = {}

    # Inventario
    inv = Existencias.objects.filter(product_id__in=prod_list).values(
        'product_id','lote_id','fecha_caducidad','unidades',
        'ubicacion_id','ubicacion__bodega','ubicacion__pasillo','ubicacion__modulo','ubicacion__nivel',
        'ubicacion__distancia_puerta',
        #'unidades',
        'estado'
    )#.order_by('ubicacion__nivel')

    mov_bodega_df = pd.DataFrame(movimientos.order_by('fecha_caducidad').values('product_id', 'ubicacion__bodega'))
    mov_bodega_df = mov_bodega_df.rename(columns={'ubicacion__bodega':'bodega_mov'})
    mov_bodega_df = mov_bodega_df.drop_duplicates(subset='product_id', keep='first').fillna('')
    
    exi_bodega_df = pd.DataFrame(inv.order_by('fecha_caducidad'))#[['product_id','ubicacion__bodega']]
    exi_bodega_df = exi_bodega_df.rename(columns={'ubicacion__bodega':'bodega_exi'})
    exi_bodega_df = exi_bodega_df.drop_duplicates(subset='product_id', keep='first').fillna('')
    
    if not mov_bodega_df.empty and not exi_bodega_df.empty:
        bodega_df = exi_bodega_df.merge(mov_bodega_df, on='product_id', how='left').fillna('')
        bodega_df['primera_bodega'] = bodega_df.apply(lambda x: x['bodega_exi'] if not x['bodega_mov'] else x['bodega_mov'], axis=1)       
        #bodega_df = bodega_df.rename(columns={'product_id':'PRODUCT_ID'})[['PRODUCT_ID','primera_bodega']]
        bodega_df = bodega_df[['product_id','primera_bodega']]
        #bodega_df = bodega_df[['PRODUCT_ID','primera_bodega']]
        #bodega_df = bodega_df.rename(columns={'PRODUCT_ID':'product_id'})
        
    elif not mov_bodega_df.empty and exi_bodega_df.empty:
        bodega_df = mov_bodega_df
        bodega_df['primera_bodega'] = ''
    else:
        bodega_df = exi_bodega_df
        bodega_df['bodega_mov'] = ''
        bodega_df['primera_bodega'] = ''
    
    # bodega_df['primera_bodega'] = bodega_df.apply(lambda x: x['bodega_exi'] if not x['bodega_mov'] else x['bodega_mov'], axis=1)       
    # bodega_df = bodega_df.rename(columns={'product_id':'PRODUCT_ID'})[['PRODUCT_ID','primera_bodega']]
    # bodega_df = bodega_df[['product_id','primera_bodega']]
    
    if inv.exists():
        inv = pd.DataFrame(inv).sort_values(by=['lote_id','fecha_caducidad','ubicacion__nivel'], ascending=[True,True,True])
        inv['fecha_caducidad'] = inv['fecha_caducidad'].astype(str)

        r_lote = wms_reservas_lotes_datos()
        if not r_lote.empty:
            inv = inv.merge(r_lote, on=['product_id','lote_id'], how='left')
            inv = de_dataframe_a_template(inv)
    else:
        inv = {}

    # Calculo Cartones
    # pedido['cartones'] = pedido['QUANTITY'] / pedido['Unidad_Empaque']
    pedido['cartones'] = pedido['quantity'] / pedido['Unidad_Empaque']  
    # pedido = pedido.merge(bodega_df, on='PRODUCT_ID', how='left').sort_values(by='primera_bodega')
    try:
        pedido = pedido.merge(bodega_df, on='product_id', how='left').sort_values(by='primera_bodega') 
    except:
        pedido = pedido #pedido.merge(bodega_df, on='product_id', how='left') #.sort_values(by='primera_bodega')
    ped = de_dataframe_a_template(pedido)

    for i in prod_list:
        for j in ped:
            # if j['PRODUCT_ID'] == i:
            if j['product_id'] == i:  
                j['ubi'] = ubi_list = []
                j['pik'] = pik_list = []
                for k in inv:
                    if k['product_id'] == i:
                        ubi_list.append(k)
                for m in mov:
                    if m['product_id'] == i:
                        pik_list.append(m)
    
    cabecera = Reservas.objects.filter(contrato_id=contrato_id).first()
    
    context = {
        'cabecera':cabecera,
        'n_ped':cabecera.contrato_id + '.0',
        'cli':ped[0],
        'pedido':ped,
        'estado':estado,
        'estado_id':estado_id,
        'foto':foto,
        'foto_2':foto_2
    }

    return render(request, 'wms/picking_misreservas.html', context)


# Estado Picking AJAX
@permisos(['BODEGA'], '/wms/picking/list', 'cambio de estado de picking')
def wms_estado_picking_ajax(request):

    contrato_id = request.POST['n_ped'] 
    # contrato = contrato_id.split(',')[0]
    estado = request.POST['estado']
    user_id = int(request.POST['user_id'])
    user_perfil_id   = UserPerfil.objects.get(user__id=user_id).id

    reserva = wms_reserva_por_contratoid(contrato_id) #;print(reserva)
    cli     = clientes_warehouse()[['CODIGO_CLIENTE','CLIENT_TYPE']] #; print(cli)
    reserva = reserva.merge(cli, on='CODIGO_CLIENTE', how='left') #; print(reserva)
    
    cliente        = reserva['NOMBRE_CLIENTE'].iloc[0]
    fecha_pedido   = reserva['FECHA_PEDIDO'].iloc[0]
    tipo_cliente   = reserva['CLIENT_TYPE'].iloc[0]
    bodega         = reserva['WARE_CODE'].iloc[0]
    codigo_cliente = reserva['CODIGO_CLIENTE'].iloc[0]
    data           = (reserva[['PRODUCT_ID', 'QUANTITY']]).to_dict() ;print(data)
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
            return JsonResponse({
                'msg':f'✅ Estado de picking {estado_picking.estado}',
                'alert':'success'
            })
    except Exception as e:
        # print(e)
        return JsonResponse({
            'msg':f'❌ Error, {e} !!!',
            'alert':'danger'
        })


## Agregar foto a picking
def wms_agregar_foto_picking_ajax(request):
    
    id_picking = request.POST.get('id_picking')
    foto = request.FILES.get("foto")
    foto2 = request.FILES.get("foto2")

    try:
    
        picking = EstadoPicking.objects.get(id=id_picking)
        picking.foto_picking = foto
        if foto2 is not None:
            picking.foto_picking_2 = foto2
        
        picking.save()
        
        return JsonResponse({
            "alert":"success",
            "msg":"Foto agregada correctamente"
        })

    except:
        return JsonResponse({
            "alert":"danger",
            "msg":"Error al subir la foto"
        })


def reservas_lote_n_picking(n_picking): #request
    ''' Colusta de clientes por ruc a la base de datos '''
    
    try:
        # pk = n_picking.split('.')[0]
        with connections['gimpromed_sql'].cursor() as cursor:
            cursor.execute(f"SELECT PRODUCT_ID, LOTE_ID, EGRESO_TEMP FROM reservas_lote_2 WHERE CONTRATO_ID = '{n_picking}'")        
            columns = [col[0].lower() for col in cursor.description]
            reservas_lote = [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]
            reservas_lote = pd.DataFrame(reservas_lote)  
            reservas_lote['lote_id'] = reservas_lote['lote_id'].str.replace('.', '')
            reservas_lote = reservas_lote.groupby(by=['product_id','lote_id'])['egreso_temp'].sum().reset_index()
            
            return reservas_lote
    except:
        reservas_lote = pd.DataFrame()
        reservas_lote['product_id'] = ''
        reservas_lote['lote_id'] = ''
        reservas_lote['egreso_temp'] = 0
        return reservas_lote


def ciudad_principal_cliente(codigo_cliente):
    try:
        with connections['gimpromed_sql'].cursor() as cursor:
            cursor.execute(f"SELECT CIUDAD_PRINCIPAL FROM warehouse.clientes WHERE CODIGO_CLIENTE = '{codigo_cliente}';")
            columns = [col[0] for col in cursor.description]
            ciudad = [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ][0]       
        return ciudad['CIUDAD_PRINCIPAL']
    except:
        return '-'


def wms_correo_picking(n_pedido):
    
    n_pedido_int = n_pedido.split('.')[0]
    # try:
    #     data_wms = pd.DataFrame(Movimiento.objects.filter(n_referencia=n_pedido).values('product_id', 'lote_id', 'unidades'))  
    #     data_wms['lote_id'] = data_wms['lote_id'].str.replace('.', '')
    #     data_wms['unidades_wms'] = data_wms['unidades'] *-1
    #     data_wms['lote_wms'] = data_wms['lote_id']
    #     data_wms = data_wms.groupby(by=['product_id','lote_id','lote_wms'])['unidades_wms'].sum().reset_index()
        
    #     data_mba = reservas_lote_n_picking(n_pedido_int)
    #     data_mba['lote_mba'] = data_mba['lote_id']
    #     data_mba = data_mba.fillna('-')
        
    #     # data = data_wms.merge(data_mba, on=['product_id','lote_id'], how='outer')
    #     data =  pd.merge(left=data_wms, right=data_mba, on=['product_id','lote_id'], how='outer').fillna('-')
    #     data['unidades_wms'] = data['unidades_wms'].astype('int')
    #     data['egreso_temp'] = data['egreso_temp'].astype('int')
    #     data['revision_lotes'] = data['lote_wms'] == data['lote_mba']
    #     data['revision_unidades'] = data['unidades_wms'] == data['egreso_temp']
    #     data['revision'] = data['revision_lotes'] == data['revision_unidades']
        
    #     prods = productos_odbc_and_django()[['product_id', 'Nombre', 'Marca']]
    #     data = data.merge(prods, on='product_id', how='left') 
    #     data = de_dataframe_a_template(data)
    # except Exception as e:
    #     data = {}
    
    try:
        # --- Cargar datos desde WMS ---
        data_wms = pd.DataFrame(
            Movimiento.objects.filter(n_referencia=n_pedido)
            .values("product_id", "lote_id", "unidades")
        )

        if not data_wms.empty:
            data_wms["lote_id"] = data_wms["lote_id"].astype(str).str.replace(".", "", regex=False)
            data_wms["unidades_wms"] = data_wms["unidades"] * -1
            # Agrupación por producto y lote
            data_wms = (
                data_wms.groupby(["product_id", "lote_id"], as_index=False)["unidades_wms"]
                .sum()
            )
            data_wms["lote_wms"] = data_wms["lote_id"]

        # --- Cargar datos desde MBA ---
        data_mba = reservas_lote_n_picking(n_pedido_int).copy()
        data_mba["lote_mba"] = data_mba["lote_id"]
        data_mba = data_mba.fillna("-")

        # --- Merge de WMS y MBA ---
        data = pd.merge(
            left=data_wms,
            right=data_mba,
            on=["product_id", "lote_id"],
            how="outer"
        ).fillna("-")

        # Conversión segura de tipos
        data["unidades_wms"] = pd.to_numeric(data["unidades_wms"], errors="coerce").fillna(0).astype(int)
        data["egreso_temp"] = pd.to_numeric(data["egreso_temp"], errors="coerce").fillna(0).astype(int)

        # --- Validaciones ---
        data["revision_lotes"] = data["lote_wms"] == data["lote_mba"]
        data["revision_unidades"] = data["unidades_wms"] == data["egreso_temp"]
        data["revision"] = data["revision_lotes"] & data["revision_unidades"]

        # --- Enriquecer con datos de productos ---
        prods = productos_odbc_and_django()[["product_id", "Nombre", "Marca"]]
        data = data.merge(prods, on="product_id", how="left")

        # --- Convertir para template ---
        data = de_dataframe_a_template(data)

    except Exception as e:
        # logger.error(f"Error procesando pedido {n_pedido}: {e}", exc_info=True)
        data_error_str = str(e)
        data = {}

    try:
        lista_correos = [
            'egarces@gimpromed.com',
            'bcerezos@gimpromed.com',
            'ncastillo@gimpromed.com',
            'jgualotuna@gimpromed.com',
            get_vendedor_email_by_contrato(n_pedido_int)[0]
        ]
        
        picking = EstadoPicking.objects.get(n_pedido=n_pedido)
        ciudad = ciudad_principal_cliente(picking.codigo_cliente)
        
        hostipitales = [
            'CLI00015',  # CLI00015   HOSPITAL EUGENIO ESPEJO
            'CLI00125',  # CLI00125   HOSPITAL JOSE CARRASCO ARETEAGA
            'CLI01205'   # CLI01205   HOSPITAL PROVINCIAL GENERAL DOCENTE RIOBAMBA
        ]
        
        if picking.codigo_cliente in hostipitales:
            lista_correos += ['Dtrujillo@gimpromed.com']
        
        context = {
            'picking': picking,
            'data': data,
            'ciudad':ciudad
        }
        
        html_message = render_to_string('emails/picking.html', context)
        plain_message = strip_tags(html_message)
        
        email = EmailMultiAlternatives(
            subject=f'Cerezos-Picking Finalizado - {picking.cliente}',
            from_email=settings.EMAIL_HOST_USER,
            body=plain_message,
            to=lista_correos
        )
        email.attach_alternative(html_message, 'text/html')
        email.attach_file(picking.foto_picking.path)
        
        if picking.foto_picking_2:
            email.attach_file(picking.foto_picking_2.path)
        email.send()
        
        picking.email_picking_send = True
        picking.email_picking_fecha_hora = datetime.now()
        picking.email_picking_errors = f'Data error: {data_error_str}' if not data else ''
        picking.save()
    except Exception as e:
        picking.email_picking_fecha_hora = datetime.now()
        picking.email_picking_errors = f'Data error !!! ; {str(e)}'  if not data else str(e)
        picking.save()


# Actualizar Estado Picking AJAX
@permisos(['BODEGA'], '/wms/picking/list', 'cambio de estado de picking')
def wms_estado_picking_actualizar_ajax(request):

    id_picking = int(request.POST['id_picking'])
    estado_post = request.POST['estado']
    estado_picking = EstadoPicking.objects.get(id=id_picking)
    
    contrato_id = estado_picking.n_pedido
    contrato_id = contrato_id.split('.')[0]   
        
    if estado_picking.bodega == 'BCT':
    
        pedido = Reservas.objects.filter(contrato_id=contrato_id)
        data = list(pedido.values('product_id', 'quantity'))
        data   = json.dumps(data)
        estado_picking.detalle = data
        estado_picking.save()
        
    elif estado_picking.bodega == 'BAN':
        pedido = pedido_por_cliente(n_pedido=estado_picking.n_pedido) 
        data   = (pedido[['PRODUCT_ID', 'QUANTITY']]).to_dict()
        data   = json.dumps(data)
        estado_picking.detalle = data
        estado_picking.save()

    if estado_post == 'FINALIZADO':
        
        data_reservas = Reservas.objects.filter(contrato_id=contrato_id).values_list('quantity', flat=True)
        movs = Movimiento.objects.filter(n_referencia=estado_picking.n_pedido, estado_picking='En Despacho').values_list('unidades', flat=True)
        # movs = Movimiento.objects.filter(n_referencia=estado_picking.n_pedido).values_list('unidades', flat=True)
        
        movs_total_unidades = sum(movs) * -1  
        data_reservas_total_unidades = sum(data_reservas) 
        if estado_picking.bodega == 'BCT':
            
            if movs_total_unidades < data_reservas_total_unidades: #pick_total_unidades:
                return JsonResponse({
                    'msg':' ⚠ Aun no a completado el picking !!!',
                    'alert':'warning'
                })
                
            elif movs_total_unidades != data_reservas_total_unidades: #pick_total_unidades: 
                return JsonResponse({
                    # 'msg':f' ⚠ El total de items de WMS {movs_total_unidades} es diferente al total de items MBA {pick_total_unidades} !!!',
                    'msg':f' ⚠ El total de items de WMS {movs_total_unidades} es diferente al total de items MBA {data_reservas_total_unidades} !!!',
                    'alert':'warning'
                })
            
            elif not estado_picking.foto_picking:
                return JsonResponse({
                    'msg':' ⚠ Agrega la foto del picking !!!',
                    'alert':'warning'
                })
            
            # elif pick_total_unidades == movs_total_unidades:
            elif data_reservas_total_unidades == movs_total_unidades:
                
                estado_picking.estado = estado_post
                estado_picking.fecha_actualizado = datetime.now()

                try:
                    estado_picking.save()
                    wms_correo_picking(estado_picking.n_pedido)
                    if estado_picking.id:
                        return JsonResponse({'msg':f'✅ Estado de picking {estado_picking.estado}',
                                        'alert':'success'}, status=200)
                except Exception as e:
                    return JsonResponse({'msg':f'❌ Exception, {e} !!!',
                                        'alert':'danger'})
        
        elif estado_picking.bodega == 'BAN':
            
            estado_picking.estado = estado_post
            estado_picking.fecha_actualizado = datetime.now()

            try:
                estado_picking.save()

                if estado_picking.id:
                    return JsonResponse({'msg':f'✅ Estado de picking {estado_picking.estado}',
                                    'alert':'success'}, status=200)
            except Exception as e:
                return JsonResponse({'msg': f'❌ Exception, {e} !!!',
                                    'alert':'danger'})
            
    else:
            estado_picking.estado = estado_post
            estado_picking.fecha_actualizado = datetime.now()

            try:
                estado_picking.save()

                if estado_picking.id:
                    return JsonResponse({'msg':f'✅ Estado de picking {estado_picking.estado}',
                                    'alert':'success'}, status=200)
            except Exception as e:
                return JsonResponse({'msg': f'❌ Exception, {e} !!!',
                                    'alert':'danger'})


# Actualizar Estado Picking AJAX
@permisos(['BODEGA'], '/wms/picking/list', 'cambio de estado de picking')
def wms_actualizar_picking_ajax(request):

    n_ped = request.POST['n_ped']
    picking = EstadoPicking.objects.get(n_pedido=n_ped)
    
    picking.estado = 'EN PROCESO'
    picking.fecha_actualizado = datetime.now()
    picking.foto_picking = None
    if picking.foto_picking_2:
        picking.foto_picking_2= None
    
    picking.save()
    
    return JsonResponse({
        'msg':f' ⚠ El picking esta nuevamente EN PROCESO !!!',
        'alert':'warning'
    })


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

    # pedido = pedido_por_cliente(n_picking)
    # pedido = pedido[pedido['PRODUCT_ID']==prod_id][['PRODUCT_ID','QUANTITY']]#.reset_index()
    # pedido = pedido.groupby(by='PRODUCT_ID').sum().to_dict('records')[0]
    # total_pedido = pedido['quantity']

    contrato_id = n_picking.split('.')[0]
    pedido = Reservas.objects.filter(
        Q (contrato_id=contrato_id) &
        Q (product_id = prod_id)
        ).values_list('quantity', flat=True)
    total_pedido = sum(pedido)

    if not existencia.exists():
        return JsonResponse({'msg':'❌ Error, revise las existencias o refresque la pagina !!!'})
    elif existencia.exists():
        if unds_egreso > existencia.last().unidades:
            return JsonResponse({'msg':'❌ No puede retirar más unidades de las existentes !!!'})
        elif unds_egreso == 0 or unds_egreso < 0:
            return JsonResponse({'msg':'❌ La cantidad debe ser mayor 0 !!!'})
        elif total_mov > total_pedido: #check
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
    en_despacho = en_despacho.drop_duplicates(subset='n_referencia', keep='last') 
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
            picking = picking.groupby(by=['product_id','lote_id','estado_picking','lote_wms'])['unidades'].sum().reset_index() 
            
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


def facturas_df():
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute("SELECT NOMBRE_CLIENTE, NUMERO_PEDIDO_SISTEMA FROM warehouse.facturas")
        columns = [col[0] for col in cursor.description]
        facturas = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
        facturas_df = pd.DataFrame( facturas )
        facturas_df['NUMERO_PEDIDO_SISTEMA'] = facturas_df['NUMERO_PEDIDO_SISTEMA'].astype('str')
        facturas_df = facturas_df.drop_duplicates(subset='NUMERO_PEDIDO_SISTEMA')
        return facturas_df


# Cruce de picking y factura
# url: 'wms/cruce/picking/facturas'
@login_required(login_url='login')
@permisos(['BODEGA'], '/wms/home', 'ingresar a cruce de picking-factura')
def wms_cruce_picking_factura(request):

    # Picking y facturas
    picking_factura = Movimiento.objects.filter(
        Q(referencia='Picking') &
        Q(estado_picking='Despachado')
    )
    
    picking_factura_df = pd.DataFrame(picking_factura.values(
        'referencia',
        'n_referencia',
        'n_factura',
        'fecha_hora',
        'actualizado',
        'usuario__first_name',
        'usuario__last_name',
        )).drop_duplicates(subset='n_referencia').sort_values(by='n_referencia', ascending=False)
    picking_factura_df['picking'] = picking_factura_df['n_referencia'].str.slice(0,-2)
    picking_factura_df['factura'] = picking_factura_df['n_factura'].apply(split_factura_movimiento)
    picking_factura_df['actualizado'] = picking_factura_df['actualizado'].astype('str').str.slice(0,16)

    picking_factura_df = picking_factura_df.merge(
        facturas_df(),
        left_on='picking',
        right_on='NUMERO_PEDIDO_SISTEMA',
        how='left'
    )[:100]

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
    context = {
        'picking_factura_df': de_dataframe_a_template(picking_factura_df),
    }
    return render(request, 'wms/cruce_picking_factura.html', context)

@login_required(login_url='login')
def nueva_orden_salida(request, n_factura):
    
    n_factura_mba = f'FCSRI-1001{int(n_factura):09d}-GIMPR'
    mov = Movimiento.objects.filter(n_factura=n_factura)
    prods = productos_odbc_and_django()[['product_id','Nombre','Unidad']]
    movimientos = pd.DataFrame(mov.values())
    movimientos = movimientos.merge(prods, on='product_id', how='left')
    movimientos['unidades'] = movimientos['unidades'].abs()
    
    def data_cliente_fun(n_factura_mba):
        try:
            with connections['gimpromed_sql'].cursor() as cursor:
                cursor.execute(f"""
                    SELECT 
                        vf.NOMBRE_CLIENTE,
                        vf.CODIGO_FACTURA,
                        vf.NUMERO_PEDIDO_SISTEMA,
                        vf.FECHA_FACTURA,
                        c.IDENTIFICACION_FISCAL,
                        c.CODIGO_CLIENTE,
                        c.NOMBRE_CLIENTE
                    FROM warehouse.clientes c
                    LEFT JOIN warehouse.facturas vf 
                    ON c.NOMBRE_CLIENTE = vf.NOMBRE_CLIENTE
                    WHERE CODIGO_FACTURA = '{n_factura_mba}'""")
                columns = [col[0] for col in cursor.description]
                cliente = [
                    dict(zip(columns, row))
                    for row in cursor.fetchall()
                ][0]       
            return cliente
        except:
            return None
    
    if request.method == "POST":
        
        orden_salida = OrdenSalida.objects.filter(n_factura=n_factura)
        if orden_salida.exists():
            form = OrdenSalidaForm(request.POST, instance=orden_salida.first())
            if form.is_valid():
                form.save()
                messages.success(request, 'Orden de salida actualizada correctamente !!!')
                return HttpResponseRedirect(f'/wms/orden-salida/{n_factura}')
            messages.error(request, f'Error {form.errors} !!!')
        else:
            form = OrdenSalidaForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Orden de salida creada correctamente !!!')
                return HttpResponseRedirect(f'/wms/orden-salida/{n_factura}')
            # messages.error(request, 'Error al crear la orden de salida !!!')
    
    data_cliente = data_cliente_fun(n_factura_mba) 
    context = {
        'n_factura': n_factura,
        'data_cliente': data_cliente,
        'picking':mov.first().n_referencia if mov.exists() else '',
        'orden_salida': OrdenSalida.objects.get(n_factura=n_factura) if OrdenSalida.objects.filter(n_factura=n_factura).exists() else '',
        'movimientos': de_dataframe_a_template(movimientos)
    }
    return render(request, 'wms/orden_salida.html', context)


def orden_salida_pdf(request, n_factura):
    
    orden_salida = OrdenSalida.objects.get(n_factura=n_factura)
    movimientos = pd.DataFrame(Movimiento.objects.filter(n_factura=n_factura).values())
    prods = productos_odbc_and_django()[['product_id','Nombre','Unidad']]
    movimientos = movimientos.groupby(by='product_id')['unidades'].sum().reset_index().sort_values(by='product_id')
    movimientos = movimientos.merge(prods, on='product_id', how='left')
    movimientos['unidades'] = movimientos['unidades'].abs()
    
    context = {
        'orden_salida': orden_salida,
        'movimientos': de_dataframe_a_template(movimientos)
    }
    
    output = io.BytesIO()
    html_string = render_to_string('wms/orden_salida_pdf.html', context)
    pdf_statur = pisa.CreatePDF(html_string, dest=output)
    if pdf_statur.err:
        return HttpResponse('We had some errors <pre>' + html_string + '</pre>')
    response = HttpResponse(output.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="orden_salida_{n_factura}.pdf"'
    return response


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
        # items.update(estado_picking='Despachado', n_factura=n_factura)
        # 13/02/2025
        for i in items:
            i.estado_picking = 'Despachado'
            i.n_factura = n_factura
            i.save()

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

        trasf_mba = transferencias_mba(n_trasf)
        trasf_mba['unidades'] = trasf_mba['unidades'].astype('int') 
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

    except Exception as e:
        print(e)
        return HttpResponse(f'Error: {e}')



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
    
    if transf_status.estado == 'FINALIZADO':
        # enviar email
        correo_finalizacion_picking(n_transferencia=n_transf)

    return JsonResponse({
        'msg':{
            'tipo':'success',
            'texto':f'✅ Transferencia {n_transf} actualizado !!!'
        }
    })


def correo_finalizacion_picking(n_transferencia):
    
    # Obtener transferencias (base de datos por defecto)
    transferencia = Transferencia.objects.filter(n_transferencia=n_transferencia)

    # Extraer los product_ids en Python (sin query adicional)
    product_ids = [t.product_id for t in transferencia]

    # Obtener productos (base de datos gimpromed_sql)
    productos = (
        Producto.objects
        .using('gimpromed_sql')
        .filter(codigo__in=product_ids)
        )
    
    data_transferencia = []
    for i in transferencia:
        data = {
            'product_id':i.product_id,
            'nombre':productos.filter(codigo=i.product_id).first().nombre,
            'marca':productos.filter(codigo=i.product_id).first().marca,
            'lote':i.lote_id,
            'fecha_caducidad':i.fecha_caducidad,
            'unidades':i.unidades
        }
        data_transferencia.append(data)
    
    context = {
        'n_transferencia':n_transferencia,
        'data_transferencia':data_transferencia
    }
    
    html_message = render_to_string('emails/finalizar_transferencia.html', context)
    plain_message = strip_tags(html_message)
    
    email = EmailMultiAlternatives(
        subject=f'Picking Transferencia Finalizada # {n_transferencia}',
        from_email=settings.EMAIL_HOST_USER,
        body=plain_message,
        to=[
            'pespinosa@gimpromed.com',
            'jgualotuna@gimpromed.com',
            'egarces@gimpromed.com'
            ],
    )
    
    email.attach_alternative(html_message, 'text/html')
    email.send()


def wms_transferencia_data_pdf_email(n_transferencia):
    
    transferencia = pd.DataFrame(Transferencia.objects.filter(n_transferencia=n_transferencia).order_by('ubicacion','product_id').values())
    transferencia['fecha_elaboracion'] = transferencia['fecha_elaboracion'].astype('str')
    transferencia['fecha_caducidad'] = transferencia['fecha_caducidad'].astype('str')
    productos = productos_odbc_and_django()[['product_id','Nombre','Marca']]
    transferencia = transferencia.merge(productos, on='product_id', how='left')
    transferencia['fecha_hora'] = pd.to_datetime(transferencia['fecha_hora']).dt.date 
    transferencia['fecha_hora'] = transferencia['fecha_hora'].astype('str')
    transferencia = transferencia.replace('None', '-')
    transferencia = de_dataframe_a_template(transferencia)
    
    for i in transferencia:
        product_id = i['product_id']
        ubicacion = ProductoUbicacion.objects.filter(product_id=product_id)
        if ubicacion.exists():
            
            # i['ubicacion_andagoya'] = ubicacion.first().ubicaciones.all().order_by('bodega','estanteria')
            ubicaciones = ubicacion.first().ubicaciones.all().order_by('bodega','estanteria')
            ubi_estanteria = ubicaciones.filter(estanteria=True)
            ubi_no_estanteria = ubicaciones.filter(estanteria=False)
            
            if ubi_no_estanteria:
                i['ubicacion_andagoya'] = ubi_no_estanteria #.first()
            elif not ubi_no_estanteria and ubi_estanteria:
                i['ubicacion_andagoya'] = ubi_estanteria #.first()
    
    obs = []
    for i in  Transferencia.objects.filter(n_transferencia=n_transferencia).order_by('ubicacion','product_id'):
        if i.observacion:
            obs.append(i)
    
    return {
        'cabecera':transferencia[0],
        'transferencia':transferencia,
        'obs':obs
    }


@pdf_decorator(pdfname='transferencia.pdf')
def wms_transferencia_pdf(request, n_transferencia):

    context = {
        'n_transferencia':n_transferencia, 
        'transferencia':wms_transferencia_data_pdf_email(n_transferencia)
    }
    return render(request, 'emails/transferencia_pdf.html', context)


def wms_transferencia_correo(n_transferencia):
    
    transferencia = wms_transferencia_data_pdf_email(n_transferencia) 
    correos = [
        'bcerezos@gimpromed.com',
        'ncastillo@gimpromed.com',
        'jgualotuna@gimpromed.com',
        'egarces@gimpromed.com',
        'pespinosa@gimpromed.com',
        'carcosh@gimpromed.com',
        'dreyes@gimpromed.com'
        ]
    
    if len(transferencia) >= 1:
        context = {'n_transferencia':n_transferencia, 'transferencia':transferencia, 'STATIC_ROOT': settings.STATIC_ROOT}
        html_message  = render_to_string('emails/transferencia.html', context)
        html_pdf_file = render_to_string('emails/transferencia_pdf.html', context)
        plain_message = strip_tags(html_message)
        
        output = io.BytesIO()
        pdf_status = pisa.CreatePDF(html_pdf_file, dest=output)
        
        if not pdf_status.err:
        
            output.seek(0)
            
            email = EmailMultiAlternatives(
                subject    = f'TRASFERENCIA DE BODEGA {n_transferencia}',
                body       = plain_message,
                from_email = settings.EMAIL_HOST_USER,
                to         = correos
            )
        
            email.attach_alternative(html_message, 'text/html')
            email.attach(f'Transferencia_{n_transferencia}.pdf', output.getvalue(), 'application/pdf')
            email.send()
            return True
        else:
            return False  # Retornar False si hubo un error
        
    else:
        print(f"No se encontró transferencia con número {n_transferencia}")
        return False


# Agregar transferencia para realizar picking de transferencia 
@login_required(login_url='login')
def wms_transferencia_input_ajax(request):
    
    n_trasf = request.POST['n_trasf']
    
    trans_mba = transferencias_mba(n_trasf)
    
    if trans_mba.empty:
        return JsonResponse({
            'msg':f'La Transferencia {n_trasf} no existe !!!',
            'alert':'danger'
        })
    
    if Transferencia.objects.filter(n_transferencia=n_trasf).exists():
        return JsonResponse({
            'msg':f'La Transferencia {n_trasf} ya fue añadida anteriormente !!!',
            'alert':'danger'
        })

    # trans_mba['n_transferencia'] = n_trasf
    # trans_mba['lote_id'] = trans_mba['lote_id'].str.replace('.','')
    # trans_mba = trans_mba.groupby(by=['doc','n_transferencia','product_id','lote_id','f_elab','f_cadu','bodega_salida','UBICACION']).sum().reset_index()
    trans_mba['f_cadu'] = trans_mba['f_cadu'].astype('str')
    trans_mba['f_elab'] = trans_mba['f_elab'].astype('str')
    
    trans_mba = de_dataframe_a_template(trans_mba)

    tr_list = []
    for i in trans_mba:
        tr = Transferencia(
            doc_gimp        = i['doc'],
            n_transferencia = i['n_transferencia'],
            product_id      = i['product_id'],
            lote_id         = i['lote_id'],
            fecha_elaboracion = i['f_elab'],
            fecha_caducidad = i['f_cadu'],
            bodega_salida   = i['bodega_salida'],
            unidades        = i['unidades'],
            # ubicacion       = i['UBICACION']
            ubicacion       = i['ubicacion']
            
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


@login_required(login_url='login')
@permisos(['BODEGA', 'OPERACIONES'], '/wms/home', 'ingresar a lista de transferencias')
def wms_transferencias_list(request):
    
    # transferencia_wms = (
    #     Transferencia.objects
    #     .filter(Q(bodega_salida='BCT') | Q(bodega_salida='CUC'))
    #     .values('n_transferencia') 
    #     .annotate(
    #         estado=Subquery(
    #             TransferenciaStatus.objects.filter(
    #                 n_transferencia=OuterRef('n_transferencia')
    #             )
    #             #.order_by('-fecha_hora')  # si tienes fecha
    #             .values('estado')[:1]
    #         )
    #     )
    #     .order_by('-n_transferencia')
    # ).distinct() # -> distinc fuera de queryset
    
    transferencias_wms = (
        TransferenciaStatus.objects.all()
        .annotate(
            fecha_hora = Subquery(
                Transferencia.objects.filter(
                    n_transferencia = OuterRef('n_transferencia')
                )
                .values('fecha_hora')[:1]
            )
        )
        .order_by('-n_transferencia')
    )
    
    context = {
        'transf_wms': transferencias_wms #transf_wms
    }

    return render(request, 'wms/transferencias_list.html', context)


@login_required(login_url='login')
@permisos(['BODEGA', 'OPERACIONES'], '/wms/home', 'ingresar a picking de transferencia')
def wms_transferencia_picking(request, n_transf):
    
    estado = TransferenciaStatus.objects.get(n_transferencia=n_transf)
    prod   = productos_odbc_and_django()[['product_id','Nombre','Marca','Unidad_Empaque','Volumen']]
    
    # Trasferencia
    transf = pd.DataFrame(Transferencia.objects.filter(n_transferencia=n_transf).values())
    transf_group = transf.groupby(by=['product_id','lote_id','fecha_caducidad'])['unidades'].sum().reset_index()
    transf_group = transf_group.merge(prod, on='product_id', how='left')
    transf_group['fecha_caducidad'] = pd.to_datetime(transf_group['fecha_caducidad']).dt.strftime('%d-%m-%Y').astype(str)
    transf_group['cartones'] = transf_group['unidades'] / transf_group['Unidad_Empaque']
    transf_group['vol'] = transf_group['cartones'] * (transf_group['Volumen']/1000000)
    transf_group['id_max'] = ''
    transf_group.at[transf_group['vol'].idxmax(), 'id_max'] = 'max'
    transf = transf_group
    
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
        ).order_by('fecha_caducidad','ubicacion__nivel','-ubicacion__modulo','-ubicacion__distancia_puerta','ubicacion__pasillo')
        if ext.exists():
            for j in ext:
                ext_id.append(j)

    prod = list(transf['product_id'].unique())
    
    existencias_bodega_df = (pd.DataFrame(Existencias.objects
            .filter(
                Q(product_id__in=prod) & 
                Q(estado='Disponible')
            )
            .values('product_id','lote_id','ubicacion__bodega','ubicacion__pasillo')
            .order_by('fecha_caducidad'))
            .drop_duplicates(subset=['product_id','lote_id','ubicacion__bodega','ubicacion__pasillo']))
    
    if not existencias_bodega_df.empty:
        existencias_bodega_df['ubi_show'] = existencias_bodega_df['ubicacion__bodega'] + '-' + existencias_bodega_df['ubicacion__pasillo']
    
    existencias_bodega_df = de_dataframe_a_template(existencias_bodega_df)

    transf_template = de_dataframe_a_template(transf)
    
    for i in prod:
        for j in transf_template:
            if j['product_id'] == i:
                j['ubi'] = ubi_list = []
                j['pik'] = pik_list = []
                j['primera_bodega'] = primera_bodega = []
                for k in ext_id:
                    if k['product_id'] == i:
                        ubi_list.append(k)
                for m in mov_list:
                    if m['product_id'] == i:
                        pik_list.append(m)
                for l in existencias_bodega_df:
                    if l['product_id'] == i and l['lote_id'] == j['lote_id']:
                        primera_bodega.append(l['ubi_show'])
    
    transf_template = sorted(transf_template, key=lambda x:x['primera_bodega'], reverse=False)
    
    context = {
        'transf':transf_template,
        'n_transf':n_transf,
        'estado':estado.estado,
        'avance':estado.avance,
        'vol_max':transf['vol'].max()
    }
    return render(request, 'wms/transferencia_picking.html', context)


def wms_transferencia_product_observacion_ajax(request):

    if request.method == 'GET':
        
        n_transf = request.GET.get('n_transf')
        prod_id = request.GET.get('prod_id')
        lote_id = request.GET.get('lote_id')
        
        trasnferencia = Transferencia.objects.filter(
            Q(n_transferencia=n_transf) &
            Q(product_id=prod_id) &
            Q(lote_id=lote_id)
            )
        transf = trasnferencia.first()
        
        return JsonResponse({
            'observacion':transf.observacion
        })
    
    if request.method == 'POST':
        
        n_transf = request.POST.get('n_transf')
        prod_id = request.POST.get('prod_id')
        lote_id = request.POST.get('lote_id')
        obs = request.POST.get('obs')
        
        trasnferencia = Transferencia.objects.filter(
            Q(n_transferencia=n_transf) &
            Q(product_id=prod_id) &
            Q(lote_id=lote_id)
            )
        
        transf = trasnferencia.first()
        transf.observacion = obs
        transf.save()
        return JsonResponse({
            'msg':'ok'
        })


# @permisos(['OPERACIONES'], '/wms/home', 'ingresar a picking de transferencia')
def wms_transferencia_correo_request(request):
    
    n_transf = request.POST.get('n_transf')
    email = wms_transferencia_correo(n_transf)
    
    if email:
        return JsonResponse({
            'type':'success',
            'msg':'Correo de detalle de lotes enviado !!!'
            })
    else:
        return JsonResponse({
            'type':'danger',
            'msg':'Error al enviar el correo'
            })
    
    

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


# def wms_busqueda_ajuste(request, n_ajuste):

#     user = request.user.id
    
#     cnxn = pyodbc.connect('DSN=mba3;PWD=API')
#     cursorOdbc = cnxn.cursor()
    

#     # La variable 'n' no está siendo usada en la consulta. Asegúrate de que sea necesario.
#     n = 'A-00000' + str(n_ajuste) + '-GIMPR'
    
#     #Transferencia Egreso
#     try:
#         cursorOdbc.execute(
#             "SELECT INVT_Producto_Lotes_Bodegas.Doc_id_Corp, "
#             "INVT_Producto_Lotes_Bodegas.PRODUCT_ID_CORP, "
#             "INVT_Producto_Lotes_Bodegas.LOTE_ID, "
#             "INVT_Producto_Lotes_Bodegas.WARE_CODE, "
#             "INVT_Producto_Lotes_Bodegas.LOCATION "
#             "FROM INVT_Producto_Lotes_Bodegas "
#             f"WHERE (INVT_Producto_Lotes_Bodegas.Doc_id_Corp='{n}') "
#         )
        
#         ajuste = [tuple(row) for row in cursorOdbc.fetchall()]

#         ajuste_df = pd.DataFrame(ajuste, columns=['DOC_ID_CORP', 'PRODUCT_ID_CORP', 'LOTE_ID', 'WARE_CODE', 'LOCATION']) if ajuste else pd.DataFrame()
        
#         # Segunda consulta
#         cursorOdbc.execute(
#             "SELECT INVT_Lotes_Ubicacion.DOC_ID_CORP, INVT_Lotes_Ubicacion.PRODUCT_ID_CORP, INVT_Lotes_Ubicacion.LOTE_ID, "
#             "INVT_Lotes_Ubicacion.EGRESO_TEMP, INVT_Lotes_Ubicacion.COMMITED, INVT_Lotes_Ubicacion.WARE_CODE_CORP, "
#             "INVT_Lotes_Ubicacion.UBICACION, INVT_Producto_Lotes.Fecha_elaboracion_lote, INVT_Producto_Lotes.FECHA_CADUCIDAD "
#             "FROM INVT_Lotes_Ubicacion, INVT_Producto_Lotes "
#             "WHERE INVT_Lotes_Ubicacion.PRODUCT_ID_CORP = INVT_Producto_Lotes.PRODUCT_ID_CORP "
#             "AND INVT_Producto_Lotes.LOTE_ID = INVT_Lotes_Ubicacion.LOTE_ID "
#             f"AND ((INVT_Lotes_Ubicacion.DOC_ID_CORP='{n}') AND (INVT_Producto_Lotes.ENTRADA_TIPO='OC')) "
#         )
#         inventario = [tuple(row) for row in cursorOdbc.fetchall()]
#         inventario_df = pd.DataFrame(inventario, columns=['DOC_ID_CORP', 'PRODUCT_ID_CORP', 'LOTE_ID', 'EGRESO_TEMP', 'COMMITED', 'WARE_CODE_CORP', 'UBICACION', 'Fecha_elaboracion_lote', 'FECHA_CADUCIDAD']) if inventario else pd.DataFrame()
        
#         # Unión (merge) de los DataFrames en los campos comunes
#         if not ajuste_df.empty and not inventario_df.empty:
#             resultado_df = pd.merge(ajuste_df, inventario_df, on=['DOC_ID_CORP', 'PRODUCT_ID_CORP', 'LOTE_ID'], how='inner')
#             resultado_df = resultado_df.drop_duplicates(subset=['DOC_ID_CORP', 'PRODUCT_ID_CORP', 'LOTE_ID'])
            
#             if 'Fecha_elaboracion_lote' in resultado_df.columns:
#                 resultado_df['Fecha_elaboracion_lote'] = resultado_df['Fecha_elaboracion_lote'].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notnull(x) else x)
#             if 'FECHA_CADUCIDAD' in resultado_df.columns:
#                 resultado_df['FECHA_CADUCIDAD'] = resultado_df['FECHA_CADUCIDAD'].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notnull(x) else x)
            
#             #eliminar por DOC_ID_CORP
#             LiberacionCuarentena.objects.filter(doc_id_corp = n ).delete(),
            

#             #si ya existe un registro con los mismos datos en doc_id_corp, product_id_corp ,lote_id que lo actualize o cree
#             #sino que lo cree
            
#             for index, row in resultado_df.iterrows():
#                 #busca si existe el registro
#                 existe = LiberacionCuarentena.objects.filter(doc_id_corp = row['DOC_ID_CORP']).filter(product_id_corp = row['PRODUCT_ID_CORP']).filter(lote_id = row['LOTE_ID']).exists()
#                 if existe==False:
#                     LiberacionCuarentena.objects.update_or_create(
#                     #replace string
#                     doc_id = n_ajuste,
#                     doc_id_corp = row['DOC_ID_CORP'],
#                     product_id_corp = row['PRODUCT_ID_CORP'],
#                     product_id= row['PRODUCT_ID_CORP'].replace('-GIMPR',''),
#                     lote_id = row['LOTE_ID'],
#                     ware_code = row['WARE_CODE'],
#                     location = row['LOCATION'],
#                     egreso_temp = row['EGRESO_TEMP'],
#                     commited = row['COMMITED'],
#                     ware_code_corp = row['WARE_CODE_CORP'],
#                     ubicacion = row['UBICACION'],
#                     fecha_elaboracion_lote = row['Fecha_elaboracion_lote'],
#                     fecha_caducidad = row['FECHA_CADUCIDAD'],
#                     estado=0
#                     )
#                     #wms_get_existencias(row,n_ajuste,user)
#                 else:
#                     if(existe.estado==0):
#                         pass
#                         #wms_get_existencias(row,n_ajuste,user)

#             # LiberacionCuarentena.objects.bulk_create(liberacion_cuarentena_objects)

#             # Asegúrate de que las columnas de fecha estén en un formato de fecha reconocible
#             # Si las columnas ya están en formato de fecha, no necesitas hacer nada más.
#             # Si necesitas ajustar el formato, puedes hacerlo aquí.

#             # Convertir DataFrame a JSON, asegurándose de que las fechas se formateen correctamente
#             resultado_json = resultado_df.to_json(orient='records', force_ascii=False, date_format='iso')
        
#             return HttpResponse(resultado_json, content_type='application/json')
#         else:
#             return JsonResponse({'error': 'No se encontraron datos para realizar la unión.'}, status=404)

#     except Exception as e:
#         print(e)
#         return JsonResponse({'error': str(e)}, status=500)      

#     finally:
#         # Cerrar la conexión con el ODBC
#         cnxn.close()
#         cursorOdbc.close()


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
        except Exception as e:
            print(e)
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


@login_required(login_url='login')
def wms_ajuste_liberacion_input_ajax(request):
    
    tipo_liberacion = request.POST['tipo']
    n_liberacion = request.POST['n_liberacion']
    
    liberacion_data = wms_ajuste_query_api(n_liberacion) 
    liberacion_data['LOTE_ID'] = liberacion_data['LOTE_ID'].str.replace('.', '') 
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


@login_required(login_url='login')
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
                #unidades        = int(i['unidades_cuc']) *-1,
                unidades        = int(i['egreso_temp']) *-1,
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
                #unidades        = int(i['unidades_cuc']),
                unidades        = int(i['egreso_temp']),
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
    
    picking_factura = Movimiento.objects.filter(
            Q(referencia='Picking') &
            Q(estado_picking='No Despachado')
            # Q(estado_picking=estado_de_picking)
        )
        
    picking_factura_df = pd.DataFrame(picking_factura.values(
        'referencia',
        'n_referencia',
        'n_factura',
        'fecha_hora',
        'actualizado',
        'usuario__first_name',
        'usuario__last_name',
        )).drop_duplicates(subset='n_referencia').sort_values(by='n_referencia', ascending=False)
    
    picking_factura_df['picking'] = picking_factura_df['n_referencia'].str.slice(0,-2)
    picking_factura_df['factura'] = picking_factura_df['n_factura'].apply(split_factura_movimiento)
    picking_factura_df['actualizado'] = picking_factura_df['actualizado'].astype('str').str.slice(0,16)
    
    # context = {
    #     'picking_factura_df': de_dataframe_a_template(picking_factura_df),
    #     #'titulo': 'LISTA DE PICKING - FACTURA' if estado_de_picking == 'Despachado' else 'LISTA DE PICKING - PRODUCTOS NO DESPACHADOS'
    # }

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
                #if estado == 'FINALIZADO':
                    picking = Movimiento.objects.filter(n_referencia=n_picking).filter(estado_picking='En Despacho')
                    
                    context = {
                        'picking':picking,
                        'cabecera':estado_picking.last()
                        }
                    
                    return render(request, 'wms/retiro_producto_despacho_list.html', context)
                
                #else:
                    #messages.error(request, f"El Picking {request.POST['n_picking']} su estado es {estado}")
    
    context = {
        'picking_factura_df': de_dataframe_a_template(picking_factura_df),
    }
    
    return render(request, 'wms/retiro_producto_despacho_list.html', context)


@login_required(login_url='login')
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
@login_required(login_url='login')
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
@login_required(login_url='login')
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


@login_required(login_url='login')
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


@login_required(login_url='login')
@permisos(['ADMINISTRADOR','OPERACIONES','BODEGA'],'/wms/home', 'ingresar a reporte')
def wms_reporte_bodegas457(request):
    
    products = Existencias.objects.all().values_list('product_id', flat=True).distinct()
    
    products_list_final = []    
    for i in products:
        existencia = Existencias.objects.filter(
            Q(product_id=i) &
            Q(estado='Disponible')
            #Q(ubicacion__bodega__in = ['CN4','CN5','CN7']) # En este nuevo reporte se comento esta linea
        ).order_by('fecha_caducidad', 'lote_id')
        
        
        if existencia.exists():
            if existencia.first().ubicacion.bodega != 'CN6': # esta linea se agrego  en este nuevo reporte
                products_list_final.append(existencia.first().id)
    
    
    df = pd.DataFrame(Existencias.objects.filter(id__in = products_list_final).values(
        'product_id','lote_id','fecha_caducidad','unidades',
        'ubicacion__bodega','ubicacion__pasillo','ubicacion__modulo','ubicacion__nivel'
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


# @login_required(login_url='login')
# @permisos(['ADMINISTRADOR','OPERACIONES','BODEGA'],'/wms/home', 'ingresar a ubicaciones')
# def wms_reporte_reposicion_alertas_obsoleto(request):    
    
#     """Crear un reporte que muestre los productos con mayor frecuencia de ventas para mover al nivel 1 con alertas segun demanda"""
#     ventas = frecuancia_ventas()
#     productos_ventas = set(ventas['PRODUCT_ID'].unique())    
#     productos_existencias = set(Existencias.objects.values_list('product_id', flat=True))
#     productos_analisis = productos_ventas.intersection(productos_existencias)

#     reporte_existencias_list = []
#     for i in productos_analisis:
#         existencias_by_product = Existencias.objects.filter(product_id=i).order_by('fecha_caducidad', 'lote_id', 'ubicacion__bodega', 'ubicacion__nivel')
        
#         if len(existencias_by_product) == 1 and existencias_by_product.first().ubicacion.nivel == '1':
#             pass
            
#         elif len(existencias_by_product) >= 1:
            
#             producto_uno = existencias_by_product[0]
#             #producto_dos = existencias_by_product[1]            
            
#             total_unidades_nivel_uno_query = existencias_by_product.filter(
#                 Q(ubicacion__nivel='1') & 
#                 Q(lote_id=producto_uno.lote_id)
#                 )
            
#             if total_unidades_nivel_uno_query.exists():
#                 total_unidades_nivel_uno = total_unidades_nivel_uno_query.aggregate(unidades_nivel_uno=Sum('unidades'))['unidades_nivel_uno']
#             else:
#                 total_unidades_nivel_uno = 0
            
            
#             suma_iteracion = 0
#             for j in existencias_by_product:
#                 suma_iteracion += j.unidades
#                 if suma_iteracion > total_unidades_nivel_uno:
#                     producto_dos = j
#                     break
            
#             ventas_product_mensual = ventas.loc[ventas['PRODUCT_ID']==i, 'ANUAL'].values[0] / 12
#             producto_uno_alerta_mensual = round(total_unidades_nivel_uno / ventas_product_mensual, 1)
            
#             if producto_uno_alerta_mensual <= 1.5 and producto_dos.ubicacion.nivel != '1':
                
#                 product = {
#                     'product_id':producto_uno.product_id,
#                     'lote_id':producto_uno.lote_id,
#                     'fecha_caducidad': producto_uno.fecha_caducidad,
#                     'ubicacion':producto_uno.ubicacion.nombre_completo,
#                     'total_unidades_nivel_uno':total_unidades_nivel_uno,
#                     'ventas_product_mensual':ventas_product_mensual,
#                     'unidades':producto_uno.unidades,
#                     'meses':producto_uno_alerta_mensual,
#                 }
        
#                 reporte_existencias_list.append(product)
        
#     reporte_existencias_df = pd.DataFrame(reporte_existencias_list)
    
#     if not reporte_existencias_df.empty:
#         productos = productos_odbc_and_django()[['product_id','Nombre','Marca']]
#         reporte = reporte_existencias_df.merge(productos, on='product_id', how='left').sort_values(by='meses')
#         reporte['fecha_caducidad'] = reporte['fecha_caducidad'].astype('str')
    
#     context = {
#         'reporte':de_dataframe_a_template(reporte),
#     }
    
#     return render(request, 'wms/reporte_reposicion_alertas.html', context)



@login_required(login_url='login')
@permisos(['ADMINISTRADOR','OPERACIONES','BODEGA'],'/wms/home', 'ingresar a ubicaciones')
def wms_reporte_reposicion_alertas(request):    
    
    """Crear un reporte que muestre los productos con mayor frecuencia de ventas para mover al nivel 1 con alertas segun demanda"""
    ventas = frecuancia_ventas() #;print(ventas)
    productos_ventas = set(ventas['PRODUCT_ID'].unique())    
    productos_existencias = set(Existencias.objects.values_list('product_id', flat=True))
    productos_analisis = productos_ventas.intersection(productos_existencias)

    # NUMERO DE PROUDUCTOS EN NIVEL UNO
    n_products = []
    for i in productos_analisis:
        n_product_nivel = Existencias.objects.filter(product_id=i, ubicacion__nivel='1').count()
        n_product = {
            'product_id': i,
            'n_product_nivel': n_product_nivel,
        }
        
        n_products.append(n_product)

    n_products_df = pd.DataFrame(n_products)

    # REPORTE
    reporte_existencias_list = []
    for i in productos_analisis:
        existencias_by_product = Existencias.objects.filter(product_id=i).order_by('fecha_caducidad', 'lote_id', 'ubicacion__bodega', 'ubicacion__nivel')
        
        if len(existencias_by_product) == 1 and existencias_by_product.first().ubicacion.nivel == '1':
            continue
            
        elif len(existencias_by_product) >= 1:
            nivel_de_productos = []
            for j in existencias_by_product:
                if j.ubicacion.nivel == '1':
                    nivel_de_productos.append(True)
                else:
                    nivel_de_productos.append(False)
            
            if all(nivel_de_productos):
                continue
            
            else:
            
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
            reporte = reporte.merge(n_products_df, on='product_id', how='left')
            reporte['fecha_caducidad'] = reporte['fecha_caducidad'].astype('str')
    
    context = {
        'reporte':de_dataframe_a_template(reporte),
    }
    
    return render(request, 'wms/reporte_reposicion_alertas.html', context)


@login_required(login_url='login')
@permisos(['BODEGA'], '/wms/inventario', 'ingrear a Movimiento interno')
def wms_movimiento_grupal(request):
    
    if request.method == 'POST':
        cabecera = json.loads(request.POST['cabecera'])
        productos = json.loads(request.POST['productos'])
        
        if len(productos) > 0:
        
            for i in productos:

                usuario = User.objects.get(username=cabecera['usuario'])
                ubicacion_destino = int(cabecera['ubi_destino'])
                existencia = Existencias.objects.get(id=int(i['id_existencia']))
                
                # Crear movimiento de salida
                mov_egreso = Movimiento(
                    product_id=existencia.product_id,
                    lote_id=existencia.lote_id,
                    fecha_caducidad=existencia.fecha_caducidad,
                    tipo='Egreso',
                    descripcion='N/A',
                    referencia='Movimiento Grupal',
                    ubicacion=existencia.ubicacion,
                    unidades=(existencia.unidades) * -1,
                    estado=existencia.estado,
                    usuario=usuario,
                )
                mov_egreso.save()
                
                # Crear movimiento de ingreso
                mov_ingreso = Movimiento(
                    product_id=existencia.product_id,
                    lote_id=existencia.lote_id,
                    fecha_caducidad=existencia.fecha_caducidad,
                    tipo='Ingreso',
                    descripcion='N/A',
                    referencia='Movimiento Grupal',
                    ubicacion_id=ubicacion_destino,
                    unidades=existencia.unidades,
                    estado=existencia.estado,
                    usuario=usuario,
                )
                mov_ingreso.save()
                
                wms_existencias_query_product_lote(product_id=existencia.product_id, lote_id=existencia.lote_id)

            return JsonResponse({
                'msg':'Se movieron todos los productos seleccionados !!!',
                'type':'success'
            })                

        else:
            return JsonResponse({
                'msg':'Seleccione almenos un producto !!!',
                'type':'danger'
            })
    
    return render(request, 'wms/movimiento_grupal.html', {})


def wms_movimiento_grupal_get_ubi_list_ajax(request):

    bodega  = request.POST['bodega']
    pasillo = request.POST['pasillo']
    ubi_salida = request.POST['ubi_salida']

    if not ubi_salida:
        ubi_list = pd.DataFrame(Ubicacion.objects
            .filter(disponible=True)
            .filter(bodega=bodega)
            .filter(pasillo=pasillo)
            .values()
            ).sort_values(by=['bodega','pasillo','modulo','nivel'])

        ubi_list = de_dataframe_a_template(ubi_list)

        return JsonResponse({'ubi_list':ubi_list}, status=200)
    else:
        ubi_list = pd.DataFrame(Ubicacion.objects
            .exclude(id=int(ubi_salida))
            .filter(disponible=True)
            .filter(bodega=bodega)
            .filter(pasillo=pasillo)
            .values()
            ).sort_values(by=['bodega','pasillo','modulo','nivel'])

        ubi_list = de_dataframe_a_template(ubi_list)

        return JsonResponse({'ubi_list':ubi_list}, status=200)


def wms_movimiento_grupal_ubicacion_salida_ajax(request):

    ubi_salida = int(request.POST['ubi_salida'])
    ubi = Ubicacion.objects.get(id=ubi_salida)
    ubicaciones_destino = pd.DataFrame(Ubicacion.objects.exclude(id=ubi.id).values()).sort_values(by=['bodega','pasillo','modulo','nivel'])
    existencia_ubi_salida = pd.DataFrame(Existencias.objects.filter(ubicacion_id=ubi_salida).values())

    if not existencia_ubi_salida.empty:
        existencia_ubi_salida = existencia_ubi_salida[[
            'id', 
            'product_id', 
            'lote_id', 
            'unidades',
            'ubicacion_id'
        ]].sort_values(by=['product_id','lote_id'])
        
        rows_html = []
        
        for index, row in existencia_ubi_salida.iterrows():
            
            row_tr = f"""
                <tr>
                    <td>{row['product_id']}</td>
                    <td>{row['lote_id']}</td>
                    <td class="text-end">{row['unidades']}</td>
                    <td class="text-center" id="tr-inputs">
                        <input class="mover-checkbox form-check-input" type="checkbox">
                        <input class="existencia-hidden" type="hidden" value="{row['id']}">
                    </td>
                </tr>
            """
            rows_html.append(row_tr)
        
        table = f"""
        <table border="1" class="table table-responsive table-bordered m-0 p-0" id="tabla_existencias">
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
            'ubicaciones_destino':de_dataframe_a_template(ubicaciones_destino)
            })

    else:
        return JsonResponse({
            'msg':f'✅ Posición {ubi} vacia !!!',
            'type':'success'
        })



## ARMADOS
## Correo de creación de armados
def wms_correo_creacion_armado(orden):
    
    lista_correos_andagoya = [
        'ncaisapanta@gimpromed.com',
        'ncastillo@gimpromed.com',
        'jgualotuna@gimpromed.com',
        'kenriquez@gimpromed.com',
        'carcosh@gimpromed.com',
        'dreyes@gimpromed.com',
    ]
    
    lista_correos_cerezos = [
        'ncaisapanta@gimpromed.com',
        'ncastillo@gimpromed.com',
        'jgualotuna@gimpromed.com',
        'kenriquez@gimpromed.com',
        'carcosh@gimpromed.com',
        'dreyes@gimpromed.com',
        'bodega2@gimpromed.com',
    ]
    
    if orden.bodega=='Andagoya':
        correos = lista_correos_andagoya
    elif orden.bodega=='Cerezos':
        correos = lista_correos_cerezos

    
    context = {'orden':orden}
    html_message  = render_to_string('emails/crear_armado.html', context)
    plain_message = strip_tags(html_message)
    
    email = EmailMultiAlternatives(
        subject    = f'SOLICITUD DE ARMADO {orden.bodega}',
        from_email = settings.EMAIL_HOST_USER,
        body       = plain_message,
        to         = correos
    )
    
    email.attach_alternative(html_message, 'text/html')
    email.attach_file(path=orden.archivo.path)
    email.send()


def wms_correo_editar_bodega_armado(orden):

    context = {'orden':orden}
    html_message  = render_to_string('emails/editar_armado.html', context)
    plain_message = strip_tags(html_message)
    
    email = EmailMultiAlternatives(
        subject=f'SOLICITUD DE ARMADO {orden.bodega} - CAMBIO DE BODEGA',
        from_email=settings.EMAIL_HOST_USER,
        body=plain_message,
        to=[
            'ncaisapanta@gimpromed.com',
            'ncastillo@gimpromed.com',
            'jgualotuna@gimpromed.com',
            'kenriquez@gimpromed.com',
            'carcosh@gimpromed.com',
            'dreyes@gimpromed.com',
            'bodega2@gimpromed.com',
            'bcerezos@gimpromed.com'
            ],
    )
    
    email.attach_alternative(html_message, 'text/html')
    email.send()


def wms_correo_finalizado_armado(orden):

    context = {'orden':orden}
    html_message  = render_to_string('emails/finalizar_armado.html', context)
    plain_message = strip_tags(html_message)
    
    email = EmailMultiAlternatives(
        subject=f'SOLICITUD ARMADO #{orden.enum} - FINALIZADO',
        from_email=settings.EMAIL_HOST_USER,
        body=plain_message,
        to=[
            'ncaisapanta@gimpromed.com',
            'ncastillo@gimpromed.com',
            'jgualotuna@gimpromed.com',
            'kenriquez@gimpromed.com',
            'carcosh@gimpromed.com',
            'dreyes@gimpromed.com',
            'bodega2@gimpromed.com',
            'bcerezos@gimpromed.com',
            ],
    )
    
    email.attach_alternative(html_message, 'text/html')
    email.send()


def wms_correo_anular_armado(orden):

    context = {'orden':orden}
    html_message  = render_to_string('emails/anular_armado.html', context)
    plain_message = strip_tags(html_message)
    
    email = EmailMultiAlternatives(
        subject=f'SOLICITUD ARMADO #{orden.enum} - ANULADO',
        from_email=settings.EMAIL_HOST_USER,
        body=plain_message,
        to=[
            'ncaisapanta@gimpromed.com',
            'ncastillo@gimpromed.com',
            'jgualotuna@gimpromed.com',
            'kenriquez@gimpromed.com',
            'carcosh@gimpromed.com',
            'dreyes@gimpromed.com',
            'bodega2@gimpromed.com',
            'bcerezos@gimpromed.com'
            ],
    )
    
    email.attach_alternative(html_message, 'text/html')
    email.send()


@login_required(login_url='login')
@permisos(['ADMINISTRADOR','OPERACIONES',], '/wms/inventario', 'ingrear a lista de armados')
def wms_armados_list(request):
    
    armados = OrdenEmpaque.objects.all().order_by('-id')#.exclude(estado='Anulado')
    form_orden = OrdenEmpaqueForm()
    form_nuevo_producto = ProductoNuevoArmadoForm()
    
    ruc_list = clientes_warehouse()[['IDENTIFICACION_FISCAL']]
    cliente_list = clientes_warehouse()[['NOMBRE_CLIENTE']]
    products_list = productos_odbc_and_django()[['product_id']]
    
    if request.method == 'POST':
        form_orden = OrdenEmpaqueForm(request.POST)
        form_nuevo_producto = ProductoNuevoArmadoForm(request.POST)
        if form_orden.is_valid() and form_nuevo_producto.is_valid():
            orden = form_orden.save()
            nuevo_producto = form_nuevo_producto.save()
            
            orden.nuevo_producto = nuevo_producto
            if orden.bodega == 'Cerezos':
                nuevo_producto.ubicacion = 'CN7-A-1'
                nuevo_producto.save()
            
            orden.save()
            
            # enviar correo electronico
            # wms_correo_creacion_armado(orden)
            
            return HttpResponseRedirect(f'/wms/orden-armado/{orden.id}')
        else:
            messages.error(request, form_orden.errors)
    
    context = {
        'armados':armados,
        'form_nuevo_producto':form_nuevo_producto,
        'form_orden':form_orden,
        'products_list':de_dataframe_a_template(products_list),
        'ruc_list':de_dataframe_a_template(ruc_list),
        'cliente_list':de_dataframe_a_template(cliente_list)
    }
    
    return render(request, 'wms/armados_list.html', context)


def get_product_data_by_product_id_ajax(request):
    
    try:
        if request.method == 'POST':
            product_id = request.POST.get('product_id')
            
            if product_id:
            
                with connections['gimpromed_sql'].cursor() as cursor:
                    cursor.execute("SELECT * FROM productos WHERE Codigo = %s", [product_id])
                    columns = [col[0] for col in cursor.description]
                    product = [dict(zip(columns, row)) for row in cursor.fetchall()][0]
                
                return JsonResponse({
                    'nombre':product['Nombre'],
                    'marca':product['Marca'],
                })
                
            else:
                return JsonResponse({'error': 'Llene el código de producto'})
    except:
        return JsonResponse({'error': 'Error en el código de producto'})


def get_ruc_by_name_client_ajax(request):
    
    try:
        if request.method == 'POST':
            nombre_cliente = request.POST.get('cliente_name')
            
            if nombre_cliente:
            
                ''' Colusta de clientes por ruc a la base de datos '''
                with connections['gimpromed_sql'].cursor() as cursor:
                    cursor.execute("SELECT * FROM clientes WHERE NOMBRE_CLIENTE = %s", [nombre_cliente])
                    columns = [col[0] for col in cursor.description]
                    clientes = [dict(zip(columns, row)) for row in cursor.fetchall()][0]
                
                return JsonResponse({
                    'ruc':clientes['IDENTIFICACION_FISCAL'],
                    'codigo_cliente':clientes['CODIGO_CLIENTE'],
                })
                
            else:
                return JsonResponse({'error': 'Llene el nombre del cliente'})
    except:
        return JsonResponse({'error': 'No hay ventas registradas'})


def get_precio_by_product_client_ajax(request):
    
    try:
        if request.method == 'POST':
            product_id = request.POST.get('product_id')
            codigo_cliente = request.POST.get('codigo_cliente')
            
            if product_id and codigo_cliente:
            
                ''' Colusta de clientes por ruc a la base de datos '''
                with connections['gimpromed_sql'].cursor() as cursor:
                    cursor.execute(f"""
                        SELECT * 
                        FROM warehouse.venta_facturas 
                        WHERE PRODUCT_ID = '{product_id}' 
                        AND CODIGO_CLIENTE = '{codigo_cliente}' 
                        ORDER BY STR_TO_DATE(FECHA, '%Y-%m-%d') DESC
                        """)
                    columns = [col[0] for col in cursor.description]
                    precio = [dict(zip(columns, row)) for row in cursor.fetchall()][0]
                    
                return JsonResponse({
                    'precio':precio['UNIT_PRICE'],
                })
                
            else:
                return JsonResponse({'error': 'Llene el código y cliente'})
    except:
        return JsonResponse({'error': 'Este cliente no ha comprado este producto por ello el precio es 0.0, edite el precio.'})


@login_required(login_url='login')
@permisos(['ADMINISTRADOR','OPERACIONES',], '/wms/inventario', 'ingrear a detalle de armado')
def wms_orden_armado(request, id):

    # Orden
    orden = OrdenEmpaque.objects.get(id=id)
    form_componente = ComponenteArmadoForm()
    producto_nuevo_form = ProductoNuevoArmadoUpdateForm()
    
    # Movimientos
    mov = Movimiento.objects.filter(n_referencia=orden.enum)
    
    # Componentes
    componentes = orden.componentes.all()
    componente_picking = []
    for i in componentes:
        movimiento = mov.filter(product_id=i)
        c_m = {
            'componente':i,
            'movimiento':movimiento
        }
        componente_picking.append(c_m)    
    
    # Agregar Componente
    if request.method == 'POST':
        form_componente = ComponenteArmadoForm(request.POST)
        if form_componente.is_valid():
            form_componente.save()
            nuevo_producto = form_componente.save()
            orden.componentes.add(nuevo_producto)
            messages.success(request, 'Componente agregado exitosamente')
            return redirect('wms_orden_armado', id=id)
        else:
            messages.error(request, form_componente.errors)
            return redirect('wms_orden_armado', id=id)
        
    context = {
        'orden':orden,
        'producto_nuevo_form':producto_nuevo_form,
        'componente_picking':componente_picking,
        'form_componente':form_componente,
        'products_list':de_dataframe_a_template(productos_odbc_and_django()[['product_id']]),
        'clientes':de_dataframe_a_template(clientes_warehouse()[['NOMBRE_CLIENTE']]),
        'ruc':de_dataframe_a_template(clientes_warehouse()[['IDENTIFICACION_FISCAL']]),
    }
    
    return render(request, 'wms/armados_orden.html', context)


def wms_editar_orden_ajax(request):
    
    if request.method == 'GET':
        id_orden = int(request.GET.get('id_orden'))
        orden = OrdenEmpaque.objects.get(id=id_orden)
        form  = OrdenEmpaqueUpdateForm(instance=orden) 
        return HttpResponse(form.as_p())
    
    elif request.method == 'POST':
        id_orden = int(request.POST.get('id_orden'))
        orden = OrdenEmpaque.objects.get(id=id_orden)
        form  = OrdenEmpaqueUpdateForm(request.POST, instance=orden)
        anterior_bodega = orden.bodega
        if form.is_valid():
            nueva_orden = form.save()
            
            # Enviar correo - si cambia de bodega            
            nueva_bodega = form.cleaned_data['bodega']
            
            if anterior_bodega != nueva_bodega:
                wms_correo_editar_bodega_armado(orden=nueva_orden)
            
            messages.success(request, 'Orden editada con exito !!!')
            return HttpResponseRedirect(f'/wms/orden-armado/{orden.id}')
        else:
            messages.error(request, form.errors)
            return HttpResponseRedirect(f'/wms/orden-armado/{orden.id}')


def wms_editar_nuevo_producto_ajax(request):
    
    if request.method == 'GET':
        id_nuevo_producto = int(request.GET.get('id_nuevo_producto'))
        nuevo_producto = ProductoArmado.objects.get(id=id_nuevo_producto)
        form  = ProductoNuevoArmadoForm(instance=nuevo_producto)
        return HttpResponse(form.as_p())
    
    elif request.method == 'POST':
        id_nuevo_producto = int(request.POST.get('id_nuevo_producto'))
        nuevo_producto = ProductoArmado.objects.get(id=id_nuevo_producto)
        orden = OrdenEmpaque.objects.get(nuevo_producto=nuevo_producto)
        form  = ProductoNuevoArmadoForm(request.POST, instance=nuevo_producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Nuevo producto editado con exito !!!')
            return HttpResponseRedirect(f'/wms/orden-armado/{orden.id}')
        else:
            messages.error(request, form.errors)
            return HttpResponseRedirect(f'/wms/orden-armado/{orden.id}')


def wms_completar_componente_ajax(request):
    
    if request.method == 'GET':
        id_componente = int(request.GET.get('id_componente'))
        componente = ProductoArmado.objects.get(id=id_componente)
        form  = ProductoNuevoArmadoUpdateForm(instance=componente)
        return HttpResponse(form.as_p())
    
    elif request.method == 'POST':
        id_componente = int(request.POST.get('id_componente'))
        componente = ProductoArmado.objects.get(id=id_componente)
        
        if OrdenEmpaque.objects.filter(nuevo_producto=componente).exists():
            orden = OrdenEmpaque.objects.get(nuevo_producto=componente)
            tipo_request = 'nuevo'
        else:
            orden = OrdenEmpaque.objects.filter(componentes=componente).first()
            tipo_request = 'componente'
        
        form  = ProductoNuevoArmadoUpdateForm(request.POST, instance=componente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Nuevo producto editado con exito !!!')
            if tipo_request == 'nuevo':
                # return HttpResponseRedirect(f'/wms/orden-armado/{orden.id}')
                return HttpResponseRedirect(f'/wms/armados-picking/{orden.id}')
            else:
                # return HttpResponseRedirect(f'/wms/armados-picking/{orden.id}')
                return HttpResponseRedirect(f'/wms/armados-picking/{orden.id}')
        else:
            messages.error(request, form.errors)
            if tipo_request == 'nuevo':
                # return HttpResponseRedirect(f'/wms/orden-armado/{orden.id}')
                return HttpResponseRedirect(f'/wms/armados-picking/{orden.id}')
            else:
                # return HttpResponseRedirect(f'/wms/armados-picking/{orden.id}')
                return HttpResponseRedirect(f'/wms/armados-picking/{orden.id}')


def wms_editar_componente_ajax(request):
    
    if request.method == 'GET':
        id_componente = int(request.GET.get('id_componente'))
        componente = ProductoArmado.objects.get(id=id_componente)
        form  = ComponenteArmadoForm(instance=componente)
        return HttpResponse(form.as_p())
    
    elif request.method == 'POST':
        id_componente = int(request.POST.get('id_componente'))
        componente = ProductoArmado.objects.get(id=id_componente)
        orden = componente.componentes.all().first()
        form  = ComponenteArmadoForm(request.POST, instance=componente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Nuevo producto editado con exito !!!')
            return HttpResponseRedirect(f'/wms/orden-armado/{orden.id}')
        else:
            messages.error(request, form.errors)
            return HttpResponseRedirect(f'/wms/orden-armado/{orden.id}')


def wms_eliminar_componente_ajax(request):
    
    if request.method == 'POST':    
        id_componente = int(request.POST.get('id_componente'))
        componente = ProductoArmado.objects.get(id=id_componente)
        componente.delete()
        return JsonResponse({
            'msg':'Componete eliminado exitosamente'
        }) 


@login_required(login_url='login')
@permisos(['BODEGA'], '/wms/inventario', 'ingrear a Picking de armados')
def wms_armado_picking_list(request):
    
    armados = OrdenEmpaque.objects.filter(
            Q(bodega = 'Cerezos')
        ).order_by('-id').exclude(estado='Anulado')
    
    context = {
        'armados':armados
    }
    
    return render(request, 'wms/armados_picking_list.html', context)


@login_required(login_url='login')
@permisos(['BODEGA'], '/wms/inventario', 'ingrear a Picking de armados')
def wms_armado_picking(request, id):

    orden = OrdenEmpaque.objects.get(id=id)
    
    # Componentes
    componentes = orden.componentes.all()
    componentes_product_list = componentes.values_list('product_id', flat=True)
    
    # Existencias
    existencias = Existencias.objects.filter(
        Q(estado='Disponible') &
        Q(product_id__in = componentes_product_list)
        ).values(
            'id',
            'product_id','lote_id','fecha_caducidad','unidades','estado',
            'ubicacion__id','ubicacion__bodega', 'ubicacion__pasillo', 'ubicacion__modulo', 'ubicacion__nivel'
        )
    
    # Movimiento 
    movimientos = Movimiento.objects.filter(
        Q(n_referencia=orden.enum) &
        Q(tipo='Egreso') &
        Q(referencia='Picking O.Empaque')
    ).values(
        'id',
        'product_id','lote_id','fecha_caducidad',
        'unidades','ubicacion__bodega','ubicacion__pasillo','ubicacion__modulo','ubicacion__nivel',
    )
    
    # Total picking
    total_picking = []
    for i in componentes_product_list:
        total_picking_unds = Movimiento.objects.filter(
            Q(product_id=i) & 
            Q(n_referencia=orden.enum) &
            Q(tipo='Egreso') &
            Q(referencia='Picking O.Empaque')).aggregate(total_picking=Sum('unidades'))['total_picking']
        if total_picking_unds:
            total_picking_unds = total_picking_unds * -1
            dict_total = {
                'product_id' : i,
                'total_picking' : total_picking_unds
            }
            total_picking.append(dict_total)
    
    # Data para picking
    componentes_template = componentes.values()
    for i in componentes_product_list:
        for j in componentes_template:
            if j['product_id'] == i:
                j['ubi'] = ubi_list = []
                j['pik'] = pik_list = []
                for k in existencias:
                    if k['product_id'] == i:
                        ubi_list.append(k)
                for k in movimientos:
                    if k['product_id'] == i:
                        pik_list.append(k)
                for l in total_picking:
                    if l['product_id'] == i:
                        j['total_picking'] = l['total_picking']
    
    # Total Unidades Picking
    total_unidades_picking_todos = [(i['unidades'] * -1) for i in movimientos]
    total_unidades_picking_todos = sum(total_unidades_picking_todos)
    
    # Total Unidades componentes
    total_componentes = componentes.aggregate(total=Sum('unidades'))['total']
    total_componentes = total_componentes if total_componentes else 0
    
    context = {
        'orden':orden,
        'componentes_template':componentes_template,
        'total_unidades_picking_todos':total_unidades_picking_todos,
        'total_componentes':total_componentes
    }
    
    return render(request, 'wms/armado_picking.html', context)


@login_required(login_url='login')
def wms_armado_movimiento_egreso(request):
    
    # Verificar si se ingresaron unidades
    unds_egreso = request.POST.get('unds')
    if not unds_egreso:
        unds_egreso = 0
        return JsonResponse({'msg':'❌ Error, ingrese una cantidad !!!'})
    else:
        unds_egreso = int(unds_egreso)
    
    # Existencia
    id_existencia = int(request.POST.get('id_existencia'))
    existencia = Existencias.objects.get(id=id_existencia)
    
    # Total Picking por producto
    total_picking = Movimiento.objects.filter(
        Q(product_id=existencia.product_id) &
        Q(n_referencia=request.POST.get('orden_empaque')) &
        Q(tipo='Egreso') &    
        Q(referencia='Picking O.Empaque')).aggregate(total_picking=Sum('unidades'))['total_picking']    
    total_picking = int(total_picking) * -1 if total_picking else 0
    
    # Total Egreso
    total_componente = OrdenEmpaque.objects.get(id=int(request.POST.get('orden_empaque_id'))).componentes.get(product_id=existencia.product_id).unidades
    
    if not existencia:
        return JsonResponse({'msg':'❌ Error, revise las existencias o refresque la pagina !!!'})
    elif existencia:
        if unds_egreso > existencia.unidades:
            return JsonResponse({'msg':'❌ No puede retirar más unidades de las existentes !!!'})
        elif unds_egreso == 0 or unds_egreso < 0:
            return JsonResponse({'msg':'❌ La cantidad debe ser mayor 0 !!!'})
        elif total_picking + unds_egreso > total_componente:
            return JsonResponse({'msg':'❌ No puede retirar más unidades de las solicitadas en el Picking !!!'})
        elif total_picking + unds_egreso <= total_componente:
            
            picking = Movimiento(
                product_id      = existencia.product_id,
                lote_id         = existencia.lote_id,
                fecha_caducidad = existencia.fecha_caducidad,
                tipo            = 'Egreso',
                descripcion     = 'N/A',
                referencia      = 'Picking O.Empaque',
                n_referencia    = request.POST.get('orden_empaque'),
                ubicacion_id    = existencia.ubicacion.id,
                unidades        = unds_egreso*-1,
                estado          = existencia.estado,
                estado_picking  = 'Despachado',
                usuario_id      = request.user.id,
            )

            picking.save()
            wms_existencias_query_product_lote(product_id=picking.product_id, lote_id=picking.lote_id)

            # Actualizar campos de fechas y lote de producto seleccionado
            actualizar_componente = OrdenEmpaque.objects.get(id=int(request.POST.get('orden_empaque_id'))).componentes.get(product_id=existencia.product_id)
            actualizar_componente.lote_id = picking.lote_id
            actualizar_componente.fecha_caducidad = picking.fecha_caducidad
            actualizar_componente.save()
            
            # Cambio de estado de orden
            orden = OrdenEmpaque.objects.get(id=int(request.POST.get('orden_empaque_id')))
            if orden.estado == 'Creado':
                orden.estado = 'En Picking'
                orden.save()
            
            return JsonResponse({'msg':f'✅ Producto {existencia.product_id}, lote {existencia.lote_id} seleccionado correctamente !!!'})
        return JsonResponse({'msg':'❌ Error !!!'})
    return JsonResponse({'msg':'❌Error !!!'})


@login_required(login_url='login')
def wms_armado_editar_estado(request):
    
    if request.method == 'POST':
        
        id_orden = int(request.POST.get('orden_empaque_id'))
        orden = OrdenEmpaque.objects.get(id=id_orden)
        
        nuevo_estado = request.POST.get('estado')
        
        if nuevo_estado != 'Finalizado' and nuevo_estado != 'Anular':
            orden.estado = nuevo_estado
            orden.save()
        
        elif nuevo_estado == 'Anular':
            orden.estado = 'Anulado'
            orden.save()
            wms_correo_anular_armado(orden)
        
        elif nuevo_estado == 'Finalizado':
            
            # Comprobar que los campos lotes y fechas se hayan completado antes de finalizar
            componentes = orden.componentes.all()
            
            componentes_llenos_list = []
            for i in componentes:
                
                if i.lote_id:
                    componentes_llenos_list.append(True)
                else:
                    componentes_llenos_list.append(False)
                    
                # if i.fecha_elaboracion:
                #     componentes_llenos_list.append(True)
                # else:
                #     componentes_llenos_list.append(False)
                    
                if i.fecha_caducidad:
                    componentes_llenos_list.append(True)
                else:
                    componentes_llenos_list.append(False)
                
                
            if all(componentes_llenos_list):
                orden.estado = nuevo_estado
                orden.save()

                # Enviar Correo
                wms_correo_finalizado_armado(orden)
                
            else:
                return JsonResponse({
                    'msg':f'❌ No puede finalizar la Orden N° {orden.enum} hasta completar los lotes y fechas de los productos',
                    'type':'danger'
                    })
                
        return JsonResponse({
            'msg':f'✅ Orden N° {orden.enum} {orden.estado}',
            'type':'success'
            })


@login_required(login_url='login')
def wms_armado_orden_pdf(request, orden_id):
    
    if request.method == 'POST':
        try:
            # Orden
            orden = OrdenEmpaque.objects.get(id=orden_id)
            
            # Movimientos
            mov = Movimiento.objects.filter(n_referencia=orden.enum)
            
            # Componentes
            componentes = orden.componentes.all()
            componente_picking = []
            for i in componentes:
                movimiento = mov.filter(product_id=i)
                c_m = {
                    'componente':i,
                    'movimiento':movimiento
                }
                componente_picking.append(c_m)    
                
            context = {'orden':orden,'componente_picking':componente_picking,}
            
            
            output = io.BytesIO()
            html_string = render_to_string('wms/armado_orden_pdf.html', context)
            
            pdf_status = pisa.CreatePDF(html_string, dest=output)
            
            if pdf_status.err:
                return HttpResponse('Error al generar el PDF')
            
            output.seek(0)
            
            archivo = ContentFile(output.getvalue(), f'O_empaque_{orden.enum}.pdf')
            
            orden.archivo = archivo
            orden.save()
            
            # send email
            wms_correo_creacion_armado(orden)
            
            messages.success(request, f'Armado {orden.enum} PDF creado exitosamente !!!')
            return HttpResponseRedirect(f'/wms/armados-list')
            
        except Exception:
            messages.error(request, f'Armado {orden.enum} PDF Error !!!')
            return HttpResponseRedirect(f'/wms/armados-list')
            # return JsonResponse({
            #     'type':'danger',
            #     'msg':'Error al generar el PDF !!!'
            #     })


@login_required(login_url='login')
@pdf_decorator(pdfname='orden_armado.pdf')
def wms_armado_orden_pdf_view(request, orden_id):
    
    # Orden
    orden = OrdenEmpaque.objects.get(id=orden_id)
    
    # Movimientos
    mov = Movimiento.objects.filter(n_referencia=orden.enum)
    
    # Componentes
    componentes = orden.componentes.all()
    componente_picking = []
    for i in componentes:
        movimiento = mov.filter(product_id=i)
        c_m = {
            'componente':i,
            'movimiento':movimiento
        }
        componente_picking.append(c_m)    
        
    context = {
        'orden':orden,
        'componente_picking':componente_picking,
        }
    
    return render(request, 'wms/armado_orden_pdf.html', context)


@login_required(login_url='login')
def wms_reporte_componentes_armados(request):
    # Componentes armados
    componentes_armados = ProductoArmado.objects.filter(componentes__isnull=False).values()
    
    if componentes_armados.exists():
        reporte = pd.DataFrame(componentes_armados)
        reporte = reporte.groupby(by=['product_id', 'nombre', 'marca', 'creado'])['unidades'].sum()
        reporte = reporte.reset_index()
        reporte = reporte[['product_id','nombre','marca','unidades', 'creado']]
        
        date_time = str(datetime.now())
        date_time = date_time[0:16]
        n = 'Reporte Inventario Completo_' + date_time + '_.xlsx'
        nombre = 'attachment; filename=' + '"' + n + '"'
        
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = nombre
        
        reporte.to_excel(response, index=False)

        return response    
    
    else:
        return messages.error(request, 'No hay componentes armados') #HttpResponse('No hay componentes armados')



def split_factura_movimiento(n_factura):
    
    if '-' in n_factura:
        factura = n_factura.split('-')[1][4:]
        factura = int(factura)
        return str(factura)
    else:
        return n_factura


@login_required(login_url='login')
def wms_referenica_detalle(request, referencia, n_referencia):
    
    try:
        # Picking
        picking = Movimiento.objects.filter(
            Q(referencia=referencia) &
            Q(n_referencia=n_referencia)
            )
        
        picking_df = pd.DataFrame(picking.values(
            'product_id',
            'lote_id',
            'unidades',
            'estado_picking',
            'usuario__first_name',
            'usuario__last_name'
        ))
        productos = productos_odbc_and_django()[['product_id','Nombre','Marca']]
        picking_df = picking_df.merge(productos, on='product_id', how='left')
        picking_df['unidades'] = picking_df['unidades'] * -1 
        
        context = {
            'picking' : picking.first(),
            'picking_df': de_dataframe_a_template(picking_df)
        }
        
        return render(request, 'wms/picking_detalle.html', context)
    
    except Exception as e:
        context = {'error':str(e)}
        return render(request, 'wms/picking_detalle.html', context)


def detalle_anulacion_factura_ajax(request):
    
    try:
    
        n_factura = request.POST.get('n_factura', None)
        movimientos = Movimiento.objects.filter(n_factura=n_factura)
        n_picking = movimientos.first().n_referencia
        nombre_cliente = EstadoPicking.objects.get(n_pedido=n_picking)
        
        if movimientos.exists():
            
            return JsonResponse({
                'tipo':'success',
                'msg':'Factura pendiente de anulación',
                'n_picking':movimientos.first().n_referencia.split('.')[0],
                'cliente': nombre_cliente.cliente 
            })
        else:
            return JsonResponse({
                    'tipo':'danger',
                    'msg':'La factura no existe, intente con otro número '
                })
    except:
        return JsonResponse({
            'tipo':'danger',
            'msg':'La factura no existe, intente con otro número '
        })


@transaction.atomic
def anulacion_factura_movimientos_ajax(request):
    
    try:
        if request.method == 'POST':
            n_factura = request.POST.get('n_factura')
            factura = FacturaAnulada.objects.get(n_factura=n_factura)

            if factura.estado != 'Anulado':
                movimientos = Movimiento.objects.filter(n_factura=n_factura)
                for i in movimientos:
                    mov = Movimiento(
                        product_id=i.product_id,
                        lote_id=i.lote_id,
                        fecha_caducidad=i.fecha_caducidad,
                        tipo='Ingreso',
                        descripcion='N/A',
                        referencia='Factura anulada',
                        n_referencia=n_factura,
                        n_factura='',
                        ubicacion_id=606,
                        unidades=i.unidades * -1,
                        estado='Disponible',
                        estado_picking='',
                        usuario_id=i.usuario.id,
                    )
                    
                    mov.save()
                    wms_existencias_query_product_lote(product_id=mov.product_id, lote_id=mov.lote_id)
                movimientos.update(estado_picking='No Despachado')
                factura.estado = 'Anulado'
                factura.save()

                return JsonResponse({
                    'tipo': 'success',
                    'msg': 'Factura anulada correctamente'
                })
    except Exception as e:
        
        movimientos = Movimiento.objects.filter(n_factura=n_factura)
        factura.estado = 'Pendiente'
        factura.save()

        return JsonResponse({
            'tipo': 'danger',
            'msg': f'Error al anular factura {e}'
        })


@login_required(login_url='login')
@permisos(['ADMINISTRADOR','OPERACIONES'],'/wms/home', 'ingresar a anulación de picking')
def lista_facturas_anualdas(request):
    
    facturas = FacturaAnulada.objects.all()
    
    if request.method == 'POST':
        form = FacturaAnuladaForm(request.POST)
        if form.is_valid():
            factura = form.save()
            
            if factura:
                messages.success(request, f'Factura {factura.n_factura} Anulada !!!')
                return HttpResponseRedirect('/wms/facturas-anuladas/lista') 
            else:
                messages.error(request, f'Error anulando la factura {factura.n_factura} !!!')
                return HttpResponseRedirect('/wms/facturas-anuladas/lista') 
        else:
            messages.error(request, form.errors)
            
    context = {
        'facturas': facturas,
    }
    
    return render(request, 'wms/anulacion_factura_lista.html', context)


@login_required(login_url='login')
@permisos(['ADMINISTRADOR','OPERACIONES'],'/wms/home', 'ingresar a anulación de picking')
def factura_anulada_detalle(request, n_factura):
    
    productos = productos_odbc_and_django()[['product_id','Nombre','Marca']]
    factura = FacturaAnulada.objects.get(n_factura=n_factura)
    
    mov_anulados = pd.DataFrame(Movimiento.objects.filter(n_factura=n_factura).values(
        'product_id',
        'lote_id',
        'fecha_caducidad',
        'estado_picking',
        'unidades',
        'usuario__first_name',
        'usuario__last_name'
    ))
    mov_ingresados = pd.DataFrame(Movimiento.objects.filter(n_referencia=n_factura).values(
        'product_id',
        'lote_id',
        'fecha_caducidad',
        'estado_picking',
        'unidades',
        'usuario__first_name',
        'usuario__last_name'
    ))
    
    if not mov_anulados.empty:
        mov_anulados = mov_anulados.merge(productos, on='product_id', how='left')
        mov_anulados['fecha_caducidad'] = mov_anulados['fecha_caducidad'].astype('str')
        mov_anulados['unidades'] = mov_anulados['unidades'] * -1
    
    if not mov_ingresados.empty:
        mov_ingresados = mov_ingresados.merge(productos, on='product_id', how='left')
        mov_ingresados['fecha_caducidad'] = mov_ingresados['fecha_caducidad'].astype('str')
    
    context = {
        'factura': factura,
        'anulados': de_dataframe_a_template(mov_anulados),
        'ingresados': de_dataframe_a_template(mov_ingresados),
    }
    
    return render(request, 'wms/anulacion_factura_detail.html', context)


def wms_reporte_diferencia_mba_wms(request):
    
    from datos.views import resporte_diferencia_mba_wms
    reporte  = resporte_diferencia_mba_wms()
    
        # Excel
    if not reporte.empty:
        hoy = datetime.today().strftime('%Y-%m-%d_%H-%M-%S')
        nombre_archivo = f'Reporte-Diferencia_MBA_WMS_{hoy}.xlsx'
        content_disposition = f'attachment; filename="{nombre_archivo}"'

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = content_disposition

        with pd.ExcelWriter(response, engine='openpyxl') as writer:
            
            reporte.to_excel(writer, sheet_name='Reporte-Reservas', index=False)
            
            workbook = writer.book
            worksheet = writer.sheets['Reporte-Reservas']
            
            worksheet.column_dimensions['A'].width = 20 # PRODUCT_ID
            worksheet.column_dimensions['B'].width = 20 # LOTE_ID
            worksheet.column_dimensions['C'].width = 20 # WARE_CODE
            worksheet.column_dimensions['D'].width = 20 # LOCATION
            worksheet.column_dimensions['E'].width = 15 # OH2
            worksheet.column_dimensions['F'].width = 20 # WARE_CODE_WMS
            worksheet.column_dimensions['G'].width = 20 # LOCATION_WMS
            worksheet.column_dimensions['H'].width = 15 # OH2_WMS
            
        return response

    else:
        messages.success(request, 'Reservas actualizadas, no hay items que mover !!!')
        return HttpResponseRedirect('/etiquetado/revision/imp/llegadas/list')


### COSTOS IMPORTACIÓN
# def importar_datos_costo():
    
#     path = 'C:\Erik\Egares Gimpromed\Desktop/importaciones.xlsx'
#     excel = pd.read_excel(path)
#     excel['COSTO UNIT'] = pd.to_numeric(excel['COSTO UNIT'], errors='coerce')
#     excel['DÓLAR IMPORTADO'] = pd.to_numeric(excel['DÓLAR IMPORTADO'], errors='coerce')
#     excel['ITEM'] = excel['ITEM'].astype('str')
#     excel['ITEM'] = excel['ITEM'].str.strip()
#     excel = excel.fillna('')
    
#     for i in excel.to_dict('records'):
        
#         row = CostoImportacion(
#             product_id = i['ITEM'],
#             # nombre = '', i['Nombre'],
#             # marca = '', # i['MarcaDet'],
#             costo_unitario = float(i['COSTO UNIT']),
#             dolar_importado = None if not i['DÓLAR IMPORTADO'] else float(i['DÓLAR IMPORTADO']),
#             importacion = i['IMP'],
#             gim = i['GIM'],
#             fecha_llegada = i['FECHA LLEGADA']
#         )
        
#         # row.save()
#         # print(row)


@require_POST
@csrf_exempt
def costo_importacion_cargar_excel(request):
    
    try:
        if 'archivo_excel' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No se encontró archivo'})
        
        archivo = request.FILES['archivo_excel']
        
        # Validar extensión
        if not archivo.name.endswith(('.xlsx', '.xls')):
            return JsonResponse({'success': False, 'error': 'Formato de archivo no válido'})
        
        excel_file = io.BytesIO(archivo.read())        
        df = pd.read_excel(excel_file, engine='openpyxl')
        
        if df.empty:
            return JsonResponse({
                'success':False,
                'msg':'El archivo excel esta vacio'
        })
        
        df.columns = df.columns.str.strip()
        required_columns = ['ITEM', 'COSTO UNIT', 'DÓLAR IMPORTADO', 'IMP', 'GIM', 'FECHA LLEGADA']
        missing = [col for col in required_columns if col not in df.columns]
        
        if missing:
            return JsonResponse({
                'success': False,
                'msg': 'Faltan estas columnas dentro del excel' + ', '.join(missing)
            })
        
        df['COSTO UNIT'] = pd.to_numeric(df['COSTO UNIT'], errors='coerce')
        df['DÓLAR IMPORTADO'] = pd.to_numeric(df['DÓLAR IMPORTADO'], errors='coerce')
        df['ITEM'] = df['ITEM'].astype('str')
        df['ITEM'] = df['ITEM'].str.strip()
        df = df.fillna('') 

        for i in df.to_dict('records'):
            
            row_exist = CostoImportacion.objects.filter(Q(product_id=i['ITEM']) & Q(importacion=i['IMP']))
            if row_exist.exists():
                continue
            else:
                row = CostoImportacion(
                    product_id = i['ITEM'],
                    costo_unitario = float(i['COSTO UNIT']),
                    dolar_importado = None if not i['DÓLAR IMPORTADO'] else float(i['DÓLAR IMPORTADO']),
                    importacion = i['IMP'],
                    gim = i['GIM'],
                    fecha_llegada = i['FECHA LLEGADA']
                )
                row.save()
            
        completar_data_products()
        
        return JsonResponse({
            'success':True
        })
        
    except Exception as e:
        return JsonResponse({
            'success':False,
            'msg':str(e)
        })


def completar_data_products():
    
    try:
        costos_imp = CostoImportacion.objects.filter(Q(nombre='') | Q(marca=''))
        
        def mba_data(product_id: str) -> dict:
            with connections['gimpromed_sql'].cursor() as cursor:
                cursor.execute("""
                    SELECT Nombre, MarcaDet 
                    FROM warehouse.productos 
                    WHERE Codigo = %s
                """, [product_id])  # ✅ evita inyección SQL

                row = cursor.fetchone()
                if not row:
                    return {}  # si no hay producto, devolver dict vacío

                columns = [col[0].lower() for col in cursor.description]
                return dict(zip(columns, row))

        
        for i in costos_imp:
            prod = mba_data(i.product_id)
            i.nombre = prod['nombre']
            i.marca  = prod['marcadet']
            i.save()
    except:
        pass


def lista_productos_costo_importacion(_request):
    
    prods = productos_mba_django()[['product_id', 'nombre', 'marca']]
    product_list = pd.DataFrame(CostoImportacion.objects.values('product_id').distinct())
    product_list = product_list.merge(prods, on='product_id', how='left').sort_values(by=['marca', 'product_id']).fillna('')
    
    return JsonResponse({
        'success': True,
        'data': de_dataframe_a_template(product_list)
    })


def costo_importacion_product_id(request, product_id):
    data = CostoImportacion.objects.filter(product_id=product_id).order_by('fecha_llegada', 'gim').values()
    return JsonResponse({
        'success':True,
        'data':list(data)
    })


@login_required(login_url='login')
@permisos(['COSTO IMPORTACION'],'/wms/home', 'ingresar a costos de importación')
def wms_costo_importacion(request):
    return render(request, 'wms/costo_importacion.html')
