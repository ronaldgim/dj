# API MBA
from api_mba.mba import api_mba_sql

# BD Connection
from django.db import connections

# Send mail
from django.core.mail import send_mail
from django.conf import settings

# datetime
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# Pandas
import pandas as pd

# Queries de mba por api
from api_mba.api_query import (
    api_query_clientes_mba
    )

# datos de actualización
from datos.models import TimeStamp


# eliminar datos de tablas en wharehouse
def delete_data_warehouse(table_name):
    
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(f"DELETE FROM {table_name}")


# obtener columnas de tabla por nombre de la tabla
def get_columns_table_warehouse(table_name):
    
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(f"SHOW COLUMNS FROM {table_name}")
        columns = [row[0] for row in cursor.fetchall()]
        
    return columns


# insertar datos en tabla de warehouse
def insert_data_warehouse(table_name, data):   
    
    get_columns = get_columns_table_warehouse(table_name)
    
    columnas = ", ".join(get_columns)
    valores  = ", ".join(["%s"] * len(get_columns))
    sql_insert = f"INSERT INTO {table_name} ({columnas}) VALUES ({valores})"
    
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.executemany(sql_insert, data)


###### FUNCIONES PARA ACTUALIZAR DATOS EN WAREHOUSE ######
### ACTUALIZAR CLIENTES WAREHOUSE POR API DATA
def api_actualizar_clientes_warehouse():
    
    try:
    
        clientes_mba = api_query_clientes_mba()

        if clientes_mba["status"] == 200:
            
            data = [tuple(i.values()) for i in clientes_mba['data']]
            
            # Borrar datos de tabla clientes
            delete_data_warehouse('clientes')
            
            # Insertar datos de tabla clientes
            insert_data_warehouse('clientes', data)
        
        else:
            
            send_mail(
                subject='Error DB WAREHOUSE',
                message=f"""
                
                TABLA: CLIENTES - 'warehouse.clientes'
                
                ERROR : ERROR API - STATUS: {clientes_mba["status"]}
                
                """,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=['egarces@gimpromed.com'],
                fail_silently=False,
            )

    except Exception as e:
        
        send_mail(
            subject='Error DB WAREHOUSE',
            message=f"""
            
            TABLA: CLIENTES - 'warehouse.clientes'
            
            ERROR : {e}
            
            """,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=['egarces@gimpromed.com'],
            fail_silently=False,
        )


### ACTUALIZAR FACTURAS WAREHOUSE
def api_actualizar_facturas_warehouse():
    
    try:
    
        currentTimeDate = datetime.now() - relativedelta(days=90)
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
        
            # Borrar datos de tabla facturas
            delete_data_warehouse('facturas')
            
            # Insertar datos de tabla facturas
            insert_data_warehouse('facturas', data)
        
        else:
            
            send_mail(
                subject='Error DB WAREHOUSE',
                message=f"""
                
                TABLA: FACTURAS - 'warehouse.facturas'
                
                ERROR : ERROR API - STATUS: {facturas_mba["status"]}
                
                """,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=['egarces@gimpromed.com'],
                fail_silently=False,
            )
    
    except Exception as e:
        
        send_mail(
            subject='Error DB WAREHOUSE',
            message=f"""
            
            TABLA: FACTURAS - 'warehouse.facturas'
            
            ERROR : {e}
            
            """,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=['egarces@gimpromed.com'],
            fail_silently=False,
        )


