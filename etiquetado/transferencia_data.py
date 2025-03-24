# DB
from django.db import connections

# Pandas
import pandas as pd

# Numpy 
import numpy as np

# Wms
from wms.models import Existencias


# Data
from datos.views import frecuancia_ventas, productos_odbc_and_django, stock_de_seguridad


def stock_andagoya(): 
    
    with connections['gimpromed_sql'].cursor() as cursor:
        # cursor.execute("SELECT * FROM warehouse.stock_lote WHERE WARE_CODE = 'BAN'")
        cursor.execute("SELECT PRODUCT_ID, OH2 FROM warehouse.stock_lote WHERE WARE_CODE = 'BAN'")
        columns = [col[0] for col in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]

        data = pd.DataFrame(data)
        
        data = data.groupby('PRODUCT_ID')['OH2'].sum().reset_index()
        
    return data


def productos_transferencia(): 
    
    with connections['gimpromed_sql'].cursor() as cursor:
        # cursor.execute("SELECT * FROM warehouse.productos_transito")
        cursor.execute("SELECT PRODUCT_ID, OH FROM warehouse.productos_transito WHERE Bod_Trf_OrigDest = 'BAN'")
        columns = [col[0] for col in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]

        if data:
            data = pd.DataFrame(data)
            data = data.groupby('PRODUCT_ID')['OH'].sum().reset_index()
            return data
        
        else:
            return pd.DataFrame()


def pedidos_andagoya():
    
    with connections['gimpromed_sql'].cursor() as cursor:
        # cursor.execute("SELECT * FROM warehouse.reservas WHERE WARE_CODE = 'BAN'")
        cursor.execute("SELECT PRODUCT_ID, QUANTITY, SEC_NAME_CLIENTE FROM warehouse.reservas WHERE WARE_CODE = 'BAN'")
        columns = [col[0] for col in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]

        data = pd.DataFrame(data)
        
        data = data.groupby(by=['PRODUCT_ID', 'SEC_NAME_CLIENTE'])['QUANTITY'].sum().reset_index()
        data = data[data['SEC_NAME_CLIENTE']!='RESERVA']
        data = data[data['SEC_NAME_CLIENTE']!='PUBLICO']
        
    return data


def reservas_andagoya():
    
    with connections['gimpromed_sql'].cursor() as cursor:
        # cursor.execute("SELECT * FROM warehouse.reservas WHERE WARE_CODE = 'BAN'")
        cursor.execute("SELECT PRODUCT_ID, QUANTITY, SEC_NAME_CLIENTE FROM warehouse.reservas WHERE WARE_CODE = 'BAN'")
        columns = [col[0] for col in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]

        data = pd.DataFrame(data)
        
        data = data.groupby(by=['PRODUCT_ID', 'SEC_NAME_CLIENTE'])['QUANTITY'].sum().reset_index()
        data = data[data['SEC_NAME_CLIENTE']=='RESERVA']
        data = data[data['SEC_NAME_CLIENTE']!='PUBLICO']
        
    return data


def reservas_gimpromed():

    with connections['gimpromed_sql'].cursor() as cursor:
        # cursor.execute("SELECT * FROM warehouse.reservas WHERE WARE_CODE = 'BAN'")
        cursor.execute("SELECT CODIGO_CLIENTE, PRODUCT_ID, QUANTITY, SEC_NAME_CLIENTE FROM warehouse.reservas WHERE CODIGO_CLIENTE = 'CLI01002' ")
        columns = [col[0] for col in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]

        data = pd.DataFrame(data)
        
        data = data.groupby(by=['PRODUCT_ID', 'SEC_NAME_CLIENTE'])['QUANTITY'].sum().reset_index()
        data = data[data['SEC_NAME_CLIENTE']=='RESERVA']
        
    return data



def pedidos_reservas(product_id):
    
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(f"SELECT PRODUCT_ID, CONTRATO_ID, QUANTITY, SEC_NAME_CLIENTE, NOMBRE_CLIENTE, WARE_CODE FROM warehouse.reservas WHERE PRODUCT_ID = '{product_id}'")
        
        columns = [col[0] for col in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]

        data = pd.DataFrame(data)
        if not data.empty:
            data = data.groupby(by=['PRODUCT_ID', 'CONTRATO_ID','NOMBRE_CLIENTE', 'WARE_CODE', 'SEC_NAME_CLIENTE'])['QUANTITY'].sum().reset_index()   
            data['TIPO'] = data.apply(lambda x: 'RESERVA' if x['SEC_NAME_CLIENTE']=='RESERVA' else 'PEDIDO', axis=1)
            data['CONTRATO_ID'] = data['CONTRATO_ID'].str.slice(0, 5)
            return data
        else:
            return pd.DataFrame()

