# API MBA
from api_mba.mba import api_mba_sql #, api_mba_sql_pedidos

# Conexión ODBC
import pyodbc

# BD Connection
from django.db import connections #, transaction
from django.db.models import Q

# Send mail
from django.core.mail import send_mail
from django.conf import settings

# datetime
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# Pandas
import pandas as pd

# Queries de mba por api
from api_mba.api_query import api_query_clientes_mba

# datos de actualización
from datos.models import AdminActualizationWarehaouse
from datos.models import Reservas

# models de etiqutados
from etiquetado.models import EstadoPicking

from users.models import User

import requests

# Utils
from utils.warehouse_data import (
    get_cliente, 
    get_numero_factura_by_numero_pedido, 
    email_cliente_by_codigo,
    get_vendedor_email_by_contrato,
    cartones_volumen_factura
)

# eliminar datos de tablas en wharehouse
def delete_data_warehouse(table_name):
    
    try:
        with connections['gimpromed_sql'].cursor() as cursor:
            cursor.execute(f"DELETE FROM {table_name}")
            print("Borrando tabla datawarehouse " + table_name)
    except Exception as e:
        print(e)
    finally:
        connections['gimpromed_sql'].close()


# obtener columnas de tabla por nombre de la tabla
def get_columns_table_warehouse(table_name):
    
    try:
        with connections['gimpromed_sql'].cursor() as cursor:
            cursor.execute(f"SHOW COLUMNS FROM {table_name}")
            columns = [row[0] for row in cursor.fetchall()]
            
        return columns
    except Exception as e:
        print(e)
    finally:
        connections['gimpromed_sql'].close()


# insertar datos en tabla de warehouse
def insert_data_warehouse(table_name, data):   
    
    try:
        get_columns = get_columns_table_warehouse(table_name)
        
        columnas = ", ".join(get_columns)
        valores  = ", ".join(["%s"] * len(get_columns))
        sql_insert = f"INSERT INTO {table_name} ({columnas}) VALUES ({valores})"
        
        with connections['gimpromed_sql'].cursor() as cursor:
            cursor.executemany(sql_insert, data)
            print("Insertando datos en warehouse " + table_name)
    except Exception as e:
        print(e)
    finally:
        connections['gimpromed_sql'].close()


def admin_warehouse_timestamp(tabla, actualizar_datetime, mensaje):
    
    timestamp = AdminActualizationWarehaouse.objects.filter(table_name=tabla)
    
    if timestamp.exists():
        
        if actualizar_datetime:
            registro = timestamp.first() 
            registro.datetime = datetime.now()
            registro.mensaje = mensaje
            registro.save()
        else:
            registro = timestamp.first()
            registro.mensaje = mensaje
            registro.save()
    else:
        AdminActualizationWarehaouse.objects.create(table_name=tabla, mensaje=mensaje,datetime=datetime.now())


###### FUNCIONES PARA ACTUALIZAR DATOS EN WAREHOUSE ######
# 1 QUERY CLIENTES
QUERY_CLIENTES = """
    SELECT 
        CLNT_Ficha_Principal.CODIGO_CLIENTE, 
        CLNT_Ficha_Principal.IDENTIFICACION_FISCAL, 
        CLNT_Ficha_Principal.NOMBRE_CLIENTE, 
        CLNT_Ficha_Principal.CIUDAD_PRINCIPAL, 
        CLNT_Ficha_Principal.CLIENT_TYPE, 
        CLNT_Ficha_Principal.SALESMAN, 
        CLNT_Ficha_Principal.LIMITE_CREDITO, 
        CLNT_Ficha_Principal.PriceList, 
        CLNT_Ficha_Principal.E_MAIL, 
        CLNT_Ficha_Principal.Email_Fiscal, 
        CLNT_Ficha_Principal.DIRECCION_PRINCIPAL_1, 
        CLNT_Ficha_Principal.FAX 
    FROM 
        CLNT_Ficha_Principal CLNT_Ficha_Principal
"""
### 1 API ACTUALIZAR CLIENTES WAREHOUSE 
def api_actualizar_clientes_warehouse():
    
    try:
    
        clientes_mba = api_query_clientes_mba()

        if clientes_mba["status"] == 200:
            
            data = [tuple(i.values()) for i in clientes_mba['data']]
            
            #with transaction.atomic():
            
            # Borrar datos de tabla clientes
            delete_data_warehouse('clientes')
            
            # Insertar datos de tabla clientes
            insert_data_warehouse('clientes', data)
            
            admin_warehouse_timestamp(tabla='clientes', actualizar_datetime=True, mensaje='API- Actualizado correctamente')
            
        else:
            
            admin_warehouse_timestamp(tabla='clientes', actualizar_datetime=False, mensaje=f'API- Error api: status {clientes_mba["status"]}')

    except Exception as e:
        
        admin_warehouse_timestamp(tabla='clientes', actualizar_datetime=False, mensaje=f'API- Error exception: {e}')


### 1 ODBC ACTUALIZAR CLIENTES WAREHOUSE 
def odbc_actualizar_clientes_warehouse():
    
    try:
        cnx = pyodbc.connect("DSN=mba3;PWD=API")
        cursor = cnx.cursor()
        clientes_query = cursor.execute(QUERY_CLIENTES)
        
        data = clientes_query.fetchall()

        if len(data) >= 1:
            
            # Borrar datos de tabla clientes
            delete_data_warehouse('clientes')
            
            # Insertar datos de tabla clientes
            insert_data_warehouse('clientes', data)

            admin_warehouse_timestamp(tabla='clientes', actualizar_datetime=True, mensaje='ODBC - Actualizado correctamente')
        else:
            admin_warehouse_timestamp(tabla='clientes', actualizar_datetime=False, mensaje='ODBC NO TRAE DATOS')
    
    except Exception as e:
        
        admin_warehouse_timestamp(tabla='clientes', actualizar_datetime=False, mensaje=f'ODBC Error exception: {e}')


### 2 ACTUALIZAR FACTURAS WAREHOUSE
def api_actualizar_facturas_warehouse():
    
    try:
    
        #currentTimeDate = datetime.now() - relativedelta(days=90)
        currentTimeDate = datetime.now() - relativedelta(days=270)
        OneMonthTime = currentTimeDate.strftime('%d-%m-%Y')
        
        facturas_mba = api_mba_sql(
            f"""
            SELECT 
                CLNT_Factura_Principal.CODIGO_FACTURA, 
                CLNT_Factura_Principal.FECHA_FACTURA, 
                CLNT_Ficha_Principal.NOMBRE_CLIENTE, 
                INVT_Ficha_Principal.PRODUCT_ID, 
                INVT_Ficha_Principal.PRODUCT_NAME, 
                INVT_Ficha_Principal.GROUP_CODE, 
                INVT_Producto_Movimientos.QUANTITY, 
                CLNT_Factura_Principal.NUMERO_PEDIDO_SISTEMA 
            FROM 
                CLNT_Factura_Principal CLNT_Factura_Principal, 
                CLNT_Ficha_Principal CLNT_Ficha_Principal, 
                INVT_Ficha_Principal INVT_Ficha_Principal, 
                INVT_Producto_Movimientos INVT_Producto_Movimientos 
            WHERE 
                INVT_Ficha_Principal.PRODUCT_ID_CORP = INVT_Producto_Movimientos.PRODUCT_ID_CORP AND 
                CLNT_Factura_Principal.CODIGO_CLIENTE = CLNT_Ficha_Principal.CODIGO_CLIENTE AND 
                CLNT_Factura_Principal.CODIGO_FACTURA = INVT_Producto_Movimientos.DOC_ID_CORP2 AND 
                ((INVT_Producto_Movimientos.CONFIRM=TRUE And INVT_Producto_Movimientos.CONFIRM=TRUE) AND 
                (INVT_Producto_Movimientos.I_E_SIGN='-') AND 
                (INVT_Producto_Movimientos.ADJUSTMENT_TYPE='FT') AND 
                (CLNT_Factura_Principal.ANULADA=FALSE)) AND  FECHA_FACTURA >='{OneMonthTime}'
            """
        )
        
        if  facturas_mba["status"] == 200:

            #data = [tuple(i.values()) for i in facturas_mba['data']]

            data = []
            for i in facturas_mba['data']:
                
                codigo_factura = i['CODIGO_FACTURA']
                fecha_factura = datetime.strptime(i['FECHA_FACTURA'][:10], '%d/%m/%Y')
                nombre_cliente = i['NOMBRE_CLIENTE']
                product_id = i['PRODUCT_ID']
                product_name = i['PRODUCT_NAME']
                group_code = i['GROUP_CODE']
                quantity = i['QUANTITY']
                numero_pedido_sistema = i['NUMERO_PEDIDO_SISTEMA']
                
                row = (
                    codigo_factura,
                    fecha_factura,
                    nombre_cliente,
                    product_id,
                    product_name,
                    group_code,
                    quantity,
                    numero_pedido_sistema,
                )
                
                data.append(row)
        
            #with transaction.atomic():
            # Borrar datos de tabla facturas
            delete_data_warehouse('facturas')
            
            # Insertar datos de tabla facturas
            insert_data_warehouse('facturas', data)
    
            admin_warehouse_timestamp('facturas', actualizar_datetime=True, mensaje='Actualizado correctamente')
                
        else:
            
            admin_warehouse_timestamp(tabla='facturas', actualizar_datetime=False, mensaje=f'Error api: status {facturas_mba["status"]}')
    
    except Exception as e:
        
        admin_warehouse_timestamp(tabla='facturas', actualizar_datetime=False, mensaje=f'Error exception: {e}')


