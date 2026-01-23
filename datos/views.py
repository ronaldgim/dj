# DB
from django.db import connections, transaction
from django.db.models import Q

import time
    
# Shortcuts
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

# Messages
from django.contrib import messages

# Generic View
from django.views.generic import TemplateView

# Models
from datos.models import TimeStamp, Product, AdminActualizationWarehaouse, ErrorLoteReporte, ErrorLoteDetalle, ErrorLoteV2, PickingEstadistica #Vehiculos 
from etiquetado.models import EstadoPicking, EtiquetadoAvance
from wms.models import Existencias

# Autentication
from django.contrib.auth.mixins import LoginRequiredMixin

# Pandas
import pandas as pd
import numpy as np

# SSH DATA TUNEL
import pymysql
import logging
import sshtunnel
from sshtunnel import SSHTunnelForwarder

# Json
import json

# HTTP
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse

# Time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

### PERMISOS PERSONALIZADOS
from users.models import UserPerfil
from django.contrib.auth.models import User

### PERMISO PERSONALIZADO
from functools import wraps

# rexex
import re

# API MBA
from api_mba.mba import api_mba_sql

# ACTUALIZAR WAREHOUSER POR API DATA
from api_mba.tablas_warehouse import (
    admin_warehouse_timestamp,
    
    api_actualizar_clientes_warehouse,         # 1
    odbc_actualizar_clientes_warehouse,
    
    api_actualizar_facturas_warehouse,         # 2
    odbc_actualizar_stock_lote_warehouse,
    
    api_actualizar_imp_llegadas_warehouse,     # 3
    api_actualizar_imp_transito_warehouse,     # 4
    api_actualizar_pedidos_warehouse,          # 5
    api_actualizar_productos_warehouse,        # 6
    api_actualizar_producto_transito_warehouse,# 7
    api_actualizar_proformas_warehouse,        # 8
    api_actualizar_reservas_warehouse,         # 9
    api_actualizar_reservas_lotes_warehouse,   # 10
    api_actualizar_reservas_lotes_2_warehouse, # 11
    api_actualizar_stock_lote_warehouse,       # 12
    api_actualizar_mis_reservas_etiquetado,
    notificaciones_email_whatsapp
    )


# FUNCIONES UTILES
# Chequear si el usuario tiene permiso
def user_perm(user_id, permiso_function):
    
    user = User.objects.get(id=user_id)
    superuser = user.is_superuser

    if superuser: 
        return True
    
    else:
        permisos_user_list = list(UserPerfil.objects.get(user_id=user.id).permisos.values_list('permiso', flat=True))
        
        perm_true_list = []
        for permiso in permiso_function:
            p = permiso in permisos_user_list
            perm_true_list.append(p)
        
        if True in perm_true_list:
            return True
        else:
            return False


# Decorador de permiso de vista
def permisos(permiso, redirect_url, modulo):
    def decorador(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user_has_perm = user_perm(request.user.id, permiso)
            if user_has_perm:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, f'{request.user} no tiene permiso de {modulo} !!!')
                return redirect(redirect_url)
        return _wrapped_view
    return decorador


# DE DATAFRAME A LISTA DE DICCIONARIOS PARA PASAR A UN TEMPLATE
def de_dataframe_a_template(dataframe):

    json_records = dataframe.reset_index().to_json(orient='records') # reset_index().
    dataframe = json.loads(json_records)

    return dataframe


# QUITAR PREFIJOS EN REG SAN, PROCEDENCIA
def quitar_prefijo(texto):
    if ':' in texto:
        texto = texto.split(':')[1]
        return texto
    else:
        return texto
    
    
def extraer_fecha(texto):
    # Buscar una fecha en formato dd/mm/yyyy en el texto
    match = re.search(r'\b\d{2}/\d{2}/\d{4}\b', texto)
    
    if match:
        fecha_str = match.group(0)
        try:
            # Convertir la cadena a un objeto datetime
            fecha = datetime.strptime(fecha_str, '%d/%m/%Y')
            return fecha
        except ValueError:
            print("Formato de fecha inválido")
            return None
    else:
        print("No se encontró una fecha en el texto")
        return None


# HOME PRINCIPAL
class Inicio(LoginRequiredMixin, TemplateView):
    template_name = 'inicio.html'