def stock_cerezos_wms():
    
    df = Existencias.objects.filter(estado='Disponible').values('product_id', 'unidades')
    df = pd.DataFrame(df)
    df = df.groupby('product_id')['unidades'].sum().reset_index()
    df = df.rename(columns={
        'product_id':'PRODUCT_ID', 
        'unidades':'STOCK_CEREZOS'   
        })
    
    return df


# Analisis
def data_andagoya():
    
    # Productos 
    productos = productos_odbc_and_django().rename(columns={'product_id': 'PRODUCT_ID'})[['PRODUCT_ID', 'Unidad_Empaque', 'Nombre', 'Marca']]
    productos = productos[~productos['PRODUCT_ID'].str.contains('-un')] # quitar productos que contentan en su product_id el texto '-un'
    productos = productos[~productos['PRODUCT_ID'].str.contains('-pr')] # quitar productos que contentan en su product_id el texto '-pr'
    productos = productos[~productos['PRODUCT_ID'].str.contains('-par')] # quitar productos que contentan en su product_id el texto '-par'
    productos = productos.drop_duplicates(subset=['PRODUCT_ID', 'Unidad_Empaque', 'Nombre', 'Marca']) # quitar duplicate
    
    # Stock Andagoya
    stock = stock_andagoya().rename(columns={'OH2': 'STOCK_ANDAGOYA'})
    
    # Productos Transferencia
    productos_transferencia_df = productos_transferencia()
    
    # Frecuencia Ventas
    frecuencia_ventas_df = frecuancia_ventas()
    frecuencia_ventas_df['CONSUMO_MENSUAL'] = round((frecuencia_ventas_df['ANUAL'] / 12), 0) 
    frecuencia_ventas_df['CONSUMO_SEMANAL'] = round((frecuencia_ventas_df['CONSUMO_MENSUAL'] / 4), 0) 
    
    # Andagoya
    if not productos_transferencia_df.empty:
        productos_transferencia_df = productos_transferencia_df.rename(columns={'OH': 'TRANSITO'})
        andagoya = pd.merge(stock, productos_transferencia_df, how='outer', on='PRODUCT_ID').fillna(0)
        andagoya['TOTAL_DISPONIBLE'] = andagoya['STOCK_ANDAGOYA'] + andagoya['TRANSITO']
    else:
        andagoya = stock
        andagoya['TRANSITO'] = 0
        andagoya['TOTAL_DISPONIBLE'] = andagoya['STOCK_ANDAGOYA'] + andagoya['TRANSITO']
    
    # Data
    data = pd.merge(productos, andagoya, how='left', on='PRODUCT_ID').fillna(0)
    data = pd.merge(data, frecuencia_ventas_df, how='left', on='PRODUCT_ID').fillna(0)
    
    return data