### 3 ACTUALIZAR IMP LLEGADAS WAREHOUSE
def api_actualizar_imp_llegadas_warehouse():

    try:
        imp_llegadas_mba = api_mba_sql(
            """
            SELECT 
                INVT_Lotes_Trasabilidad.DOC_ID_CORP, 
                INVT_Lotes_Trasabilidad.ENTRADA_FECHA, 
                INVT_Lotes_Trasabilidad.PRODUCT_ID_CORP, 
                INVT_Lotes_Trasabilidad.LOTE_ID, 
                INVT_Lotes_Trasabilidad.FECHA_CADUCIDAD, 
                INVT_Lotes_Trasabilidad.AVAILABLE, 
                INVT_Lotes_Trasabilidad.EGRESO_TEMP, 
                INVT_Lotes_Trasabilidad.OH, 
                INVT_Lotes_Trasabilidad.WARE_COD_CORP, 
                CLNT_Pedidos_Principal.MEMO 
            FROM 
                INVT_Lotes_Trasabilidad INVT_Lotes_Trasabilidad 
            LEFT JOIN 
                CLNT_Pedidos_Principal ON INVT_Lotes_Trasabilidad.DOC_ID_CORP = CLNT_Pedidos_Principal.CONTRATO_ID_CORP 
            WHERE 
                (INVT_Lotes_Trasabilidad.ENTRADA_TIPO='OC') AND 
                (INVT_Lotes_Trasabilidad.ENTRADA_FECHA>'2023-01-01') AND 
                (INVT_Lotes_Trasabilidad.Tipo_Movimiento='RP')
            """
        )
        
        
        proveedor_mba = api_mba_sql(
            """
            SELECT 
                CLNT_Pedidos_Principal.CONTRATO_ID_CORP, 
                PROV_Ficha_Principal.VENDOR_NAME 
            FROM 
                CLNT_Pedidos_Principal CLNT_Pedidos_Principal, 
                PROV_Ficha_Principal PROV_Ficha_Principal 
            WHERE 
                CLNT_Pedidos_Principal.CLIENT_ID_CORP = PROV_Ficha_Principal.CODIGO_PROVEEDOR_EMPRESA AND
                ((CLNT_Pedidos_Principal.FECHA_PEDIDO>'01-01-2023') AND 
                (CLNT_Pedidos_Principal.PEDIDO_CERRADO=false) AND (CLNT_Pedidos_Principal.VOID=false))
            """
        )
        
        
        if  imp_llegadas_mba['status'] == 200 and proveedor_mba['status'] == 200:
            
            imp_llegadas_df = pd.DataFrame(imp_llegadas_mba['data']) #; print(imp_llegadas_df)
            proveedor_df = pd.DataFrame(proveedor_mba['data']).rename(columns={'CONTRATO_ID_CORP':'DOC_ID_CORP'})
            
            # Unir nombre de proveedor
            imp_llegadas = imp_llegadas_df.merge(proveedor_df, on='DOC_ID_CORP', how='left').fillna('')
            
            # Transformar datos de fechas
            #imp_llegadas['ENTRADA_FECHA'] = imp_llegadas['ENTRADA_FECHA'].str.slice(0,10); 
            imp_llegadas['ENTRADA_FECHA'] = pd.to_datetime(imp_llegadas['ENTRADA_FECHA'].str.slice(0, 10), format='%d/%m/%Y').dt.date
            
            #imp_llegadas['FECHA_CADUCIDAD'] = imp_llegadas['FECHA_CADUCIDAD'].str.slice(0, 10)
            imp_llegadas['FECHA_CADUCIDAD'] = pd.to_datetime(imp_llegadas['FECHA_CADUCIDAD'].str.slice(0, 10), format='%d/%m/%Y').dt.date
            imp_llegadas['FECHA_CADUCIDAD'] = imp_llegadas['FECHA_CADUCIDAD'].astype('str')
            
            # Ordenar por fecha de entrada
            imp_llegadas = imp_llegadas.sort_values(by='ENTRADA_FECHA')
            
            # Ordenar columnas para insertar datos
            imp_llegadas = imp_llegadas[[
                'DOC_ID_CORP', 
                'VENDOR_NAME',
                'ENTRADA_FECHA',
                'PRODUCT_ID_CORP', # TRANSFORMA MAS ADELANTE
                'LOTE_ID',
                'FECHA_CADUCIDAD',
                'AVAILABLE',
                'EGRESO_TEMP',
                'OH',
                'WARE_COD_CORP',
                'MEMO'
            ]]
            
            data = imp_llegadas.values.tolist()
            
            #with transaction.atomic():
            # Borrar datos de tabla imp_llegadas
            delete_data_warehouse('imp_llegadas')
            
            # Insertar datos de tabla imp_llegadas
            insert_data_warehouse('imp_llegadas', data)
            
            admin_warehouse_timestamp('imp_llegadas', actualizar_datetime=True, mensaje='Actualizado correctamente')
        
        else:
            
            admin_warehouse_timestamp(tabla='imp_llegadas', actualizar_datetime=False, mensaje=f"""Error api imp_llegadas: status {imp_llegadas_mba['status']}\nError api proveedor: status{proveedor_mba['status']}""")
            
    except Exception as e:
        
        admin_warehouse_timestamp(tabla='imp_llegadas', actualizar_datetime=False, mensaje=f'Error exception: {e}')


### 4 ACTUALIZAR IMP TRANSITO WAREHOUSE
def api_actualizar_imp_transito_warehouse():
    
    try:
        imp_transito_mba = api_mba_sql(
            """
            SELECT 
                CLNT_Pedidos_Principal.CONTRATO_ID, 
                PROV_Ficha_Principal.VENDOR_NAME, 
                CLNT_Pedidos_Detalle.PRODUCT_ID, 
                CLNT_Pedidos_Detalle.QUANTITY, 
                CLNT_Pedidos_Principal.FECHA_ENTREGA, 
                CLNT_Pedidos_Principal.MEMO 
            FROM 
                CLNT_Pedidos_Detalle CLNT_Pedidos_Detalle, 
                CLNT_Pedidos_Principal CLNT_Pedidos_Principal, 
                PROV_Ficha_Principal PROV_Ficha_Principal 
            WHERE 
                CLNT_Pedidos_Detalle.CONTRATO_ID_CORP = CLNT_Pedidos_Principal.CONTRATO_ID_CORP AND 
                CLNT_Pedidos_Principal.CLIENT_ID_CORP = PROV_Ficha_Principal.CODIGO_PROVEEDOR_EMPRESA AND 
                (CLNT_Pedidos_Principal.PEDIDO_CERRADO=false) AND 
                (CLNT_Pedidos_Principal.CONFIRMED=false) AND 
                (CLNT_Pedidos_Principal.VOID=false))
            """
            
        )
        
        if imp_transito_mba['status'] == 200:
            
            # data = [tuple(i.values()) for i in imp_transito_mba['data']]
            
            data = []
            for i in imp_transito_mba['data']:
                
                contrato_id = i['CONTRATO_ID']
                vendor_name = i['VENDOR_NAME']
                product_id = i['PRODUCT_ID']
                quantity = i['QUANTITY']
                fecha_entrega = datetime.strptime(i['FECHA_ENTREGA'][:10], '%d/%m/%Y')
                memo = i['MEMO']
                
                row = (
                    contrato_id,
                    vendor_name,
                    product_id,
                    quantity,
                    fecha_entrega,
                    memo
                )
                
                data.append(row)
                
                
            #with transaction.atomic():
            # Borrar datos de tabla imp_transito
            delete_data_warehouse('imp_transito')
            
            # # Insertar datos de tabla imp_transito
            insert_data_warehouse('imp_transito', data)
            
            admin_warehouse_timestamp(tabla='imp_transito', actualizar_datetime=True, mensaje='Actualizado correctamente')
    
        else:
        
            admin_warehouse_timestamp(tabla='imp_transito', actualizar_datetime=False, mensaje=f'Error api: status {imp_transito_mba["status"]}')
    
    except Exception as e:
        
        admin_warehouse_timestamp(tabla='imp_transito', actualizar_datetime=False, mensaje=f'Error exception {e}')