### ACTUALIZAR IMP LLEGADAS WAREHOUSE
def api_actualizar_imp_llegadas_warehouse():

    try:
        # actualizar_imp_llegadas_odbc
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
            
            imp_llegadas_df = pd.DataFrame(imp_llegadas_mba['data'])
            proveedor_df = pd.DataFrame(proveedor_mba['data']).rename(columns={'CONTRATO_ID_CORP':'DOC_ID_CORP'})
            
            # Unir nombre de proveedor
            imp_llegadas = imp_llegadas_df.merge(proveedor_df, on='DOC_ID_CORP', how='left').fillna('')
            
            # Transformar datos de fechas
            imp_llegadas['ENTRADA_FECHA'] = pd.to_datetime(imp_llegadas['ENTRADA_FECHA'].str.slice(0, 10)).dt.date
            imp_llegadas['FECHA_CADUCIDAD'] = pd.to_datetime(imp_llegadas['FECHA_CADUCIDAD'].str.slice(0, 10)).dt.date
            
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
            
            # Borrar datos de tabla imp_llegadas
            delete_data_warehouse('imp_llegadas')
            
            # Insertar datos de tabla imp_llegadas
            insert_data_warehouse('imp_llegadas', data)
        
        else:
            
            send_mail(
                subject='Error DB WAREHOUSE',
                message=f"""
                
                TABLA: IMPORTACIONES LLEGADAS - 'warehouse.imp_llegadas'
                
                ERROR : ERROR API - STATUS: imp_llegadas_status:{imp_llegadas_mba['status']}, proveedor_status:{proveedor_mba['status']}
                
                """,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=['egarces@gimpromed.com'],
                fail_silently=False,
            )
            
    except Exception as e:
        
        send_mail(
            subject='Error DB WAREHOUSE',
            message=f"""
            
            TABLA: IMPORTACIONES LLEGADAS - 'warehouse.imp_llegadas'
            
            ERROR : {e}
            
            """,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=['egarces@gimpromed.com'],
            fail_silently=False,
        )


### ACTUALIZAR IMP TRANSITO WAREHOUSE
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
                
                # Borrar datos de tabla imp_transito
                delete_data_warehouse('imp_transito')
                
                # # Insertar datos de tabla imp_transito
                insert_data_warehouse('imp_transito', data)
    
        else:
        
            send_mail(
                subject='Error DB WAREHOUSE',
                message=f"""
                
                TABLA: IMP TRNASITO - 'warehouse.imp_transito'
                
                ERROR : ERROR API - STATUS: {imp_transito_mba['status']}
                
                """,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=['egarces@gimpromed.com'],
                fail_silently=False,
            )
    
    except Exception as e:
        
        send_mail(
            subject='Error DB WAREHOUSE',
            message=f"""
            
            TABLA: IMPORTACIONES EN TRANSITO - 'warehouse.imp_transito'
            
            ERROR : {e}
            
            """,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=['egarces@gimpromed.com'],
            fail_silently=False,
        )


