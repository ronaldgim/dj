from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
from datos.models import Reservas
from datos.views import productos_odbc_and_django, de_dataframe_a_template
# from etiquetado.views import calculos_pedido
import pandas as pd
from datetime import timedelta
from typing import Dict, List, Optional, Any
import numpy as np

from etiquetado.models import AddEtiquetadoPublico, PedidosEstadoEtiquetado #PedidoTemporal
from django.forms.models import model_to_dict
from django.db import connections

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
        't_total_vol': pedido['vol_total'].sum(),
        't_total_pes': pedido['pes_total'].sum(), 
        't_cartones': pedido['Cartones'].sum(),
        't_unidades': pedido['quantity'].sum(),
        
        # Tiempos totales
        'tt_str_1p': _segundos_a_timedelta_str(pedido['t_s_1p'].sum()),
        'tt_str_2p': _segundos_a_timedelta_str(pedido['t_s_2p'].sum()),
        'tt_str_3p': _segundos_a_timedelta_str(pedido['t_s_3p'].sum()),
        
        # Indicador de peso cero
        'p_cero': (pedido['pes_total'] == 0).any()
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
        return 't2'
    elif not cero_in_t1:
        return 't1'
    elif not cero_in_t3:
        return 't3'
    else:
        return 'F'


def lista_pedidos_publico():
    """
    Lista de pedidos publicos sec_name_cliente = 'PUBLICO'
    Lista de pedidos agregados etiquetado models 'AddEtiquetadoPublico'
    Lista de pedidos temporales
    """
    
    pedidos_publicos = Reservas.objects.filter(sec_name_cliente='PUBLICO').values_list('contrato_id', flat=True).distinct()
    agregados = AddEtiquetadoPublico.objects.all().values_list('contrato_id', flat=True).distinct()
    pedidos_mas_agregados = pedidos_publicos.union(agregados)
    finalizados = PedidosEstadoEtiquetado.objects.filter(estado__id=3).order_by('-n_pedido').values_list('n_pedido', flat=True).distinct()[:500]
    # temporales = PedidoTemporal.objects.all()
    
    pedidos_mas_agregados_set = set(pedidos_mas_agregados)
    
    finalizados_list = []
    for i in finalizados:
        contrato_id = i.split('.')[0]
        finalizados_list.append(contrato_id)
    
    finalizados_set = set(finalizados_list)
    
    publico_dashboard = pedidos_mas_agregados_set - finalizados_set
    
    return list(publico_dashboard)


def metricas_pedido(contrato_id):

    pedido_db = Reservas.objects.filter(contrato_id=contrato_id).values('product_id', 'quantity')
    pedido_df = pd.DataFrame(pedido_db).groupby('product_id')['quantity'].sum().reset_index()
    products_master = productos_odbc_and_django()[['product_id','Nombre','Marca','Unidad_Empaque', 't_etiq_1p', 't_etiq_2p', 't_etiq_3p', 'vol_m3', 'Peso']]
    
    pedido = pedido_df.merge(products_master, on='product_id', how='left').fillna(0)
    
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


def cliente_from_codigo(codigo_cliente):
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(f"SELECT * FROM warehouse.clientes WHERE CODIGO_CLIENTE = '{codigo_cliente}';")
        connections['gimpromed_sql'].close()
        columns = [col[0] for col in cursor.description]
        result = cursor.fetchone()
        if result:
            return dict(zip(columns, result))
        return {}


def calcular_cabecera_totales(contrato_id):
    
    contrato = Reservas.objects.filter(contrato_id=contrato_id) #.first()

    cabecera = model_to_dict(instance=contrato.first(), fields=['contrato_id', 'fecha_pedido', 'hora_llegada','ware_code','confirmed'])
    cliente = cliente_from_codigo(contrato.first().codigo_cliente)
    
    
    return {
        'cabecera':cabecera,
        'cliente':cliente,
        'totales':_calcular_totales(metricas_pedido(contrato_id)),
        'tiempo':_determinar_tipo_tiempo(metricas_pedido(contrato_id))
    }


def pedido_data(request):
    
    publico = lista_pedidos_publico()[:1]
    
    for i in publico:
        cal = calcular_cabecera_totales(i)
        print(cal)
    
    
    
    return HttpResponse('ok')