### 5 ACTUALIZAR PEDIDOS
def api_actualizar_pedidos_warehouse():
    
    try:
        
        data_api = api_mba_sql(
        """ 
        SELECT 
            CLNT_Pedidos_Principal.CONTRATO_ID, 
            CLNT_Pedidos_Principal.FECHA_PEDIDO, 
            CLNT_Pedidos_Principal.WARE_CODE,
            CLNT_Pedidos_Principal.CONFIRMED, 
            CLNT_Pedidos_Principal.HORA_LLEGADA,
            CLNT_Pedidos_Principal.Preparacion_numero, 
            CLNT_Pedidos_Principal.Entry_by
        FROM 
            CLNT_Pedidos_Principal CLNT_Pedidos_Principal
        ORDER BY CLNT_Pedidos_Principal.CONTRATO_ID DESC
        """
        )

        if data_api['status'] == 200:
            
            data = []
            for i in data_api['data']:
                
                contrato_id = i['CONTRATO_ID']
                fecha_pedido = datetime.strptime(i['FECHA_PEDIDO'][:10], '%d/%m/%Y')
                ware_code = i['WARE_CODE']
                confirmed = 0 if i['CONFIRMED'] == 'false' else 1
                hora_llegada = i['HORA_LLEGADA']
                preparacion_numero = i['PREPARACION_NUMERO']
                entry_by = i['ENTRY_BY']
                
                row = (
                    contrato_id,
                    fecha_pedido,
                    ware_code,
                    confirmed,
                    hora_llegada,
                    preparacion_numero,
                    entry_by
                )
                
                data.append(row)
                
            #while transaction.atomic():
            # Borrar datos de tabla stock_lote
            delete_data_warehouse('pedidos')
            
            # Insertar datos de tabla stock_lote
            insert_data_warehouse('pedidos', data)
            
            admin_warehouse_timestamp(tabla='pedidos', actualizar_datetime=True, mensaje='Actualizado correctamente')
            
        else:
            
            admin_warehouse_timestamp(tabla='pedidos', actualizar_datetime=False, mensaje='Error fetch ODBC')
            
    except Exception as e:
        # print(e)
        admin_warehouse_timestamp(tabla='pedidos', actualizar_datetime=False, mensaje=f'Error ODBC exception: {e}')


### 6 ACTUALIZAR PRODUCTOS WAREHOUSE POR API DATA
def api_actualizar_productos_warehouse():
    
    try:
    
        productos_mba = api_mba_sql(
        """
            SELECT 
                INVT_Ficha_Principal.PRODUCT_ID, 
                INVT_Ficha_Principal.PRODUCT_NAME, 
                INVT_Ficha_Principal.UM, 
                INVT_Ficha_Principal.GROUP_CODE, 
                INVT_Grupo_SubGrupo_Lista.DESCRIPTION, 
                INVT_Ficha_Principal.UNIDADES_EMPAQUE, 
                INVT_Ficha_Principal.Custom_Field_1,
                INVT_Ficha_Principal.Custom_Field_2, 
                INVT_Ficha_Principal.Custom_Field_4, 
                INVT_Ficha_Principal.INACTIVE, 
                INVT_Ficha_Principal.LARGO, 
                INVT_Ficha_Principal.ANCHO, 
                INVT_Ficha_Principal.ALTURA, 
                INVT_Ficha_Principal.VOLUMEN, 
                INVT_Ficha_Principal.WEIGHT, 
                INVT_Ficha_Principal.AVAILABLE, 
                INVT_Ficha_Principal.UnidadesPorPallet 
            FROM 
                INVT_Ficha_Principal INVT_Ficha_Principal, 
                INVT_Grupo_SubGrupo_Lista INVT_Grupo_SubGrupo_Lista 
            WHERE 
                INVT_Ficha_Principal.GROUP_CODE = INVT_Grupo_SubGrupo_Lista.GROUP_CODE AND 
                INVT_Grupo_SubGrupo_Lista.SUB_GROUP=false 
        """
        )    
        
        if productos_mba['status'] == 200:
            
            # data = [tuple(i.values()) for i in productos_mba['data']]
            
            # Trasformar data
            data = []
            
            for i in productos_mba["data"]:
                
                product_id = i['PRODUCT_ID']
                product_name = i['PRODUCT_NAME']
                group_code = i['GROUP_CODE']
                marcadet = i['DESCRIPTION']
                um = i['UM']
                unidades_empaque = i['UNIDADES_EMPAQUE']
                custom_field_1 = i['CUSTOM_FIELD_1']
                custom_field_2 = i['CUSTOM_FIELD_2']
                custom_field_4 = i['CUSTOM_FIELD_4']
                inactive = 0 if i['INACTIVE'] == 'false' else 1 # SOLO POR ESTE DATO SE CREA EL CICLO FOR 
                largo = i['LARGO']
                ancho = i['ANCHO'] 
                altura = i['ALTURA'] 
                volumen = i['VOLUMEN'] 
                weight = i['WEIGHT']
                available = i['AVAILABLE']
                unidadesporpallet = i['UNIDADESPORPALLET']
                
                row = (
                    product_id,
                    product_name,
                    group_code,
                    marcadet,
                    um,
                    unidades_empaque,
                    custom_field_1,
                    custom_field_2,
                    custom_field_4,
                    inactive,
                    largo,
                    ancho,
                    altura,
                    volumen,
                    weight,
                    available,
                    unidadesporpallet
                )
                
                data.append(row)
            
            #with transaction.atomic():
            # Borrar datos de tabla productos
            delete_data_warehouse('productos')
            
            # Insertar datos de tabla productos
            insert_data_warehouse('productos', data)
            
            admin_warehouse_timestamp(tabla='productos', actualizar_datetime=True, mensaje='Actualizado correctamente')

        else:
        
            admin_warehouse_timestamp(tabla='productos', actualizar_datetime=False, mensaje=f'Error api: status {productos_mba["status"]}')
    
    except Exception as e:
        
        admin_warehouse_timestamp(tabla='productos', actualizar_datetime=False, mensaje=f'Error exception: {e}')