### ACTUALIZAR PRODUCTOS WAREHOUSE POR API DATA
def api_actualizar_productos_warehouse():
    
    try:
    
        productos_mba = api_mba_sql(
            """
            SELECT 
                INVT_Ficha_Principal.PRODUCT_ID, 
                INVT_Ficha_Principal.PRODUCT_NAME, 
                INVT_Ficha_Principal.UM, 
                INVT_Ficha_Principal.GROUP_CODE, 
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
                INVT_Ficha_Principal INVT_Ficha_Principal
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
            
            # Borrar datos de tabla productos
            delete_data_warehouse('productos')
            
            # Insertar datos de tabla productos
            insert_data_warehouse('productos', data)

        else:
        
            send_mail(
                subject='Error DB WAREHOUSE',
                message=f"""
                
                TABLA: PRODUCTOS - 'warehouse.productos'
                
                ERROR : ERROR API - STATUS: {productos_mba['status']}
                
                """,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=['egarces@gimpromed.com'],
                fail_silently=False,
            )
    
    except Exception as e:
        
        send_mail(
            subject='Error DB WAREHOUSE',
            message=f"""
            
            TABLA: PRODUCTOS - 'warehouse.productos'
            
            ERROR : {e}
            
            """,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=['egarces@gimpromed.com'],
            fail_silently=False,
        )


### ACTUALIZAR PRODUCTOS EN TRANSITO
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
                INVT_Producto_Lotes.WARE_CODE_CORP 
            FROM 
                INVT_Ficha_Principal INVT_Ficha_Principal, 
                INVT_Producto_Lotes INVT_Producto_Lotes 
            WHERE 
                INVT_Ficha_Principal.PRODUCT_ID_CORP = INVT_Producto_Lotes.PRODUCT_ID_CORP AND ((INVT_Producto_Lotes.WARE_CODE_CORP='TRN'))
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

                row = (
                    product_id, 
                    oh, 
                    lote_id, 
                    fecha_elaboracion_lote, 
                    fecha_caducidad,
                    ware_code_corp
                )

                data.append(row)
                
            # Borrar datos de tabla clientes
            delete_data_warehouse('productos_transito')
            
            # Insertar datos de tabla clientes
            insert_data_warehouse('productos_transito', data)
    
        else:
        
            send_mail(
                subject='Error DB WAREHOUSE',
                message=f"""
                
                TABLA: PRODUCTOS EN TRANSITO - 'warehouse.productos_transito'
                
                ERROR : ERROR API - STATUS: {productos_transito_mba["status"]}
                
                """,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=['egarces@gimpromed.com'],
                fail_silently=False,
            )
    
    except Exception as e:
        
        send_mail(
            subject='Error DB WAREHOUSE',
            message=f"""
            
            TABLA: PRODUCTOS EN TRANSITO - 'warehouse.productos_transito'
            
            ERROR : {e}
            
            """,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=['egarces@gimpromed.com'],
            fail_silently=False,
        )



### ACTULIZAR PROFORMAS
def api_actualizar_proformas_warehouse():
    
    try:
        
        today = datetime.today() - timedelta(days=45)
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
            
            # Borrar datos de tabla proformas
            delete_data_warehouse('proformas')
            
            # Insertar datos de tabla proformas
            insert_data_warehouse('proformas', data)
        
        else:
            
            send_mail(
                subject='Error DB WAREHOUSE',
                message=f"""
                
                TABLA: PROFORMAS - 'warehouse.proformas'
                
                ERROR : ERROR API - STATUS: {proformas_mba['data']}
                
                """,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=['egarces@gimpromed.com'],
                fail_silently=False,
            )
        
    except Exception as e:
        
        send_mail(
            subject='Error DB WAREHOUSE',
            message=f"""
            
            TABLA: PROFORMAS - 'warehouse.proformas'
            
            ERROR : {e}
            
            """,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=['egarces@gimpromed.com'],
            fail_silently=False,
        )


### ACTUALIZAR RESERVAS WAREHOUSE
def api_actualizar_reservas_warehouse():
    
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
                CLNT_Pedidos_Principal.SEC_NAME_CLIENTE 
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
        
        # r = pd.DataFrame(reservas_mba['data'])
        # print(r['SEC_NAME_CLIENTE'].unique())
        
        if  reservas_mba["status"] == 200:
            
            # data = [tuple(i.values()) for i in reservas_mba['data']]
            
            data = []
            for i in reservas_mba['data']:
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
                
                #sec_name_cliente = i['SEC_NAME_CLIENTE']
                s_n_c = i['SEC_NAME_CLIENTE']
                if s_n_c.startswith('P'):
                    sec_name_cliente = 'PUBLICO'
                elif s_n_c.startswith('R'):
                    sec_name_cliente = 'RESERVA'
                else:
                    sec_name_cliente = ''
                
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
                )
                
                data.append(row)
            
            # Borrar datos de tabla reservas
            delete_data_warehouse('reservas')
            
            # Insertar datos de tabla reservas
            insert_data_warehouse('reservas', data)

        else:
        
            send_mail(
                subject='Error DB WAREHOUSE',
                message=f"""
                
                TABLA: RESERVAS - 'warehouse.reservas'
                
                ERROR : ERROR API - STATUS: {reservas_mba["status"]}
                
                """,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=['egarces@gimpromed.com'],
                fail_silently=False,
            )

    except Exception as e:
        
        send_mail(
            subject='Error DB WAREHOUSE',
            message=f"""
            
            TABLA: RESERVAS - 'warehouse.reservas'
            
            ERROR : {e}
            
            """,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=['egarces@gimpromed.com'],
            fail_silently=False,
        )


### ACTUALIZAR RESERVAS LOTES WAREHOUSE
def api_actualizar_reservas_lotes_warehouse():
    
    try:
    
        reservas_lotes_mba = api_mba_sql(
            """
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
        )
        
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
                
            # Borrar datos de tabla reservas_lote
            delete_data_warehouse('reservas_lote')
            
            # Insertar datos de tabla reservas_lote
            insert_data_warehouse('reservas_lote', data)

        else:
        
            send_mail(
                subject='Error DB WAREHOUSE',
                message=f"""
                
                TABLA: RESERVAS LOTE - 'warehouse.reservas_lote'
                
                ERROR : ERROR API - STATUS: {reservas_lotes_mba["status"]}
                
                """,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=['egarces@gimpromed.com'],
                fail_silently=False,
            )
        
    except Exception as e:
        
        send_mail(
            subject='Error DB WAREHOUSE',
            message=f"""
            
            TABLA: RESERVAS LOTES - 'warehouse.reservas_lote'
            
            ERROR : {e}
            
            """,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=['egarces@gimpromed.com'],
            fail_silently=False,
        )