def andagoya_saldos():
    
    # Data
    data = data_andagoya()
    
    # Stock Wms Cerezos
    cerezos = stock_cerezos_wms()
    
    # Calculos
    data['SALDOS'] = data.apply(lambda x: x['TOTAL_DISPONIBLE'] < x['Unidad_Empaque'], axis=1)
    data = data[data['SALDOS']==True]
    data['TOTAL_DISPONIBLE_UNDS_CARTON'] = round(((data['TOTAL_DISPONIBLE'] / data['Unidad_Empaque']) * 100), 2)
    data['TOTAL_DISPONIBLE_VS_CONSUMO_MENSUAL'] = round(((data['TOTAL_DISPONIBLE'] / data['CONSUMO_MENSUAL']) * 100), 2)
    data = data.replace([np.inf, -np.inf], np.nan).fillna(0)
    
    # merge cerezos
    data = data.merge(cerezos, how='left', on='PRODUCT_ID').fillna(0)
    
    data['F_ACUMULADA'] = round(data['F_ACUMULADA'], 2) 
    data['TOTAL_DISPONIBLE_CARTONES'] = round(data['TOTAL_DISPONIBLE'] / data['Unidad_Empaque'], 2)
    data['STOCK_CEREZOS_CARTONES']   = round(data['STOCK_CEREZOS'] / data['Unidad_Empaque'], 2)
    data['CONSUMO_MENSUAL_CARTONES'] = round(data['CONSUMO_MENSUAL'] / data['Unidad_Empaque'], 2)
    data['RATE'] = round((data['TOTAL_DISPONIBLE'] / data['STOCK_CEREZOS']) * 100, 2)
    
    # data = data.sort_values(by=['TOTAL_DISPONIBLE_UNDS_CARTON', 'CONSUMO_MENSUAL', 'TOTAL_DISPONIBLE_VS_CONSUMO_MENSUAL', 'F_ACUMULADA'], ascending=[True, False, False, False])
    data = data.sort_values(by=['TOTAL_DISPONIBLE_VS_CONSUMO_MENSUAL', 'RATE',], ascending=[True, True])
    data = data[data['STOCK_CEREZOS'] > 0]
    
    # data['filtro'] = data.apply(lambda x: 'OCULTAR' if x['TOTAL_DISPONIBLE_VS_CONSUMO_MENSUAL'] == 0 and x['TOTAL_DISPONIBLE'] == 0 else 'MOSTRAR', axis=1)
    data['filtro'] = data.apply(lambda x: 'OCULTAR' if x['TOTAL_DISPONIBLE'] > 0 and x['TOTAL_DISPONIBLE_VS_CONSUMO_MENSUAL'] == 0 else 'MOSTRAR', axis=1)
    
    data = data[data['filtro']=='MOSTRAR']
    
    #data['TOTAL_DISPONIBLE'] = data['TOTAL_DISPONIBLE'].apply(lambda x: '{:,.2f}'.format(x))
    #data['STOCK_ANDAGOYA'] = pd.to_numeric(data['STOCK_ANDAGOYA'], errors='coerce').map('{:,.2f}'.format)
    
    data = data[[
        'PRODUCT_ID',
        'Nombre',
        'Marca',
        'Unidad_Empaque',
        'F_ACUMULADA',
        'STOCK_ANDAGOYA', 
        'TRANSITO', 
        'TOTAL_DISPONIBLE',
        'STOCK_CEREZOS',
        #'CONSUMO_SEMANAL',
        'CONSUMO_MENSUAL',
        'TOTAL_DISPONIBLE_UNDS_CARTON',
        'TOTAL_DISPONIBLE_VS_CONSUMO_MENSUAL',
        'TOTAL_DISPONIBLE_CARTONES',
        'STOCK_CEREZOS_CARTONES',
        'CONSUMO_MENSUAL_CARTONES',
        'RATE',
        'filtro'
    ]]
    
    data['n_fila'] = range(1, len(data) + 1)
    
    return data


# def sugerencia():
    
#     # Data
#     data = data_andagoya()
    
#     # Stock Cerezos WMS
#     cerezos = stock_cerezos_wms()
    
#     # Pedidos
#     pedidos_df = pedidos_andagoya().rename(columns={'QUANTITY': 'PEDIDOS'})
    
#     # Reservas
#     reservas_df = reservas_andagoya().rename(columns={'QUANTITY': 'RESERVAS', 'SEC_NAME_CLIENTE': 'RESERVA_INDICADOR'})
    
#     # Merge    
#     data = pd.merge(data, pedidos_df, how='left', on='PRODUCT_ID').fillna(0)
#     data = pd.merge(data, reservas_df, how='left', on='PRODUCT_ID').fillna(0)
#     data = pd.merge(data, cerezos, how='left', on='PRODUCT_ID').fillna(0)
    
#     # Calculos
#     data['DISPONIBLE_MENOS_RESERVAS'] = data['TOTAL_DISPONIBLE'] - data['RESERVAS']
#     data['STOCK_SEGURIDAD'] = (data['PEDIDOS'] + data['CONSUMO_SEMANAL'] * 2)
#     data['NIVEL_ABASTECIMIENTO'] = (data['DISPONIBLE_MENOS_RESERVAS'] / data['STOCK_SEGURIDAD']) * 100
#     # data = data.replace([np.inf, -np.inf], np.nan).fillna(0)
    
#     # Cartones
#     data['STOCK_ANDAGOYA_CARTONES'] = data['STOCK_ANDAGOYA'] / data['Unidad_Empaque']
#     data['STOCK_CEREZOS_CARTONES'] = data['STOCK_CEREZOS'] / data['Unidad_Empaque']
#     data['TOTAL_DISPONIBLE_CARTONES'] = data['TOTAL_DISPONIBLE'] / data['Unidad_Empaque']
#     data['DISPONIBLE_MENOS_RESERVAS_CARTONES'] = data['DISPONIBLE_MENOS_RESERVAS'] / data['Unidad_Empaque']
    
#     # Orden
#     data = data.sort_values(by=['NIVEL_ABASTECIMIENTO', 'F_ACUMULADA', 'CONSUMO_SEMANAL'], ascending=[True, False, False])
#     data = data[data['STOCK_CEREZOS'] > 0]
    