### 7 ACTUALIZAR PRODUCTOS EN TRANSITO
def api_actualizar_producto_transito_warehouse():
    
    try:
    
        productos_transito_mba = api_mba_sql(
            
            """
            SELECT 
                INVT_Ficha_Principal.PRODUCT_ID, 
                INVT_Producto_Lotes.OH, 
                INVT_Producto_Lotes.LOTE_ID, 
                INVT_Producto_Lotes.Fecha_elaboracion_lote, 
                INVT_Producto_Lotes.FECHA_CADUCIDAD, 
                INVT_Producto_Lotes.WARE_CODE_CORP, 
                INVT_Producto_Movimientos.WAR_CODE, 
                INVT_Producto_Movimientos.Bod_Trf_OrigDest 
            FROM 
                INVT_Ficha_Principal INVT_Ficha_Principal, 
                INVT_Producto_Lotes INVT_Producto_Lotes, 
                INVT_Producto_Movimientos 
                INVT_Producto_Movimientos 
            WHERE 
                INVT_Ficha_Principal.PRODUCT_ID_CORP = INVT_Producto_Lotes.PRODUCT_ID_CORP AND 
                INVT_Producto_Movimientos.PRODUCT_ID_CORP = INVT_Producto_Lotes.PRODUCT_ID_CORP AND 
                INVT_Producto_Lotes.ENTRADA_DOC_REFERENCIA = INVT_Producto_Movimientos.ORIGIN_REF AND 
                ((INVT_Producto_Lotes.WARE_CODE_CORP='TRN') AND (INVT_Producto_Movimientos.ADJUSTMENT_TYPE='TE'))
            """
        )
    
        if productos_transito_mba["status"] == 200:
            
            # data = [tuple(i.values()) for i in productos_transito_mba["data"]]
            
            data = []
            for i in productos_transito_mba['data']:
                product_id = i['PRODUCT_ID']
                oh = i['OH']
                lote_id = i['LOTE_ID']
                fecha_elaboracion_lote = i['FECHA_ELABORACION_LOTE'][:10] # cortar formato de fecha que trae la api
                fecha_caducidad = i['FECHA_CADUCIDAD'][:10] # cortar formato de fecha que trae la api
                ware_code_corp = i['WARE_CODE_CORP']
                ware_code = i['WAR_CODE']
                bod_trans_oring_destino = i['BOD_TRF_ORIGDEST']

                row = (
                    product_id, 
                    oh, 
                    lote_id.replace('.',''), 
                    fecha_elaboracion_lote, 
                    fecha_caducidad,
                    ware_code_corp,
                    ware_code,
                    bod_trans_oring_destino
                )
                
                data.append(row)
                
            #with transaction.atomic():
            # Borrar datos de tabla clientes
            delete_data_warehouse('productos_transito')
            
            # Insertar datos de tabla clientes
            insert_data_warehouse('productos_transito', data)
            
            admin_warehouse_timestamp(tabla='productos_transito', actualizar_datetime=True, mensaje='Actualizado correctamente')
    
        else:
        
            admin_warehouse_timestamp(tabla='productos_transito', actualizar_datetime=False, mensaje=f'Error api: status {productos_transito_mba["status"]}')
    
    except Exception as e:
        
        admin_warehouse_timestamp(tabla='productos_transito', actualizar_datetime=False, mensaje=f'Error exception: {e}')


### 8 ACTULIZAR PROFORMAS
def api_actualizar_proformas_warehouse():
    
    try:
        
        #today = datetime.today() - timedelta(days=45)
        today = datetime.today() - timedelta(days=90)
        today = today.strftime('%Y-%m-%d')
        
        proformas_mba = api_mba_sql(
            f"""
            SELECT 
                CLNT_Pedidos_Principal.CONTRATO_ID, 
                CLNT_Ficha_Principal.NOMBRE_CLIENTE, 
                CLNT_Pedidos_Principal.FECHA_PEDIDO, 
                CLNT_Pedidos_Principal.FECHA_HASTA, 
                CLNT_Pedidos_Principal.SALESMAN, 
                CLNT_Pedidos_Principal.CONFIRMED, 
                CLNT_Pedidos_Detalle.PRODUCT_ID, 
                CLNT_Pedidos_Detalle.QUANTITY 
            FROM 
                CLNT_Ficha_Principal CLNT_Ficha_Principal, 
                CLNT_Pedidos_Detalle CLNT_Pedidos_Detalle, 
                CLNT_Pedidos_Principal CLNT_Pedidos_Principal 
            WHERE 
                CLNT_Pedidos_Detalle.CONTRATO_ID_CORP = CLNT_Pedidos_Principal.CONTRATO_ID_CORP AND 
                CLNT_Ficha_Principal.CODIGO_CLIENTE_EMPRESA = CLNT_Pedidos_Principal.CLIENT_ID_CORP AND 
                CLNT_Pedidos_Principal.FECHA_PEDIDO >='{today}' AND 
                ((CLNT_Pedidos_Detalle.TIPO_DOCUMENTO='CT') AND (CLNT_Pedidos_Principal.VOID=False))
            """
        )
        
        if proformas_mba['status'] == 200:
            
            # data = [tuple(i.values()) for i in proformas_mba['data']]
            
            data = []
            
            for i in proformas_mba['data']:
                
                contrato_id = i['CONTRATO_ID']
                nombre_cliente = i['NOMBRE_CLIENTE']            
                fecha_pedido = '' if not i['FECHA_PEDIDO'] else i['FECHA_PEDIDO'][:10]            
                fecha_hasta = '' if not i['FECHA_HASTA'] else i['FECHA_HASTA'][:10] 
                salesman = i['SALESMAN']
                confirmed = 0 if i['CONFIRMED'] == 'false' else 1
                product_id = i['PRODUCT_ID']
                quantity = i['QUANTITY']
                
                row = (
                    contrato_id,
                    nombre_cliente,
                    fecha_pedido,
                    fecha_hasta,
                    salesman,
                    confirmed,
                    product_id,
                    quantity,
                )
                
                data.append(row)
            
            
            #with transaction.atomic():
            # Borrar datos de tabla proformas
            delete_data_warehouse('proformas')
            
            # Insertar datos de tabla proformas
            insert_data_warehouse('proformas', data)
            
            admin_warehouse_timestamp(tabla='proformas', actualizar_datetime=True, mensaje='Actualizado correctamente')
        
        else:
            
            admin_warehouse_timestamp(tabla='proformas', actualizar_datetime=False, mensaje=f'Error api: status {proformas_mba["status"]}')
        
    except Exception as e:
        
        admin_warehouse_timestamp(tabla='proformas', actualizar_datetime=False, mensaje=f'Error exepction: {e}')


