from django.shortcuts import render
from django.http import HttpResponse, JsonResponse

# Create your views here.
from datos.models import Reservas
from datos.views import productos_odbc_and_django, de_dataframe_a_template
# from etiquetado.views import calculos_pedido
import pandas as pd
from datetime import timedelta
from typing import Dict, List, Optional, Any
import numpy as np

from etiquetado.models import AddEtiquetadoPublico, PedidosEstadoEtiquetado, EtiquetadoAvance, FechaEntrega, EstadoPicking, PedidoTemporal
from django.forms.models import model_to_dict
from django.db import connections
from datetime import datetime, timedelta
from wms.models import Existencias


"""
# # publico = ['90447', '90420', '90392', '90456', '90324']
# publico = ['90324']

# reservas = Reservas.objects.filter(contrato_id__in=publico)


# def calculos_pedido(productos_values):
    
#     productos_df = productos_odbc_and_django()
#     productos = pd.DataFrame(productos_values).rename(columns={'id':'id_product_temporal'})
    
#     if not productos.empty:
    
#         pedido = productos.merge(productos_df, on='product_id', how='left').fillna(0)
#         # pedido = pedido.rename(columns={
#         #     'product_id':'PRODUCT_ID',
#         #     'Nombre':'PRODUCT_NAME',
#         #     'cantidad':'QUANTITY'})
#         print(pedido)
#         # Calculos
#         # pedido['Cartones'] = (pedido['QUANTITY'] / pedido['Unidad_Empaque']).round(2)
#         pedido['Cartones'] = (pedido['quantity'] / pedido['Unidad_Empaque']).round(2)
        
#         #pedido = pedido.fillna(0.0).replace(np.inf, 0.0)
        
#         pedido['t_una_p_min'] = (pedido['Cartones'] * pedido['t_etiq_1p']) / 60
#         pedido['t_una_p_hor'] = pedido['t_una_p_min'] / 60
#         pedido['t_dos_p_hor'] = ((pedido['Cartones'] * pedido['t_etiq_2p']) / 60) / 60
#         pedido['t_tre_p_hor'] = ((pedido['Cartones'] * pedido['t_etiq_3p']) / 60) / 60
#         pedido['vol_total'] = pedido['Cartones'] * (pedido['Volumen'] / 1000000)
#         pedido['pes_total'] = pedido['Cartones'] * pedido['Peso']
        
#         p_cero = 0 in list(pedido['pes_total']) 
        
#         #pedido = pedido.fillna(0.0).replace(np.inf, 0.0) 

#         # Mejor formato de tiempo
#         pedido['t_s_1p']   = (pedido['Cartones'] * pedido['t_etiq_1p'].round(0))
#         pedido['t_str_1p'] = [str(timedelta(seconds=int(i))) for i in pedido['t_s_1p']] 

#         pedido['t_s_2p']   = (pedido['Cartones'] * pedido['t_etiq_2p']).round(0)
#         pedido['t_str_2p'] = [str(timedelta(seconds=int(i))) for i in pedido['t_s_2p']]

#         pedido['t_s_3p']   = (pedido['Cartones'] * pedido['t_etiq_3p'].round(0))
#         pedido['t_str_3p'] = [str(timedelta(seconds=int(i))) for i in pedido['t_s_3p']]

#         tt_str_1p = str(timedelta(seconds=int(pedido['t_s_1p'].sum())))
#         tt_str_2p = str(timedelta(seconds=int(pedido['t_s_2p'].sum())))
#         tt_str_3p = str(timedelta(seconds=int(pedido['t_s_3p'].sum())))
        
#         cero_in_t1 = 0 in list(pedido['t_s_1p'])
#         cero_in_t2 = 0 in list(pedido['t_s_2p'])
#         cero_in_t3 = 0 in list(pedido['t_s_3p'])
        
#         t_total_vol = pedido['vol_total'].sum()
#         t_total_pes = pedido['pes_total'].sum()
#         t_cartones = pedido['Cartones'].sum()
#         # t_unidades = pedido['QUANTITY'].sum()
#         t_unidades = pedido['quantity'].sum()
        

#         pedido = {
#             'productos': de_dataframe_a_template(pedido)
#             }
        
#         if not cero_in_t2:
#             pedido['TIEMPOS'] = 't2'
#         elif cero_in_t2 and not cero_in_t1:
#             pedido['TIEMPOS'] = 't1'
#         elif cero_in_t1 and cero_in_t2 and not cero_in_t3:
#             pedido['TIEMPOS'] = 't3'
#         elif cero_in_t1 and cero_in_t2 and cero_in_t3:
#             pedido['TIEMPOS'] = 'F'
        
#         pedido['tt_str_1p'] = tt_str_1p
#         pedido['tt_str_2p'] = tt_str_2p
#         pedido['tt_str_3p'] = tt_str_3p
        
#         pedido['t_total_vol'] = t_total_vol
#         pedido['t_total_pes'] = t_total_pes
#         pedido['t_cartones'] = t_cartones
#         pedido['t_unidades'] = t_unidades
        
#         pedido['p_cero'] = p_cero

#         return pedido
    
#     else:
#         return {}
"""