### ACTULIZAR STOCK LOTE POR ODBC
import pyodbc
def actualizar_stock_lote_odbc():

    try:
        cnxn = pyodbc.connect('DSN=mba3;PWD=API')
        cursor = cnxn.cursor()
        
        stock_lote_query_mba = cursor.execute(
            """
            SELECT 
                INVT_Ficha_Principal.PRODUCT_ID, 
                INVT_Ficha_Principal.PRODUCT_NAME, 
                INVT_Ficha_Principal.GROUP_CODE, 
                INVT_Ficha_Principal.UM, 
                INVT_Producto_Lotes.OH, 
                INVT_Producto_Lotes_Bodegas.OH, 
                INVT_Producto_Lotes_Bodegas.COMMITED, 
                INVT_Producto_Lotes_Bodegas.QUANTITY, 
                INVT_Producto_Lotes.LOTE_ID, 
                INVT_Producto_Lotes.Fecha_elaboracion_lote, 
                INVT_Producto_Lotes.FECHA_CADUCIDAD, 
                INVT_Producto_Lotes_Bodegas.WARE_CODE, 
                INVT_Producto_Lotes_Bodegas.LOCATION 
                
            FROM 
                INVT_Ficha_Principal INVT_Ficha_Principal, 
                INVT_Producto_Lotes INVT_Producto_Lotes, 
                INVT_Producto_Lotes_Bodegas INVT_Producto_Lotes_Bodegas 
            WHERE 
                INVT_Ficha_Principal.PRODUCT_ID_CORP = INVT_Producto_Lotes.PRODUCT_ID_CORP AND 
                INVT_Producto_Lotes_Bodegas.PRODUCT_ID_CORP = INVT_Ficha_Principal.PRODUCT_ID_CORP AND 
                INVT_Producto_Lotes.LOTE_ID = INVT_Producto_Lotes_Bodegas.LOTE_ID AND 
                INVT_Producto_Lotes.WARE_CODE_CORP = INVT_Producto_Lotes_Bodegas.WARE_CODE AND 
                ((INVT_Producto_Lotes.OH>0) AND (INVT_Producto_Lotes_Bodegas.OH>0))
            """
                )

        data = [tuple(i) for i in stock_lote_query_mba.fetchall()]
        
        if len(data) > 0:
            
            # Borrar datos de tabla stock_lote
            delete_data_warehouse('stock_lote')
            
            # Insertar datos de tabla stock_lote
            insert_data_warehouse('stock_lote', data)
            time = str(datetime.now())
            TimeStamp.objects.create(actulization_facturas=time)
            
    
    except Exception as e:
        
        send_mail(
            subject='Error DB WAREHOUSE',
            message=f"""
            
            OJO : REALIZADO CON ODBC
            
            TABLA: STOCK LOTE - 'warehouse.stock_lote'
            
            ERROR : {e}
            
            """,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=['egarces@gimpromed.com'],
            fail_silently=False,
        )



## NO TRAE EL DATO DE OH2
### ACTUALIZAR STOCK LOTE
# def actualizar_stock_lote_warehouse():
#     try:
    