### 9 ACTUALIZAR RESERVAS WAREHOUSE
def api_actualizar_reservas_warehouse():
    
    try:    
        reservas_mba = api_mba_sql(
        # """
        # SELECT 
        #     CLNT_Pedidos_Principal.FECHA_PEDIDO, 
        #     CLNT_Pedidos_Principal.CONTRATO_ID, 
        #     CLNT_Ficha_Principal.CODIGO_CLIENTE, 
        #     CLNT_Ficha_Principal.NOMBRE_CLIENTE,
        #     CLNT_Pedidos_Detalle.PRODUCT_ID, 
        #     CLNT_Pedidos_Detalle.PRODUCT_NAME, 
        #     CLNT_Pedidos_Detalle.QUANTITY, 
        #     CLNT_Pedidos_Detalle.Despachados, 
        #     CLNT_Pedidos_Principal.WARE_CODE, 
        #     CLNT_Pedidos_Principal.CONFIRMED,
        #     CLNT_Pedidos_Principal.HORA_LLEGADA, 
        #     CLNT_Pedidos_Principal.SEC_NAME_CLIENTE, 
        #     CLNT_Pedidos_Detalle.UNIQUE_ID
        # FROM 
        #     CLNT_Ficha_Principal CLNT_Ficha_Principal, 
        #     CLNT_Pedidos_Detalle CLNT_Pedidos_Detalle, 
        #     CLNT_Pedidos_Principal CLNT_Pedidos_Principal
        # WHERE 
        #     CLNT_Pedidos_Principal.CONTRATO_ID_CORP = CLNT_Pedidos_Detalle.CONTRATO_ID_CORP AND 
        #     CLNT_Ficha_Principal.CODIGO_CLIENTE = CLNT_Pedidos_Principal.CLIENT_ID AND 
        #     CLNT_Pedidos_Detalle.Despachados=0 AND 
        #     ((CLNT_Pedidos_Principal.PEDIDO_CERRADO=false) AND (CLNT_Pedidos_Detalle.TIPO_DOCUMENTO='PE') AND 
        #     (CLNT_Pedidos_Detalle.PRODUCT_ID<>'MANTEN')) ORDER BY CLNT_Pedidos_Principal.CONTRATO_ID DESC
        # """
        
        """
        SELECT 
            CLNT_Pedidos_Principal.FECHA_PEDIDO, 
            CLNT_Pedidos_Principal.CONTRATO_ID, 
            CLNT_Ficha_Principal.CODIGO_CLIENTE, 
            CLNT_Ficha_Principal.NOMBRE_CLIENTE, 
            CLNT_Pedidos_Detalle.PRODUCT_ID, 
            CLNT_Pedidos_Detalle.PRODUCT_NAME, 
            CLNT_Pedidos_Detalle.QUANTITY, 
            CLNT_Pedidos_Detalle.Despachados, 
            CLNT_Pedidos_Principal.WARE_CODE, 
            CLNT_Pedidos_Principal.CONFIRMED, 
            CLNT_Pedidos_Principal.HORA_LLEGADA, 
            CLNT_Pedidos_Principal.MEMO, 
            CLNT_Pedidos_Detalle.UNIQUE_ID 
        FROM 
            CLNT_Ficha_Principal CLNT_Ficha_Principal, 
            CLNT_Pedidos_Detalle CLNT_Pedidos_Detalle, 
            CLNT_Pedidos_Principal CLNT_Pedidos_Principal 
        WHERE 
            CLNT_Pedidos_Principal.CONTRATO_ID_CORP = CLNT_Pedidos_Detalle.CONTRATO_ID_CORP AND 
            CLNT_Ficha_Principal.CODIGO_CLIENTE = CLNT_Pedidos_Principal.CLIENT_ID AND 
            CLNT_Pedidos_Detalle.Despachados=0 AND 
            ((CLNT_Pedidos_Principal.PEDIDO_CERRADO=false) AND 
            (CLNT_Pedidos_Detalle.TIPO_DOCUMENTO='PE') AND 
            (CLNT_Pedidos_Detalle.PRODUCT_ID<>'MANTEN')) ORDER BY CLNT_Pedidos_Principal.CONTRATO_ID DESC
        """
        )
        
        
        if  reservas_mba["status"] == 200:
            
            # data = [tuple(i.values()) for i in reservas_mba['data']]
            
            data = []
            for i in reservas_mba['data']:
                
                if i['PRODUCT_ID'] == 'ETIQUE' or i['PRODUCT_ID'] == 'MANTEN' or i['PRODUCT_ID'] == 'TRANS':
                    continue
                else:
                    fecha_pedido = datetime.strptime(i['FECHA_PEDIDO'][:10], '%d/%m/%Y') # date
                    contrato_id = str(i['CONTRATO_ID']) + '.0' # str
                    codigo_cliente = i['CODIGO_CLIENTE']
                    nombre_cliente = i['NOMBRE_CLIENTE']
                    product_id = i['PRODUCT_ID']
                    product_name = i['PRODUCT_NAME']
                    quantity = i['QUANTITY']
                    despachado = i['DESPACHADOS']
                    ware_code = i['WARE_CODE']
                    confirmed = 0 if i['CONFIRMED'] == 'false' else 1
                    hora_llegada = i['HORA_LLEGADA'] # time
                    
                    # s_n_c = i['SEC_NAME_CLIENTE']
                    s_n_c = i['MEMO']
                    if s_n_c.startswith('P'):
                        sec_name_cliente = 'PUBLICO'
                    elif s_n_c.startswith('R'):
                        sec_name_cliente = 'RESERVA'
                    else:
                        #sec_name_cliente = ''
                        sec_name_cliente = i['MEMO']
                    
                    unique_id = i['UNIQUE_ID']
                    
                    row = (
                        fecha_pedido,
                        contrato_id,
                        codigo_cliente,
                        nombre_cliente,
                        product_id,
                        product_name,
                        quantity,
                        despachado,
                        ware_code,
                        confirmed,
                        hora_llegada,
                        sec_name_cliente,
                        unique_id 
                    )
                    
                    data.append(row)
            
            # with transaction.atomic():
            # Borrar datos de tabla reservas
            delete_data_warehouse('reservas')
            
            # Insertar datos de tabla reservas
            insert_data_warehouse('reservas', data)
            
            admin_warehouse_timestamp(tabla='reservas', actualizar_datetime=True, mensaje='Actualizado correctamente')

        else:
        
            admin_warehouse_timestamp(tabla='reservas', actualizar_datetime=False, mensaje=f'Error api: status {reservas_mba["status"]}')

    except Exception as e:
        
        admin_warehouse_timestamp(tabla='reservas', actualizar_datetime=False, mensaje=f'Error exception: {e}')


### 10 ACTUALIZAR RESERVAS LOTES WAREHOUSE
QUERY_RESERVAS_LOTE = """
    SELECT 
        CLNT_Pedidos_Principal.FECHA_PEDIDO, 
        CLNT_Pedidos_Principal.CONTRATO_ID, 
        CLNT_Ficha_Principal.CODIGO_CLIENTE, 
        CLNT_Pedidos_Detalle.PRODUCT_ID, 
        CLNT_Pedidos_Principal.WARE_CODE, 
        INVT_Lotes_Trasabilidad.EGRESO_TEMP, 
        INVT_Lotes_Trasabilidad.LOTE_ID, 
        INVT_Lotes_Trasabilidad.FECHA_CADUCIDAD, 
        INVT_Producto_Lotes.Fecha_elaboracion_lote, 
        CLNT_Pedidos_Principal.CONFIRMED, 
        CLNT_Pedidos_Detalle.UNIT_COST 
    
    FROM 
        CLNT_Ficha_Principal CLNT_Ficha_Principal, 
        CLNT_Pedidos_Detalle CLNT_Pedidos_Detalle, 
        CLNT_Pedidos_Principal CLNT_Pedidos_Principal, 
        INVT_Lotes_Trasabilidad INVT_Lotes_Trasabilidad, 
        INVT_Producto_Lotes INVT_Producto_Lotes 
    
    WHERE 
        CLNT_Pedidos_Principal.CONTRATO_ID_CORP = CLNT_Pedidos_Detalle.CONTRATO_ID_CORP AND 
        CLNT_Ficha_Principal.CODIGO_CLIENTE = CLNT_Pedidos_Principal.CLIENT_ID AND 
        CLNT_Pedidos_Detalle.CONTRATO_ID_CORP = INVT_Lotes_Trasabilidad.DOC_ID_CORP AND 
        CLNT_Pedidos_Detalle.PRODUCT_ID_CORP = INVT_Lotes_Trasabilidad.PRODUCT_ID_CORP AND 
        INVT_Lotes_Trasabilidad.PRODUCT_ID_CORP = INVT_Producto_Lotes.PRODUCT_ID_CORP AND
        INVT_Lotes_Trasabilidad.LOTE_ID = INVT_Producto_Lotes.LOTE_ID AND 
        INVT_Lotes_Trasabilidad.WARE_COD_CORP = INVT_Producto_Lotes.WARE_CODE_CORP AND 
        ((CLNT_Pedidos_Principal.PEDIDO_CERRADO=false) AND (CLNT_Pedidos_Detalle.TIPO_DOCUMENTO='PE')) 
    
    ORDER BY CLNT_Pedidos_Principal.CONTRATO_ID, CLNT_Pedidos_Detalle.PRODUCT_ID DESC    
"""

def api_actualizar_reservas_lotes_warehouse():
    
    try:
    
        reservas_lotes_mba = api_mba_sql(QUERY_RESERVAS_LOTE)
        
        if reservas_lotes_mba["status"] == 200:
        
            #data = [tuple(i.values()) for i in reservas_lotes_mba['data']]
        
            data = []
            for i in reservas_lotes_mba['data']:
                fecha_pedido = datetime.strptime(i['FECHA_PEDIDO'][:10], '%d/%m/%Y') # date
                contrato_id = i['CONTRATO_ID']
                codigo_cliente = i['CODIGO_CLIENTE']
                product_id = i['PRODUCT_ID']
                ware_code = i['WARE_CODE']
                egreso_temp = i['EGRESO_TEMP']
                lote_id = i['LOTE_ID']
                fecha_caducidad = datetime.strptime(i['FECHA_CADUCIDAD'][:10], '%d/%m/%Y') # date
                confirmed = 0 if i['CONFIRMED'] == 'false' else 1
                fecha_elaboracion_lote = datetime.strptime(i['FECHA_ELABORACION_LOTE'][:10], '%d/%m/%Y') # date
                unit_cost = i['UNIT_COST']           
                
                row = (
                    fecha_pedido,
                    contrato_id,
                    codigo_cliente,
                    product_id,
                    ware_code,
                    egreso_temp,
                    lote_id,
                    fecha_caducidad,
                    confirmed,
                    fecha_elaboracion_lote,
                    unit_cost,
                )
                
                data.append(row)
            print(data[:5])
            #with transaction.atomic():
            # Borrar datos de tabla reservas_lote
            delete_data_warehouse('reservas_lote')
            
            # Insertar datos de tabla reservas_lote
            insert_data_warehouse('reservas_lote', data)
            
            admin_warehouse_timestamp(tabla='reservas_lote', actualizar_datetime=True, mensaje='API - Actualizado correctamente')

        else:
        
            admin_warehouse_timestamp(tabla='reservas_lote', actualizar_datetime=False, mensaje=f'API - Error api: status {reservas_lotes_mba["status"]}')
        
    except Exception as e:
        
        admin_warehouse_timestamp(tabla='reservas_lote', actualizar_datetime=False, mensaje=f'API - Error exception: {e}')