def calculos_pedido_optimized(productos_values: List[Dict]) -> Dict[str, Any]:
    """
    Optimiza cálculos de pedido con mejor rendimiento y manejo de errores.
    
    Args:
        productos_values: Lista de diccionarios con productos del pedido
        
    Returns:
        Dict con datos calculados del pedido o dict vacío si no hay productos
    """
    # Validación temprana
    if not productos_values:
        # logger.warning("Lista de productos vacía")
        return {}
    
    try:
        # Convertir a DataFrame una sola vez
        productos_df = pd.DataFrame(productos_values) #.rename(
        #     columns={'id': 'id_product_temporal'}
        # )
        
        if productos_df.empty:
            return {}
        
        # Obtener datos de productos (cachear si es posible)
        productos_master = productos_odbc_and_django()
        
        # Merge optimizado con validación
        pedido = productos_df.merge(
            productos_master, 
            on='product_id', 
            how='left'
        )#.fillna(0).infer_objects(copy=False)
        
        # Calcular todas las métricas en una pasada
        pedido = _calcular_metricas_pedido(pedido)
        
        # Calcular totales y tiempos
        totales = _calcular_totales(pedido)
        
        # Determinar tipo de tiempo óptimo
        tipo_tiempo = _determinar_tipo_tiempo(pedido)
        
        # Preparar resultado final
        resultado = {
            'productos': de_dataframe_a_template(pedido),
            'TIEMPOS': tipo_tiempo,
            **totales
        }
        
        # logger.info(f"Pedido calculado: {len(pedido)} productos, tipo tiempo: {tipo_tiempo}")
        return resultado
        
    except Exception as e:
        # logger.error(f"Error en cálculos de pedido: {str(e)}")
        return {}