def productos_odbc_and_django():
    with connections['gimpromed_sql'].cursor() as cursor:
        #cursor.execute("SELECT Codigo, Nombre, Unidad, Marca, Unidad_Empaque, Unidad_Box, Inactivo FROM productos")
        # cursor.execute("SELECT * FROM productos")
        cursor.execute("SELECT * FROM productos WHERE Inactivo = 0")
        columns = [col[0] for col in cursor.description]
        products = [ # Lista de diccionarios
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        products = pd.DataFrame(products)
        products = products.rename(columns={
            'Codigo':'product_id'
        })

        p = pd.DataFrame(Product.objects.filter(activo=True).values())

        products = products.merge(p, on='product_id', how='left')
        products['vol_m3'] = products['Volumen'] / 1000000
        products['vol_m3'] = products['vol_m3'].replace(np.inf, 0)
        
    return products


def pedidos_cuenca_odbc(n_pedido): #n_pedido

    open_ssh_tunnel()
    mysql_connect()

    df = run_query(        
        # "SELECT orders.id,seller_code,client_code,client_name,client_identification,orders.created_at,order_products.product_id,orders.status,order_products.product_name,"
        # "order_products.product_group_code,order_products.quantity,order_products.price FROM orders LEFT JOIN order_products "
        # "ON orders.id = order_products.order_id where seller_code='VEN03' AND orders.status='TCR';"
        
        # PEDIDOS 5455 | 5495
        
        "SELECT orders.id,seller_code,client_code,client_name,client_identification,orders.created_at,order_products.product_id,orders.status,order_products.product_name,"
        "order_products.product_group_code,order_products.quantity,order_products.price FROM orders LEFT JOIN order_products "
        #f"ON orders.id = order_products.order_id where orders.id='{n_pedido}' AND orders.status='TCR';" 
        f"ON orders.id = order_products.order_id where orders.id='{n_pedido}'" 
    )
    
    mysql_disconnect()
    close_ssh_tunnel()
    
    return df


def ventas_desde_fecha(fecha, codigo_cliente):
    ''' Colusta de ventas desde fecha especifica '''
    
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(
            f"SELECT CODIGO_CLIENTE, FECHA, PRODUCT_ID FROM venta_facturas WHERE fecha > '{fecha}' AND codigo_cliente = '{codigo_cliente}'"
            )
        columns = [col[0] for col in cursor.description]
        ventas = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
        
        ventas = pd.DataFrame(ventas)
        
        return ventas



# FRECUENCIA DE VENTAS DATA
# SSH DATA TUNEL
ssh_host = '10.10.3.4'
ssh_username = 'root'
ssh_password =  'Gimcen2025/*$' #'Gimcen2021'
database_username = 'felipe'
database_password = '19860915'
database_name = 'gimpromed_api'
localhost = '127.0.0.1'


def open_ssh_tunnel(verbose=False):
    """Open an SSH tunnel and connect using a username and password.
    :param verbose: Set to True to show logging
    :return tunnel: Global SSH tunnel connection
    """

    if verbose:
        sshtunnel.DEFAULT_LOGLEVEL = logging.DEBUG
    global tunnel
    tunnel = SSHTunnelForwarder(
        (ssh_host, 22),
        ssh_username=ssh_username,
        ssh_password=ssh_password,
        remote_bind_address=('127.0.0.1', 3306)
    )
    tunnel.start()


def mysql_connect():
    """Connect to a MySQL server using the SSH tunnel connection
    :return connection: Global MySQL database connection"""
    global connection
    connection = pymysql.connect(
        host='127.0.0.1',
        user=database_username,
        passwd=database_password,
        db=database_name,
        port=tunnel.local_bind_port
    )


def run_query(sql):
    """Runs a given SQL query via the global database connection.

    :param sql: MySQL query
    :return: Pandas dataframe containing results
    """

    return pd.read_sql_query(sql, connection)


def mysql_disconnect():
    """Closes the MySQL database connection.
    """

    connection.close()


def close_ssh_tunnel():
    """Closes the SSH tunnel connection.
    """

    tunnel.close


def frecuancia_ventas():

    open_ssh_tunnel()
    mysql_connect()
    
    df = run_query(
        "SELECT T.PRODUCT_ID, T.ANUAL, R.rpm, A.F_ACUMULADA FROM (SELECT PRODUCT_ID, SUM(QUANTITY) as ANUAL FROM consumo_anual GROUP BY PRODUCT_ID) AS T "
        "LEFT JOIN alertas_reservas R ON T.PRODUCT_ID = R.PRODUCT_ID LEFT JOIN analisis_abc A on R.PRODUCT_ID = A.PRODUCT_ID;"
        )

    
    mysql_disconnect()
    close_ssh_tunnel()

    return df


def stock_de_seguridad():

    open_ssh_tunnel()
    mysql_connect()
    
    df = run_query("SELECT product_id, sum(sum_quantity) FROM gimpromed_api.output_ventasTotales group by product_id;")
    df['stock_seguridad_mensual'] = round(df['sum(sum_quantity)'] / 12, 0)
    df['stock_seguridad_semanal'] = round(df['stock_seguridad_mensual'] / 4, 0)
    df = df.rename(columns={'product_id':'PRODUCT_ID'})
    
    mysql_disconnect()
    close_ssh_tunnel()

    return df


def clientes_warehouse():

    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(
            "SELECT * FROM clientes"
        )

        columns = [col[0] for col in cursor.description]
        clientes = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
    clientes = pd.DataFrame(clientes)

    return clientes


def productos_transito_odbc():
    ### TRANSITO
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(
            "SELECT * FROM productos_transito"
        )

        columns = [col[0] for col in cursor.description]
        transito = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
    transito = pd.DataFrame(transito)
    
    return transito



## ACTUALIZAR DATOS DE WAREHOUSE
#@transaction.atomic
def actualizar_datos_etiquetado_fun():
    ### STOCK
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(
            "SELECT * FROM stock_lote"
        )

        columns = [col[0] for col in cursor.description]
        stock = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
    stock = pd.DataFrame(stock)

    stock = stock.pivot_table(index=['PRODUCT_ID', 'PRODUCT_NAME', 'GROUP_CODE'], values='OH2', columns='WARE_CODE', aggfunc='sum').fillna(0)
    
    if 'CUA' in stock.columns and 'CUC' in stock.columns:
        stock['Cuarentena'] = stock['CUA'] + stock['CUC']
        
    elif 'CUA' in stock.columns:
        stock['Cuarentena'] = stock['CUA'] 
    
    elif 'CUC' in stock.columns:
        stock['Cuarentena'] = stock['CUC']
        
    stock['Disponible Total'] = stock['BAN'] + stock['BCT']
    stock = stock[['Disponible Total', 'Cuarentena']]
    stock = stock.reset_index()
    lista_marcas = [
        'MEDLI',
        'CONME',
        'SALTE',
        'HYDRO',
        'SUMI',
        'LINVA'
        ]
    stock = stock[stock.GROUP_CODE.isin(lista_marcas)]
    stock = stock.query('Cuarentena>0')
    stock = stock.sort_values(by=['GROUP_CODE'], ascending=[True])

    ### STOCK SEGURIDAD MENSUAL
    stock_mensual = frecuancia_ventas().fillna(0) 
    stock_mensual['Mensual'] = (stock_mensual['ANUAL'] / 12).round(0) 
    stock_mensual['Cat'] = stock_mensual.apply(lambda x: 'A' if x['F_ACUMULADA'] <= 80 else 'B' if x['F_ACUMULADA'] <=90 else 'C', axis=1)

    ### RESERVAS
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(
            "SELECT * FROM reservas"
        )

        columns = [col[0] for col in cursor.description]
        reservas = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
    reservas = pd.DataFrame(reservas)

    clientes = clientes_warehouse()[['NOMBRE_CLIENTE', 'CLIENT_TYPE']]
    clientes = clientes[clientes['CLIENT_TYPE']=='HOSPU']
    clientes = list(clientes['NOMBRE_CLIENTE'])

    reservas_filtrado = reservas[reservas.NOMBRE_CLIENTE.isin(clientes)]
    reservas_filtrado = reservas_filtrado[reservas_filtrado['WARE_CODE']!='BCT']
    reservas_filtrado = reservas_filtrado[reservas_filtrado['NOMBRE_CLIENTE']!='GIMPROMED CIA. LTDA.']
    reservas_filtrado = reservas_filtrado[reservas_filtrado['CONFIRMED']!=0]


    reservas_fc = lambda x: x['NOMBRE_CLIENTE'] not in clientes
    reservas_r = reservas[reservas.apply(reservas_fc, axis=1)]
    reservas_r = reservas_r[reservas_r['WARE_CODE']!='BCT']
    reservas_r = reservas_r[reservas_r['NOMBRE_CLIENTE']!='GIMPROMED CIA. LTDA.']

    r = pd.concat([reservas_filtrado, reservas_r])
    r = r.pivot_table(index=['PRODUCT_ID'], values='QUANTITY', aggfunc='sum')
    r = r.rename(columns={'QUANTITY':'Reservas'})

    ### TRANSITO
    transito = productos_transito_odbc()

    if transito.empty == True:
        transito['PRODUCT_ID'] = transito['PRODUCT_ID'] = 0
        transito['Transito'] = transito['Transito'] = 0
    else:
        transito = transito.pivot_table(index=['PRODUCT_ID'], values='OH', aggfunc='sum')
        transito = transito.reset_index()
        transito['PRODUCT_ID'] = transito['PRODUCT_ID'].astype(str)
        transito = transito.rename(columns={'OH':'Transito'})

    eti = stock.merge(stock_mensual, on='PRODUCT_ID', how='left')
    eti = eti.merge(r, on='PRODUCT_ID', how='left')
    eti = eti.merge(transito, on='PRODUCT_ID', how='left')

    eti = eti.fillna(0)

    eti['Disp_Total'] = eti['Disponible Total'] + eti['Transito']
    # eti['Disp.Mensual'] = eti['Disp_Total'] - eti['Mensual']
    eti['Meses'] = ((eti['Disp_Total']-eti['Reservas']) / eti['Mensual']).round(2)
    eti['Tres_Semanas'] = ((eti['Mensual']/4)*3).round(0)
    eti['Disp_Reserva'] = eti['Disp_Total'] - eti['Reservas']
    # eti['Disp.Reserva'] = eti['Reservas'] - eti['Disp.Total']
    eti['O_Etiquetado'] = eti['Mensual'] - eti['Disp_Reserva']

    eti['Stock_Mensual'] = 0.0

    t_act = pd.DataFrame(TimeStamp.objects.all().values())[['actulization_stoklote']]
    t_act = list(t_act['actulization_stoklote'])

    t = []
    for i in t_act:
        if i != '':
            t.append(i)
    t_a = t[-1][:-7]
    eti['actulizado'] = t_a

    eti = eti.fillna(0.0)
    eti = eti.sort_values(by='Meses', ascending=True)

    id_data = []
    for i in range(0, len(eti['PRODUCT_ID'])):
        a = i + 1
        id_data.append(a)

    eti['id'] = id_data
    eti = eti[['id','PRODUCT_ID','PRODUCT_NAME','GROUP_CODE','Cat','Reservas','Transito','Disp_Reserva','Disp_Total','Mensual','Cuarentena','Tres_Semanas','Stock_Mensual','Meses','O_Etiquetado','actulizado']]

    eti = eti.replace([np.inf, -np.inf], 0)

    with connections['default'].cursor() as cursor:

        e = [tuple(i) for i in eti.values] 
        cursor.execute("TRUNCATE etiquetado_etiquetadostock")
        cursor.executemany(
        """
        REPLACE INTO etiquetado_etiquetadostock (id,PRODUCT_ID,PRODUCT_NAME,GROUP_CODE,Cat,Reservas,Transito,Disp_Reserva,Disp_Total,Mensual,Cuarentena,Tres_Semanas,Stock_Mensual,Meses,O_Etiquetado,actulizado)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", e)

    admin_warehouse_timestamp('etiquetado_stock', actualizar_datetime=True, mensaje='Actualizado correctamente')

    return print('etiquetado-fun')



def obtener_conexion_config(table_name):
    return AdminActualizationWarehaouse.objects.get(table_name=table_name).conexion



## Carga la tabla de stock lote automaticamente
@csrf_exempt
def stock_lote(request):
    
    time = str(datetime.now())
    context = {
        'context':time
    }
    
    if request.method == "POST":
        
        data = json.loads(request.body)
        table_name = data.get("table_name", None)
        todo = data.get("get", None)

        if todo:
            
            # 1 Clientes
            # warehouse.clientes
            if obtener_conexion_config('clientes') == 'api':
                api_actualizar_clientes_warehouse()
            elif obtener_conexion_config('clientes') == 'odbc':
                odbc_actualizar_clientes_warehouse()
            
            # 2 Facturas (ultimos 2 meses)
            # warehouse.facturas
            if obtener_conexion_config('stock_lote') == 'api':
                api_actualizar_facturas_warehouse()
            elif obtener_conexion_config('stock_lote') == 'odbc':
                odbc_actualizar_stock_lote_warehouse()
            
            # 3 Imp Llegadas
            # warehouse.imp_llegadas
            api_actualizar_imp_llegadas_warehouse()
            
            # 4 Imp Transito
            # warehouse.imp_transito
            api_actualizar_imp_transito_warehouse()

            # 5 ACTUALIZAR PRODUCTOS 
            # warehouse.productos
            api_actualizar_productos_warehouse()
            
            # 6 ACTUALIZAR PEDIDOS 
            # warehouse.pedidos
            api_actualizar_pedidos_warehouse()

            # 7 Productos en Transito
            # warehouse.productos_transito
            api_actualizar_producto_transito_warehouse()

            # 8 ACTUALIZAR PROFORMAS
            # warehouse.proformas
            api_actualizar_proformas_warehouse()
            
            # 9 Reservas  (Pedidos Abiertos) - (<> MANTEN)
            # warehouse.reservas
            api_actualizar_reservas_warehouse()

            # 10 Reservas lotes
            # warehouse.reservas_lotes
            api_actualizar_reservas_lotes_warehouse()
            
            # 11 Reservas lotes 2
            # warehouse.reservas_lotes
            api_actualizar_reservas_lotes_2_warehouse()

            # 12 Stock Lotes
            # warehouse.stock_lotes
            api_actualizar_stock_lote_warehouse()

            ### TABLA DJANGO
            # 13 tabla de etiquetado estock
            actualizar_datos_etiquetado_fun()
            
            ### TABLA DJANGO
            # 14 Tabla mis reservas
            api_actualizar_mis_reservas_etiquetado()
            
            ### TABLA ERROR LOTE
            # 15 Tabla datos_errorlotereporte, datos_errorlotedetalle
            actualizar_data_error_lote()
            
            ### TABLA ERROR LOTE
            # 16 Tabla datos_errorlotereporte, datos_errorlotedetalle
            actualizar_data_error_lote_v2()
            
            # 17 NOTIFICACIONES DE EMAIL Y WHATSAAP
            notificaciones_email_whatsapp()
            
        elif table_name:
            
            if table_name == "clientes":
                # api_actualizar_clientes_warehouse()
                if obtener_conexion_config('clientes') == 'api':
                    api_actualizar_clientes_warehouse()
                elif obtener_conexion_config('clientes') == 'odbc':
                    odbc_actualizar_clientes_warehouse()
                
            elif table_name == "facturas":
                api_actualizar_facturas_warehouse()
            elif table_name == "imp_llegadas":
                api_actualizar_imp_llegadas_warehouse()
            elif table_name == "imp_transito":
                api_actualizar_imp_transito_warehouse()
            elif table_name == "productos":
                api_actualizar_productos_warehouse()
            elif table_name == "pedidos":
                api_actualizar_pedidos_warehouse()
            elif table_name == "productos_transito":
                api_actualizar_producto_transito_warehouse()
            elif table_name == "proformas":
                api_actualizar_proformas_warehouse()
            elif table_name == "reservas":
                api_actualizar_reservas_warehouse()
            elif table_name == "reservas_lote":
                api_actualizar_reservas_lotes_warehouse()
            elif table_name == "reservas_lote_2":
                api_actualizar_reservas_lotes_2_warehouse()
                
            elif table_name == "stock_lote":
                if obtener_conexion_config('stock_lote') == 'api':
                    api_actualizar_facturas_warehouse()
                elif obtener_conexion_config('stock_lote') == 'odbc':
                    odbc_actualizar_stock_lote_warehouse()
                
            elif table_name == "etiquetado_stock":
                actualizar_datos_etiquetado_fun()
            elif table_name == "mis_reservas":
                api_actualizar_mis_reservas_etiquetado()
            elif table_name == 'error_lote':
                actualizar_data_error_lote()
            elif table_name == 'error_lote_v2':
                actualizar_data_error_lote_v2()    
            elif table_name == 'notificaciones':
                notificaciones_email_whatsapp()

    #return render(request, 'datos/stock_lote.html', {})
    return render(request, 'datos/stock_lote.html', context)


### ACTUALIZAR TABLAS WAREHAUSE CON BOTON REQUEST
def actualizar_proformas_ajax(request):
    api_actualizar_proformas_warehouse()    
    return JsonResponse({
        'tipo':'success',
        'msg': 'Proformas actualizadas exitosamente !!!'
        })


def actualizar_imp_llegadas_odbc(request):
    api_actualizar_imp_llegadas_warehouse()
    return HttpResponse('ok')


def etiquetado_ajax(request):
    actualizar_datos_etiquetado_fun()
    return HttpResponseRedirect('/etiquetado/stock')


# FRON ADMIN ACTULIZACIONES WAREHOUSE
def admin_actualizar_warehouse_json_response(request):
    query = AdminActualizationWarehaouse.objects.all().order_by('orden').values()
    data = list(query.values())
    return JsonResponse(data, safe=False)
    #return render(request, 'datos/admin_actualizar_warehouse.html', context)

def admin_actualizar_warehouse_view(request):
    return render(request, 'datos/admin_actualizar_warehouse.html')


### UTILS 
def transferencias_mba(n_transf):
    
    n_transf_str = f'{int(n_transf):010d}' 
    n = 'A-' + n_transf_str + '-GIMPR' 
    
    data = api_mba_sql(
        f"""
        SELECT 
            INVT_Lotes_Ubicacion.DOC_ID_CORP, 
            INVT_Lotes_Ubicacion.PRODUCT_ID_CORP, 
            INVT_Lotes_Ubicacion.LOTE_ID, 
            INVT_Lotes_Ubicacion.EGRESO_TEMP, 
            INVT_Producto_Lotes.WARE_CODE_CORP, 
            INVT_Producto_Lotes.ANIADIDO, 
            INVT_Lotes_Ubicacion.UBICACION, 
            INVT_Producto_Lotes.Fecha_elaboracion_lote, 
            INVT_Producto_Lotes.FECHA_CADUCIDAD, 
            INVT_Producto_Lotes.ENTRADA_TIPO, 
            INVT_Lotes_Ubicacion.UBICACION, 
            INVT_Lotes_Ubicacion.WARE_CODE_CORP 
        FROM 
            INVT_Lotes_Ubicacion INVT_Lotes_Ubicacion, 
            INVT_Producto_Lotes INVT_Producto_Lotes 
        WHERE 
            INVT_Lotes_Ubicacion.PRODUCT_ID_CORP = INVT_Producto_Lotes.PRODUCT_ID_CORP AND 
            INVT_Producto_Lotes.LOTE_ID = INVT_Lotes_Ubicacion.LOTE_ID AND 
            ((INVT_Lotes_Ubicacion.DOC_ID_CORP='{n}') AND 
            (INVT_Lotes_Ubicacion.EGRESO_TEMP>0) AND 
            (INVT_Producto_Lotes.WARE_CODE_CORP='BCT'))
        """
    )
    
    
    if data['status'] == 200:
        
        transf_list = []
        for i in data['data']:
            row = {
                    'doc':i['DOC_ID_CORP'],
                    'n_transferencia':n_transf,
                    'product_id':i['PRODUCT_ID_CORP'].replace('-GIMPR', ''),
                    'lote_id':i['LOTE_ID'],
                    'f_elab': datetime.strptime(i['FECHA_ELABORACION_LOTE'][:10], '%d/%m/%Y'),
                    'f_cadu': datetime.strptime(i['FECHA_CADUCIDAD'][:10], '%d/%m/%Y'),
                    'bodega_salida':i['WARE_CODE_CORP'],
                    'unidades':i['EGRESO_TEMP'],
                    'ubicacion': i['UBICACION'],
                }
            
            transf_list.append(row)
        transf_df = pd.DataFrame(transf_list)
        transf_df['lote_id'] = transf_df['lote_id'].str.replace('.', '')
        transf_df = transf_df.groupby(by=['doc','n_transferencia','product_id','lote_id','f_elab','f_cadu','bodega_salida','ubicacion'])['unidades'].sum().reset_index()
        return transf_df
    
    else:
        return pd.DataFrame()



def importaciones_llegadas_odbc():

    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(
            "SELECT * FROM imp_llegadas"
            )
        columns = [col[0] for col in cursor.description]
        importaciones_llegadas = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
        
        importaciones_llegadas = pd.DataFrame(importaciones_llegadas)
        importaciones_llegadas['product_id'] = list(map(lambda x:x[:-6], list(importaciones_llegadas['PRODUCT_ID_CORP'])))
        #importaciones_llegadas['product_id'] = importaciones_llegadas['product_id'].str.replace('9P-1510', '9p-1510')

    return importaciones_llegadas


def importaciones_llegadas_por_docid_odbc(doc_id):

    prod = productos_odbc_and_django()[['product_id', 'description','Nombre','marca2','Marca','Unidad_Empaque','Procedencia']]
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(
            f"SELECT * FROM imp_llegadas where DOC_ID_CORP ='{doc_id}'"
            )
        columns = [col[0] for col in cursor.description]
        importaciones_llegadas = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        importaciones_llegadas = pd.DataFrame(importaciones_llegadas)
        importaciones_llegadas['product_id'] = list(map(lambda x:x[:-6], list(importaciones_llegadas['PRODUCT_ID_CORP'])))
        importaciones_llegadas = importaciones_llegadas.groupby(by=['DOC_ID_CORP', 'PROVEEDOR', 'MEMO','product_id'])['OH'].sum().reset_index()
        
        importaciones_llegadas = importaciones_llegadas.merge(prod, on='product_id', how='left')
        importaciones_llegadas['CARTONES'] = importaciones_llegadas['OH']/importaciones_llegadas['Unidad_Empaque']
        
    return importaciones_llegadas


def importaciones_tansito_list():

    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(
            "SELECT * FROM imp_transito"
            )
        columns = [col[0] for col in cursor.description]
        importaciones_transito = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        importaciones_transito = pd.DataFrame(importaciones_transito)
    
    return importaciones_transito


def importaciones_tansito_por_contratoid(contrato_id):

    prod = productos_odbc_and_django()[['product_id', 'description','Nombre','marca2','Marca','Unidad_Empaque','Procedencia']]
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(
            f"SELECT * FROM imp_transito WHERE CONTRATO_ID = '{contrato_id}'"
            )
        columns = [col[0] for col in cursor.description]
        importaciones_transito = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        importaciones_transito = pd.DataFrame(importaciones_transito)
        importaciones_transito = importaciones_transito.groupby(
            ['CONTRATO_ID','VENDOR_NAME','PRODUCT_ID','MEMO']
        ).sum()
        importaciones_transito = importaciones_transito.reset_index()
        importaciones_transito = importaciones_transito.rename(columns={'PRODUCT_ID':'product_id','QUANTITY':'OH'})
        importaciones_transito = importaciones_transito.merge(prod, on='product_id', how='left')
        importaciones_transito['CARTONES'] = importaciones_transito['OH']/importaciones_transito['Unidad_Empaque']
    
    return importaciones_transito



def importaciones_llegadas_ocompra_odbc(o_compra):

    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(
            #"SELECT DOC_ID_CORP, ENTRADA_FECHA, PRODUCT_ID_CORP, LOTE_ID, FECHA_CADUCIDAD, AVAILABLE, EGRESO_TEMP, OH, WARE_COD_CORP FROM imp_llegadas WHERE "
            f"SELECT * FROM imp_llegadas WHERE DOC_ID_CORP = '{o_compra}'"
            )
        columns = [col[0] for col in cursor.description]
        importaciones_llegadas = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        importaciones_llegadas = pd.DataFrame(importaciones_llegadas)
        importaciones_llegadas['product_id'] = list(map(lambda x:x[:-6], list(importaciones_llegadas['PRODUCT_ID_CORP'])))

    return importaciones_llegadas



def importaciones_en_transito_odbc():

    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(
            "SELECT * FROM imp_transito"
            )
        columns = [col[0] for col in cursor.description]
        importaciones_transito = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        importaciones_transito = pd.DataFrame(importaciones_transito)

    return importaciones_transito


def importaciones_en_transito_detalle_odbc(contrato_id):

    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(
            f"SELECT * FROM imp_transito Where CONTRATO_ID = '{contrato_id}'"
            )
        columns = [col[0] for col in cursor.description]
        importaciones_transito = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        importaciones_transito = pd.DataFrame(importaciones_transito)

    return importaciones_transito


def ventas_facturas_odbc(): # PARA REGISTRO DE GUIAS
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(
            #"SELECT * FROM venta_facturas WHERE FECHA>'2023-04-01'"
            "SELECT * FROM facturas"
        )

        columns = [col[0] for col in cursor.description]
        ventas_facturas = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
    ventas_facturas = pd.DataFrame(ventas_facturas)

    return ventas_facturas


def ventas_odbc_facturas(desde, hasta, cli): 
    
    try:
        with connections['gimpromed_sql'].cursor() as cursor:
            cursor.execute(
                f"""
                SELECT 
                    CODIGO_CLIENTE,
                    FECHA,
                    PRODUCT_ID,
                    QUANTITY,
                    UNIT_PRICE,
                    CODIGO_FACTURA
                FROM venta_facturas 
                WHERE CODIGO_CLIENTE = '{cli}' AND STR_TO_DATE(FECHA, '%Y-%m-%d') BETWEEN '{desde}' AND '{hasta}'
                """
            )
            columns = [col[0] for col in cursor.description]
            ventas_facturas = [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]
            ventas_facturas = pd.DataFrame(ventas_facturas).fillna(0)
            ventas_facturas['PRECIO_TOTAL'] = ventas_facturas['QUANTITY'] * ventas_facturas['UNIT_PRICE']
            # ventas_facturas['factura_str'] = ventas_facturas['CODIGO_FACTURA'].str.split('-')[1]
            return ventas_facturas
    except Exception as e:
        print(e)
        return str(e)


def ventas_armados_facturas_odbc(producto):
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(
            f"SELECT CODIGO_CLIENTE, FECHA, QUANTITY FROM venta_facturas WHERE PRODUCT_ID = '{producto}'"
        )

        columns = [col[0] for col in cursor.description]
        ventas_facturas = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
    ventas_facturas = pd.DataFrame(ventas_facturas)
    ventas_facturas['FECHA'] = pd.to_datetime(ventas_facturas['FECHA'])

    un_anio = datetime.now() - timedelta(days=395)

    ventas_facturas = ventas_facturas[ventas_facturas['FECHA']>un_anio]

    return ventas_facturas


def lotes_facturas_odbc(n_factura, product_id):
    
    data = api_mba_sql(
        f"""SELECT CLNT_Factura_Principal.CODIGO_FACTURA, INVT_Ficha_Principal.PRODUCT_ID, INVT_Lotes_Trasabilidad.EGRESO_TEMP, INVT_Lotes_Trasabilidad.LOTE_ID, INVT_Lotes_Trasabilidad.FECHA_CADUCIDAD
        FROM CLNT_Factura_Principal CLNT_Factura_Principal, INVT_Ficha_Principal INVT_Ficha_Principal, INVT_Lotes_Trasabilidad INVT_Lotes_Trasabilidad, INVT_Producto_Movimientos INVT_Producto_Movimientos
        WHERE INVT_Ficha_Principal.PRODUCT_ID_CORP = INVT_Producto_Movimientos.PRODUCT_ID_CORP AND
        CLNT_Factura_Principal.CODIGO_FACTURA = INVT_Producto_Movimientos.DOC_ID_CORP2 AND
        INVT_Lotes_Trasabilidad.PRODUCT_ID_CORP = INVT_Ficha_Principal.PRODUCT_ID_CORP AND
        CLNT_Factura_Principal.CODIGO_FACTURA = INVT_Lotes_Trasabilidad.DOC_ID_CORP AND
        ((INVT_Producto_Movimientos.CONFIRM=TRUE) AND (CLNT_Factura_Principal.CODIGO_FACTURA='{n_factura}')
        AND
        (INVT_Producto_Movimientos.PRODUCT_ID='{product_id}') AND (INVT_Producto_Movimientos.I_E_SIGN='-') AND (INVT_Producto_Movimientos.ADJUSTMENT_TYPE='FT') AND
        (CLNT_Factura_Principal.ANULADA=FALSE))
        """)
    
    if data['status'] == 200:
        data_df = pd.DataFrame(data['data'])
        data_df = data_df.rename(columns={
            'CODIGO_FACTURA':'n_factura',
            'PRODUCT_ID':'product_id',
            'EGRESO_TEMP':'unidades',
            'LOTE_ID':'lote',
            'FECHA_CADUCIDAD':'fecha_caducidad'
        })
        return de_dataframe_a_template(data_df)

    return None


def reservas_lotes_actualizar_odbc(request):

    api_actualizar_reservas_lotes_warehouse()

    time = str(datetime.now())
    TimeStamp.objects.create(actualization_reserva_lote=time)

    return HttpResponseRedirect('/etiquetado/revision/imp/llegadas/list')


def reservas_lote(): #request
    ''' Colusta de clientes por ruc a la base de datos '''
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute("SELECT * FROM reservas_lote")
        columns = [col[0] for col in cursor.description]
        reservas_lote = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
        reservas_lote = pd.DataFrame(reservas_lote)
    return reservas_lote


def reservas_lotes_group():

    r_lote = reservas_lote()
    r_lote = r_lote.groupby(['PRODUCT_ID','LOTE_ID','WARE_CODE','FECHA_CADUCIDAD']).sum().reset_index()
    r_lote = r_lote[['PRODUCT_ID','LOTE_ID','WARE_CODE','FECHA_CADUCIDAD','EGRESO_TEMP']]
    r_lote['FECHA_CADUCIDAD'] = pd.to_datetime(r_lote['FECHA_CADUCIDAD'])

    return r_lote


def stock_disponible(bodega, items_list): #request
    
    if bodega == 'BAN':
        with connections['gimpromed_sql'].cursor() as cursor:
            cursor.execute(
                f"SELECT * FROM stock_lote where WARE_CODE = '{bodega}'"
            )
            columns = [col[0] for col in cursor.description]
            stock_disp = [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]
            stock_disp = pd.DataFrame(stock_disp)
            stock_disp = stock_disp[stock_disp['PRODUCT_ID'].isin(items_list)][['PRODUCT_ID','PRODUCT_NAME','GROUP_CODE','UM','OH','OH2','COMMITED','QUANTITY','LOTE_ID','WARE_CODE','LOCATION']]
            stock_disp = stock_disp.groupby(by='PRODUCT_ID')['OH2'].sum().reset_index()[['PRODUCT_ID','OH2']]
            stock_disp = stock_disp.rename(columns={'OH2':'stock_disp'})
            
        return stock_disp
    
    elif bodega == 'BCT':

        stock_disp = Existencias.objects.filter(
            Q(estado='Disponible') & 
            Q(product_id__in=items_list)
        )
        if stock_disp.exists():
            stock_disp = pd.DataFrame(stock_disp.values('product_id', 'unidades')).groupby(by='product_id')['unidades'].sum().reset_index() 
            stock_disp = stock_disp.rename(columns={'product_id':'PRODUCT_ID','unidades':'stock_disp'})
            return stock_disp
        
        else:
            stock_disp = pd.DataFrame()
            stock_disp['PRODUCT_ID'] = items_list
            stock_disp['stock_disp'] = 0
            return stock_disp


def stock_total(): #request
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(
            f"SELECT * FROM stock_lote"
        )
        columns = [col[0] for col in cursor.description]
        stock = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
        stock = pd.DataFrame(stock)
                
    return stock


def facturas_odbc(): #request
    """ Tabla de facturas """
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute("SELECT * FROM facturas")
        columns = [col[0] for col in cursor.description]
        facturas = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
        facturas = pd.DataFrame(facturas)

    return facturas


def factura_detalle_odbc(n_factura):
    """ Tabla de facturas """
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(
            f"SELECT * FROM facturas WHERE CODIGO_FACTURA = '{n_factura}'"
            )
        columns = [col[0] for col in cursor.description]
        facturas = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
        facturas = pd.DataFrame(facturas)

    return facturas



def factura_lote_odbc(n_factura):
    
    fac = api_mba_sql(f"""
        SELECT CLNT_Factura_Principal.CODIGO_FACTURA, CLNT_Factura_Principal.CODIGO_CLIENTE, CLNT_Factura_Principal.FECHA_FACTURA, INVT_Ficha_Principal.PRODUCT_ID,
        INVT_Ficha_Principal.PRODUCT_NAME, INVT_Ficha_Principal.GROUP_CODE, INVT_Lotes_Trasabilidad.EGRESO_TEMP, INVT_Lotes_Trasabilidad.LOTE_ID, INVT_Lotes_Trasabilidad.FECHA_CADUCIDAD,
        INVT_Ficha_Principal.Custom_Field_1
        FROM CLNT_Factura_Principal CLNT_Factura_Principal, INVT_Ficha_Principal INVT_Ficha_Principal, INVT_Lotes_Trasabilidad INVT_Lotes_Trasabilidad
        WHERE INVT_Lotes_Trasabilidad.PRODUCT_ID_CORP = INVT_Ficha_Principal.PRODUCT_ID_CORP AND CLNT_Factura_Principal.CODIGO_FACTURA = INVT_Lotes_Trasabilidad.DOC_ID_CORP AND
        ((CLNT_Factura_Principal.CODIGO_FACTURA='{n_factura}') AND (CLNT_Factura_Principal.ANULADA=FALSE))
    """)
    
    if fac['status'] == 200:
        factura = pd.DataFrame(fac['data'])
        factura['FECHA_FACTURA'] = factura['FECHA_FACTURA'].str.slice(0, 10)
        factura['FECHA_CADUCIDAD'] = factura['FECHA_CADUCIDAD'].str.slice(0, 10)
        factura = factura.rename(columns={'GROUP_CODE':'PRODUCT_GROUP'}) 
        
        return factura
    
    else:
        return pd.DataFrame()



def ultima_actualizacion(columna):

    ultimo_tiempo = pd.DataFrame(TimeStamp.objects.all().values())
    ultimo_tiempo = list(ultimo_tiempo[columna])
    ul=[]
    for i in ultimo_tiempo:
        if i != '':
            ul.append(i)
    actulizado = ul[-1][0:19]

    return actulizado



def cliente_detalle_odbc(codigo_cliente):
    """ Tabla de facturas """
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(
            f"SELECT * FROM clientes WHERE CODIGO_CLIENTE = '{codigo_cliente}'"
            )
        columns = [col[0] for col in cursor.description]
        cliente = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ][0]
    return cliente


# PEDIDO POR CLIENTE
def pedido_por_cliente(n_pedido):
    """ Retorna el litado de items por numero de contrato y cliente """
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute("SELECT * FROM reservas WHERE CONTRATO_ID = %s", [n_pedido])

        columns = [col[0] for col in cursor.description]

        reservas = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        r = pd.DataFrame(reservas)
        
    return r


# CALCULADORA DE COSTO DE ENVIO TRAMACO
def tramaco_function(pesototal, producto, trayecto):
    """ Retorna el valor de costo de envio de transporte tramaco """

    if producto=='CARGA COURIER' or producto=='CARGA LIVIANA':

        kgarranque = 10

        if trayecto == 'PRINCIPAL':
            tarifa_arranque = 2.77
            kgadicional     = 0.41

            kg = pesototal-kgarranque
            costototal = round(tarifa_arranque + (kg * kgadicional), 2)

        elif trayecto == 'SECUNDARIO':
            tarifa_arranque = 3.9
            kgadicional     = 0.59

            kg = pesototal-kgarranque
            costototal = round(tarifa_arranque + (kg * kgadicional), 2)

        elif trayecto == 'T.ESPECIAL':
            tarifa_arranque = 5.17
            kgadicional     = 0.78

            kg = pesototal-kgarranque
            costototal = round(tarifa_arranque + (kg * kgadicional), 2)

        elif trayecto == 'URBANO':
            tarifa_arranque = 1.67
            kgadicional     = 0.26

            kg = pesototal-kgarranque
            costototal = round(tarifa_arranque + (kg * kgadicional), 2)

        elif trayecto == 'RURAL':
            tarifa_arranque = 1.97
            kgadicional     = 0.3

            kg = pesototal-kgarranque
            costototal = round(tarifa_arranque + (kg * kgadicional), 2)

    elif producto=='DOCUMENTOS':
        kgarranque = 2
        kgadicional = 0

        if trayecto == 'PRINCIPAL':
            tarifa_arranque = 2.77

            kg = pesototal-kgarranque
            costototal = round(tarifa_arranque + (kg * kgadicional), 2)

        elif trayecto == 'SECUNDARIO':
            tarifa_arranque = 3.9

            kg = pesototal-kgarranque
            costototal = round(tarifa_arranque + (kg * kgadicional), 2)

        elif trayecto == 'T.ESPECIAL':
            tarifa_arranque = 5.17

            kg = pesototal-kgarranque
            costototal = round(tarifa_arranque + (kg * kgadicional), 2)

        elif trayecto == 'URBANO':
            tarifa_arranque = 1.67

            kg = pesototal-kgarranque
            costototal = round(tarifa_arranque + (kg * kgadicional), 2)

        elif trayecto == 'RURAL':
            tarifa_arranque = 1.97

            kg = pesototal-kgarranque
            costototal = round(tarifa_arranque + (kg * kgadicional), 2)

    else:
        costototal=0

    return costototal


def nueva_tramaco_function(pesototal, producto, trayecto):

    costos_fijos = {
        'DOCUMENTOS': {
            'PRINCIPAL': 2.90,
            'SECUNDARIO': 4.1,
            'T.ESPECIAL': 5.43,
            'URBANO': 1.76,
            'RURAL': 2.07
        },
        'CARGA': {
            'PRINCIPAL': 2.90,
            'SECUNDARIO': 4.1,
            'T.ESPECIAL': 5.43,
            'URBANO': 1.76,
            'RURAL': 2.07
        }
    }

    # Factores de multiplicación por trayecto
    factores_multiplicacion = {
        'PRINCIPAL': 0.44,
        'SECUNDARIO': 0.61,
        'T.ESPECIAL': 0.81,
        'URBANO': 0.27,
        'RURAL': 0.31
    }
    
    # Inicializar costo total
    costototal = 0
    
    # Si el peso total es 0, retornar costo 0
    if pesototal == 0:
        return costototal
    
    # Costos para documentos
    if producto == 'DOCUMENTOS':
        # Obtener costo fijo para el trayecto, si no existe usar 0
        costo_base = costos_fijos['DOCUMENTOS'].get(trayecto, 0)
        if pesototal <= 1:
            costototal = costo_base
        else:
            peso_adicional = pesototal - 1
            factor = factores_multiplicacion.get(trayecto, 0)
            costototal = round(costo_base + (peso_adicional * factor), 2)
    
    # Costos para carga courier y carga liviana
    elif producto in ['CARGA COURIER', 'CARGA LIVIANA']:
        # Obtener costo fijo para el trayecto, si no existe usar 0
        costo_base = costos_fijos['CARGA'].get(trayecto, 0)
        if pesototal <= 9:
            costototal = costo_base
        else:
            peso_adicional = pesototal - 9
            factor = factores_multiplicacion.get(trayecto, 0)
            costototal = round(costo_base + (peso_adicional * factor), 2)
    
    # return costototal
    costo_nuevo = round(costototal*1.06, 2) if costototal > 0 else 0  # (costototal*1.06)
    return f'{costototal} - ($ {costo_nuevo})'


def tramaco_function_ajax(request):

    producto = request.POST['producto']
    trayecto = request.POST['trayecto']
    
    peso_total = request.POST['peso_total']
    peso_total = peso_total.replace(',', '.')
    peso_total = float(peso_total)    

    #costo = tramaco_function(peso_total, producto, trayecto)
    costo = nueva_tramaco_function(peso_total, producto, trayecto)

    return HttpResponse(costo)


# Alerta de stock faltante por contrato
def stock_faltante_contrato(contratos, bodega):
    cont = []
    disp = []
    for i in contratos:
        res = pedido_por_cliente(i)[['PRODUCT_ID','QUANTITY']]
        items = list(res['PRODUCT_ID'].unique())
        
        
        stock = stock_disponible(bodega, items)
        
        
        res = res.merge(stock, on='PRODUCT_ID', how='left').fillna(0)        
        res['disp'] = res.apply(lambda x: 'OK' if x['stock_disp']>x['QUANTITY'] else 'NOT', axis=1)
        res = res[res['PRODUCT_ID']!='MANTEN']

        dis = 'NOT' in list(res['disp'])
        
        if dis:
            cont.append(i)
            disp.append('NOT')
    
    sto = pd.DataFrame()
    sto['CONTRATO_ID'] = cont
    sto['DISP'] = disp
    
    return sto





# Función para quitar puntos de un str
def quitar_puntos(lista):

    lista_str_sp = []
    
    for i in lista:
        x = str(i)
        x = i.replace('.','')
        x = x.rstrip()
        x = x.lstrip()
        lista_str_sp.append(x)

    return lista_str_sp



# RESERVAS POR PRODUCTO
def reservas_lote_product_id(product_id_list):
    """ Retorna la reservas filtradas por product_id """

    cli = clientes_warehouse()[['CODIGO_CLIENTE', 'NOMBRE_CLIENTE']]

    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute("SELECT * FROM reservas_lote")
        columns = [col[0] for col in cursor.description]

        reservas_lote = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        reservas_lote = pd.DataFrame(reservas_lote)
        reservas_lote = reservas_lote[reservas_lote.PRODUCT_ID.isin(product_id_list)]
        reservas_lote['CONFIRMED'] = reservas_lote['CONFIRMED'].astype(int)

        if not reservas_lote.empty:
            reservas_lote = reservas_lote.merge(cli, on='CODIGO_CLIENTE', how='left')


    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute("SELECT * FROM reservas")
        columns = [col[0] for col in cursor.description]

        reservas_sinlote = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        reservas_sinlote = pd.DataFrame(reservas_sinlote)
        reservas_sinlote = reservas_sinlote[reservas_sinlote.PRODUCT_ID.isin(product_id_list)]
        reservas_sinlote['CONTRATO_ID']  = reservas_sinlote['CONTRATO_ID'].astype(float)
        reservas_sinlote['CONTRATO_ID']  = reservas_sinlote['CONTRATO_ID'].astype(int)
        reservas_sinlote['FECHA_PEDIDO'] = reservas_sinlote['FECHA_PEDIDO'].astype(str)
    
    reservas = pd.concat([reservas_lote, reservas_sinlote])

    reservas = reservas.drop_duplicates(subset='CONTRATO_ID', keep='first')
    # print(reservas)
    # reservas = reservas[['CONTRATO_ID','NOMBRE_CLIENTE','PRODUCT_ID_x']]
    reservas = de_dataframe_a_template(reservas)

    return reservas


def reservas_sinlote(): 
    ''' Colusta de clientes por ruc a la base de datos '''
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute("SELECT * FROM reservas")
        columns = [col[0] for col in cursor.description]
        reservas_sinlote = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
        reservas_sinlote = pd.DataFrame(reservas_sinlote)
    return reservas_sinlote



def stock_lote_odbc(): 
    
    # Stock
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute("SELECT * FROM stock_lote")
        columns = [col[0] for col in cursor.description]
        stock_lote = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
        stock_lote = pd.DataFrame(stock_lote)
    
        stock_lote = stock_lote[stock_lote['WARE_CODE']!='CUC']
        stock_lote = stock_lote[stock_lote['WARE_CODE']!='CUA']

        connections['gimpromed_sql'].close()
        return stock_lote


def reservas_lote_2():

    ''' Colusta de clientes por ruc a la base de datos '''
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute("SELECT * FROM reservas_lote_2 WHERE SEC_NAME_CLIENTE LIKE '%RESERV%'")
        columns = [col[0] for col in cursor.description]
        reservas_lote = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
        reservas_lote = pd.DataFrame(reservas_lote) 
        connections['gimpromed_sql'].close()
        return reservas_lote

def reservas_publico_lote_2():

    ''' Colusta de clientes por ruc a la base de datos '''
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute("SELECT * FROM reservas_lote_2 WHERE SEC_NAME_CLIENTE LIKE '%PUBLIC%'")
        columns = [col[0] for col in cursor.description]
        reservas_lote = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
        reservas_lote = pd.DataFrame(reservas_lote) 
        connections['gimpromed_sql'].close()
        return reservas_lote


def pickin_de_reservas_finalizado():
    
    desde = datetime.now() - timedelta(days=90)
    data = EstadoPicking.objects.filter(fecha_creado__gte = desde).values('n_pedido', 'estado')
    df = pd.DataFrame(data).rename(columns={'n_pedido':'CONTRATO_ID'})  
    df['CONTRATO_ID'] = df['CONTRATO_ID'].astype('float') 
    df['CONTRATO_ID'] = df['CONTRATO_ID'].astype('int') #;print(df)
    return df


def etiquetados_no_finalizados():
    
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute("SELECT * FROM reservas WHERE SEC_NAME_CLIENTE = 'PUBLICO' ")
        columns = [col[0] for col in cursor.description]
        publico = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
        cursor.close()
        publico = pd.DataFrame(publico) 
        publico['CONTRATO_ID'] = publico['CONTRATO_ID'].astype('float')
        publico['CONTRATO_ID'] = publico['CONTRATO_ID'].astype('int') #;print(publico)
        
        connections['gimpromed_sql'].close()
        return publico



# NUEVAAA
def revision_reservas_fun():
    
    try:
        
        # 1. Obtener datos
        df_reservas_lote    = reservas_lote_2()
        df_reservas_publico = reservas_publico_lote_2()
        stock               = stock_lote_odbc()
        productos_list = df_reservas_lote['PRODUCT_ID'].unique() 
        
        # 2. DATAFRAME RESERVAS LOTE AGRUPADAS POR PRODUCTO, LOTE Y FECHA_CADUCIDAD
        df_reservas_productos = df_reservas_lote.copy()
        df_reservas_productos = df_reservas_productos.rename(columns={'EGRESO_TEMP':'UND_RESERVA'})
        df_reservas_productos['LOTE_ID'] = df_reservas_productos['LOTE_ID'].str.replace('.', '')
        df_reservas_productos['LOTE_ID'] = df_reservas_productos['LOTE_ID'].str.strip()
        df_reservas_productos = df_reservas_productos.pivot_table(
            index=['PRODUCT_ID', 'LOTE_ID', 'FECHA_CADUCIDAD','WARE_CODE'],
            values='UND_RESERVA',
            aggfunc='sum'
        ).reset_index()
        
        # 3. DATAFRAME RESERVAS AGRUPADAS POR CONTRATO_ID
        df_reservas_contratos = df_reservas_lote.copy()
        df_reservas_contratos['CONTRATO_ID'] = df_reservas_contratos['CONTRATO_ID'].astype('str')
        df_reservas_contratos = df_reservas_contratos.pivot_table(
            index=['PRODUCT_ID', 'LOTE_ID', 'FECHA_CADUCIDAD', 'WARE_CODE'], 
            values='CONTRATO_ID', 
            aggfunc = lambda x: ' - '.join(x)
        ).reset_index()
        
        # 3.1 AGREGAR DATOS DE COMPRAS PUBLICAS
        df_reservas_publico = df_reservas_publico.copy()
        df_reservas_publico = df_reservas_publico.rename(columns={'EGRESO_TEMP':'UND_PUBLICO'})
        df_reservas_publico['LOTE_ID'] = df_reservas_publico['LOTE_ID'].str.replace('.', '')
        df_reservas_publico['LOTE_ID'] = df_reservas_publico['LOTE_ID'].str.strip()
        df_reservas_publico = df_reservas_publico.pivot_table(
            index=['PRODUCT_ID', 'LOTE_ID', 'FECHA_CADUCIDAD','WARE_CODE'],
            values='UND_PUBLICO',
            aggfunc='sum'
        ).reset_index()        
        
        # 4. DATAFRAME STOCK
        stock = stock.rename(columns={'OH2':'UND_EXISTENCIA'})
        stock['LOTE_ID'] = stock['LOTE_ID'].str.replace('.', '')
        stock['LOTE_ID'] = stock['LOTE_ID'].str.strip()
        stock = stock.pivot_table(
            index=['PRODUCT_ID','LOTE_ID','FECHA_CADUCIDAD','WARE_CODE'],
            values='UND_EXISTENCIA',
            aggfunc='sum'
        ).reset_index()
        
        # 5. MERGE STOCK - RESERVAS
        stock_reservas = stock.merge(
            df_reservas_productos,
            on=['PRODUCT_ID','LOTE_ID','FECHA_CADUCIDAD','WARE_CODE'],
            how='left'
        ).fillna(0)
        stock_reservas = stock_reservas.merge(
            df_reservas_publico,
            on=['PRODUCT_ID','LOTE_ID','FECHA_CADUCIDAD','WARE_CODE'],
            how='left',
            suffixes=('', '_PUBLICO')
        ).fillna(0)
        
        # 5.1 CREAR COLUMNA DISPONIBLE-RESERVAS
        stock_reservas['DISPONIBLE'] =  stock_reservas['UND_EXISTENCIA'] - stock_reservas['UND_RESERVA'] - stock_reservas['UND_PUBLICO']
        
        # 5.2 FILTRAR SOLO POR PRODUCTOS Y LOTES QUE TIENEN RESERVAS
        stock_reservas = stock_reservas[stock_reservas['PRODUCT_ID'].isin(productos_list)]
        
        # 5.3 UNIR RESERVAS POR CONTRATO
        stock_reservas = stock_reservas.merge(df_reservas_contratos, on=['PRODUCT_ID','LOTE_ID','FECHA_CADUCIDAD','WARE_CODE'], how='left')
        
        # 5.4 PRODUCTO_UNICO
        frecuencia = stock_reservas['PRODUCT_ID'].value_counts() 
        stock_reservas['PRODUCT_ID_UNICO'] = stock_reservas['PRODUCT_ID'].map(lambda x: frecuencia[x] == 1)
        
        ### FILTROS Y CONDICIONES
        # 6. SOLO PRODUCTOS CON MAS DE 1 LOTE
        stock_reservas = stock_reservas[stock_reservas['PRODUCT_ID_UNICO'] == False]
        
        # 6.1 FILTRO POR DISPONIBLE MENOR A CERO
        stock_reservas = stock_reservas[stock_reservas['DISPONIBLE'] >= 0]
        
        # stock_reservas.to_excel('stock2.xlsx', index=False)
        # print(stock_reservas)
        
        df = stock_reservas.sort_values(
            by        = ['PRODUCT_ID','FECHA_CADUCIDAD'],
            ascending = [True, False]
        )
        
        reporte = []
        for product_id, group in df.groupby('PRODUCT_ID'):
            
            lotes = group.to_dict(orient='records') #; print(lotes)
            lote_destino = lotes[0]  # LOTE CON FECHA DE CADUCIDAD MAS POSTERIOR
            
            for lote_origen in lotes[1:]:
                
                if lote_origen['UND_RESERVA'] > 0:
                    reserva_total = lote_destino['UND_RESERVA'] + lote_origen['UND_RESERVA']
                    if lote_destino['UND_EXISTENCIA'] >= reserva_total:   # filtrar y solucionar condición
                    # if lote_destino['UND_EXISTENCIA'] > 0:    
                        reporte.append({
                            'CONTRATO':lote_origen['CONTRATO_ID'],
                            'PRODUCT_ID': product_id,
                            'LOTE_RESERVADO': lote_origen['LOTE_ID'],
                            'FECHA_RESERVADO': lote_origen['FECHA_CADUCIDAD'].strftime('%d/%m/%Y'),
                            'RESERVA_RESERVADO': lote_origen['UND_RESERVA'],
                            'BODEGA_RESERVADO':lote_origen['WARE_CODE'],
                            
                            'LOTE_DISPONIBLE': lote_destino['LOTE_ID'],
                            'FECHA_DISPONIBLE': lote_destino['FECHA_CADUCIDAD'].strftime('%d/%m/%Y'),
                            'BODEGA_DISPONIBLE':lote_destino['WARE_CODE'],
                            'EXISTENCIA_DISPONIBLE': lote_destino['UND_EXISTENCIA'],
                            'RESERVA_DISPONIBLE_ACTUAL': lote_destino['UND_RESERVA'],
                            'RESERVA_DISPONIBLE_NUEVA': reserva_total,
                            'DISPONIBLE_DISPONIBLE': lote_destino['UND_EXISTENCIA'] - reserva_total
                        })
            
        df_reporte = pd.DataFrame(reporte)
        df_reporte['OBSERVACIONES'] = df_reporte.apply(
            lambda x: 
                # "LAS FECHAS DE LOS LOTES SON IGUALES" if x['FECHA_RESERVADO'] == x['FECHA_DISPONIBLE'] 
                "EXCLUIR" if x['FECHA_RESERVADO'] == x['FECHA_DISPONIBLE'] 
                else f"CAMBIAR ESTA RESERVA A UN LOTE CON FECHA DE CADUCIDAD POSTERIOR LA CANTIDAD {x['RESERVA_RESERVADO']}"
                , axis=1
        )
        
        df_reporte = df_reporte[df_reporte['OBSERVACIONES']!='EXCLUIR']
        
        return df_reporte

    except Exception as e:
        print('EXCEPTION', e)
        return pd.DataFrame()



### Consulta de productos en cuarentena para etiquetado stock
def stock_lote_cuc_etiquetado_detalle_odbc(): 
    
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(f"SELECT * FROM stock_lote WHERE WARE_CODE = 'CUC'")
        columns = [col[0] for col in cursor.description]
        stock_lote = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
        stock_lote = pd.DataFrame(stock_lote)
        stock_lote = stock_lote.sort_values('FECHA_CADUCIDAD')
        
        connections['gimpromed_sql'].close()
        return stock_lote


def trazabilidad_api_mba(cod, lot):
    try:
        data = api_mba_sql(
        f"""
            SELECT INVT_Lotes_Trasabilidad.DOC_ID_CORP, INVT_Lotes_Trasabilidad.PRODUCT_ID_CORP, INVT_Lotes_Trasabilidad.LOTE_ID, 
            INVT_Lotes_Trasabilidad.AVAILABLE, INVT_Lotes_Trasabilidad.COMMITED, INVT_Lotes_Trasabilidad.EGRESO_TEMP, INVT_Lotes_Trasabilidad.OH, 
            INVT_Lotes_Trasabilidad.Ingreso_Egreso, INVT_Lotes_Trasabilidad.Tipo_Movimiento, INVT_Lotes_Trasabilidad.Id_Linea_Egreso_Movimiento, 
            INVT_Lotes_Trasabilidad.Link_Id_Linea_Ingreso, INVT_Lotes_Trasabilidad.CONFIRMADO, INVT_Lotes_Trasabilidad.Devolucio_MP, INVT_Lotes_Trasabilidad.Lote_Agregado, 
            INVT_Lotes_Trasabilidad.WARE_COD_CORP, 
            INVT_Ajustes_Principal.DATE_I , CLNT_Factura_Principal.FECHA_FACTURA, CLNT_Ficha_Principal.NOMBRE_CLIENTE, INVT_Lotes_Trasabilidad.Codigo_Alt_Clnt, CLNT_Pedidos_Principal.FECHA_DESDE 
            FROM INVT_Lotes_Trasabilidad INVT_Lotes_Trasabilidad 
            LEFT JOIN INVT_Ajustes_Principal INVT_Ajustes_Principal 
            ON INVT_Lotes_Trasabilidad.DOC_ID_CORP = INVT_Ajustes_Principal.DOC_ID_CORP 
            LEFT JOIN CLNT_Factura_Principal CLNT_Factura_Principal 
            ON INVT_Lotes_Trasabilidad.DOC_ID_CORP = CLNT_Factura_Principal.CODIGO_FACTURA 
            LEFT JOIN CLNT_Ficha_Principal CLNT_Ficha_Principal 
            ON INVT_Lotes_Trasabilidad.Codigo_Alt_Clnt = CLNT_Ficha_Principal.CODIGO_CLIENTE 
            LEFT JOIN CLNT_Pedidos_Principal CLNT_Pedidos_Principal 
            ON INVT_Lotes_Trasabilidad.DOC_ID_CORP = CLNT_Pedidos_Principal.CONTRATO_ID_CORP 
            WHERE (INVT_Lotes_Trasabilidad.PRODUCT_ID_CORP='{cod}-GIMPR') AND (INVT_Lotes_Trasabilidad.LOTE_ID LIKE '%{lot}%') AND (INVT_Lotes_Trasabilidad.CONFIRMADO=TRUE) 
            ORDER BY INVT_Lotes_Trasabilidad.LINK_ID_LINEA_INGRESO
        """
        )
        if data['status'] == 200:
            df_trazabilidad = pd.DataFrame(data['data'])
            df_trazabilidad['NOMBRE_CLIENTE'] = df_trazabilidad['NOMBRE_CLIENTE'].fillna('-')
            df_trazabilidad['FECHA_FACTURA'] = df_trazabilidad['FECHA_FACTURA'].str.slice(0, 10)            
            df_trazabilidad['FECHA_DESDE'] = df_trazabilidad['FECHA_DESDE'].str.slice(0, 10)            
            df_trazabilidad['DATE_I'] = df_trazabilidad['DATE_I'].str.slice(0, 10)
            # print(df_trazabilidad[['DOC_ID_CORP', 'FECHA_FACTURA', 'FECHA_DESDE', 'DATE_I']])
            return df_trazabilidad.fillna('')
        else:
            return pd.DataFrame()
    except Exception as e:
        print(f"Error: {e}")
        return pd.DataFrame()



# Filtrar avance de etiquetado por pedido
def etiquetado_avance_pedido(n_pedido):
    avance = EtiquetadoAvance.objects.filter(n_pedido=n_pedido).values()
    avance = pd.DataFrame(avance) 
    avance = avance.rename(columns={'product_id':'PRODUCT_ID'})
    #avance = avance.groupby(by=['id','n_pedido','PRODUCT_ID'])['unidades'].sum().reset_index()
    #avance = avance.groupby(by=['n_pedido','PRODUCT_ID'])['unidades'].sum().reset_index()
    #print(avance)

    return avance



def calculo_etiquetado_avance(n_pedido):
    
    avance = etiquetado_avance_pedido(n_pedido)
    
    if avance.empty:
        return 0.0
    
    else:
        pedido = pedido_por_cliente(n_pedido)['QUANTITY']
        avance = avance['unidades']
    
        p_total = pedido.sum()
        a_total = avance.sum()
        
        porcentaje_avance = (a_total/p_total) * 100
        porcentaje_avance = round(porcentaje_avance, 1)
        
        return porcentaje_avance



def lotes_bodega(bodega, product_id):
    
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(f"SELECT * FROM stock_lote WHERE WARE_CODE = '{bodega}' AND PRODUCT_ID = '{product_id}'")
        columns = [col[0] for col in cursor.description]
        stock_lote = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]    
        
        stock_lote = pd.DataFrame(stock_lote)
        if not stock_lote.empty:
            stock_lote = stock_lote.sort_values(by='FECHA_CADUCIDAD')
            stock_lote = stock_lote[['LOCATION','LOTE_ID','FECHA_CADUCIDAD','OH2']]
            stock_lote = stock_lote.rename(columns={
                'LOCATION':'Ubicación',
                'LOTE_ID':'Lote',
                'FECHA_CADUCIDAD':'Caducidad',
                'OH2':'Unds'
                })
        
        connections['gimpromed_sql'].close()
        return stock_lote


def wms_reservas_lotes_datos():
    r_lote = reservas_lote()[['CONTRATO_ID','CODIGO_CLIENTE','PRODUCT_ID','LOTE_ID','EGRESO_TEMP']]
    r_lote = r_lote.rename(columns={
        'PRODUCT_ID':'product_id',
        'LOTE_ID':'lote_id'}
    ).drop_duplicates(subset=['product_id','lote_id'])   
    
    return r_lote


def wms_reservas_lote_consulta(product_id, lote_id):
    
    with connections['gimpromed_sql'].cursor() as cursor:
        
        cursor.execute(f"SELECT * FROM reservas_lote WHERE PRODUCT_ID = '{product_id}' AND LOTE_ID = '{lote_id}' ")
        
        columns = [col[0] for col in cursor.description]
        r_lote = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
        
        connections['gimpromed_sql'].close()
        r_lote = pd.DataFrame(r_lote)
        
    cli = clientes_warehouse()[['CODIGO_CLIENTE','NOMBRE_CLIENTE']]
    
    if not r_lote.empty:
        r_lote = r_lote.merge(cli, on='CODIGO_CLIENTE', how='left')
            
        # r_lote = r_lote[['CONTRATO_ID','NOMBRE_CLIENTE','FECHA_PEDIDO','PRODUCT_ID','LOTE_ID','EGRESO_TEMP']]
        # r_lote = r_lote[['CONTRATO_ID','NOMBRE_CLIENTE','FECHA_PEDIDO','LOTE_ID','EGRESO_TEMP']]
        r_lote = r_lote[['CONTRATO_ID','NOMBRE_CLIENTE','FECHA_PEDIDO','EGRESO_TEMP']]
        r_lote = r_lote.rename(columns={
            'CONTRATO_ID':'Contrato',
            'NOMBRE_CLIENTE':'Cliente',
            'FECHA_PEDIDO':'F.Pedido',
            'PRODUCT_ID':'Item',
            #'LOTE_ID':'Lote',
            'EGRESO_TEMP':'Unds'
        })
        
        r_lote['F.Pedido']  = pd.to_datetime(r_lote['F.Pedido'])
        r_lote              = r_lote.sort_values(by='F.Pedido') 
        r_lote['F.Pedido']  = r_lote['F.Pedido'].astype(str)
        r_lote['Contrato']  = r_lote['Contrato'].astype(str)
        r_lote.loc['Total'] = r_lote.sum(numeric_only=True)
        r_lote['Unds']      = r_lote['Unds'].apply(lambda x:'{:,.0f}'.format(x))
        
        r_lote = r_lote.fillna('').replace(np.nan,'Total')
        
        r_lote = r_lote.to_html(
            float_format='{:,.0f}'.format,
            classes='table table-responsive table-bordered m-0 p-0',
            table_id= 'reservas_table',
            index=False,
            justify='start'
        )
        
    return r_lote 



def wms_detalle_factura(n_factura):
    
    query = ("SELECT CLNT_Factura_Principal.CODIGO_FACTURA, CLNT_Factura_Principal.CODIGO_CLIENTE, CLNT_Factura_Principal.FECHA_FACTURA, INVT_Ficha_Principal.PRODUCT_ID, INVT_Ficha_Principal.PRODUCT_NAME, INVT_Ficha_Principal.GROUP_CODE, INVT_Lotes_Trasabilidad.EGRESO_TEMP, INVT_Lotes_Trasabilidad.LOTE_ID, INVT_Lotes_Trasabilidad.FECHA_CADUCIDAD, INVT_Ficha_Principal.Custom_Field_1, CLNT_Factura_Principal.NUMERO_PEDIDO_SISTEMA "
    "FROM CLNT_Factura_Principal CLNT_Factura_Principal, INVT_Ficha_Principal INVT_Ficha_Principal, INVT_Lotes_Trasabilidad INVT_Lotes_Trasabilidad "
    f"WHERE INVT_Lotes_Trasabilidad.PRODUCT_ID_CORP = INVT_Ficha_Principal.PRODUCT_ID_CORP AND CLNT_Factura_Principal.CODIGO_FACTURA = INVT_Lotes_Trasabilidad.DOC_ID_CORP AND ((CLNT_Factura_Principal.CODIGO_FACTURA='{n_factura}') AND (CLNT_Factura_Principal.ANULADA=FALSE))")
    
    df = api_mba_sql(query)
    df = pd.DataFrame(df['data']) 
    
    # df = pd.read_sql_query(query, cnxn)
    cli = clientes_warehouse()[['CODIGO_CLIENTE','NOMBRE_CLIENTE','IDENTIFICACION_FISCAL']]
    df = df.merge(cli, on='CODIGO_CLIENTE', how='left') 
    df['FECHA_FACTURA']   = df['FECHA_FACTURA'].astype('str').str[:10]
    df['FECHA_CADUCIDAD'] = df['FECHA_CADUCIDAD'].astype('str').str[:10]
    df['NUMERO_PEDIDO_SISTEMA'] = df['NUMERO_PEDIDO_SISTEMA'].astype('str') + '.0'
    df['EGRESO_TEMP'] = df['EGRESO_TEMP'].astype('int')
    df = df.rename(columns={
            'PRODUCT_ID':'product_id',
            'LOTE_ID':'lote_id'
        })
    
    return df


def wms_reserva_por_contratoid(contrato_id):
    
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(f"SELECT * FROM warehouse.reservas WHERE CONTRATO_ID = '{contrato_id}'")
        columns = [col[0] for col in cursor.description]
        reserva = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
        reserva = pd.DataFrame(reserva)
        
        connections['gimpromed_sql'].close()
        return reserva


def wms_stock_lote_products():
    
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(
            f"SELECT PRODUCT_ID, PRODUCT_NAME, GROUP_CODE FROM warehouse.stock_lote ;")
        columns = [col[0] for col in cursor.description]
        products = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
        products = pd.DataFrame(products) 
        
        products = products.drop_duplicates(subset='PRODUCT_ID')
        products = products.rename(
            columns={
                'PRODUCT_ID':'product_id',
                'PRODUCT_NAME':'Nombre',
                'GROUP_CODE':'Marca'
            }).sort_values(by=['Marca','product_id'], ascending=[True, True])
        
        products = de_dataframe_a_template(products)
        
        connections['gimpromed_sql'].close()
        return products


def wms_stock_lote_cerezos_by_product(product_id):
    
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(f"SELECT * FROM warehouse.stock_lote WHERE (WARE_CODE = 'BCT' OR WARE_CODE = 'CUC') AND PRODUCT_ID = '{product_id}';")
        columns = [col[0] for col in cursor.description]
        stock = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
        stock = pd.DataFrame(stock)
        
        connections['gimpromed_sql'].close()
        return stock


def wms_datos_nota_entrega(nota_entrega):
    
    try:
        ne = 'A-' + f'{nota_entrega:010d}' + '-GIMPR'
        
        query = (       
            "SELECT INVT_Lotes_Ubicacion.DOC_ID_CORP, INVT_Lotes_Ubicacion.PRODUCT_ID_CORP, "
            "INVT_Lotes_Ubicacion.LOTE_ID, INVT_Lotes_Ubicacion.EGRESO_TEMP, INVT_Lotes_Ubicacion.COMMITED, "
            "INVT_Lotes_Ubicacion.WARE_CODE_CORP, INVT_Lotes_Ubicacion.UBICACION, INVT_Producto_Lotes.Fecha_elaboracion_lote, "
            "INVT_Producto_Lotes.FECHA_CADUCIDAD "
            "FROM INVT_Lotes_Ubicacion INVT_Lotes_Ubicacion, INVT_Producto_Lotes INVT_Producto_Lotes "
            "WHERE INVT_Lotes_Ubicacion.PRODUCT_ID_CORP = INVT_Producto_Lotes.PRODUCT_ID_CORP AND "
            "INVT_Producto_Lotes.LOTE_ID = INVT_Lotes_Ubicacion.LOTE_ID AND "
            f"((INVT_Lotes_Ubicacion.DOC_ID_CORP='{ne}') "
            #"((INVT_Lotes_Ubicacion.DOC_ID_CORP='A-0000062645-GIMPR') "
            "AND (INVT_Producto_Lotes.ENTRADA_TIPO='OC'))"
        )
        
        data = api_mba_sql(query)
        if data['status'] == 200:
            df = pd.DataFrame(data['data'])  
            df['product_id'] = df['PRODUCT_ID_CORP'].str.replace('-GIMPR','')
            df['doc_id']     = nota_entrega            
            df = df.rename(columns={
                'DOC_ID_CORP':'doc_id_corp',
                'LOTE_ID':'lote_id',
                'EGRESO_TEMP':'unidades',
                'FECHA_CADUCIDAD':'fecha_caducidad'
            })
            
            df = df[['doc_id_corp', 'doc_id','product_id','lote_id','fecha_caducidad','unidades']]
            
            # df['fecha_caducidad'] = df['fecha_caducidad'].str.slice(0,10)
            df['fecha_caducidad'] = df['fecha_caducidad'].astype('str').str.slice(0,10) 
            df['fecha_caducidad'] = pd.to_datetime(df['fecha_caducidad'], format='%d/%m/%Y', dayfirst=True)
            df = df[df['unidades']!=0] 
            return df.to_dict(orient='records')
        else:
            df = pd.DataFrame()
    
    except Exception as e:
        print(e)


def wms_ajuste_query_api(n_ajuste):
    
    # La variable 'n' no está siendo usada en la consulta. Asegúrate de que sea necesario.
    n = 'A-00000' + str(n_ajuste) + '-GIMPR'
    #Transferencia Egreso
    try:

        # Segunda consulta
        api_sql = api_mba_sql(
            "SELECT INVT_Lotes_Ubicacion.DOC_ID_CORP, INVT_Lotes_Ubicacion.PRODUCT_ID_CORP, INVT_Lotes_Ubicacion.LOTE_ID, "
            "INVT_Lotes_Ubicacion.EGRESO_TEMP, INVT_Lotes_Ubicacion.COMMITED, INVT_Lotes_Ubicacion.WARE_CODE_CORP, "
            "INVT_Lotes_Ubicacion.UBICACION, INVT_Producto_Lotes.Fecha_elaboracion_lote, INVT_Producto_Lotes.FECHA_CADUCIDAD "
            "FROM INVT_Lotes_Ubicacion, INVT_Producto_Lotes "
            "WHERE INVT_Lotes_Ubicacion.PRODUCT_ID_CORP = INVT_Producto_Lotes.PRODUCT_ID_CORP "
            "AND INVT_Producto_Lotes.LOTE_ID = INVT_Lotes_Ubicacion.LOTE_ID "
            f"AND ((INVT_Lotes_Ubicacion.DOC_ID_CORP='{n}') AND (INVT_Producto_Lotes.ENTRADA_TIPO='OC')) "
        )
        
        if api_sql['status'] == 200:
            data = pd.DataFrame(api_sql['data'])
            # data = pd.DataFrame(data, columns=['DOC_ID_CORP', 'PRODUCT_ID_CORP', 'LOTE_ID', 'EGRESO_TEMP', 'COMMITED', 'WARE_CODE_CORP', 'UBICACION', 'Fecha_elaboracion_lote', 'FECHA_CADUCIDAD']) if data else pd.DataFrame()
            data['product_id'] = list(map(lambda x:x[:-6], list(data['PRODUCT_ID_CORP'])))
            data['FECHA_CADUCIDAD'] = data['FECHA_CADUCIDAD'].str.slice(0,10)
            data['FECHA_ELABORACION_LOTE'] = data['FECHA_ELABORACION_LOTE'].str.slice(0,10)
            
            data['FECHA_CADUCIDAD'] = pd.to_datetime(data['FECHA_CADUCIDAD'], format='%d/%m/%Y', dayfirst=True)
            data['FECHA_ELABORACION_LOTE'] = pd.to_datetime(data['FECHA_ELABORACION_LOTE'], format='%d/%m/%Y', dayfirst=True)

        return data
        
    except Exception as e:
        print(e)


# TRAER TELEFONO DE CLIENTES
def whastapp_cliente_por_codigo(codigo_cliente):
    
    with connections['gimpromed_sql'].cursor() as cursor:
        
        cursor.execute(f"""
            SELECT CAST(WP AS CHAR) AS WP
            FROM warehouse.clientes
            WHERE CODIGO_CLIENTE = '{codigo_cliente}';"""
            )
        
        wp = cursor.fetchone()[0] 
        wp = wp.replace(' ', '')
        
        connections['gimpromed_sql'].close()
        return wp 
    
    
def email_cliente_por_codigo(codigo_cliente):
    
    with connections['gimpromed_sql'].cursor() as cursor:
        
        cursor.execute(f"""
            SELECT EMAIL, Email_Fiscal
            FROM warehouse.clientes
            WHERE CODIGO_CLIENTE = '{codigo_cliente}';"""
            )
        
        correo = cursor.fetchone() 
        
        email = []
        
        if correo[0]:
            e = correo[0].split(',')[0]
        
        elif not correo[0]:
            e = correo[1].split(',')[0]
        
        if e:
            email.append(e)
        else:
            email = None
            
        connections['gimpromed_sql'].close()
        return email
    
    
# Obtener todas las proformas
def lista_proformas_odbc():
    
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute("SELECT * FROM proformas")
        columns = [col[0] for col in cursor.description]
        proformas = [dict(zip(columns, row)) for row in cursor.fetchall()]
        proformas = pd.DataFrame(proformas)
        
        connections['gimpromed_sql'].close()
        return proformas


# Obtener una proforma por contrato_id
def proformas_por_contrato_id_odbc(contrato_id):
    
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(f"SELECT * FROM proformas WHERE contrato_id = '{contrato_id}'")
        columns = [col[0] for col in cursor.description]
        proformas = [dict(zip(columns, row)) for row in cursor.fetchall()]
        proformas = pd.DataFrame(proformas)
        
        connections['gimpromed_sql'].close()
        return proformas
    
    
# Obtener una datos picking por contrato_id -PARA CABECERA DE ANEXO
def datos_anexo(contrato_id): 
    
    # Anexo
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(
            f"""
            SELECT
                reservas_lote.CONTRATO_ID,
                reservas_lote.FECHA_PEDIDO,
                clientes.IDENTIFICACION_FISCAL,
                clientes.NOMBRE_CLIENTE,
                clientes.DIRECCION
            FROM
                warehouse.reservas_lote
            INNER JOIN
                clientes ON reservas_lote.CODIGO_CLIENTE = clientes.CODIGO_CLIENTE
            WHERE
                reservas_lote.CONTRATO_ID = '{contrato_id}'
            LIMIT 1;
            """
            )
            
        columns = [col[0] for col in cursor.description]
        anexo = [dict(zip(columns, row)) for row in cursor.fetchall()][0]
        
        connections['gimpromed_sql'].close()
        return anexo


# Obtener una datos picking por contrato_id -PARA LISTA DE PRODUCTOS DE ANEXO
def datos_anexo_product_list(contrato_id): 
    
    # Anexo
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(
            f"""
            SELECT                
                reservas_lote.PRODUCT_ID,
                productos.Nombre,
                productos.Unidad,
                productos.Marca,
                productos.Procedencia,
                productos.Reg_San,
                reservas_lote.LOTE_ID,
                reservas_lote.Fecha_elaboracion_lote,
                reservas_lote.FECHA_CADUCIDAD,
                reservas_lote.EGRESO_TEMP,
                reservas_lote.Price                
            FROM
                warehouse.reservas_lote
            INNER JOIN
                productos ON reservas_lote.PRODUCT_ID = productos.Codigo
            WHERE
                reservas_lote.CONTRATO_ID = '{contrato_id}';
            """
            )
        
        columns = [col[0] for col in cursor.description]
        anexo_product_list = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        connections['gimpromed_sql'].close()
        return anexo_product_list



# ESTRAER NÚMERO DE FACTURA
def extraer_numero_de_factura(fac):
    
    try:
        n_fac = fac.split('-')[1][6:]
        n_fac = str(int(n_fac))
        return n_fac
    except:
        return fac


def resporte_diferencia_mba_wms():
    
    def stock_cerezos_mba():
        with connections['gimpromed_sql'].cursor() as cursor:
            cursor.execute("SELECT PRODUCT_ID, LOTE_ID, OH2,  WARE_CODE, LOCATION FROM warehouse.stock_lote WHERE WARE_CODE = 'BCT' or WARE_CODE = 'CUC'")
            columns = [col[0] for col in cursor.description]
            data = [dict(zip(columns, row)) for row in cursor.fetchall()]
            data = pd.DataFrame(data)
            data['LOTE_ID'] = data['LOTE_ID'].str.replace('.','')
            data = data.groupby(by=['PRODUCT_ID','LOTE_ID','WARE_CODE','LOCATION'])['OH2'].sum().reset_index().sort_values(by='WARE_CODE')
            
            connections['gimpromed_sql'].close()
            return data
    
    def stock_cerezos_wms():
        data = pd.DataFrame(Existencias.objects.all().values(
            'product_id', 'lote_id', 'estado', 'ubicacion__bodega','unidades'
        ))
        data['lote_id'] = data['lote_id'].str.replace('.','')
        data = data.groupby(by=['product_id','lote_id','estado','ubicacion__bodega'])['unidades'].sum().reset_index()
        data['WARE_CODE_WMS'] = data.apply(lambda x: 'BCT' if x['estado'] == 'Disponible' else 'CUC', axis=1)
        data = data.rename(columns={
            'product_id':'PRODUCT_ID',
            'lote_id':'LOTE_ID',
            'unidades':'OH2_WMS',
            'ubicacion__bodega':'LOCATION_WMS'
        })
        data = data[['PRODUCT_ID','LOTE_ID','WARE_CODE_WMS','LOCATION_WMS','OH2_WMS']].sort_values(by='WARE_CODE_WMS')
        return data
    
    reporte = pd.merge(
        left  = stock_cerezos_mba(),
        right = stock_cerezos_wms(),
        on = ['PRODUCT_ID', 'LOTE_ID'],
        how='outer'
    )
    
    reporte['bodega'] = reporte['LOCATION'] == reporte['LOCATION_WMS']
    reporte = reporte[reporte['bodega']==False]
    reporte = reporte[['PRODUCT_ID', 'LOTE_ID', 'WARE_CODE', 'LOCATION', 'OH2', 'WARE_CODE_WMS', 'LOCATION_WMS', 'OH2_WMS']].fillna('')
    
    return reporte


def analisis_error_lote_data():
    
    def stock_sin_lote():
        stock_sin_lote = api_mba_sql(            
            """
                SELECT 
                    INVT_Ficha_Principal.PRODUCT_ID, 
                    INVT_Ficha_Principal.OH 
                FROM 
                    INVT_Ficha_Principal INVT_Ficha_Principal 
                WHERE (INVT_Ficha_Principal.INACTIVE=FALSE)
            """
        )
        
        if stock_sin_lote['status'] == 200:
            
            stock_sin_lote_df = pd.DataFrame(stock_sin_lote['data']) 
            stock_sin_lote_df = stock_sin_lote_df.groupby('PRODUCT_ID')['OH'].sum().reset_index()
            stock_sin_lote_df['OH'] = stock_sin_lote_df['OH'].astype('float')
            
            stock_sin_lote_df = stock_sin_lote_df[stock_sin_lote_df['PRODUCT_ID']!='ETIQUE']
            stock_sin_lote_df = stock_sin_lote_df[stock_sin_lote_df['PRODUCT_ID']!='MANTEN']
            stock_sin_lote_df = stock_sin_lote_df[stock_sin_lote_df['PRODUCT_ID']!='TRANS']
            
            return stock_sin_lote_df
        
        return pd.DataFrame()
    
    def stock_con_lote():
        with connections['gimpromed_sql'].cursor() as cursor:
            cursor.execute("SELECT PRODUCT_ID, LOTE_ID, OH, OH2, COMMITED FROM warehouse.stock_lote")
            connections['gimpromed_sql'].close()
            columns = [col[0] for col in cursor.description]
            data = [dict(zip(columns, row)) for row in cursor.fetchall()]
            data = pd.DataFrame(data)
            data['LOTE_ID'] = data['LOTE_ID'].str.replace('.','')
            data = data.groupby(by=['PRODUCT_ID','LOTE_ID']).sum().reset_index()
            data['OH'] = data['OH'].astype('int')
            data['OH2'] = data['OH2'].astype('int')
            data = data[data['OH2']!=0]
            return data
    
    def transferencia_en_curso():
        with connections['gimpromed_sql'].cursor() as cursor:
            cursor.execute("SELECT PRODUCT_ID, LOTE_ID, OH FROM warehouse.productos_transito")
            connections['gimpromed_sql'].close()
            columns = [col[0] for col in cursor.description]
            data = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            if data:
                data = pd.DataFrame(data)
                data['LOTE_ID'] = data['LOTE_ID'].str.replace('.','')
                data = data.groupby(by=['PRODUCT_ID','LOTE_ID']).sum().reset_index()
                data['OH'] = data['OH'].astype('int')
                data = data.rename(columns={'OH':'OH_TRANSF'})
                return data
            else:
                data = pd.DataFrame()
                data['PRODUCT_ID'] = ['-']
                data['LOTE_ID']    = ['-']
                data['OH_TRANSF'] = [0]
                return data
    
    stock_sin_lote_df = stock_sin_lote()
    stock_con_lote_df = stock_con_lote()
    transferencia_df  = transferencia_en_curso()
    
    # COMMITED
    commited_agrupado = stock_con_lote_df.copy() 
    commited_agrupado['COMMITED_NEGATIVO'] = commited_agrupado.apply(lambda x: 'SI' if x['COMMITED'] < 0 else 'NO', axis=1)
    commited_agrupado = commited_agrupado[commited_agrupado['COMMITED_NEGATIVO']=='SI'][['PRODUCT_ID','LOTE_ID','COMMITED_NEGATIVO']] 
    commited_agrupado_product = commited_agrupado.copy()
    commited_agrupado_product = commited_agrupado_product.drop_duplicates(subset='PRODUCT_ID')
    
    # TRANSFERENCIA AGURPADO
    transferencia_agrupado_df = transferencia_df.copy()
    transferencia_agrupado_df = transferencia_agrupado_df.groupby('PRODUCT_ID')['OH_TRANSF'].sum().reset_index()
    
    stock_agrupado = stock_con_lote_df.groupby('PRODUCT_ID')['OH2'].sum().reset_index()
    stock_agrupado = stock_agrupado.merge(transferencia_agrupado_df, on='PRODUCT_ID', how='left').fillna(0)
    stock_agrupado['OH2_MAS_TRANSF'] = stock_agrupado['OH2'] + stock_agrupado['OH_TRANSF']
    
    # REPORTE
    reporte = stock_sin_lote_df.merge(stock_agrupado, on='PRODUCT_ID', how='left').fillna(0)
    reporte['error'] = reporte['OH'] != reporte['OH2_MAS_TRANSF']  # reporte['OH2']
    reporte = reporte[reporte['error'] == True]
    reporte['diff'] = reporte['OH'] - reporte['OH2_MAS_TRANSF']  # reporte['OH2']
    
    # ADD COMMITED A REPORTE
    if not commited_agrupado_product.empty:
        # reporte = reporte.merge(commited_agrupado_product, on='PRODUCT_ID', how='left')
        reporte = reporte.merge(commited_agrupado_product, on='PRODUCT_ID', how='outer')
        reporte['COMMITED_NEGATIVO'] = reporte['COMMITED_NEGATIVO'].fillna('NO')
        
    else:
        reporte['COMMITED_NEGATIVO'] = 'NO'
    
    reporte = reporte.fillna(0)
    # print(reporte, len(reporte))
    if reporte.empty:
        return None
    
    productos = productos_odbc_and_django()[['product_id','Nombre','Marca']]
    productos = productos.rename(columns={'product_id':'PRODUCT_ID'})
    reporte = reporte.merge(productos, on='PRODUCT_ID',how='left') 
    lotes_list = reporte['PRODUCT_ID'].unique()
    lotes = stock_con_lote().copy()
    lotes = lotes[lotes['PRODUCT_ID'].isin(lotes_list)]
    lotes = lotes.merge(transferencia_df, on=['PRODUCT_ID', 'LOTE_ID'], how='left').fillna(0)
    
    if not commited_agrupado.empty:
        lotes = lotes.merge(commited_agrupado, on=['PRODUCT_ID', 'LOTE_ID'], how='left')
        lotes['COMMITED_NEGATIVO'] = lotes['COMMITED_NEGATIVO'].fillna('NO')
    else:
        lotes['COMMITED_NEGATIVO'] = 'NO'
    
    lotes['diff'] = lotes['OH'] - lotes['OH2']
    lotes['error'] = lotes['OH'] != lotes['OH2']
    
    return {
        'reporte':de_dataframe_a_template(reporte),
        'lotes':de_dataframe_a_template(lotes)
    }


def analisis_error_lote_data_v2():
    
    def diff_quantity_available():
        with connections['gimpromed_sql'].cursor() as cursor:
            cursor.execute("SELECT PRODUCT_ID, LOTE_ID, QUANTITY, AVAILABLE, LOCATION FROM warehouse.stock_lote")
            connections['gimpromed_sql'].close()
            columns = [col[0] for col in cursor.description]
            data = [dict(zip(columns, row)) for row in cursor.fetchall()]
            data = pd.DataFrame(data)
            data['LOTE_ID'] = data['LOTE_ID'].str.replace('.','')
            
            data = data.groupby(by=['PRODUCT_ID','LOTE_ID']).agg({
                'QUANTITY': 'sum',
                'AVAILABLE': 'sum',
                'LOCATION': lambda x: ', '.join(x.dropna().astype(str).unique()),
                #'WARE_CODE': lambda x: ', '.join(x.dropna().astype(str).unique()),
            }).reset_index()
            
            data['DIFF_AVAILABLE'] = data['QUANTITY'] - data['AVAILABLE']
            data['error_filter'] = data['QUANTITY'] != data['AVAILABLE']
            data = data[data['error_filter'] == True]
            data['error'] = 'diff_qty_ava'
            data = data[['PRODUCT_ID', 'LOTE_ID', 'QUANTITY', 'AVAILABLE', 'DIFF_AVAILABLE', 'LOCATION', 'error']]
            return data

    def commited_negativo():
        with connections['gimpromed_sql'].cursor() as cursor:
            cursor.execute("SELECT PRODUCT_ID, LOTE_ID, COMMITED, LOCATION FROM warehouse.stock_lote")
            connections['gimpromed_sql'].close()
            columns = [col[0] for col in cursor.description]
            data = [dict(zip(columns, row)) for row in cursor.fetchall()]
            data = pd.DataFrame(data)
            data['LOTE_ID'] = data['LOTE_ID'].str.replace('.','')
            
            data = data.groupby(by=['PRODUCT_ID','LOTE_ID']).agg({
                'COMMITED':'sum',
                'LOCATION': lambda x: ', '.join(x.dropna().astype(str).unique()),
                #'WARE_CODE': lambda x: ', '.join(x.dropna().astype(str).unique()),
                }).reset_index()
            
            data = data[data['COMMITED'] < 0]
            data['error'] = 'commited_negativo'
            return data

    diff_available_df = diff_quantity_available() 
    commited_negativo_df = commited_negativo() 
    reporte_lotes = pd.concat([diff_available_df, commited_negativo_df]).fillna('')
    cols_num = ['QUANTITY', 'AVAILABLE', 'DIFF_AVAILABLE', 'COMMITED']
    reporte_lotes[cols_num] = reporte_lotes[cols_num].apply(pd.to_numeric, errors='coerce')
    
    df_grouped_product_lote = reporte_lotes.groupby(['PRODUCT_ID', 'LOTE_ID'], as_index=False).agg({
        'QUANTITY': 'sum',
        'AVAILABLE': 'sum',
        'DIFF_AVAILABLE': 'sum',
        'COMMITED': 'sum',
        'LOCATION': lambda x: ', '.join(x.dropna().astype(str).unique()),
        #'WARE_CODE': lambda x: ', '.join(x.dropna().astype(str).unique()),
        'error': lambda x: ', '.join(x.dropna().astype(str).unique())
    }) 
    
    df_grouped_product_lote['error_commited'] = df_grouped_product_lote['error'].str.contains('commited_negativo')
    df_grouped_product_lote['error_available'] = df_grouped_product_lote['error'].str.contains('diff_qty_ava')
    
    if df_grouped_product_lote.empty:
        return None
    
    else:
        prods = productos_odbc_and_django()[['product_id','Nombre','Marca']]
        df_grouped_product_lote = pd.merge(left=df_grouped_product_lote, right=prods, left_on='PRODUCT_ID', right_on='product_id', how='left')
        return {
            'lotes':de_dataframe_a_template(df_grouped_product_lote)
        }


def actualizar_data_error_lote():
    data = analisis_error_lote_data()
    # print(data)
    if data is None:
        ErrorLoteReporte.objects.all().delete()
        ErrorLoteDetalle.objects.all().delete()
        adm_table = AdminActualizationWarehaouse.objects.get(table_name='error_lote')
        adm_table.datetime = datetime.now()
        adm_table.mensaje = 'No se encuntran lotes con error'
        adm_table.save()
    
    elif data is not None:
        # reporte
        ErrorLoteReporte.objects.all().delete()
        reporte = data['reporte']
        obj_list = []
        for i in reporte:
            obj = ErrorLoteReporte(
                product_id = i.get('PRODUCT_ID'),
                nombre = i.get('Nombre'),
                marca = i.get('Marca'),
                unds_total = i.get('OH'),
                unds_lotes = i.get('OH2'),
                unds_transf = i.get('OH_TRANSF'),
                unds_total_mas_transf = i.get('OH2_MAS_TRANSF'),
                unds_diff = i.get('diff'),
                commited_negativo = i.get('COMMITED_NEGATIVO')
            )
            
            obj_list.append(obj)

        ErrorLoteReporte.objects.bulk_create(obj_list)
        
        # lotes
        ErrorLoteDetalle.objects.all().delete()
        lotes = data['lotes']
        obj_lotes = []
        for j in lotes:
            obj_l = ErrorLoteDetalle(
                product_id = j.get('PRODUCT_ID'),
                lote_id = j.get('LOTE_ID'),
                oh = j.get('OH'),
                oh2 = j.get('OH2'),
                oh_transf = j.get('OH_TRANSF'),
                diff = j.get('diff'),
                commited_negativo = j.get('COMMITED_NEGATIVO'),
                error = j.get('error')
            )
            
            obj_lotes.append(obj_l)
        ErrorLoteDetalle.objects.bulk_create(obj_lotes)
        
        adm_table = AdminActualizationWarehaouse.objects.get(table_name='error_lote')
        adm_table.datetime = datetime.now()
        adm_table.mensaje = 'Actualizado correctamente'
        adm_table.save()


def actualizar_data_error_lote_v2():
    data = analisis_error_lote_data_v2() 

    if data is None:
        ErrorLoteV2.objects.all().delete()
        adm_table = AdminActualizationWarehaouse.objects.get(table_name='error_lote_v2')
        adm_table.datetime = datetime.now()
        adm_table.mensaje = 'No se encuntran lotes con error'
        adm_table.save()
    
    elif data is not None:
        # reporte
        ErrorLoteV2.objects.all().delete()

        lotes = data['lotes']
        obj_lotes = []
        for j in lotes:
            
            cerezos = {'CN4', 'CN5', 'CN6', 'CN7', 'CUC'}
            andagoya = {'AN1', 'AN4', 'BN1', 'BN2', 'BN3', 'BN4', 'CUA'}
            
            # Dividir y crear conjunto de ubicaciones
            locations = set(loc.strip() for loc in str(j.get('LOCATION', '')).split(','))
            
            # Verificar intersecciones
            has_cerezos = bool(locations & cerezos)
            has_andagoya = bool(locations & andagoya)
            
            # Determinar bod
            if has_cerezos and has_andagoya:
                bod = 'BCT, BAN'
            elif has_cerezos:
                bod = 'BCT'
            elif has_andagoya:
                bod = 'BAN'
            else:
                bod = 'N/U'
            
            obj_l = ErrorLoteV2(
                product_id = j.get('PRODUCT_ID'),
                nombre = j.get('Nombre', '-'),
                marca = j.get('Marca', '-'),
                lote_id = j.get('LOTE_ID'),
                ubicacion = j.get('LOCATION'),
                bodega = bod, #j.get('WARE_CODE', '-'),
                quantity = j.get('QUANTITY'),
                available = j.get('AVAILABLE'),
                diff_available = j.get('DIFF_AVAILABLE'),
                commited = j.get('COMMITED'),
                error = j.get('error'),
                error_commited = j.get('error_commited'),
                error_available = j.get('error_available'),
            )
            
            obj_lotes.append(obj_l)
        ErrorLoteV2.objects.bulk_create(obj_lotes)
        
        adm_table = AdminActualizationWarehaouse.objects.get(table_name='error_lote_v2')
        adm_table.datetime = datetime.now()
        adm_table.mensaje = 'Actualizado correctamente'
        adm_table.save()

@csrf_exempt
def cambiar_conexion_de_warehouse(request):
    
    # from api_mba.tablas_warehouse import odbc_actualizar_clientes_warehouse    
    # odbc_actualizar_clientes_warehouse()
    # return HttpResponse('ok')
    
    if request.method == 'POST':
        data = json.loads(request.body)
        table_name = data.get("table_name", None)
        if table_name:
            nueva_conexion = data.get("nueva_conexion", None)
            if nueva_conexion:
                adm = AdminActualizationWarehaouse.objects.get(table_name=table_name)
                adm.conexion = nueva_conexion
                adm.save()
                return JsonResponse({
                    'tipo':'ok'
                })
            return JsonResponse({
                'tipo':'fail'
            })
        return JsonResponse({
            'tipo':'fail'
        })


### PICKING ESTADISTICAS 
estado_picking_query = (
    EstadoPicking.objects
    .filter(estado='FINALIZADO').values(
        'n_pedido',
        'bodega',
        'codigo_cliente',
        'tipo_cliente',
        'cliente',
        'detalle',
        'fecha_creado',
        'fecha_actualizado',
        'user__user__username',
    )
).order_by('-n_pedido')[:200]


def datos_reserva_by_contrato_id(contrato_id) -> dict:
    """
    Obtener datos de cabecera de reserva en MBA por contrato_id
    """
    query = f"""
        SELECT 
            pp.CONTRATO_ID, 
            pp.FECHA_PEDIDO, 
            pp.HORA_LLEGADA,
            pp.WARE_CODE, 
            pp.Entry_by,
            fp.CODIGO_CLIENTE, 
            fp.NOMBRE_CLIENTE, 
            fp.CLIENT_TYPE
        FROM 
            CLNT_Pedidos_Principal pp,
            CLNT_Pedidos_Detalle pd,
            CLNT_Ficha_Principal fp
        WHERE 
            pp.CONTRATO_ID_CORP = pd.CONTRATO_ID_CORP
            AND fp.CODIGO_CLIENTE = pp.CLIENT_ID
            AND pd.TIPO_DOCUMENTO = 'PE'
            AND TRIM(pp.CONTRATO_ID) = '{contrato_id}'
        ORDER BY pp.CONTRATO_ID DESC
    """
    
    reserva = api_mba_sql(query)
    
    if reserva['status'] == 200:
        try:
            data = reserva['data'][0]
            fecha_pedido = str(data['FECHA_PEDIDO'])[:10]   # slicing correcto
            hora_llegada = str(data['HORA_LLEGADA'])
            creado_mba_str = f"{fecha_pedido} {hora_llegada}"            
            try:
                creado_mba = datetime.strptime(creado_mba_str, '%d/%m/%Y %H:%M:%S')
            except ValueError:
                creado_mba = datetime.strptime(creado_mba_str, '%d/%m/%Y %H:%M')

            data['creado_mba'] = creado_mba
            return data
        except Exception as e:
            print(e)
            return {}
    else:
        return {}


def datos_pedido_by_contrato_id(contrato_id) -> list:
    """
    Obtener datos de detalle de reserva en MBA por contrato_id
    """
    query = f"""
        SELECT 
            pp.CONTRATO_ID,             
            pd.PRODUCT_ID, 
            pd.QUANTITY
        FROM 
            CLNT_Pedidos_Principal pp,
            CLNT_Pedidos_Detalle pd
        WHERE 
            pp.CONTRATO_ID_CORP = pd.CONTRATO_ID_CORP
            AND pd.TIPO_DOCUMENTO = 'PE'
            AND pd.PRODUCT_ID <> 'MANTEN'
            AND TRIM(pp.CONTRATO_ID) = '{contrato_id}'
        ORDER BY pp.CONTRATO_ID DESC
    """
    reserva = api_mba_sql(query)
    
    if reserva['status'] == 200:
        return reserva['data']
    
    return []


def datos_facturacion_by_contrato_id(contrato_id) -> dict:
    """
    Obtener datos de facturación en MBA por contrato_id
    """
    query = f"""
        SELECT DISTINCT
            f.CODIGO_FACTURA,
            f.FECHA_FACTURA,
            f.HORA_FACTURA,
            f.NUMERO_PEDIDO_SISTEMA
        FROM 
            CLNT_Factura_Principal f
        INNER JOIN 
            INVT_Producto_Movimientos pm
            ON f.CODIGO_FACTURA = pm.DOC_ID_CORP2
        WHERE 
            pm.CONFIRM = TRUE
            AND pm.I_E_SIGN = '-'
            AND pm.ADJUSTMENT_TYPE = 'FT'
            AND TRIM(f.NUMERO_PEDIDO_SISTEMA) = '{contrato_id}';
        """
        
    facturas = api_mba_sql(query)
    
    if facturas['status'] == 200:
        try:
            data = facturas['data'][0] 
            fecha_factura_str = str(data['FECHA_FACTURA'])[:10]
            hora_factura_str = str(data['HORA_FACTURA'])
            fecha_factura_completa_str = f"{fecha_factura_str} {hora_factura_str}" 
            try:
                fecha_factura = datetime.strptime(fecha_factura_completa_str, '%d/%m/%Y %H:%M:%S')
            except ValueError:
                fecha_factura = datetime.strptime(fecha_factura_completa_str, '%d/%m/%Y %H:%M')
            data['fecha_factura'] = fecha_factura
            return data
        except Exception as e:
            print(e)
            return {}
    else:
        return {}


def obtener_data_picking_estadistica(request):

    for i in estado_picking_query:
        
        contrato_id = i['n_pedido']
        contrato_id = str(contrato_id).strip().split('.')[0] if '.' in str(contrato_id) else str(contrato_id)
        reserva = datos_reserva_by_contrato_id(contrato_id)
        
        PickingEstadistica.objects.create(
            contrato_id = contrato_id,
            creado_mba = reserva.get('creado_mba') if reserva else None,
            bodega = reserva.get('WARE_CODE') if reserva else '',
            creado_por_mba = reserva.get('ENTRY_BY') if reserva else None,
            codigo_cliente = reserva.get('CODIGO_CLIENTE') if reserva else '',
            nombre_cliente = reserva.get('NOMBRE_CLIENTE') if reserva else '',
            tipo_cliente = reserva.get('CLIENT_TYPE') if reserva else '',
            inicio_picking = i.get('fecha_creado'),
            fin_picking = i.get('fecha_actualizado'),
            usuario_picking = i.get('user__user__username'),
        )
        
        actualizar_datos_calculo_pedidos_picking_estadisticas()
        actualizar_datos_usuario_mba()
        actualizar_datos_facturacion()
        
        time.sleep(2)  # Simular tiempo de procesamiento por cada registro
    
    return HttpResponse("OK")


def actualizar_datos_calculo_pedidos_picking_estadisticas():
    estadisticas = PickingEstadistica.objects.filter(datos_completos=False)

    for e in estadisticas:
        data_mba = datos_pedido_by_contrato_id(e.contrato_id)
        prod = productos_odbc_and_django()[[
            'product_id', 'Unidad_Empaque', 'vol_m3', 'Peso'
        ]]
        prod['Unidad_Empaque'] = (
            pd.to_numeric(prod['Unidad_Empaque'], errors='coerce')
            .replace(0, 0.0025)
            .fillna(0.0025)
        )

        data = pd.DataFrame(data_mba)

        if data.empty:
            continue

        # Merge seguro
        data = data.merge(
            prod,
            left_on='PRODUCT_ID',
            right_on='product_id',
            how='left'
        )

        # Conversión segura de tipos
        for col in ['Unidad_Empaque', 'vol_m3', 'Peso', 'QUANTITY']:
            data[col] = pd.to_numeric(data[col], errors='coerce')

        # Evitar división por cero
        data['Unidad_Empaque'] = data['Unidad_Empaque'].replace(0, np.nan)

        # Cálculos
        data['Cartones'] = data['QUANTITY'] / data['Unidad_Empaque']

        items = data['PRODUCT_ID'].nunique()

        total_volumen = (
            data['vol_m3'] * data['Cartones']
        ).fillna(0).sum()

        total_peso = (
            data['Peso'] * data['QUANTITY']
        ).fillna(0).sum()

        # Guardar resultados
        e.total_items = items
        e.total_volumen_m3 = total_volumen
        e.total_peso_kg = total_peso
        # e.save(update_fields=[
        #     'total_items',
        #     'total_volumen_m3',
        #     'total_peso_kg',
        #     'datos_completos'
        # ])
        e.save()


def actualizar_datos_usuario_mba():
    
    def email_by_entry_by(entry_by):
        with connections['gimpromed_sql'].cursor() as cursor:
            cursor.execute(f"""
                SELECT 
                    pp.Entry_by,
                    um.mail AS email_usuario
                FROM 
                    warehouse.pedidos pp
                LEFT JOIN 
                    warehouse.user_mba um
                    ON TRIM(pp.Entry_by) = TRIM(um.codigo_usuario)
                WHERE 
                    TRIM(pp.Entry_by) = '{entry_by}';
            """
            )
            
            email = cursor.fetchone()
            connections['gimpromed_sql'].close()
            if email:
                return email[1]
            return None
    
    estadisticas = PickingEstadistica.objects.filter(datos_completos=False)
    for e in estadisticas:
        if e.creado_por_mba and not e.creado_por_mba_username:
            email = email_by_entry_by(e.creado_por_mba) 
            try:
                username = User.objects.filter(email=email).first()
            except Exception as ex:
                username = '' 
            e.creado_por_mba_username = username
            # e.save(update_fields=['creado_por_mba_username'])
            e.save()


def actualizar_datos_facturacion():
    
    estadisticas = PickingEstadistica.objects.filter(datos_completos=False)

    for e in estadisticas:
        data_facturacion = datos_facturacion_by_contrato_id(e.contrato_id)
        if not data_facturacion:
            continue

        e.numero_factura = data_facturacion.get('CODIGO_FACTURA', '')
        e.fecha_facturacion = data_facturacion.get('fecha_factura', None)
        # e.save(update_fields=[
        #     'numero_factura',
        #     'fecha_facturacion',
        # ])
        e.save()


def actualizar_picking_stadisticas_all(request):
    
    print('Actualizando Picking Estadisticas')
    actualizar_datos_calculo_pedidos_picking_estadisticas()
    actualizar_datos_usuario_mba()
    actualizar_datos_facturacion()
    
    return HttpResponse("OK")