def odbc_actualizar_reservas_lotes_warehouse():
    
    try:
        
        cnx = pyodbc.connect("DSN=mba3;PWD=API")
        cursor = cnx.cursor()
        reservas_lotes_query = cursor.execute(QUERY_RESERVAS_LOTE)
        data = reservas_lotes_query.fetchall() 
        
        data_transformada = []
        if len(data) >= 1 :
            
            for i in data:
                # print(i)
                fecha_pedido = i[0]
                contrato_id = str(i[1]).split('.')[0] #;print(contrato_id)
                codigo_cliente = i[2]
                product_id = i[3]
                ware_code = i[4]
                egreso_temp = i[5]
                lote_id = i[6]
                fecha_caducidad = i[7]
                confirmed = i[9]
                fecha_elaboracion_lote = i[8]
                price = i[10]
                
                row = (
                    fecha_pedido,
                    contrato_id,
                    codigo_cliente,
                    product_id,
                    ware_code,
                    egreso_temp,
                    lote_id,
                    fecha_caducidad,
                    confirmed,
                    fecha_elaboracion_lote,
                    price
                )
                # print(row)
                data_transformada.append(row)
            
            #with transaction.atomic():
            # Borrar datos de tabla reservas_lote
            delete_data_warehouse('reservas_lote')
            
            # Insertar datos de tabla reservas_lote
            # insert_data_warehouse('reservas_lote', data)
            insert_data_warehouse('reservas_lote', data_transformada)
            
            admin_warehouse_timestamp(tabla='reservas_lote', actualizar_datetime=True, mensaje='ODBC - Actualizado correctamente')

        else:
        
            admin_warehouse_timestamp(tabla='reservas_lote', actualizar_datetime=False, mensaje=f'ODBC - ERROR ODBC NO TRAE DATOS')
        
    except Exception as e:
        print(e)
        admin_warehouse_timestamp(tabla='reservas_lote', actualizar_datetime=False, mensaje=f'ODBC - Error exception: {e}')


### 11 ACTUALIZAR RESERVAS LOTES WAREHOUSE
def api_actualizar_reservas_lotes_2_warehouse():
    
    try:
        reservas_lotes_2_mba = api_mba_sql(
            """
            SELECT 
                CLNT_Pedidos_Principal.FECHA_PEDIDO, 
                CLNT_Pedidos_Principal.CONTRATO_ID, 
                CLNT_Ficha_Principal.CODIGO_CLIENTE, 
                INVT_Ficha_Principal.PRODUCT_ID, 
                CLNT_Pedidos_Principal.WARE_CODE, 
                INVT_Lotes_Trasabilidad.EGRESO_TEMP, 
                INVT_Lotes_Trasabilidad.LOTE_ID, 
                INVT_Lotes_Trasabilidad.FECHA_CADUCIDAD, 
                INVT_Producto_Lotes.Fecha_elaboracion_lote, 
                CLNT_Pedidos_Principal.CONFIRMED, 
                CLNT_Pedidos_Principal.MEMO 
            FROM 
                CLNT_Ficha_Principal CLNT_Ficha_Principal, 
                INVT_Ficha_Principal INVT_Ficha_Principal, 
                CLNT_Pedidos_Principal CLNT_Pedidos_Principal, 
                INVT_Lotes_Trasabilidad INVT_Lotes_Trasabilidad, 
                INVT_Producto_Lotes INVT_Producto_Lotes 
            WHERE 
                CLNT_Ficha_Principal.CODIGO_CLIENTE = CLNT_Pedidos_Principal.CLIENT_ID AND 
                INVT_Lotes_Trasabilidad.PRODUCT_ID_CORP = INVT_Producto_Lotes.PRODUCT_ID_CORP AND 
                INVT_Lotes_Trasabilidad.LOTE_ID = INVT_Producto_Lotes.LOTE_ID AND 
                INVT_Lotes_Trasabilidad.WARE_COD_CORP = INVT_Producto_Lotes.WARE_CODE_CORP AND 
                INVT_Lotes_Trasabilidad.DOC_ID_CORP = CLNT_Pedidos_Principal.CONTRATO_ID_CORP AND 
                INVT_Ficha_Principal.PRODUCT_ID_CORP = INVT_Lotes_Trasabilidad.PRODUCT_ID_CORP AND 
                ((CLNT_Pedidos_Principal.PEDIDO_CERRADO=false)) 
            ORDER BY CLNT_Pedidos_Principal.CONTRATO_ID
            """
        )
        
        if reservas_lotes_2_mba["status"] == 200:
            
            #data = [tuple(i.values()) for i in reservas_lotes_mba['data']]
            data = []
            for i in reservas_lotes_2_mba['data']:
                fecha_pedido = datetime.strptime(i['FECHA_PEDIDO'][:10], '%d/%m/%Y') # date
                contrato_id = i['CONTRATO_ID']
                codigo_cliente = i['CODIGO_CLIENTE']
                product_id = i['PRODUCT_ID']
                ware_code = i['WARE_CODE']
                egreso_temp = i['EGRESO_TEMP']
                lote_id = i['LOTE_ID']
                fecha_caducidad = datetime.strptime(i['FECHA_CADUCIDAD'][:10], '%d/%m/%Y') # date
                fecha_elaboracion_lote = datetime.strptime(i['FECHA_ELABORACION_LOTE'][:10], '%d/%m/%Y') # date
                confirmed = 0 if i['CONFIRMED'] == 'false' else 1
                # sec_name_cliente = i['SEC_NAME_CLIENTE']
                sec_name_cliente = i['MEMO']
                
                
                row = (
                    fecha_pedido,
                    contrato_id,
                    codigo_cliente,
                    product_id,
                    ware_code,
                    egreso_temp,
                    lote_id,
                    fecha_caducidad,
                    confirmed,
                    fecha_elaboracion_lote,
                    sec_name_cliente
                )
                
                data.append(row)
            
            #with transaction.atomic():
            # Borrar datos de tabla reservas_lote
            delete_data_warehouse('reservas_lote_2')
            
            # Insertar datos de tabla reservas_lote
            insert_data_warehouse('reservas_lote_2', data)
            
            admin_warehouse_timestamp(tabla='reservas_lote_2', actualizar_datetime=True, mensaje='Actualizado correctamente')
        else:
            admin_warehouse_timestamp(tabla='reservas_lote_2', actualizar_datetime=False, mensaje=f'Error api: status {reservas_lotes_2_mba["status"]}')
    except Exception as e:
        admin_warehouse_timestamp(tabla='reservas_lote_2', actualizar_datetime=False, mensaje=f'Error exception: {e}')