def _calcular_metricas_pedido(pedido: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula todas las métricas del pedido en operaciones vectorizadas.
    """
    # Validar columnas requeridas
    required_cols = ['quantity', 'Unidad_Empaque', 't_etiq_1p', 't_etiq_2p', 't_etiq_3p', 'vol_m3', 'Peso']
    
    missing_cols = [col for col in required_cols if col not in pedido.columns]
    if missing_cols:
        # logger.warning(f"Columnas faltantes: {missing_cols}")
        for col in missing_cols:
            pedido[col] = 0
    
    # Operaciones vectorizadas (mucho más rápido que iteraciones)
    with np.errstate(divide='ignore', invalid='ignore'):
        # Cálculo base
        pedido['Cartones'] = (pedido['quantity'] / pedido['Unidad_Empaque'].replace(0, 1)) #.round(2)
        
        # Tiempos en diferentes formatos (vectorizado)
        cartones = pedido['Cartones']
        
        # Tiempos en horas
        pedido['t_una_p_min'] = (cartones * pedido['t_etiq_1p']) / 60
        pedido['t_una_p_hor'] = pedido['t_una_p_min'] / 60
        pedido['t_dos_p_hor'] = (cartones * pedido['t_etiq_2p']) / 3600  # Directo a horas
        pedido['t_tre_p_hor'] = (cartones * pedido['t_etiq_3p']) / 3600
        
        # Volumen y peso totales
        pedido['vol_total'] = cartones * pedido['vol_m3']
        
        pedido['pes_total'] = cartones * pedido['Peso']
        
        # Tiempos en segundos para formato string
        pedido['t_s_1p'] = (cartones * pedido['t_etiq_1p']).round(0).astype(int)
        pedido['t_s_2p'] = (cartones * pedido['t_etiq_2p']).round(0).astype(int)
        pedido['t_s_3p'] = (cartones * pedido['t_etiq_3p']).round(0).astype(int)
        
    # Convertir tiempos a string format (solo una vez al final)
    pedido['t_str_1p'] = pedido['t_s_1p'].apply(_segundos_a_timedelta_str)
    pedido['t_str_2p'] = pedido['t_s_2p'].apply(_segundos_a_timedelta_str)
    pedido['t_str_3p'] = pedido['t_s_3p'].apply(_segundos_a_timedelta_str)
    
    # Reemplazar infinitos y NaN
    pedido = pedido.replace([np.inf, -np.inf], 0).fillna(0)
    
    return pedido


def _segundos_a_timedelta_str(segundos: int) -> str:
    """Convierte segundos a string de timedelta de forma eficiente."""
    try:
        return str(timedelta(seconds=int(segundos)))
    except (ValueError, OverflowError):
        return "0:00:00"


def _calcular_totales(pedido: pd.DataFrame) -> Dict[str, Any]:
    """
    Calcula totales del pedido de forma optimizada.
    """
    # Calcular totales usando operaciones vectorizadas de pandas
    totales = {
        't_total_vol': float(pedido['vol_total'].sum()),
        't_total_pes': float(pedido['pes_total'].sum()), 
        't_cartones': float(pedido['Cartones'].sum()),
        't_unidades': float(pedido['quantity'].sum()),
        
        # Tiempos totales
        'tt_str_1p': _segundos_a_timedelta_str(pedido['t_s_1p'].sum()),
        'tt_str_2p': _segundos_a_timedelta_str(pedido['t_s_2p'].sum()),
        'tt_str_3p': _segundos_a_timedelta_str(pedido['t_s_3p'].sum()),
        
        # Indicador de peso cero
        'p_cero': bool((pedido['pes_total'] == 0).any())
    }
    
    return totales


def _determinar_tipo_tiempo(pedido: pd.DataFrame) -> str:
    """
    Determina el tipo de tiempo óptimo basado en disponibilidad.
    Usa operaciones vectorizadas para mejor rendimiento.
    """
    # Verificar ceros usando operaciones vectorizadas
    cero_in_t1 = (pedido['t_s_1p'] == 0).any()
    cero_in_t2 = (pedido['t_s_2p'] == 0).any()
    cero_in_t3 = (pedido['t_s_3p'] == 0).any()
    
    # Lógica optimizada con early return
    if not cero_in_t2:
        # return 't2'
        tiempo =  _calcular_totales(pedido)['tt_str_2p']
    elif not cero_in_t1:
        # return 't1'
        tiempo = _calcular_totales(pedido)['tt_str_1p']
    elif not cero_in_t3:
        # return 't3'
        tiempo = _calcular_totales(pedido)['tt_str_3p']
    else:
        tiempo = 'F'
    
    return {
        'tiempo':tiempo,
        'tiempo_1':_calcular_totales(pedido)['tt_str_1p'],
        'tiempo_2':_calcular_totales(pedido)['tt_str_2p'],
        'tiempo_3':_calcular_totales(pedido)['tt_str_3p']
    }


def stock_mba_wms():
    def stock_mba_andagoya():
        with connections['gimpromed_sql'].cursor() as cursor:
            cursor.execute(f"SELECT PRODUCT_ID, WARE_CODE, OH2 FROM warehouse.stock_lote WHERE WARE_CODE = 'BAN';") # OR WARE_CODE = 'BCT'; ")
            connections['gimpromed_sql'].close()
            columns = [col[0].lower() for col in cursor.description]
            stock = [dict(zip(columns, row)) for row in cursor.fetchall()]
            stock = pd.DataFrame(stock)
            stock = stock.groupby(['product_id', 'ware_code'])['oh2'].sum().reset_index()
            stock = stock.rename(columns={'oh2':'unidades'})
            return stock
    
    def stock_wms_cerezos():
        stock = Existencias.objects.filter(estado='Disponible').values('product_id','unidades')
        stock = pd.DataFrame(stock).groupby('product_id')['unidades'].sum().reset_index()
        stock['ware_code'] = 'BCT'
        stock = stock[['product_id','ware_code','unidades']]
        return stock
    
    mba = stock_mba_andagoya() 
    wms = stock_wms_cerezos() 
    
    data = pd.concat([mba, wms]) 
    return data


def metricas_pedido(contrato_id):

    pedido_db = Reservas.objects.filter(contrato_id=contrato_id).values('product_id', 'ware_code', 'quantity')
    pedido_df = pd.DataFrame(pedido_db).groupby(['product_id','ware_code'])['quantity'].sum().reset_index()
    products_master = productos_odbc_and_django()[['product_id','Nombre','Marca','Unidad_Empaque', 't_etiq_1p', 't_etiq_2p', 't_etiq_3p', 'vol_m3', 'Peso']]
    
    pedido = pedido_df.merge(products_master, on='product_id', how='left').fillna(0)
    pedido = pedido.merge(stock_mba_wms(), on=['product_id','ware_code'], how='left').fillna(0)
    pedido['cartones'] = pedido['quantity'] / pedido['Unidad_Empaque']
    pedido['diff'] = pedido['quantity'] >= pedido['unidades']
    
    # Operaciones vectorizadas (mucho más rápido que iteraciones)
    with np.errstate(divide='ignore', invalid='ignore'):
        # Cálculo base
        pedido['Cartones'] = (pedido['quantity'] / pedido['Unidad_Empaque'].replace(0, 1)) #.round(2)
        
        # Tiempos en diferentes formatos (vectorizado)
        cartones = pedido['Cartones']
        
        # Tiempos en horas
        pedido['t_una_p_min'] = (cartones * pedido['t_etiq_1p']) / 60
        pedido['t_una_p_hor'] = pedido['t_una_p_min'] / 60
        pedido['t_dos_p_hor'] = (cartones * pedido['t_etiq_2p']) / 3600  # Directo a horas
        pedido['t_tre_p_hor'] = (cartones * pedido['t_etiq_3p']) / 3600
        
        # Volumen y peso totales
        pedido['vol_total'] = cartones * pedido['vol_m3']
        pedido['pes_total'] = cartones * pedido['Peso']
        
        # Tiempos en segundos para formato string
        pedido['t_s_1p'] = (cartones * pedido['t_etiq_1p']).round(0).astype(int)
        pedido['t_s_2p'] = (cartones * pedido['t_etiq_2p']).round(0).astype(int)
        pedido['t_s_3p'] = (cartones * pedido['t_etiq_3p']).round(0).astype(int)
        
    # Convertir tiempos a string format (solo una vez al final)
    pedido['t_str_1p'] = pedido['t_s_1p'].apply(_segundos_a_timedelta_str)
    pedido['t_str_2p'] = pedido['t_s_2p'].apply(_segundos_a_timedelta_str)
    pedido['t_str_3p'] = pedido['t_s_3p'].apply(_segundos_a_timedelta_str)
    
    # Reemplazar infinitos y NaN
    pedido = pedido.replace([np.inf, -np.inf], 0).fillna(0)

    # Stock completo
    stock_completo = bool((pedido['diff'] == False ).any()) 

    return {
        'pedido':pedido,
        'stock_completo':stock_completo
    }


def cliente_from_codigo(codigo_cliente):
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(f"SELECT * FROM warehouse.clientes WHERE CODIGO_CLIENTE = '{codigo_cliente}';")
        connections['gimpromed_sql'].close()
        columns = [col[0].lower() for col in cursor.description]
        result = cursor.fetchone()
        if result:
            return dict(zip(columns, result))
        return {}


def cliente_ciudad_from_nombre(nombre_cliente):
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(f"SELECT CIUDAD_PRINCIPAL FROM warehouse.clientes WHERE NOMBRE_CLIENTE = '{nombre_cliente}';")
        connections['gimpromed_sql'].close()
        columns = [col[0].lower() for col in cursor.description]
        result = cursor.fetchone()
        if result:
            return dict(zip(columns, result))
        return {
            'ciudad_principal':'-'
        }

"""
def prints_pedidos_por_contrato_id(contrato_id):
    with connections['gimpromed_sql'].cursor() as cursor:
        query = "
            SELECT 
                p.CONTRATO_ID,
                p.FECHA_PEDIDO,
                p.WARE_CODE,
                p.CONFIRMED,
                p.HORA_LLEGADA,
                p.NUM_PRINT,
                p.Entry_by,
                u.USER_NAME,
                u.FIRST_NAME,
                u.LAST_NAME,
                u.MAIL
            FROM 
                pedidos p
            JOIN 
                user_mba u
            ON 
                p.Entry_by = u.CODIGO_USUARIO
            WHERE 
                p.CONTRATO_ID = %s;
        "
        cursor.execute(query, [contrato_id])
        result = cursor.fetchone()

        if result:
            columns = [col[0].lower() for col in cursor.description] 
            return dict(zip(columns, result))
        return {
            'contrato_id':'-',
            'fecha_pedido':'-',
            'ware_code':'-',
            'confirmed':'-',
            'hora_llegada':'-',
            'num_print':'-',
            'entry_by':'-',
            'user_name':'-',
            'first_name':'-',
            'last_name':'-',
            'mail':'-'
        }
"""


def prints_pedidos_por_contrato(contrato_id):
    with connections['gimpromed_sql'].cursor() as cursor:
        query = f"SELECT NUM_PRINT FROM warehouse.pedidos WHERE CONTRATO_ID = '{contrato_id}';"
        cursor.execute(query)
        result = cursor.fetchone()

        if result:
            columns = [col[0].lower() for col in cursor.description] 
            return dict(zip(columns, result))
        return {
            'num_print':'-',
        }


def etiquetado(contrato_id):
    
    avance = EtiquetadoAvance.objects.filter(n_pedido=contrato_id+'.0')
    reserva = Reservas.objects.filter(contrato_id=contrato_id)
    if avance.exists():
        t_unidades_avance = sum(avance.values_list('unidades', flat=True)) 
        t_unidades_pedido = sum(reserva.values_list('quantity', flat=True)) 
        porcentaje_avance = round((t_unidades_avance / t_unidades_pedido) * 100, 1) 
        
    else:
        porcentaje_avance = 0
    
    etiquetado = PedidosEstadoEtiquetado.objects.filter(n_pedido=contrato_id+'.0')
    if etiquetado.exists():
        estado_etiquetado = etiquetado.first().estado.estado  
    else:
        estado_etiquetado = '-' 
    
    return {
        'avance':f'{porcentaje_avance} %',
        'estado_etiquetado':estado_etiquetado
    }


def picking(contrato_id):
    picking = EstadoPicking.objects.filter(n_pedido=contrato_id+'.0')
    if picking.exists():
        return {
            'estado_picking':picking.first().estado,
            'user':f'{picking.first().user.user.first_name[:1]}.{picking.first().user.user.last_name[:1]}',
            'user_full_name': f'{picking.first().user.user.first_name} {picking.first().user.user.last_name}'
        }
    else:
        return {
            'estado_picking':'-',
            'user':'-',
            'user_full_name': '-'
        }


def entrega(contrato_id):
    entrega_qs = FechaEntrega.objects.filter(pedido=contrato_id+'.0')
    entrega_obj = entrega_qs.first()
    if entrega_obj:
        try:
            dias_faltantes = (entrega_obj.fecha_hora - datetime.today()).days
        except (AttributeError, TypeError):
            dias_faltantes = '-'
        data = model_to_dict(entrega_obj, ['fecha_hora','estado'])
        data['dias_faltantes'] = dias_faltantes
        return data
    else:
        return {
            'fecha_hora': '-',
            'estado': '-',
            #'pedido': '-',
            #'user': '-',
            #'est_entrega': '-',
            #'reg_entrega': '-',
            'dias_faltantes': '-'
        }


# def calcular_cabecera_totales(contrato_id):
    
#     contrato = Reservas.objects.filter(contrato_id=contrato_id) #.first()

#     cabecera = model_to_dict(instance=contrato.first(), fields=['contrato_id', 'fecha_pedido', 'hora_llegada','ware_code','confirmed'])
#     cliente = cliente_from_codigo(contrato.first().codigo_cliente)
#     pedido = prints_pedidos_por_contrato(contrato_id=contrato_id)
    
#     entrega = FechaEntrega.objects.filter(pedido=(contrato_id+'.0'))
#     if entrega.exists():
#         entrega_data = model_to_dict(entrega.first())
#         fecha_entrega = entrega.first().fecha_hora#.date()
#         to_day = datetime.today()#.date()
#         dias_faltantes = (fecha_entrega - to_day).days
#         if dias_faltantes < 0 :
#             dias_faltantes = None
#         else:
#             dias_faltantes = dias_faltantes
#     else:
#         entrega_data = {}
#         dias_faltantes = None
    
#     tiempo = _determinar_tipo_tiempo(metricas_pedido(contrato_id)['pedido'])
    
#     if tiempo in ('t1', 't2', 't3'):  #, 'F'):
#         totales = _calcular_totales(metricas_pedido(contrato_id)['pedido'])
        
#         clave_por_tiempo = {
#             't1': 'tt_str_1p',
#             't2': 'tt_str_2p',
#             't3': 'tt_str_3p',
#             'F': 'tt_str_F',
#         }
    
#         tiempo_total = totales.get(clave_por_tiempo[tiempo])
#     elif tiempo == 'F':
#         tiempo_total = 'F' # None  # o lanzar un error si es un caso inválido
#     else:
#         tiempo_total = 'F'
    
#     return {
#         'cabecera':cabecera,
#         'cliente':cliente,
#         'totales':_calcular_totales(metricas_pedido(contrato_id)['pedido']),
#         'tiempo_total':tiempo_total,
#         'tiempos':_determinar_tipo_tiempo(metricas_pedido(contrato_id)['pedido']),
#         'entrega':entrega_data,
#         'pedido':pedido,
#         'dias_faltantes':dias_faltantes,
#         'stock_completo':metricas_pedido(contrato_id)['stock_completo'],
#         # 'estado_etiquetado':estado_avance_etiquetado(contrato_id)
#     }


def pedidos_temporales_func():
    
    try: 
        pedidos = PedidoTemporal.objects.filter(estado='PENDIENTE')
        if not pedidos.exists():
            return []
        
        product_master = productos_odbc_and_django()[['product_id','Nombre','Marca','Unidad_Empaque', 't_etiq_1p', 't_etiq_2p', 't_etiq_3p', 'vol_m3', 'Peso']]
        
        data_list = []
        for i in pedidos:
            pedido = pd.DataFrame(i.productos.all().values('product_id','cantidad'))
            pedido = pedido.rename(columns={'cantidad':'quantity'})
            pedido = pedido.merge(product_master, on='product_id', how='left')
            pedido['cartones'] = pedido['quantity'] / pedido['Unidad_Empaque']
            
            with np.errstate(divide='ignore', invalid='ignore'):
                # Cálculo base
                pedido['Cartones'] = (pedido['quantity'] / pedido['Unidad_Empaque'].replace(0, 1)) #.round(2)
                
                # Tiempos en diferentes formatos (vectorizado)
                cartones = pedido['Cartones']
                
                # Tiempos en horas
                pedido['t_una_p_min'] = (cartones * pedido['t_etiq_1p']) / 60
                pedido['t_una_p_hor'] = pedido['t_una_p_min'] / 60
                pedido['t_dos_p_hor'] = (cartones * pedido['t_etiq_2p']) / 3600  # Directo a horas
                pedido['t_tre_p_hor'] = (cartones * pedido['t_etiq_3p']) / 3600
                
                # Volumen y peso totales
                pedido['vol_total'] = cartones * pedido['vol_m3']
                pedido['pes_total'] = cartones * pedido['Peso']
                
                # Tiempos en segundos para formato string
                pedido['t_s_1p'] = (cartones * pedido['t_etiq_1p']).round(0).astype(int)
                pedido['t_s_2p'] = (cartones * pedido['t_etiq_2p']).round(0).astype(int)
                pedido['t_s_3p'] = (cartones * pedido['t_etiq_3p']).round(0).astype(int)
        
            # Convertir tiempos a string format (solo una vez al final)
            pedido['t_str_1p'] = pedido['t_s_1p'].apply(_segundos_a_timedelta_str)
            pedido['t_str_2p'] = pedido['t_s_2p'].apply(_segundos_a_timedelta_str)
            pedido['t_str_3p'] = pedido['t_s_3p'].apply(_segundos_a_timedelta_str)
            
            # Reemplazar infinitos y NaN
            pedido = pedido.replace([np.inf, -np.inf], 0).fillna(0)
            
            try:
                dias_faltantes = (i.entrega - datetime.today()).days
            except (AttributeError, TypeError):
                dias_faltantes = '-'
            
            data = {
                'id':i.id,
                'tipo_pedido':'temporal',
                'contrato_id':i.enum,
                'estado_picking': '-',
                'user_picking': '-',
                'user_picking_full_name': '',
                'confirmado': '-',
                'stock_completo': '-',
                'print': '-',
                'nombre_cliente': i.cliente, 
                'ciudad_cliente': cliente_ciudad_from_nombre(i.cliente)['ciudad_principal'], 
                'fecha_hora_entrega': i.entrega,
                'estado_fecha_hora_entrega': '-', 
                'dias_faltantes': dias_faltantes,
                'estado_etiquetado': '-',
                'avance_etiquetado':'-',
                'estado_entrega': '-', #entrega(i)['est_entrega'],
                'tiempo':_determinar_tipo_tiempo(pedido)['tiempo'],
                'tiempo_1':_determinar_tipo_tiempo(pedido)['tiempo_1'],
                'tiempo_2':_determinar_tipo_tiempo(pedido)['tiempo_2'],
                'tiempo_3': _determinar_tipo_tiempo(pedido)['tiempo_3'],
            }
        
            data_list.append(data)  
        
        return data_list
    except Exception as e:
        print(e)
        return []


def data_dashboard_pedidos(contratos_list):
    try:
        data_list = []
        for i in contratos_list:
            
            reserva = Reservas.objects.filter(contrato_id=i) # .first()
            
            if reserva.exists():
                reserva = reserva.first()

                data = {
                    'id':reserva.id,
                    'tipo_pedido':'mba',
                    'contrato_id':i,
                    'estado_picking': picking(i)['estado_picking'],
                    'user_picking': picking(i)['user'],
                    'user_picking_full_name': picking(i)['user_full_name'],
                    'confirmado': reserva.confirmed,
                    'stock_completo': metricas_pedido(i)['stock_completo'],
                    'print': prints_pedidos_por_contrato(i)['num_print'],
                    'nombre_cliente': cliente_from_codigo(reserva.codigo_cliente)['nombre_cliente'], 
                    'ciudad_cliente': cliente_from_codigo(reserva.codigo_cliente)['ciudad_principal'], 
                    'fecha_hora_entrega': entrega(i)['fecha_hora'],
                    'estado_fecha_hora_entrega': entrega(i)['estado'], 
                    'dias_faltantes': entrega(i)['dias_faltantes'], 
                    'estado_etiquetado': etiquetado(i)['estado_etiquetado'],
                    'avance_etiquetado':etiquetado(i)['avance'],
                    'estado_entrega': '-', #entrega(i)['est_entrega'],
                    'tiempo':_determinar_tipo_tiempo(metricas_pedido(i)['pedido'])['tiempo'],
                    'tiempo_1':_determinar_tipo_tiempo(metricas_pedido(i)['pedido'])['tiempo_1'],
                    'tiempo_2':_determinar_tipo_tiempo(metricas_pedido(i)['pedido'])['tiempo_2'],
                    'tiempo_3': _determinar_tipo_tiempo(metricas_pedido(i)['pedido'])['tiempo_3'],
                }
                
                data_list.append(data)
                
        # Ordenar la lista por 'fecha_hora_entrega' como objeto de tiempo si es posible
        def parse_fecha(fecha):
            if isinstance(fecha, datetime):
                return fecha
            try:
                # Intenta parsear si es string
                return datetime.fromisoformat(fecha)
            except Exception:
                return datetime.min

        data_list = sorted(data_list, key=lambda x: parse_fecha(x.get('fecha_hora_entrega')))
        return data_list
    except Exception as e:
        print(e)


def lista_publicos_dashboard_completo():
    """
    Lista de pedidos publicos sec_name_cliente = 'PUBLICO'
    Lista de pedidos agregados etiquetado models 'AddEtiquetadoPublico'
    Lista de pedidos temporales
    """
    
    pedidos_publicos = Reservas.objects.filter(sec_name_cliente='PUBLICO').values_list('contrato_id', flat=True).distinct()
    agregados = AddEtiquetadoPublico.objects.all().values_list('contrato_id', flat=True).distinct()
    pedidos_mas_agregados = pedidos_publicos.union(agregados)
    finalizados = PedidosEstadoEtiquetado.objects.filter(estado__id=3).order_by('-n_pedido').values_list('n_pedido', flat=True).distinct()[:50]
    # temporales = PedidoTemporal.objects.all()
    
    pedidos_mas_agregados_set = set(pedidos_mas_agregados)
    
    finalizados_list = []
    for i in finalizados:
        contrato_id = i.split('.')[0]
        finalizados_list.append(contrato_id)
    
    finalizados_set = set(finalizados_list)
    
    publico_dashboard = pedidos_mas_agregados_set - finalizados_set

    return list(publico_dashboard)


def lista_publicos_finalizados():
    
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(f"SELECT CONTRATO_ID FROM warehouse.reservas WHERE SEC_NAME_CLIENTE = 'PUBLICO';")
        contratos = [ i[0] for i in cursor.fetchall()]
        connections['gimpromed_sql'].close()
    
    finalizados = PedidosEstadoEtiquetado.objects.filter(estado__id=3).order_by('-n_pedido').values_list('n_pedido', flat=True).distinct()[:50]
    contratos_list = set(contratos) & set(finalizados)
    
    pedidos_por_entregar = []
    for i in contratos_list:
        contrato = i.split('.')[0]
        pedidos_por_entregar.append(contrato)
    
    return pedidos_por_entregar


# Dashboard completo
def data_publicos_dashboard_completo(request):
    
    pedidos_temporales = pedidos_temporales_func()
    pedidos = data_dashboard_pedidos(lista_publicos_dashboard_completo())
    
    if pedidos_temporales:
        pedidos += pedidos_temporales
        
    por_entregar = data_dashboard_pedidos(lista_publicos_finalizados())

    return JsonResponse({
        'pedidos':pedidos,
        'por_entregar':por_entregar
    })


def dashboard_publico(request):
    return render(request, 'dashboards/etiquetado_publico_vue.html')


def dashboard_completo(request):
    return render(request, 'dashboards/dashboard_completo_nuevo_vue.html')