#         stock_lote_mba = api_mba_sql(
#             """
#             SELECT 
#                 INVT_Ficha_Principal.PRODUCT_ID, 
#                 INVT_Ficha_Principal.PRODUCT_NAME, 
#                 INVT_Ficha_Principal.GROUP_CODE, 
#                 INVT_Ficha_Principal.UM, 
#                 INVT_Producto_Lotes.OH, 
#                 INVT_Producto_Lotes_Bodegas.OH, 
#                 INVT_Producto_Lotes_Bodegas.COMMITED, 
#                 INVT_Producto_Lotes_Bodegas.QUANTITY, 
#                 INVT_Producto_Lotes.LOTE_ID, 
#                 INVT_Producto_Lotes.Fecha_elaboracion_lote, 
#                 INVT_Producto_Lotes.FECHA_CADUCIDAD, 
#                 INVT_Producto_Lotes_Bodegas.WARE_CODE, 
#                 INVT_Producto_Lotes_Bodegas.LOCATION 
                
#             FROM 
#                 INVT_Ficha_Principal INVT_Ficha_Principal, 
#                 INVT_Producto_Lotes INVT_Producto_Lotes, 
#                 INVT_Producto_Lotes_Bodegas INVT_Producto_Lotes_Bodegas 
#             WHERE 
#                 INVT_Ficha_Principal.PRODUCT_ID_CORP = INVT_Producto_Lotes.PRODUCT_ID_CORP AND 
#                 INVT_Producto_Lotes_Bodegas.PRODUCT_ID_CORP = INVT_Ficha_Principal.PRODUCT_ID_CORP AND 
#                 INVT_Producto_Lotes.LOTE_ID = INVT_Producto_Lotes_Bodegas.LOTE_ID AND 
#                 INVT_Producto_Lotes.WARE_CODE_CORP = INVT_Producto_Lotes_Bodegas.WARE_CODE AND 
#                 ((INVT_Producto_Lotes.OH>0) AND (INVT_Producto_Lotes_Bodegas.OH>0))
#             """
#         )
    
#         if stock_lote_mba["status"] == 200:
            
#             print(stock_lote_mba['data'][0])
            #print(len(stock_lote_mba['data'][0]))
            
            # data = [tuple(i.values()) for i in productos_transito_mba["data"]]
            
            # data = []
            # for i in stock_lote_mba['data']:
            #     product_id = i['PRODUCT_ID']
            #     product_name = i['PRODUCT_NAME']
            #     group_code = i['GROUP_CODE']
            #     um = i['UM']
            #     oh = i['OH']
                
            #     oh2 = i['OH2'] #ojoo no hay en la api
                
            #     commited = i['COMMITED']
            #     quantity = i['QUANTITY']
            #     lote_id = i['LOTE_ID']
            #     fecha_elaboracion_lote = i['FECHA_ELABORACION_LOTE'][:10] # cortar formato de fecha que trae la api
            #     fecha_caducidad = i['FECHA_CADUCIDAD'][:10] # cortar formato de fecha que trae la api
            #     ware_code = i['WARE_CODE']
            #     location = i['LOCATION']

            #     t = (
            #         product_id,
            #         product_name,
            #         group_code,
            #         um,
            #         oh,
            #         oh2,
            #         commited,
            #         quantity,
            #         lote_id,
            #         fecha_elaboracion_lote,
            #         fecha_caducidad,
            #         ware_code,
            #         location,
            #     )

            #     data.append(t)
            # print(data)
            # # Borrar datos de tabla clientes
            # delete_data_warehouse('stock_lote')
            
            # # Insertar datos de tabla clientes
            # insert_data_warehouse('stock_lote', data)
    
    # except Exception as e:
        
        # send_mail(
        #     subject='Error DB WAREHOUSE',
        #     message=f"""
            
        #     TABLA: STOCK LOTE - 'warehouse.stock_lote'
            
        #     ERROR : {e}
            
        #     """,
        #     from_email=settings.EMAIL_HOST_USER,
        #     recipient_list=['egarces@gimpromed.com'],
        #     fail_silently=False,
        # )
        