### 12 ACTULIZAR STOCK LOTE
STOCK_LOTE_QUERY = """
    SELECT 
        INVT_Ficha_Principal.PRODUCT_ID, 
        INVT_Ficha_Principal.PRODUCT_NAME, 
        INVT_Ficha_Principal.GROUP_CODE,
        INVT_Ficha_Principal.UM, 
        INVT_Producto_Lotes.OH AS OH_LOTE, 
        INVT_Producto_Lotes_Bodegas.OH AS OH_BODEGA, 
        INVT_Producto_Lotes_Bodegas.COMMITED,
        INVT_Producto_Lotes_Bodegas.QUANTITY, 
        INVT_Producto_Lotes.LOTE_ID, 
        INVT_Producto_Lotes.Fecha_elaboracion_lote, 
        INVT_Producto_Lotes.FECHA_CADUCIDAD,
        INVT_Producto_Lotes_Bodegas.WARE_CODE, 
        INVT_Producto_Lotes_Bodegas.LOCATION, 
        INVT_Producto_Lotes.AVAILABLE
    FROM 
        INVT_Ficha_Principal INVT_Ficha_Principal, 
        INVT_Producto_Lotes INVT_Producto_Lotes, 
        INVT_Producto_Lotes_Bodegas INVT_Producto_Lotes_Bodegas 
    WHERE 
        INVT_Ficha_Principal.PRODUCT_ID_CORP = INVT_Producto_Lotes.PRODUCT_ID_CORP AND 
        INVT_Producto_Lotes_Bodegas.PRODUCT_ID_CORP = INVT_Ficha_Principal.PRODUCT_ID_CORP AND 
        INVT_Producto_Lotes_Bodegas.Confirm=true AND 
        INVT_Producto_Lotes.LOTE_ID = INVT_Producto_Lotes_Bodegas.LOTE_ID AND 
        INVT_Producto_Lotes.WARE_CODE_CORP = INVT_Producto_Lotes_Bodegas.WARE_CODE AND 
        ((INVT_Producto_Lotes.OH>0) AND (INVT_Producto_Lotes_Bodegas.OH>0))
"""

def api_actualizar_stock_lote_warehouse():
    
    try:
        stock_lote_mba = api_mba_sql(STOCK_LOTE_QUERY)
    
        if stock_lote_mba["status"] == 200:
            data = []
            for i in stock_lote_mba['data']:
                product_id   = i['PRODUCT_ID']
                product_name = i['PRODUCT_NAME']
                group_code   = i['GROUP_CODE']
                um           = i['UM']
                oh           = i['OH_LOTE']
                oh2          = i['OH_BODEGA'] 
                commited     = i['COMMITED']
                quantity     = i['QUANTITY']
                lote_id      = i['LOTE_ID']
                f_elab_lote  = datetime.strptime(i['FECHA_ELABORACION_LOTE'][:10], '%d/%m/%Y')
                f_cadu_lote  = datetime.strptime(i['FECHA_CADUCIDAD'][:10], '%d/%m/%Y')
                ware_code    = i['WARE_CODE']
                location     = i['LOCATION']
                available    = i['AVAILABLE']   

                t = (
                    product_id,
                    product_name,
                    group_code,
                    um,
                    oh,
                    oh2,
                    commited,
                    quantity,
                    lote_id,
                    f_elab_lote,
                    f_cadu_lote,
                    ware_code,
                    location,
                    available
                )
                data.append(t)
            # Borrar datos de tabla clientes
            delete_data_warehouse('stock_lote')
            
            # Insertar datos de tabla clientes
            insert_data_warehouse('stock_lote', data)
            
            admin_warehouse_timestamp(tabla='stock_lote', actualizar_datetime=True, mensaje='API - Actualizado correctamente')
    
        else:
            admin_warehouse_timestamp(tabla='stock_lote', actualizar_datetime=True, mensaje='API NO TRAE DATOS')
    
    except Exception as e:
        
        admin_warehouse_timestamp(tabla='stock_lote', actualizar_datetime=False, mensaje=f'API - Error: {e}')


def odbc_actualizar_stock_lote_warehouse():
    
    try:
        
        cnx = pyodbc.connect("DSN=mba3;PWD=API")
        cursor = cnx.cursor()        
        stock_lote_mba = cursor.execute(STOCK_LOTE_QUERY)
        data = stock_lote_mba.fetchall()
        
        if len(data) >=1 :

            # Borrar datos de tabla clientes
            delete_data_warehouse('stock_lote')
            
            # Insertar datos de tabla clientes
            insert_data_warehouse('stock_lote', data)
            
            admin_warehouse_timestamp(tabla='stock_lote', actualizar_datetime=True, mensaje='ODBC - Actualizado correctamente')
        else:
            admin_warehouse_timestamp(tabla='stock_lote', actualizar_datetime=True, mensaje='ODBC - NO TRAE DATOS')
    
    except Exception as e:
        
        admin_warehouse_timestamp(tabla='stock_lote', actualizar_datetime=False, mensaje=f'ODBC - Error: {e}')



### 14 ACTUALIZAR RESERVAS MODELO DE ETIQUETADO
def api_actualizar_mis_reservas_etiquetado():
    
    try:    
        reservas_mba = api_mba_sql(
        """
        SELECT 
            CLNT_Pedidos_Principal.FECHA_PEDIDO, 
            CLNT_Pedidos_Principal.CONTRATO_ID, 
            CLNT_Ficha_Principal.CODIGO_CLIENTE, 
            CLNT_Ficha_Principal.NOMBRE_CLIENTE, 
            CLNT_Pedidos_Detalle.PRODUCT_ID, 
            CLNT_Pedidos_Detalle.PRODUCT_NAME, 
            CLNT_Pedidos_Detalle.QUANTITY, 
            CLNT_Pedidos_Detalle.Despachados, 
            CLNT_Pedidos_Principal.WARE_CODE, 
            CLNT_Pedidos_Principal.CONFIRMED, 
            CLNT_Pedidos_Principal.HORA_LLEGADA, 
            CLNT_Pedidos_Principal.MEMO, 
            CLNT_Pedidos_Detalle.UNIQUE_ID 
        FROM 
            CLNT_Ficha_Principal CLNT_Ficha_Principal, 
            CLNT_Pedidos_Detalle CLNT_Pedidos_Detalle, 
            CLNT_Pedidos_Principal CLNT_Pedidos_Principal 
        WHERE 
            CLNT_Pedidos_Principal.CONTRATO_ID_CORP = CLNT_Pedidos_Detalle.CONTRATO_ID_CORP AND 
            CLNT_Ficha_Principal.CODIGO_CLIENTE = CLNT_Pedidos_Principal.CLIENT_ID AND 
            CLNT_Pedidos_Detalle.Despachados=0 AND 
            ((CLNT_Pedidos_Principal.PEDIDO_CERRADO=false) AND 
            (CLNT_Pedidos_Detalle.TIPO_DOCUMENTO='PE') AND 
            (CLNT_Pedidos_Detalle.PRODUCT_ID<>'MANTEN')) ORDER BY CLNT_Pedidos_Principal.CONTRATO_ID DESC
        """
        )
        
        if  reservas_mba["status"] == 200:
        
            for i in reservas_mba['data']:
                
                if i['PRODUCT_ID'] == 'ETIQUE' or i['PRODUCT_ID'] == 'MANTEN' or i['PRODUCT_ID'] == 'TRANS':
                    continue
                else:
                    contrato_id = str(i['CONTRATO_ID'])
                    codigo_cliente = i['CODIGO_CLIENTE']
                    product_id = i['PRODUCT_ID']
                    quantity = i['QUANTITY']
                    ware_code = i['WARE_CODE']
                    confirmed = 0 if i['CONFIRMED'] == 'false' else 1  
                    fecha_pedido = datetime.strptime(i['FECHA_PEDIDO'][:10], '%d/%m/%Y').date()
                    hora_llegada = datetime.strptime(i['HORA_LLEGADA'], '%H:%M:%S').time()

                    # s_n_c = i['SEC_NAME_CLIENTE']
                    s_n_c = i['MEMO']
                    
                    if s_n_c.startswith('P'):
                        sec_name_cliente = 'PUBLICO'
                    elif s_n_c.startswith('R'):
                        sec_name_cliente = 'RESERVA'
                    else:
                        # sec_name_cliente = i['SEC_NAME_CLIENTE']
                        sec_name_cliente = i['MEMO']
                        

                    unique_id = i['UNIQUE_ID']

                    # Buscar el registro existente
                    row = Reservas.objects.filter(unique_id=unique_id)

                    if row.exists():
                        # El registro existe, verificar si necesita actualización                        
                        reserva_existente = row.first()
                        
                        if reserva_existente.product_id is None or reserva_existente.product_id == '':
                            row.delete()
                        
                        # if  reserva_existente.quantity == 0:
                        #     row.delete()
                            
                        # Campos que siempre se pueden actualizar
                        campos_actualizables = {
                            'contrato_id': contrato_id,
                            'codigo_cliente': codigo_cliente,
                            'product_id': product_id,
                            'ware_code': ware_code,
                            'confirmed': confirmed,
                            'fecha_pedido': fecha_pedido,
                            'hora_llegada': hora_llegada,
                            'sec_name_cliente': sec_name_cliente,
                        }
                        
                        # Si alterado es False, también actualizar quantity y usuario
                        if not reserva_existente.alterado:
                            campos_actualizables['quantity'] = quantity
                            # campos_actualizables['usuario'] = None  # o el usuario actual si lo tienes
                        
                        # Verificar si hay cambios comparando campo por campo
                        hay_cambios = False
                        for campo, nuevo_valor in campos_actualizables.items():
                            valor_actual = getattr(reserva_existente, campo)
                            if valor_actual != nuevo_valor:
                                hay_cambios = True
                                break
                        
                        # Solo actualizar si hay cambios
                        if hay_cambios:
                            for campo, nuevo_valor in campos_actualizables.items():
                                setattr(reserva_existente, campo, nuevo_valor)
                            reserva_existente.save()
                            # print(f"Actualizada reserva con unique_id: {unique_id}")
                        
                    else:
                        # El registro no existe, crear uno nuevo
                        # nueva_reserva = Reservas.objects.create(
                            
                        if product_id:
                            Reservas.objects.create(
                                contrato_id=contrato_id,
                                codigo_cliente=codigo_cliente,
                                product_id=product_id,
                                quantity=quantity,
                                ware_code=ware_code,
                                confirmed=confirmed,
                                fecha_pedido=fecha_pedido,
                                hora_llegada=hora_llegada,
                                sec_name_cliente=sec_name_cliente,
                                unique_id=unique_id,
                                alterado=False
                                # usuario se puede asignar aquí si tienes el usuario actual
                            )
                        
                        
                        # Add delete
                        Reservas.objects.filter(quantity=0).delete()
                        
                        # Actualización automatica
                        admin_warehouse_timestamp(tabla='mis_reservas', actualizar_datetime=True, mensaje='Actualizado correctamente')
                        
        else:
            admin_warehouse_timestamp(tabla='mis_reservas', actualizar_datetime=False, mensaje=f'Error api: status {reservas_mba["status"]}')
            return False
        return True
        
    except Exception as e:
        admin_warehouse_timestamp(tabla='mis_reservas', actualizar_datetime=False, mensaje=f'Error exception: {e}')
        return False


