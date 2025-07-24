# DB
from django.db import connections

# Pandas
import pandas as pd

# Numpy 
import numpy as np

# Wms
from wms.models import Existencias

# Data
from datos.views import frecuancia_ventas, productos_odbc_and_django, stock_de_seguridad, clientes_warehouse

# Error lote
from datos.models import ErrorLoteDetalle

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


def reservas_menos_gipromed():
    
    with connections['gimpromed_sql'].cursor() as cursor:
    # cursor.execute("SELECT * FROM warehouse.reservas WHERE WARE_CODE = 'BAN'")
        cursor.execute("SELECT CODIGO_CLIENTE, PRODUCT_ID, QUANTITY, SEC_NAME_CLIENTE FROM warehouse.reservas WHERE SEC_NAME_CLIENTE LIKE '%RESERVA%'")
        columns = [col[0] for col in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        data = pd.DataFrame(data)
        data = data[data['CODIGO_CLIENTE']!='CLI01002']
        data = data.groupby(by='PRODUCT_ID')['QUANTITY'].sum().reset_index().dropna()
        
    return data


def andagoya_saldos():
    
    # Data
    data = data_andagoya()
    cerezos = stock_cerezos_wms()
    reservas_menos_gimpromed_df = reservas_menos_gipromed()
    
    # TOMAR RESERVAS DE CEREZOS Y QUITAR DE STOK WMS
    cerezos = cerezos.merge(reservas_menos_gimpromed_df, on='PRODUCT_ID', how='left').fillna(0) 
    cerezos['STOCK_CEREZOS_MENOS_RESGIMP'] = cerezos['STOCK_CEREZOS'] - cerezos['QUANTITY'] 
    
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
    
    # data['STOCK_CEREZOS_CARTONES']   = round(data['STOCK_CEREZOS'] / data['Unidad_Empaque'], 2)
    data['STOCK_CEREZOS_CARTONES']   = round(data['STOCK_CEREZOS_MENOS_RESGIMP'] / data['Unidad_Empaque'], 2)
    
    data['CONSUMO_MENSUAL_CARTONES'] = round(data['CONSUMO_MENSUAL'] / data['Unidad_Empaque'], 2)
    #data['RATE'] = round((data['TOTAL_DISPONIBLE'] / data['STOCK_CEREZOS']) * 100, 2)
    data['RATE'] = round((data['TOTAL_DISPONIBLE'] / data['STOCK_CEREZOS_MENOS_RESGIMP']) * 100, 2)
    
    
    # data = data.sort_values(by=['TOTAL_DISPONIBLE_UNDS_CARTON', 'CONSUMO_MENSUAL', 'TOTAL_DISPONIBLE_VS_CONSUMO_MENSUAL', 'F_ACUMULADA'], ascending=[True, False, False, False])
    data = data.sort_values(by=['TOTAL_DISPONIBLE_VS_CONSUMO_MENSUAL', 'RATE',], ascending=[True, True])
    #data = data[data['STOCK_CEREZOS'] > 0]
    data = data[data['STOCK_CEREZOS_MENOS_RESGIMP'] > 0]
    
    
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
        'STOCK_CEREZOS_MENOS_RESGIMP',
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
    reservas_menos_gimpromed_df = reservas_menos_gipromed()
    
    # TOMAR RESERVAS DE CEREZOS Y QUITAR DE STOK WMS
    cerezos = cerezos.merge(reservas_menos_gimpromed_df, on='PRODUCT_ID', how='left').fillna(0)
    cerezos['STOCK_CEREZOS_MENOS_RESGIMP'] = cerezos['STOCK_CEREZOS'] - cerezos['QUANTITY']
    
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
    # data['STOCK_CEREZOS_CARTONES'] = data['STOCK_CEREZOS'] / data['Unidad_Empaque']
    data['STOCK_CEREZOS_CARTONES'] = data['STOCK_CEREZOS_MENOS_RESGIMP'] / data['Unidad_Empaque']
    data['TOTAL_DISPONIBLE_CARTONES'] = data['TOTAL_DISPONIBLE'] / data['Unidad_Empaque']
    data['DISPONIBLE_MENOS_RESERVAS_CARTONES'] = data['DISPONIBLE_MENOS_RESERVAS'] / data['Unidad_Empaque']
    
    # Ordenar resultados
    data = data.sort_values(
        by=['NIVEL_ABASTECIMIENTO', 'stock_seguridad_semanal', 'CONSUMO_SEMANAL', 'F_ACUMULADA'], 
        ascending=[True, False, False, False]
    )
    data = data.replace([np.inf, -np.inf], np.nan).fillna(0)
    
    # Filtrar productos con stock disponible en 'Cerezos'
    # data = data[data['STOCK_CEREZOS'] > 0]
    data = data[data['STOCK_CEREZOS_MENOS_RESGIMP'] > 0]
    
    data['n_fila'] = range(1, len(data) + 1)
    
    return data


### DATOS PARA TRANSFERENCIA
def inventario_transferencia_data():
    
    def df_stock_andagoya():
        with connections['gimpromed_sql'].cursor() as cursor:
            cursor.execute("SELECT PRODUCT_ID, OH2, LOTE_ID, FECHA_CADUCIDAD, LOCATION, WARE_CODE FROM warehouse.stock_lote WHERE WARE_CODE = 'BAN'")
            connections['gimpromed_sql'].close()
            
            columns = [col[0].lower() for col in cursor.description]
            stock = [dict(zip(columns, row)) for row in cursor.fetchall()]
            stock = pd.DataFrame(stock)
            stock['lote_id'] = stock['lote_id'].str.replace('.','')
            stock = stock.groupby(by=['product_id','lote_id','fecha_caducidad','location','ware_code'])['oh2'].sum().reset_index()
            stock['bodega'] = 'BAN'
            
            return stock
    
    
    def df_stock_cerezos():
        cerezos = pd.DataFrame(Existencias.objects.all().values(
            'product_id', 'lote_id', 'fecha_caducidad', 'estado', 'ubicacion__bodega','unidades'
        ))
        cerezos['lote_id'] = cerezos['lote_id'].str.replace('.','')
        cerezos = cerezos.groupby(by=['product_id','lote_id','fecha_caducidad','ubicacion__bodega','estado'])['unidades'].sum().reset_index()
        cerezos['ware_code'] = cerezos.apply(lambda x: 'BCT' if x['estado'] == 'Disponible' else 'CUC', axis=1)
        cerezos = cerezos.rename(columns={
            'unidades':'oh2',
            'ubicacion__bodega':'location'
        })
        cerezos = cerezos[['product_id','lote_id','fecha_caducidad','location','ware_code','oh2']]
        cerezos['bodega'] = 'BCT'
        return cerezos
    
    
    def df_stock():
        stock = pd.concat([df_stock_andagoya(), df_stock_cerezos()])
        stock = stock.pivot_table(
            index=['product_id','lote_id','location','fecha_caducidad','bodega'],
            values='oh2',
            columns='ware_code',
            aggfunc='sum'
        ).fillna(0).reset_index().sort_values(by=['product_id','lote_id','fecha_caducidad','bodega'])
        return stock
    
    
    def df_reservas():
        with connections['gimpromed_sql'].cursor() as cursor:
            cursor.execute("SELECT CONTRATO_ID, CODIGO_CLIENTE, PRODUCT_ID, WARE_CODE, EGRESO_TEMP, LOTE_ID FROM warehouse.reservas_lote_2")
            connections['gimpromed_sql'].close()
            
            columns = [col[0].lower() for col in cursor.description]
            reservas = [dict(zip(columns, row)) for row in cursor.fetchall()]
            reservas = pd.DataFrame(reservas)
            reservas['lote_id'] = reservas['lote_id'].str.replace('.','')
            reservas = reservas.groupby(by=['contrato_id','codigo_cliente','product_id','lote_id','ware_code'])['egreso_temp'].sum().reset_index()
            
            return reservas
    
    
    def df_reservas_unidades():
    
        reservas_ban = df_reservas().copy()
        reservas_ban = reservas_ban[reservas_ban['ware_code']=='BAN']
        reservas_ban = reservas_ban.pivot_table(
            index=['product_id','lote_id'],
            values='egreso_temp',
            columns='ware_code',
            aggfunc='sum'
        ).fillna(0).reset_index()
        
        reservas_ban = reservas_ban.rename(columns={'BAN':'BAN_R'})
        reservas_ban['bodega'] = 'BAN'
        
        reservas_bct = df_reservas().copy()
        reservas_bct = reservas_bct[reservas_bct['ware_code']=='BCT']
        reservas_bct = reservas_bct.pivot_table(
            index=['product_id','lote_id'],
            values='egreso_temp',
            columns='ware_code',
            aggfunc='sum'
        ).fillna(0).reset_index()
        reservas_bct = reservas_bct.rename(columns={'BCT':'BCT_R'})
        reservas_bct['bodega'] = 'BCT'
        reservas_unds = pd.concat([reservas_ban, reservas_bct]).fillna(0)
        
        return reservas_unds #.reset_index()


    def df_reservas_contratos():
        
        clientes = clientes_warehouse()[['CODIGO_CLIENTE','NOMBRE_CLIENTE']]
        clientes = clientes.rename(columns={'CODIGO_CLIENTE':'codigo_cliente', 'NOMBRE_CLIENTE':'nombre_cliente'})
    
        def df_reservas_contratos_ban():
            reservas_cto = df_reservas().copy()
            reservas_cto = reservas_cto[reservas_cto['ware_code']=='BAN']
            reservas_cto = reservas_cto.merge(clientes, on='codigo_cliente', how='left').sort_values(by='ware_code')
            
            reservas_cto['detalle'] = (
                '"' + 
                reservas_cto['nombre_cliente'].astype('str') + ' - ' + reservas_cto['contrato_id'].astype('str') + ' - ' + reservas_cto['ware_code'].astype('str') + ' - ' + 'UNDS: ' + reservas_cto['egreso_temp'].astype('str') 
                + '"'
            )
            reservas_cto = reservas_cto.pivot_table(
                index=['product_id','lote_id'],
                values='detalle',
                aggfunc=lambda x: ' | '.join(x)
            ).fillna('').reset_index()
            reservas_cto['bodega'] = 'BAN'
            return reservas_cto
            
        def df_reservas_contratos_bct():
            reservas_cto = df_reservas().copy()
            reservas_cto = reservas_cto[reservas_cto['ware_code']=='BCT']
            reservas_cto = reservas_cto.merge(clientes, on='codigo_cliente', how='left').sort_values(by='ware_code')
            reservas_cto['detalle'] = (
                '"' + 
                reservas_cto['nombre_cliente'].astype('str') + ' - ' + reservas_cto['contrato_id'].astype('str') + ' - ' + reservas_cto['ware_code'].astype('str') + ' - ' + 'UNDS: ' + reservas_cto['egreso_temp'].astype('str') 
                + '"'
            )
            reservas_cto = reservas_cto.pivot_table(
                index=['product_id','lote_id'],
                values='detalle',
                aggfunc=lambda x: ' | '.join(x)
            ).fillna('').reset_index()
            reservas_cto['bodega'] = 'BCT'
            return reservas_cto
        
        reservas = pd.concat([df_reservas_contratos_ban(), df_reservas_contratos_bct()]).fillna('')
        return reservas.reset_index()
    
    
    def df_error_lote():
        
        error_lote = ErrorLoteDetalle.objects.all()
        if error_lote.exists():
            error_lote_df = pd.DataFrame(error_lote.values('product_id', 'lote_id'))
            error_lote_df['error_lote'] = True
            return error_lote_df
        
        else:
            error_lote_df = pd.DataFrame()
            error_lote_df['product_id'] = ''
            error_lote_df['lote_id'] = ''
            error_lote_df['error_lote'] = False
            return error_lote_df
    
    prods = productos_odbc_and_django()[['product_id','Nombre','Marca','Unidad_Empaque','vol_m3']]    
    prods['vol_m3'] = pd.to_numeric(prods['vol_m3'], errors='coerce')
    prods['vol_m3'] = prods['vol_m3'].fillna(0.025)
    prods['vol_m3'] = prods['vol_m3'].replace(0, 0.025)
    
    data = df_stock()
    
    if not df_reservas_unidades().empty:
        data = data.merge(df_reservas_unidades(), on=['product_id','lote_id','bodega'], how='left').fillna(0)
        
    if not df_reservas_contratos().empty:
        data = data.merge(df_reservas_contratos(), on=['product_id','lote_id','bodega'], how='left').fillna('')
        
    data = data.merge(prods, on='product_id',how='left')
    
    data['BCT_C'] = data['BCT'] // data['Unidad_Empaque']
    data['BCT_S'] = data['BCT'] %  data['Unidad_Empaque']    
    data['BCT_D']   = data['BCT'] - data['BCT_R']
    data['BCT_D_C'] = data['BCT_D'] // data['Unidad_Empaque']
    data['BCT_D_S'] = data['BCT_D'] % data['Unidad_Empaque']
    data['BCT_D_C'] = data['BCT_D_C'].fillna(0)
    data['BCT_D_S'] = data['BCT_D_S'].fillna(0)
    
    data['fecha_caducidad'] = data['fecha_caducidad'].astype('str')    
    data = data.sort_values(by=['product_id','fecha_caducidad','bodega'], ascending=[True,True,True])
    data = data.merge(df_error_lote(), on=['product_id','lote_id'], how='left')
    data['error_lote'] = data['error_lote'].fillna(False)
    
    return data