#     f_ventas = frecuancia_ventas()
#     f_ventas.to_excel('frecuencia_ventas.xlsx', index=False)
    
#     return data


def sugerencia():
    # import pandas as pd
    # import numpy as np
    
    # Data
    data = data_andagoya()  # Datos base de la bodega 'Andagoya'
    cerezos = stock_cerezos_wms()  # Stock en la bodega 'Cerezos'
    pedidos_df = pedidos_andagoya().rename(columns={'QUANTITY': 'PEDIDOS'})  # Pedidos pendientes
    reservas_df = reservas_andagoya().rename(columns={'QUANTITY': 'RESERVAS', 'SEC_NAME_CLIENTE': 'RESERVA_INDICADOR'})  # Reservas
    stock_seguridad = stock_de_seguridad()
    reservas_gimpromed_df = reservas_gimpromed().rename(columns={'QUANTITY': 'RESERVAS_GIMPROMED'})  # Reservas
    
    # Merge de datos
    data = pd.merge(data, pedidos_df, how='left', on='PRODUCT_ID').fillna(0)
    data = pd.merge(data, reservas_df, how='left', on='PRODUCT_ID').fillna(0)
    data = pd.merge(data, cerezos, how='left', on='PRODUCT_ID').fillna(0)
    data = pd.merge(data, stock_seguridad, how='left', on='PRODUCT_ID').fillna(0)
    data = pd.merge(data, reservas_gimpromed_df, how='left', on='PRODUCT_ID').fillna(0)
    
    # Cálculos intermedios
    # data['DISPONIBLE_MENOS_RESERVAS'] = data['TOTAL_DISPONIBLE'] - data['RESERVAS']
    # data['DISPONIBLE_MENOS_RESERVAS'] = data['TOTAL_DISPONIBLE'] - data['RESERVAS'] - data['PEDIDOS'] # change 
    data['DISPONIBLE_MENOS_RESERVAS'] = data['TOTAL_DISPONIBLE'] - data['RESERVAS'] - data['PEDIDOS'] + data['RESERVAS_GIMPROMED'] 
    
    # Cálculo del nivel de abastecimiento con límites
    data['NIVEL_ABASTECIMIENTO'] = (data['DISPONIBLE_MENOS_RESERVAS'] / data['stock_seguridad_mensual']) * 100
    #data['NIVEL_ABASTECIMIENTO'] = (data['DISPONIBLE_MENOS_RESERVAS'] / data['stock_seguridad_semanal']) * 100
    
    data['NIVEL_ABASTECIMIENTO'] = data['NIVEL_ABASTECIMIENTO'].clip(lower=0, upper=100)  # Limitar valores entre 0% y 100%
    data['NIVEL_ABASTECIMIENTO'] = data['NIVEL_ABASTECIMIENTO'].fillna(0)  # Reemplazar NaN por 0 para niveles no calculables
    
    # Cartones
    data['STOCK_ANDAGOYA_CARTONES'] = data['STOCK_ANDAGOYA'] / data['Unidad_Empaque']
    data['STOCK_CEREZOS_CARTONES'] = data['STOCK_CEREZOS'] / data['Unidad_Empaque']
    data['TOTAL_DISPONIBLE_CARTONES'] = data['TOTAL_DISPONIBLE'] / data['Unidad_Empaque']
    data['DISPONIBLE_MENOS_RESERVAS_CARTONES'] = data['DISPONIBLE_MENOS_RESERVAS'] / data['Unidad_Empaque']
    
    # Ordenar resultados
    data = data.sort_values(
        by=['NIVEL_ABASTECIMIENTO', 'stock_seguridad_semanal', 'CONSUMO_SEMANAL', 'F_ACUMULADA'], 
        ascending=[True, False, False, False]
    )
    data = data.replace([np.inf, -np.inf], np.nan).fillna(0)
    
    # Filtrar productos con stock disponible en 'Cerezos'
    data = data[data['STOCK_CEREZOS'] > 0]
    
    data['n_fila'] = range(1, len(data) + 1)
    
    return data





# def stock_andagoya(): 
    
#     with connections['gimpromed_sql'].cursor() as cursor:
#         cursor.execute("SELECT * FROM warehouse.stock_lote")
#         columns = [col[0] for col in cursor.description]
#         data = [dict(zip(columns, row)) for row in cursor.fetchall()]

#         data = pd.DataFrame(data)
        
        
        
#     return data


# def excel_stock_transferencia(request):
    
#     return 'ok' # HttpResponse('ok')