### 15 NOTIFICACIONES DE EMAIL Y WHATSAAP
def notificaciones_email_whatsapp():
    
    try:
        hoy = datetime.now()
        rango_dias = hoy - timedelta(days=10)  # antes se llamaba "un_mes"
        ciudades_list = ['QUITO', 'SANGOLQUI']

        pedidos = EstadoPicking.objects.filter(
            Q(estado='FINALIZADO'),
            Q(tipo_cliente__in=['DISTR', 'CONSU']),
            Q(fecha_creado__gte=rango_dias),
            facturado=False,
            whatsapp=False
        ).order_by('n_pedido')

        for pedido in pedidos:
            # time.sleep(0.5)
            try:
                cliente = get_cliente('codigo_cliente', pedido.codigo_cliente)
                ciudad_cliente = cliente.get('ciudad_principal')
                whatsapp_number = cliente.get('wp').strip()

                n_pedido = pedido.n_pedido.split('.')[0]
                n_factura = get_numero_factura_by_numero_pedido(n_pedido)

                email_vendedor = get_vendedor_email_by_contrato(n_pedido) or []
                if isinstance(email_vendedor, str):
                    email_vendedor = [email_vendedor]

                emails_list = (email_cliente_by_codigo(pedido.codigo_cliente) or []) + email_vendedor

                if ciudad_cliente in ciudades_list and n_factura:
                    
                    vol_cart = cartones_volumen_factura(n_pedido)
                    volumen_pedido = vol_cart.get('volumen', 0.0)
                    cartones_pedido = vol_cart.get('cartones', 1)
                
                    email_msg = f"""
Señores {pedido.cliente} \n
Su pedido con factura # {n_factura}, se encuentra listo para ser retirado en:
Bodega: {pedido.bodega_str}. \n
Volumen: {volumen_pedido} m3 / Cartones: {cartones_pedido}\n
Nuestro horario de atención es: Lunes a Viernes de 8:00 am a 13:30 pm y de 14:00 pm a 16:30 pm.
Estamos para servirle.\n
GIMPROMED Cia. Ltda.\n
****Esta notificación ha sido enviada automáticamente - No responder****
"""
                    try:
                        # Envío de email
                        correo_enviado = send_mail(
                            subject='Notificación Pedido FACTURADO',
                            message=email_msg,
                            from_email=settings.EMAIL_HOST_USER,
                            # recipient_list= ['egarces@gimpromed.com'], #emails_list,
                            recipient_list= emails_list,
                            # recipient_list= emails_list if emails_list else email_cliente_by_codigo(pedido.codigo_cliente) or email_vendedor,
                            fail_silently= True  #False,  # Mejor lanzar error
                        )

                        # if correo_enviado == 1:
                        #     pedido.facturado = True
                        
                        pedido.facturado = True if correo_enviado == 1 else False
                        
                        if email_vendedor:
                            user = User.objects.filter(email=email_vendedor[0]).first()
                            if user:
                                pedido.facturado_por = user
                    except Exception as e:
                        pedido.noti_email = f'Email Error: {str(e)}'
                            
                    time.sleep(0.7)
                    # Envío de whatsapp
                    if whatsapp_number and whatsapp_number.startswith('+593') and len(whatsapp_number) == 13:
                        try:
                            response = requests.post(
                                # url='http://gimpromed.com/app/api/send-whatsapp',
                                url='https://gimpromed.com/app/api/send-whatsapp',
                                #data={
                                json={
                                    'senores': pedido.cliente,
                                    # 'recipient': '+593999922603', #whatsapp_number,
                                    'recipient': whatsapp_number,
                                    'factura': n_factura,
                                    'bodega': pedido.bodega_str,
                                    'n_cartones':str(cartones_pedido)
                                },
                                timeout=15
                            )
                            if response.status_code == 200:
                                if response.json().get('success', False):
                                    pedido.whatsapp = True
                        except requests.RequestException as e:
                            # print(f"Error enviando WhatsApp: {e}")
                            # pedido.wh_fail_number = True
                            #wh_error = f'Wh Error: {str(e)}'
                            pedido.noti_errors = f'Wh Error: {str(e)}'
                    else:
                        pedido.wh_fail_number = True

                    emails_list_str = ", ".join(str(x) for x in emails_list)
                    pedido.hora_facturado = datetime.now()
                    pedido.noti_detalles = f'Emails: {emails_list_str} - Wh: {whatsapp_number}'
                    #pedido.noti_errors = wh_error
                    pedido.n_factura = n_factura
                    pedido.save()
                    
            except Exception as e:
                # print(f"Error procesando pedido {pedido.n_pedido}: {e}")
                pedido.noti_errors = str(e)
                pedido.save()
        admin_warehouse_timestamp(tabla='notificaciones', actualizar_datetime=True, mensaje='Enviados correctamente')
    except Exception as e:
        admin_warehouse_timestamp(tabla='notificaciones', actualizar_datetime=False, mensaje=f'Error exception: {e}')



# def api_prueba_fechas():
#     prueba = api_mba_sql(
#     """
#         SELECT
#             INVT_Producto_Lotes.FECHA_CADUCIDAD,
#             LENGTH(INVT_Producto_Lotes.FECHA_CADUCIDAD) AS len,
#             HEX(INVT_Producto_Lotes.FECHA_CADUCIDAD)    AS hex
#         FROM INVT_Producto_Lotes
#         WHERE INVT_Producto_Lotes.FECHA_CADUCIDAD IS NOT NULL;
#     """
#     )
#     print(prueba)
#     if prueba["status"] == 200:
#         # print(pd.DataFrame.from_records(prueba['data']))
#         print(pd.DataFrame(prueba['data'])) 
