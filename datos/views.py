# DB
from django.db import connections

# Shortcuts
from django.shortcuts import render, redirect

# Urls
from django.urls import reverse_lazy

# Messages
from django.contrib import messages

# Generic View
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView
from django.views.generic import TemplateView

# Models
from datos.models import Marca, Product, MarcaImportExcel, Vehiculos
from datos.models import TimeStamp
from etiquetado.models import EtiquetadoAvance

# Autentication
from django.contrib.auth.mixins import LoginRequiredMixin

# Pandas
import pandas as pd
import numpy as np

# Form
from datos.forms import ProductForm


# SSH DATA TUNEL
import pymysql
import logging
import sshtunnel
from sshtunnel import SSHTunnelForwarder

# Pyodbc
import pyodbc


# Json
import json


# HTTP
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse

# Time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# Mysql connector
import mysql.connector


### PERMISOS PERSONALIZADOS
from users.models import UserPerfil
from django.contrib.auth.models import User


### PERMISO PERSONALIZADO
from functools import wraps

# rexex
import re

# CONECIONES A MBA
# cnx_odbc_mba     = pyodbc.connect('DSN=mba3;PWD=API')

# # DB WAREHOUSE
# cnx_db_warehouse = mysql.connector.connect(
#     host="172.16.28.102",
#     user="standard",
#     passwd="gimpromed",
#     database="warehouse"
# )



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
    

class Inicio(LoginRequiredMixin, TemplateView):
    template_name = 'inicio.html'
    


class MarcaImportExcelCreateView(CreateView):
    model = MarcaImportExcel
    fields = '__all__'
    template_name = 'datos/marcas_import.html'
    success_url = reverse_lazy('marcas_list')



def tabla_productos():
    ''' Colusta de productos '''
    # Leer base de datos y retornar lista de diccionarios
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute("SELECT Codigo, Nombre, Marca, Unidad_Empaque FROM productos")
        columns = [col[0] for col in cursor.description]
        products = [ # Lista de diccionarios
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        # Unir datos con pandas dataframes
        # Tabla productos de base de datos
        p = pd.DataFrame(products)
        p = p.rename(columns={'Codigo':'PRODUCT_ID'})

        # Excel consolidado
        ope = pd.read_excel('Z:/GIM-OP (Operaciones)/datos_product_operaciones.xlsx')
        ope = ope[[
            'PRODUCT_ID',
            'Marca2',
            'Largo(m)',
            'Ancho(m)',
            'Alto(m)',
            'PesoBruto(kg)',
            'T C/M 1 P',
            'T C/M 2 P',
            'T C/M 3 P',
            'M3/CAJA']]

        # Unir columnas
        p = p.merge(ope, on='PRODUCT_ID', how='left')
        p = p.fillna(0)
        #p.to_excel('Z:/GIM-OP (Operaciones)/datos_product.xlsx')
        p = p.to_dict('records')
        # print(p)

        # Crear lista de tuplas para inyectar en sql
        lista_productos = []
        pk = 0

        for i in p:

            pk += 1
            cod = i.get('PRODUCT_ID')
            nom = i.get('Nombre')
            mar = i.get('Marca')

            uem = i.get('Unidad_Empaque')
            lar = i.get('Largo(m)')
            anc = i.get('Ancho(m)')
            alt = i.get('Alto(m)')
            vol = i.get('M3/CAJA')
            pes = i.get('PesoBruto(kg)')
            t1p = i.get('T C/M 1 P')
            t2p = i.get('T C/M 2 P')

            t3p = i.get('T C/M 3 P')
            ma2 = i.get('Marca2')

            # Crea una tupla de valores por cada diccionario
            prod = (pk, cod, nom, mar, uem, alt, anc, lar, pes, t1p, t2p, vol, t3p, ma2)

            # Añade la tupla a una lista
            lista_productos.append(prod)
        #print(lista_productos)

    return lista_productos


def productos_odbc_and_django():
    with connections['gimpromed_sql'].cursor() as cursor:
        #cursor.execute("SELECT Codigo, Nombre, Unidad, Marca, Unidad_Empaque, Unidad_Box, Inactivo FROM productos")
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

        p = pd.DataFrame(Product.objects.all().values())

        products = products.merge(p, on='product_id', how='left')

    return products


def productos(request):

    if request.method == 'GET':

        context = {
            'products': Product.objects.all().order_by('marca2')
        }

    elif request.method == 'POST':

        with connections['default'].cursor() as cursor:

            prod = tabla_productos()
            cursor.executemany(
                # INSERTAR
                #"INSERT INTO datos_product (id, product_id, description, marca, unidad_empaque, alto, ancho, largo, peso, t_etiq_1p, t_etiq_2p, volumen, t_etiq_3p, marca2) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", prod
                # REEMPLAZAR O ACTULIZAR
                "REPLACE INTO datos_product (id, product_id, description, marca, unidad_empaque, alto, ancho, largo, peso, t_etiq_1p, t_etiq_2p, volumen, t_etiq_3p, marca2) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", prod
                )

        context = {
            'products': Product.objects.all().order_by('marca2')
        }

    return render(request, 'datos/products_list.html', context)


def marcas_excel(): #request

    marcas = pd.read_excel('media/marcas_excel_import/marcas.xlsx', header=None)

    pk = 0
    marcas_import = []

    for i in range(len(marcas)):
        pk += 1
        m   = marcas.iloc[i][0]
        d   = marcas.iloc[i][1]
        marcas_tupla = (pk, m, d)
        marcas_import.append(marcas_tupla)

    return marcas_import



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


def cargar_marcas_excel(request): #request

    if request.method == 'GET':

        context = {
            'marcas': Marca.objects.all().order_by('marca')
        }

    elif request.method == 'POST':

        with connections['default'].cursor() as cursor:

            marcas = marcas_excel()
            cursor.executemany(
                ### INSERTAR
                #"INSERT INTO datos_product (id, marca, description) VALUES (%s,%s,%s)", marcas
                ### REEMPLAZAR O ACTULIZAR
                "REPLACE INTO datos_marca (id, marca, description) VALUES (%s,%s,%s)", marcas
                )

        context = {
            'marcas':Marca.objects.all().order_by('marca')
        }

    return render(request, 'datos/marcas_list.html', context)


# SSH DATA TUNEL
ssh_host = '10.10.3.4'
ssh_username = 'root'
ssh_password = 'Gimcen2021'
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
    
    df = run_query("SELECT T.PRODUCT_ID, T.ANUAL, R.rpm, A.F_ACUMULADA FROM (SELECT PRODUCT_ID, SUM(QUANTITY) as ANUAL FROM consumo_anual GROUP BY PRODUCT_ID) AS T "
                    "LEFT JOIN alertas_reservas R ON T.PRODUCT_ID = R.PRODUCT_ID LEFT JOIN analisis_abc A on R.PRODUCT_ID = A.PRODUCT_ID;")

    # df = run_query("SELECT product_id, sum(quantity) as anual FROM gimpromed_api.consumo_anual group by product_id;")
    
    mysql_disconnect()
    close_ssh_tunnel()

    return df


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



def etiquetado_fun():
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

    return print('etiquetado-fun')


def etiquetado_ajax(request):

    etiquetado_fun()

    return HttpResponseRedirect('/etiquetado/stock')



def importaciones_en_transito_odbc_insert_warehouse():
    
    try:
        # currentTimeDate = datetime.now() - relativedelta(days=15)
        # TwoWeekTime = currentTimeDate.strftime('%d-%m-%Y')
    
        # MBA ODBC
        cnx_odbc_mba     = pyodbc.connect('DSN=mba3;PWD=API')
        cursor_odbc_mba  = cnx_odbc_mba.cursor()
        
        cursor_odbc_mba.execute(
            "SELECT CLNT_Pedidos_Principal.CONTRATO_ID, PROV_Ficha_Principal.VENDOR_NAME, CLNT_Pedidos_Detalle.PRODUCT_ID, CLNT_Pedidos_Detalle.QUANTITY, CLNT_Pedidos_Principal.FECHA_ENTREGA, CLNT_Pedidos_Principal.MEMO "
            "FROM CLNT_Pedidos_Detalle CLNT_Pedidos_Detalle, CLNT_Pedidos_Principal CLNT_Pedidos_Principal, PROV_Ficha_Principal PROV_Ficha_Principal "
            "WHERE CLNT_Pedidos_Detalle.CONTRATO_ID_CORP = CLNT_Pedidos_Principal.CONTRATO_ID_CORP AND "
            "CLNT_Pedidos_Principal.CLIENT_ID_CORP = PROV_Ficha_Principal.CODIGO_PROVEEDOR_EMPRESA AND (CLNT_Pedidos_Principal.PEDIDO_CERRADO=false) AND "
            "(CLNT_Pedidos_Principal.CONFIRMED=false) AND (CLNT_Pedidos_Principal.VOID=false))"
        )
        
        imp_transito = cursor_odbc_mba.fetchall()
        
        # Delete
        # DB WAREHOUSE
        cnx_db_warehouse = mysql.connector.connect(
            host="172.16.28.102",
            user="standard",
            passwd="gimpromed",
            database="warehouse"
        )
        
        cursor_db_warehouse = cnx_db_warehouse.cursor()
        cursor_db_warehouse.execute("DELETE FROM imp_transito")
        cnx_db_warehouse.commit()
        
        sql_insert = """INSERT INTO imp_transito (CONTRATO_ID, VENDOR_NAME, PRODUCT_ID, QUANTITY, FECHA_ENTREGA, MEMO) VALUES (%s, %s, %s, %s, %s, %s)"""
        data_transito = [list(rows) for rows in imp_transito]
        cursor_db_warehouse.executemany(sql_insert, data_transito)
        cnx_db_warehouse.commit()
        
        print('Importaciones Warehouse Actualizados')
    except Exception as e:
        print(e)
    
    finally:
        cursor_odbc_mba.close()
        cursor_db_warehouse.close()



def actulizar_facturas_warehouse():

    actualizacion_stocklote = pd.DataFrame(TimeStamp.objects.all().values())
    actualizacion_stocklote = list(actualizacion_stocklote['actulization_stoklote'])
    actualizacion_stocklote_list = []
    for i in actualizacion_stocklote:
        if i != '':
            actualizacion_stocklote_list.append(i)
    actualizacion_stocklote_ultimo = actualizacion_stocklote_list[-1][:-7]
    actualizacion_stocklote_ultimo = datetime.strptime(actualizacion_stocklote_ultimo, '%Y-%m-%d %H:%M:%S')
    # ACTULIZACIÓN FACTURAS
    actulizacion_facturas = pd.DataFrame(TimeStamp.objects.all().values())
    actulizacion_facturas = list(actulizacion_facturas['actulization_facturas'])
    actulizacion_facturas_list = []
    for i in actulizacion_facturas:
        if i != '':
            actulizacion_facturas_list.append(i)
    actulizacion_facturas_ultimo = actulizacion_facturas_list[-1][:-7]
    actulizacion_facturas_ultimo = datetime.strptime(actulizacion_facturas_ultimo, '%Y-%m-%d %H:%M:%S')

    aho = datetime.now()
    ul_stocklote = aho - actualizacion_stocklote_ultimo
    ul_factura = aho - actulizacion_facturas_ultimo
    ul_stocklote = pd.Timedelta(ul_stocklote).total_seconds()
    ul_factura = pd.Timedelta(ul_factura).total_seconds()

    if ul_factura > 60 or ul_stocklote > 60:
        ### ACTUALIZAR FACTURAS
        from dateutil.relativedelta import relativedelta
        currentTimeDate = datetime.now() - relativedelta(days=35)
        OneMonthTime = currentTimeDate.strftime('%d-%m-%Y')
        ## LEER TABLA FACTURAS MBA
        cnxn = pyodbc.connect('DSN=mba3;PWD=API')
        cursorODBC = cnxn.cursor()
        cursorODBC.execute(
                    "SELECT CLNT_Factura_Principal.CODIGO_FACTURA, CLNT_Factura_Principal.FECHA_FACTURA, "
                    "CLNT_Ficha_Principal.NOMBRE_CLIENTE, INVT_Ficha_Principal.PRODUCT_ID, "
                    "INVT_Ficha_Principal.PRODUCT_NAME, INVT_Ficha_Principal.GROUP_CODE, INVT_Producto_Movimientos.QUANTITY, CLNT_Factura_Principal.NUMERO_PEDIDO_SISTEMA "
                    "FROM CLNT_Factura_Principal CLNT_Factura_Principal, CLNT_Ficha_Principal CLNT_Ficha_Principal, INVT_Ficha_Principal INVT_Ficha_Principal, INVT_Producto_Movimientos INVT_Producto_Movimientos "
                    "WHERE INVT_Ficha_Principal.PRODUCT_ID_CORP = INVT_Producto_Movimientos.PRODUCT_ID_CORP AND "
                    "CLNT_Factura_Principal.CODIGO_CLIENTE = CLNT_Ficha_Principal.CODIGO_CLIENTE AND CLNT_Factura_Principal.CODIGO_FACTURA = INVT_Producto_Movimientos.DOC_ID_CORP2 "
                    "AND ((INVT_Producto_Movimientos.CONFIRM=TRUE And INVT_Producto_Movimientos.CONFIRM=TRUE) AND (INVT_Producto_Movimientos.I_E_SIGN='-') "
                    "AND (INVT_Producto_Movimientos.ADJUSTMENT_TYPE='FT') AND (CLNT_Factura_Principal.ANULADA=FALSE)) AND  FECHA_FACTURA >='"+OneMonthTime+"'"
                )
        facturas_consulta = cursorODBC.fetchall()
        ## INSERTAR TABLA FACTURAS WAREHOUSE
        coneccion = mysql.connector.connect(
            host="172.16.28.102",
            user="standard",
            passwd="gimpromed",
            database="warehouse"
        )
        cn = coneccion.cursor()
        ## BORRAR DATOS ACTUALES DE FACTURAS WAREHOUSE
        cn.execute("DELETE FROM facturas")
        coneccion.commit()
        ## INSERTAR NUEVOS DATOS DE FACTURAS EN WAREHOUSE
        sql_insert = """INSERT INTO facturas (CODIGO_FACTURA,FECHA_FACTURA,NOMBRE_CLIENTE,PRODUCT_ID,PRODUCT_NAME,GROUP_CODE,QUANTITY,NUMERO_PEDIDO_SISTEMA) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"""
        data_facturas = [list(rows) for rows in facturas_consulta]
        cn.executemany(sql_insert, data_facturas)
        coneccion.commit()

        time = str(datetime.now())
        TimeStamp.objects.create(actulization_facturas=time)
    else:
        pass

    return None



def actualizar_facturas_odbc():
    # DB MBA
    cnx_odbc_mba     = pyodbc.connect('DSN=mba3;PWD=API')

    # DB WAREHOUSE
    cnx_db_warehouse = mysql.connector.connect(
        host="172.16.28.102",
        user="standard",
        passwd="gimpromed",
        database="warehouse"
    )
    
    currentTimeDate = datetime.now() - relativedelta(days=90)
    OneMonthTime = currentTimeDate.strftime('%d-%m-%Y')
    
    try:
        # CONECCIÓN ODBC
        cursorOdbc = cnx_odbc_mba.cursor()
        
        # SELECT FACTURAS ODBC
        cursorOdbc.execute(
            "SELECT CLNT_Factura_Principal.CODIGO_FACTURA, CLNT_Factura_Principal.FECHA_FACTURA, "
            "CLNT_Ficha_Principal.NOMBRE_CLIENTE, INVT_Ficha_Principal.PRODUCT_ID, "
            "INVT_Ficha_Principal.PRODUCT_NAME, INVT_Ficha_Principal.GROUP_CODE, INVT_Producto_Movimientos.QUANTITY, CLNT_Factura_Principal.NUMERO_PEDIDO_SISTEMA "
            "FROM CLNT_Factura_Principal CLNT_Factura_Principal, CLNT_Ficha_Principal CLNT_Ficha_Principal, INVT_Ficha_Principal INVT_Ficha_Principal, INVT_Producto_Movimientos INVT_Producto_Movimientos "
            "WHERE INVT_Ficha_Principal.PRODUCT_ID_CORP = INVT_Producto_Movimientos.PRODUCT_ID_CORP AND "
            "CLNT_Factura_Principal.CODIGO_CLIENTE = CLNT_Ficha_Principal.CODIGO_CLIENTE AND CLNT_Factura_Principal.CODIGO_FACTURA = INVT_Producto_Movimientos.DOC_ID_CORP2 "
            "AND ((INVT_Producto_Movimientos.CONFIRM=TRUE And INVT_Producto_Movimientos.CONFIRM=TRUE) AND (INVT_Producto_Movimientos.I_E_SIGN='-') "
            "AND (INVT_Producto_Movimientos.ADJUSTMENT_TYPE='FT') AND (CLNT_Factura_Principal.ANULADA=FALSE)) AND  FECHA_FACTURA >='"+OneMonthTime+"'"
        )
        facturas = cursorOdbc.fetchall()
        
        # CONECCIÓN WAREHOUSE
        cursorMysql = cnx_db_warehouse.cursor()
        
        # DELETE FACTURAS
        cursorMysql.execute("DELETE FROM facturas")
        cnx_db_warehouse.commit()
        print("Sucessful Deleted facturas")

        # INSERT FACTURAS
        sql_insert = """INSERT INTO facturas (CODIGO_FACTURA,FECHA_FACTURA,NOMBRE_CLIENTE,PRODUCT_ID,PRODUCT_NAME,GROUP_CODE,QUANTITY,NUMERO_PEDIDO_SISTEMA) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"""
        data_facturas = [list(rows) for rows in facturas] 
        cursorMysql.executemany(sql_insert, data_facturas)
        cnx_db_warehouse.commit()
        print("Sucessful Updated Facturas")    
        return 'ok'
    
    except Exception as e :
        print('Error --> ', e)
        return 'fail'
    
    finally:
        cnx_db_warehouse.close()
        cnx_odbc_mba.close()


# # Carga la tabla de stock lote automaticamente
def stock_lote(request):

    if request.method == 'GET':

        # currentTimeDate = datetime.now() - relativedelta(days=60)
        # OneMonthTime = currentTimeDate.strftime('%d-%m-%Y')
        # print(OneMonthTime)

        def odbc(mydb):
            # Using a DSN, but providing a password as well
            cnxn = pyodbc.connect('DSN=mba3;PWD=API')
            # Create a cursor from the connection
            cursorOdbc = cnxn.cursor()
            ####Cstock_lotes_ mba3O######
            print ("odbc_execute")

            #####Connect to MYSQL Database#####
            mycursorMysql = mydb.cursor()

            # ACTUALIZAR PRODUCTOS 
            try:
                #Productos
                cursorOdbc.execute(
                    "SELECT INVT_Ficha_Principal.PRODUCT_ID, INVT_Ficha_Principal.PRODUCT_NAME, "
                    "INVT_Ficha_Principal.UM, INVT_Ficha_Principal.GROUP_CODE, INVT_Ficha_Principal.UNIDADES_EMPAQUE, INVT_Ficha_Principal.Custom_Field_1,INVT_Ficha_Principal.Custom_Field_2, INVT_Ficha_Principal.Custom_Field_4, "
                    "INVT_Ficha_Principal.INACTIVE, INVT_Ficha_Principal.LARGO, INVT_Ficha_Principal.ANCHO, INVT_Ficha_Principal.ALTURA, INVT_Ficha_Principal.VOLUMEN, INVT_Ficha_Principal.WEIGHT, INVT_Ficha_Principal.AVAILABLE, INVT_Ficha_Principal.UnidadesPorPallet "
                    "FROM INVT_Ficha_Principal INVT_Ficha_Principal"
                )
                productos = cursorOdbc.fetchall()
                
                delete_sql = "DELETE FROM productos"
                mycursorMysql.execute(delete_sql)
                mydb.commit()
                print("Sucessful Deleted productos")
                
                sql_insert = """INSERT INTO productos (Codigo,Nombre,Unidad,Marca,Unidad_Empaque,Reg_San,Procedencia,Unidad_Box,Inactivo,Largo,Ancho,Altura,Volumen,Peso,Disponible,UnidadesPorPallet) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s,%s)"""
                data_productos = [list(rows) for rows in productos]
                mycursorMysql.executemany(sql_insert, data_productos)
                print("Sucessful Updated Productos")
                mydb.commit()
            except:
                print('Error actulizar productos')        
            

            #Reservas  (Pedidos Abiertos) - (<> MANTEN)
            cursorOdbc.execute(
                "SELECT CLNT_Pedidos_Principal.FECHA_PEDIDO, CLNT_Pedidos_Principal.CONTRATO_ID, CLNT_Ficha_Principal.CODIGO_CLIENTE, CLNT_Ficha_Principal.NOMBRE_CLIENTE, "
                "CLNT_Pedidos_Detalle.PRODUCT_ID, CLNT_Pedidos_Detalle.PRODUCT_NAME, CLNT_Pedidos_Detalle.QUANTITY, CLNT_Pedidos_Detalle.Despachados, CLNT_Pedidos_Principal.WARE_CODE, CLNT_Pedidos_Principal.CONFIRMED, CLNT_Pedidos_Principal.HORA_LLEGADA, CLNT_Pedidos_Principal.SEC_NAME_CLIENTE "
                "FROM CLNT_Ficha_Principal CLNT_Ficha_Principal, CLNT_Pedidos_Detalle CLNT_Pedidos_Detalle, CLNT_Pedidos_Principal CLNT_Pedidos_Principal "
                "WHERE CLNT_Pedidos_Principal.CONTRATO_ID_CORP = CLNT_Pedidos_Detalle.CONTRATO_ID_CORP AND CLNT_Ficha_Principal.CODIGO_CLIENTE = CLNT_Pedidos_Principal.CLIENT_ID "
                "AND CLNT_Pedidos_Detalle.Despachados=0 AND ((CLNT_Pedidos_Principal.PEDIDO_CERRADO=false) AND (CLNT_Pedidos_Detalle.TIPO_DOCUMENTO='PE') AND (CLNT_Pedidos_Detalle.PRODUCT_ID<>'MANTEN')) ORDER BY CLNT_Pedidos_Principal.CONTRATO_ID DESC"
            )

            reservas = cursorOdbc.fetchall()
            
            sql_delete="DELETE FROM reservas"
            mycursorMysql.execute(sql_delete)
            print("successfully deleted reservas")

            sql_insert_reservas = """INSERT INTO reservas (FECHA_PEDIDO, CONTRATO_ID, CODIGO_CLIENTE, NOMBRE_CLIENTE, 
            PRODUCT_ID, PRODUCT_NAME, QUANTITY, Despachados, WARE_CODE, CONFIRMED, HORA_LLEGADA, SEC_NAME_CLIENTE) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"""

            data_reservas = [list(rows) for rows in reservas]
            result = mycursorMysql.executemany(sql_insert_reservas, data_reservas)
            mydb.commit()
            print("Record inserted successfully into database_mysql-RESERVAS")
            

            # Reservas lotes
            cursorOdbc.execute(
            # "SELECT CLNT_Pedidos_Principal.FECHA_PEDIDO, CLNT_Pedidos_Principal.CONTRATO_ID, CLNT_Ficha_Principal.CODIGO_CLIENTE, CLNT_Pedidos_Detalle.PRODUCT_ID, "
            # "CLNT_Pedidos_Principal.WARE_CODE, INVT_Lotes_Trasabilidad.EGRESO_TEMP, INVT_Lotes_Trasabilidad.LOTE_ID, INVT_Lotes_Trasabilidad.FECHA_CADUCIDAD, CLNT_Pedidos_Principal.CONFIRMED "
            # "FROM CLNT_Ficha_Principal CLNT_Ficha_Principal, CLNT_Pedidos_Detalle CLNT_Pedidos_Detalle, CLNT_Pedidos_Principal CLNT_Pedidos_Principal, "
            # "INVT_Lotes_Trasabilidad INVT_Lotes_Trasabilidad "
            # "WHERE CLNT_Pedidos_Principal.CONTRATO_ID_CORP = CLNT_Pedidos_Detalle.CONTRATO_ID_CORP AND CLNT_Ficha_Principal.CODIGO_CLIENTE = CLNT_Pedidos_Principal.CLIENT_ID "
            # "AND CLNT_Pedidos_Detalle.CONTRATO_ID_CORP = INVT_Lotes_Trasabilidad.DOC_ID_CORP AND CLNT_Pedidos_Detalle.PRODUCT_ID_CORP = INVT_Lotes_Trasabilidad.PRODUCT_ID_CORP "
            # "AND ((CLNT_Pedidos_Principal.PEDIDO_CERRADO=false) AND (CLNT_Pedidos_Detalle.TIPO_DOCUMENTO='PE')) "
            # "ORDER BY CLNT_Pedidos_Principal.CONTRATO_ID, CLNT_Pedidos_Detalle.PRODUCT_ID DESC"
            
            "SELECT CLNT_Pedidos_Principal.FECHA_PEDIDO, CLNT_Pedidos_Principal.CONTRATO_ID, CLNT_Ficha_Principal.CODIGO_CLIENTE, CLNT_Pedidos_Detalle.PRODUCT_ID, "
            "CLNT_Pedidos_Principal.WARE_CODE, INVT_Lotes_Trasabilidad.EGRESO_TEMP, INVT_Lotes_Trasabilidad.LOTE_ID, INVT_Lotes_Trasabilidad.FECHA_CADUCIDAD, "
            "INVT_Producto_Lotes.Fecha_elaboracion_lote, CLNT_Pedidos_Principal.CONFIRMED, CLNT_Pedidos_Detalle.UNIT_COST "
            "FROM CLNT_Ficha_Principal CLNT_Ficha_Principal, CLNT_Pedidos_Detalle CLNT_Pedidos_Detalle, CLNT_Pedidos_Principal CLNT_Pedidos_Principal, "
            "INVT_Lotes_Trasabilidad INVT_Lotes_Trasabilidad, INVT_Producto_Lotes INVT_Producto_Lotes "
            "WHERE CLNT_Pedidos_Principal.CONTRATO_ID_CORP = CLNT_Pedidos_Detalle.CONTRATO_ID_CORP AND CLNT_Ficha_Principal.CODIGO_CLIENTE = CLNT_Pedidos_Principal.CLIENT_ID "
            "AND CLNT_Pedidos_Detalle.CONTRATO_ID_CORP = INVT_Lotes_Trasabilidad.DOC_ID_CORP AND CLNT_Pedidos_Detalle.PRODUCT_ID_CORP = INVT_Lotes_Trasabilidad.PRODUCT_ID_CORP "
            "AND INVT_Lotes_Trasabilidad.PRODUCT_ID_CORP = INVT_Producto_Lotes.PRODUCT_ID_CORP AND INVT_Lotes_Trasabilidad.LOTE_ID = INVT_Producto_Lotes.LOTE_ID AND INVT_Lotes_Trasabilidad.WARE_COD_CORP = INVT_Producto_Lotes.WARE_CODE_CORP AND ((CLNT_Pedidos_Principal.PEDIDO_CERRADO=false) AND (CLNT_Pedidos_Detalle.TIPO_DOCUMENTO='PE')) "
            "ORDER BY CLNT_Pedidos_Principal.CONTRATO_ID, CLNT_Pedidos_Detalle.PRODUCT_ID DESC"
            
            )
            reservas_lote = cursorOdbc.fetchall()

            sql_delete="DELETE FROM reservas_lote"
            mycursorMysql = mydb.cursor()
            mycursorMysql.execute(sql_delete)
            print("successfully deleted reservas con lote")

            # sql_insert_reservas_lote = """INSERT INTO reservas_lote (FECHA_PEDIDO, CONTRATO_ID, CODIGO_CLIENTE,
            # PRODUCT_ID, WARE_CODE, EGRESO_TEMP, LOTE_ID, FECHA_CADUCIDAD, CONFIRMED) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s);"""
            sql_insert_reservas_lote = """INSERT INTO reservas_lote (FECHA_PEDIDO, CONTRATO_ID, CODIGO_CLIENTE, 
            PRODUCT_ID, WARE_CODE, EGRESO_TEMP, LOTE_ID, FECHA_CADUCIDAD, Fecha_elaboracion_lote, CONFIRMED, PRICE) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"""
            data_reservas_lote = [list(rows) for rows in reservas_lote]
            mycursorMysql.executemany(sql_insert_reservas_lote, data_reservas_lote)
            print("Record inserted successfully into database_mysql - RESERVAS con LOTE")
            mydb.commit()


            #Clientes
            cursorOdbc.execute(
                "SELECT CLNT_Ficha_Principal.CODIGO_CLIENTE, CLNT_Ficha_Principal.IDENTIFICACION_FISCAL, CLNT_Ficha_Principal.NOMBRE_CLIENTE, "
                "CLNT_Ficha_Principal.CIUDAD_PRINCIPAL, CLNT_Ficha_Principal.CLIENT_TYPE, CLNT_Ficha_Principal.SALESMAN, CLNT_Ficha_Principal.LIMITE_CREDITO, "
                "CLNT_Ficha_Principal.PriceList, CLNT_Ficha_Principal.E_MAIL, CLNT_Ficha_Principal.Email_Fiscal, CLNT_Ficha_Principal.DIRECCION_PRINCIPAL_1, CLNT_Ficha_Principal.FAX "
                "FROM CLNT_Ficha_Principal CLNT_Ficha_Principal"
            )

            clientes = cursorOdbc.fetchall()

            sql_delete = "DELETE FROM clientes"
            mycursorMysql.execute(sql_delete)
            print("successfully deleted clientes")
            
            sql_insert_clientes = """INSERT INTO clientes (CODIGO_CLIENTE, IDENTIFICACION_FISCAL, NOMBRE_CLIENTE,
            CIUDAD_PRINCIPAL, CLIENT_TYPE, SALESMAN, LIMITE_CREDITO, PRICELIST, EMAIL, Email_Fiscal, DIRECCION, WP) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"""


            data_clientes = [list(rows) for rows in clientes]
            result = mycursorMysql.executemany(sql_insert_clientes, data_clientes)
            mydb.commit()
            print("Record inserted successfully into database_mysql-CLIENTES")


            ##Stock Lotes
            cursorOdbc.execute(
                "SELECT INVT_Ficha_Principal.PRODUCT_ID, INVT_Ficha_Principal.PRODUCT_NAME, INVT_Ficha_Principal.GROUP_CODE, "
                "INVT_Ficha_Principal.UM, INVT_Producto_Lotes.OH, INVT_Producto_Lotes_Bodegas.OH, INVT_Producto_Lotes_Bodegas.COMMITED, "
                "INVT_Producto_Lotes_Bodegas.QUANTITY, INVT_Producto_Lotes.LOTE_ID, INVT_Producto_Lotes.Fecha_elaboracion_lote, INVT_Producto_Lotes.FECHA_CADUCIDAD, "
                "INVT_Producto_Lotes_Bodegas.WARE_CODE, INVT_Producto_Lotes_Bodegas.LOCATION "
                "FROM INVT_Ficha_Principal INVT_Ficha_Principal, INVT_Producto_Lotes INVT_Producto_Lotes, INVT_Producto_Lotes_Bodegas INVT_Producto_Lotes_Bodegas "
                "WHERE INVT_Ficha_Principal.PRODUCT_ID_CORP = INVT_Producto_Lotes.PRODUCT_ID_CORP AND "
                "INVT_Producto_Lotes_Bodegas.PRODUCT_ID_CORP = INVT_Ficha_Principal.PRODUCT_ID_CORP AND "
                "INVT_Producto_Lotes.LOTE_ID = INVT_Producto_Lotes_Bodegas.LOTE_ID AND INVT_Producto_Lotes.WARE_CODE_CORP = INVT_Producto_Lotes_Bodegas.WARE_CODE AND "
                "((INVT_Producto_Lotes.OH>0) AND (INVT_Producto_Lotes_Bodegas.OH>0))"
                )

            infimas = cursorOdbc.fetchall()

            sql_delete="DELETE FROM stock_lote"
            mycursorMysql.execute(sql_delete)
            print("successfully deleted lotes")

            sql_insert_infimas = """INSERT INTO stock_lote (PRODUCT_ID, PRODUCT_NAME, GROUP_CODE,
            UM, OH, OH2, COMMITED, QUANTITY, LOTE_ID, Fecha_elaboracion_lote,
            FECHA_CADUCIDAD, WARE_CODE, LOCATION) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"""
            data_infimas = [list(rows) for rows in infimas]
            result = mycursorMysql.executemany(sql_insert_infimas, data_infimas)
            mydb.commit()
            print("Record stock lote inserted successfully into database_mysql-LOTES")


            # Facturas (ultimos 2 meses)
            actualizar_facturas_odbc()
            # cursorOdbc.execute(
            #     "SELECT CLNT_Factura_Principal.CODIGO_FACTURA, CLNT_Factura_Principal.FECHA_FACTURA, "
            #     "CLNT_Ficha_Principal.NOMBRE_CLIENTE, INVT_Ficha_Principal.PRODUCT_ID, "
            #     "INVT_Ficha_Principal.PRODUCT_NAME, INVT_Ficha_Principal.GROUP_CODE, INVT_Producto_Movimientos.QUANTITY, CLNT_Factura_Principal.NUMERO_PEDIDO_SISTEMA "
            #     "FROM CLNT_Factura_Principal CLNT_Factura_Principal, CLNT_Ficha_Principal CLNT_Ficha_Principal, INVT_Ficha_Principal INVT_Ficha_Principal, INVT_Producto_Movimientos INVT_Producto_Movimientos "
            #     "WHERE INVT_Ficha_Principal.PRODUCT_ID_CORP = INVT_Producto_Movimientos.PRODUCT_ID_CORP AND "
            #     "CLNT_Factura_Principal.CODIGO_CLIENTE = CLNT_Ficha_Principal.CODIGO_CLIENTE AND CLNT_Factura_Principal.CODIGO_FACTURA = INVT_Producto_Movimientos.DOC_ID_CORP2 "
            #     "AND ((INVT_Producto_Movimientos.CONFIRM=TRUE And INVT_Producto_Movimientos.CONFIRM=TRUE) AND (INVT_Producto_Movimientos.I_E_SIGN='-') "
            #     "AND (INVT_Producto_Movimientos.ADJUSTMENT_TYPE='FT') AND (CLNT_Factura_Principal.ANULADA=FALSE)) AND  FECHA_FACTURA >='"+OneMonthTime+"'"
            # )
            # facturas = cursorOdbc.fetchall()

            # # INSERT FACTURAS
            # delete_sql = "DELETE FROM facturas"
            # mycursorMysql.execute(delete_sql)
            # mydb.commit()
            # print("Sucessful Deleted facturas")

            # sql_insert = """INSERT INTO facturas (CODIGO_FACTURA,FECHA_FACTURA,NOMBRE_CLIENTE,PRODUCT_ID,PRODUCT_NAME,GROUP_CODE,QUANTITY,NUMERO_PEDIDO_SISTEMA) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"""
            # data_facturas = [list(rows) for rows in facturas] 
            # mycursorMysql.executemany(sql_insert, data_facturas)
            # print("Sucessful Updated Facturas")
            # mydb.commit()
            
            
            # Actualizar facturas warehouse
            # actulizar_facturas_warehouse()
            
            # Actualizar importaciones en transito
            importaciones_en_transito_odbc_insert_warehouse()
            
            
            #Productos en Transito
            cursorOdbc.execute(
                "SELECT INVT_Ficha_Principal.PRODUCT_ID, INVT_Producto_Lotes.OH, INVT_Producto_Lotes.LOTE_ID, INVT_Producto_Lotes.Fecha_elaboracion_lote, "
                "INVT_Producto_Lotes.FECHA_CADUCIDAD, INVT_Producto_Lotes.WARE_CODE_CORP "
                "FROM INVT_Ficha_Principal INVT_Ficha_Principal, INVT_Producto_Lotes INVT_Producto_Lotes "
                "WHERE INVT_Ficha_Principal.PRODUCT_ID_CORP = INVT_Producto_Lotes.PRODUCT_ID_CORP AND ((INVT_Producto_Lotes.WARE_CODE_CORP='TRN'))"
            )
            productos_transito = cursorOdbc.fetchall()
            
            delete_sql = "DELETE FROM productos_transito"
            mycursorMysql.execute(delete_sql)
            mydb.commit()
            print("Sucessful Deleted productos_transito")

            sql_insert = """INSERT INTO productos_transito (PRODUCT_ID,OH,LOTE_ID,FECHA_ELABORACION_LOTE,FECHA_CADUCIDAD,WARE_CODE_CORP) VALUES (%s, %s, %s, %s, %s, %s)"""
            data_productos_transito = [list(rows) for rows in productos_transito]
            mycursorMysql.executemany(sql_insert, data_productos_transito)
            print("Sucessful Updated Productos Transito")
            mydb.commit()
            
            

        def main():
            mydb = mysql.connector.connect(
                    host="172.16.28.102",
                    user="standard",
                    passwd="gimpromed",
                    database="warehouse"
                )
            odbc(mydb)

        main()

        time = str(datetime.now())
        TimeStamp.objects.create(actulization_stoklote=time)

        etiquetado_fun()

        context = {
            'context':time
        }


    return render(request, 'datos/stock_lote.html', context)



def product_detail(request, id):
    p = Product.objects.get(id=id)
    form = ProductForm(instance=p)

    context = {
        'form':form
    }

    return render(request, 'datos/product_detail.html', context)



# DATOS PARA MUESTREO DE TRANSFERENCIAS
def doc_transferencia_odbc(n_transf):

    cnxn = pyodbc.connect('DSN=mba3;PWD=API')
    cursorOdbc = cnxn.cursor()

    n = 'A-00000' + str(n_transf) + '-GIMPR'
    
    #Transferencia Egreso
    try:
        cursorOdbc.execute(
            # "SELECT INVT_Lotes_Ubicacion.DOC_ID_CORP, INVT_Lotes_Ubicacion.PRODUCT_ID_CORP, INVT_Lotes_Ubicacion.LOTE_ID, INVT_Lotes_Ubicacion.EGRESO_TEMP, "
            # "INVT_Lotes_Ubicacion.WARE_CODE_CORP, INVT_Producto_Lotes.ANIADIDO, INVT_Lotes_Ubicacion.UBICACION, INVT_Producto_Lotes.Fecha_elaboracion_lote, "
            # "INVT_Producto_Lotes.FECHA_CADUCIDAD "
            # "FROM INVT_Lotes_Ubicacion INVT_Lotes_Ubicacion, INVT_Producto_Lotes INVT_Producto_Lotes "
            # "WHERE INVT_Lotes_Ubicacion.PRODUCT_ID_CORP = INVT_Producto_Lotes.PRODUCT_ID_CORP AND INVT_Producto_Lotes.LOTE_ID = INVT_Lotes_Ubicacion.LOTE_ID AND "
            # #"((INVT_Lotes_Ubicacion.DOC_ID_CORP='A-0000054824-gimpr') AND (INVT_Producto_Lotes.ENTRADA_TIPO='OC') AND (INVT_Lotes_Ubicacion.EGRESO_TEMP>0))"
            # f"((INVT_Lotes_Ubicacion.DOC_ID_CORP='{n}') AND (INVT_Producto_Lotes.ENTRADA_TIPO='OC') AND (INVT_Lotes_Ubicacion.EGRESO_TEMP>0))"
        
            # "SELECT INVT_Lotes_Ubicacion.DOC_ID_CORP, INVT_Lotes_Ubicacion.PRODUCT_ID_CORP, INVT_Lotes_Ubicacion.LOTE_ID, INVT_Producto_Lotes.COMMITED, INVT_Lotes_Ubicacion.EGRESO_TEMP, "
            # "INVT_Lotes_Ubicacion.WARE_CODE_CORP, INVT_Lotes_Ubicacion.UBICACION, INVT_Producto_Lotes.Fecha_elaboracion_lote, "
            # "INVT_Producto_Lotes.FECHA_CADUCIDAD "
            # "FROM INVT_Lotes_Ubicacion INVT_Lotes_Ubicacion, INVT_Producto_Lotes INVT_Producto_Lotes "
            # "WHERE INVT_Lotes_Ubicacion.PRODUCT_ID_CORP = INVT_Producto_Lotes.PRODUCT_ID_CORP AND INVT_Producto_Lotes.LOTE_ID = INVT_Lotes_Ubicacion.LOTE_ID AND "
            # f"((INVT_Lotes_Ubicacion.DOC_ID_CORP='{n}') AND (INVT_Producto_Lotes.ENTRADA_TIPO='TR') AND (INVT_Lotes_Ubicacion.EGRESO_TEMP>0) AND (INVT_Producto_Lotes.WARE_CODE_CORP='BCT'))"
        
            # "SELECT INVT_Lotes_Ubicacion.DOC_ID_CORP, INVT_Lotes_Ubicacion.PRODUCT_ID_CORP, INVT_Lotes_Ubicacion.LOTE_ID, INVT_Lotes_Ubicacion.EGRESO_TEMP, "
            # "INVT_Lotes_Ubicacion.WARE_CODE_CORP, INVT_Producto_Lotes.ANIADIDO, INVT_Lotes_Ubicacion.UBICACION, INVT_Producto_Lotes.Fecha_elaboracion_lote, "
            # "INVT_Producto_Lotes.FECHA_CADUCIDAD "
            # "FROM INVT_Lotes_Ubicacion INVT_Lotes_Ubicacion, INVT_Producto_Lotes INVT_Producto_Lotes "
            # "WHERE INVT_Lotes_Ubicacion.PRODUCT_ID_CORP = INVT_Producto_Lotes.PRODUCT_ID_CORP AND INVT_Producto_Lotes.LOTE_ID = INVT_Lotes_Ubicacion.LOTE_ID AND "
            # f"((INVT_Lotes_Ubicacion.DOC_ID_CORP='{n}') AND (INVT_Lotes_Ubicacion.EGRESO_TEMP>0) AND (INVT_Producto_Lotes.ENTRADA_TIPO='TR' "
            # "Or INVT_Producto_Lotes.ENTRADA_TIPO='AE') AND (INVT_Producto_Lotes.WARE_CODE_CORP='BCT'))"
            
            
            "SELECT INVT_Lotes_Ubicacion.DOC_ID_CORP, INVT_Lotes_Ubicacion.PRODUCT_ID_CORP, INVT_Lotes_Ubicacion.LOTE_ID, INVT_Lotes_Ubicacion.EGRESO_TEMP, "
            "INVT_Producto_Lotes.WARE_CODE_CORP, INVT_Producto_Lotes.ANIADIDO, INVT_Lotes_Ubicacion.UBICACION, INVT_Producto_Lotes.Fecha_elaboracion_lote, "
            "INVT_Producto_Lotes.FECHA_CADUCIDAD, INVT_Producto_Lotes.ENTRADA_TIPO, INVT_Lotes_Ubicacion.UBICACION, INVT_Lotes_Ubicacion.WARE_CODE_CORP "
            "FROM INVT_Lotes_Ubicacion INVT_Lotes_Ubicacion, INVT_Producto_Lotes INVT_Producto_Lotes "
            "WHERE INVT_Lotes_Ubicacion.PRODUCT_ID_CORP = INVT_Producto_Lotes.PRODUCT_ID_CORP AND INVT_Producto_Lotes.LOTE_ID = INVT_Lotes_Ubicacion.LOTE_ID AND "
            # "((INVT_Lotes_Ubicacion.DOC_ID_CORP='A-0000063572-GIMPR') AND (INVT_Lotes_Ubicacion.EGRESO_TEMP>0) AND (INVT_Producto_Lotes.WARE_CODE_CORP='BCT')) "
            f"((INVT_Lotes_Ubicacion.DOC_ID_CORP='{n}') AND (INVT_Lotes_Ubicacion.EGRESO_TEMP>0) AND (INVT_Producto_Lotes.WARE_CODE_CORP='BCT'))"
            
            
        )
        
        columns = [col[0] for col in cursorOdbc.description]
        transferencia = [dict(zip(columns, row)) for row in cursorOdbc.fetchall()] 
        transferencia = pd.DataFrame(transferencia)
        transferencia['product_id'] = list(map(lambda x:x[:-6], list(transferencia['PRODUCT_ID_CORP'])))
        
        transferencia = transferencia.rename(columns={
            'DOC_ID_CORP': 'doc',
            'LOTE_ID':'lote_id',
            'EGRESO_TEMP': 'unidades',
            'WARE_CODE_CORP': 'bodega_salida',
            'FECHA_CADUCIDAD': 'f_elab',
            'FECHA_CADUCIDAD': 'f_cadu',
        })
        
    except:
        transferencia = pd.DataFrame()

    """
    try:
        cursorOdbc.execute(
            "SELECT INVT_Lotes_Ubicacion.DOC_ID_CORP, INVT_Lotes_Ubicacion.PRODUCT_ID_CORP, INVT_Lotes_Ubicacion.LOTE_ID, "
            "INVT_Lotes_Ubicacion.EGRESO_TEMP, INVT_Lotes_Ubicacion.COMMITED, INVT_Lotes_Ubicacion.WARE_CODE_CORP, INVT_Lotes_Ubicacion.UBICACION, "
            "INVT_Producto_Lotes.Fecha_elaboracion_lote, INVT_Producto_Lotes.FECHA_CADUCIDAD "
            "FROM INVT_Lotes_Ubicacion INVT_Lotes_Ubicacion, INVT_Producto_Lotes INVT_Producto_Lotes "
            "WHERE INVT_Lotes_Ubicacion.PRODUCT_ID_CORP = INVT_Producto_Lotes.PRODUCT_ID_CORP AND INVT_Producto_Lotes.LOTE_ID = INVT_Lotes_Ubicacion.LOTE_ID AND "
            # "((INVT_Lotes_Ubicacion.DOC_ID_CORP='A-0000054509-gimpr') AND (INVT_Producto_Lotes.ENTRADA_TIPO='ae') AND (INVT_Lotes_Ubicacion.EGRESO_TEMP>0))"
            f"((INVT_Lotes_Ubicacion.DOC_ID_CORP='{n}') AND (INVT_Producto_Lotes.ENTRADA_TIPO='ae') AND (INVT_Lotes_Ubicacion.EGRESO_TEMP>0))"
        )
        transferencia2 = cursorOdbc.fetchall()
        transferencia2 = [list(rows) for rows in transferencia2]
        transferencia2 = pd.DataFrame(transferencia2)
        transferencia2['product_id'] = list(map(lambda x:x[:-6], list(transferencia2[1])))

        transferencia2 = transferencia2.rename(columns={
            0:'doc',
            2:'lote_id',
            4:'unidades',
            5:'bodega_salida',
            #5:'boleano',
            #6:'bodega_entrada',
            7:'f_elab',
            8:'f_cadu'
        })

        transferencia2 = transferencia2[['doc', 'product_id', 'lote_id', 'unidades', 'bodega_salida', 'f_elab', 'f_cadu']]
    except:
        transferencia2 = pd.DataFrame()
    """
    
    #t = pd.concat([transferencia, transferencia2])
    t = transferencia.sort_values('UBICACION')
    t = t.reset_index(drop=True) 

    return t


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
            f"SELECT DOC_ID_CORP, PRODUCT_ID_CORP, OH, MEMO FROM imp_llegadas where DOC_ID_CORP ='{doc_id}'"
            )
        columns = [col[0] for col in cursor.description]
        importaciones_llegadas = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        importaciones_llegadas = pd.DataFrame(importaciones_llegadas)
        importaciones_llegadas['product_id'] = list(map(lambda x:x[:-6], list(importaciones_llegadas['PRODUCT_ID_CORP'])))
        importaciones_llegadas = importaciones_llegadas.groupby(by=['DOC_ID_CORP','MEMO','product_id']).sum().reset_index()
        
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
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(
            f"""
            SELECT * 
            FROM venta_facturas 
            WHERE CODIGO_CLIENTE = '{cli}' AND STR_TO_DATE(FECHA, '%Y-%m-%d') BETWEEN '{desde}' AND '{hasta}'
            """
        )

        columns = [col[0] for col in cursor.description]
        ventas_facturas = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
    ventas_facturas = pd.DataFrame(ventas_facturas)

    return ventas_facturas


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

    cnxn = pyodbc.connect('DSN=mba3;PWD=API')
    cursorOdbc = cnxn.cursor()

    cursorOdbc.execute(

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
        """
    )

    lote_factura = cursorOdbc.fetchall()

    lote_factura = [list(rows) for rows in lote_factura]
    lote_factura = pd.DataFrame(lote_factura)

    lote_factura = lote_factura.rename(columns={
        0:'n_factura',
        1:'product_id',
        2:'unidades',
        3:'lote',
        4:'fecha_caducidad'
    })

    lote_factura['fecha_caducidad'] = lote_factura['fecha_caducidad'].astype(str)

    lote_factura = de_dataframe_a_template(lote_factura)

    return lote_factura



def reservas_lotes_actualizar_odbc(request):

    cnxn = pyodbc.connect('DSN=mba3;PWD=API')
    cursorOdbc = cnxn.cursor()

    cursorOdbc.execute(
    "SELECT CLNT_Pedidos_Principal.FECHA_PEDIDO, CLNT_Pedidos_Principal.CONTRATO_ID, CLNT_Ficha_Principal.CODIGO_CLIENTE, CLNT_Pedidos_Detalle.PRODUCT_ID, "
    "CLNT_Pedidos_Principal.WARE_CODE, INVT_Lotes_Trasabilidad.EGRESO_TEMP, INVT_Lotes_Trasabilidad.LOTE_ID, INVT_Lotes_Trasabilidad.FECHA_CADUCIDAD, CLNT_Pedidos_Principal.CONFIRMED "
    "FROM CLNT_Ficha_Principal CLNT_Ficha_Principal, CLNT_Pedidos_Detalle CLNT_Pedidos_Detalle, CLNT_Pedidos_Principal CLNT_Pedidos_Principal, "
    "INVT_Lotes_Trasabilidad INVT_Lotes_Trasabilidad "
    "WHERE CLNT_Pedidos_Principal.CONTRATO_ID_CORP = CLNT_Pedidos_Detalle.CONTRATO_ID_CORP AND CLNT_Ficha_Principal.CODIGO_CLIENTE = CLNT_Pedidos_Principal.CLIENT_ID "
    "AND CLNT_Pedidos_Detalle.CONTRATO_ID_CORP = INVT_Lotes_Trasabilidad.DOC_ID_CORP AND CLNT_Pedidos_Detalle.PRODUCT_ID_CORP = INVT_Lotes_Trasabilidad.PRODUCT_ID_CORP "
    "AND ((CLNT_Pedidos_Principal.PEDIDO_CERRADO=false) AND (CLNT_Pedidos_Detalle.TIPO_DOCUMENTO='PE')) "
    "ORDER BY CLNT_Pedidos_Principal.CONTRATO_ID, CLNT_Pedidos_Detalle.PRODUCT_ID DESC"
    )

    reservas_lote = cursorOdbc.fetchall()
    data_reservas_lote = [list(rows) for rows in reservas_lote]

    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute("DELETE FROM reservas_lote")
    print("successfully deleted reservas con lote")

    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.executemany(
        """INSERT INTO reservas_lote (FECHA_PEDIDO, CONTRATO_ID, CODIGO_CLIENTE,
        PRODUCT_ID, WARE_CODE, EGRESO_TEMP, LOTE_ID, FECHA_CADUCIDAD, CONFIRMED)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s);""", data_reservas_lote
        )
    print("Record inserted successfully into database_mysql - RESERVAS con LOTE")


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
        stock_disp = stock_disp[stock_disp['PRODUCT_ID'].isin(items_list)]
        stock_disp = stock_disp.groupby('PRODUCT_ID').sum().reset_index()[['PRODUCT_ID','OH2']]
        
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


# def factura_detalle_lote_odbc(n_factura, product_id):

#     cnxn = pyodbc.connect('DSN=mba3;PWD=API')
#     cursorOdbc = cnxn.cursor()

#     cursorOdbc.execute(

#         f"""SELECT CLNT_Factura_Principal.CODIGO_FACTURA, INVT_Ficha_Principal.PRODUCT_ID, INVT_Producto_Movimientos.QUANTITY, INVT_Lotes_Trasabilidad.LOTE_ID, INVT_Lotes_Trasabilidad.FECHA_CADUCIDAD
#         FROM CLNT_Factura_Principal CLNT_Factura_Principal, INVT_Ficha_Principal INVT_Ficha_Principal, INVT_Lotes_Trasabilidad INVT_Lotes_Trasabilidad, INVT_Producto_Movimientos INVT_Producto_Movimientos
#         WHERE INVT_Ficha_Principal.PRODUCT_ID_CORP = INVT_Producto_Movimientos.PRODUCT_ID_CORP AND
#         CLNT_Factura_Principal.CODIGO_FACTURA = INVT_Producto_Movimientos.DOC_ID_CORP2 AND
#         INVT_Lotes_Trasabilidad.PRODUCT_ID_CORP = INVT_Ficha_Principal.PRODUCT_ID_CORP AND
#         CLNT_Factura_Principal.CODIGO_FACTURA = INVT_Lotes_Trasabilidad.DOC_ID_CORP AND
#         ((INVT_Producto_Movimientos.CONFIRM=TRUE) AND (CLNT_Factura_Principal.CODIGO_FACTURA='{n_factura}') AND
#         (INVT_Producto_Movimientos.PRODUCT_ID='{product_id}') AND
#         (INVT_Producto_Movimientos.I_E_SIGN='-') AND
#         (INVT_Producto_Movimientos.ADJUSTMENT_TYPE='FT') AND
#         (CLNT_Factura_Principal.ANULADA=FALSE))
#         """
#     )

#     lote_factura = cursorOdbc.fetchall()

#     # lote_factura = [list(rows) for rows in lote_factura]
#     # lote_factura = pd.DataFrame(lote_factura)

#     return lote_factura


def factura_lote_odbc(n_factura):

    cnxn = pyodbc.connect('DSN=mba3;PWD=API')
    cursorOdbc = cnxn.cursor()

    cursorOdbc.execute(

        f"""SELECT CLNT_Factura_Principal.CODIGO_FACTURA, CLNT_Factura_Principal.CODIGO_CLIENTE, CLNT_Factura_Principal.FECHA_FACTURA, INVT_Ficha_Principal.PRODUCT_ID,
        INVT_Ficha_Principal.PRODUCT_NAME, INVT_Ficha_Principal.GROUP_CODE, INVT_Lotes_Trasabilidad.EGRESO_TEMP, INVT_Lotes_Trasabilidad.LOTE_ID, INVT_Lotes_Trasabilidad.FECHA_CADUCIDAD,
        INVT_Ficha_Principal.Custom_Field_1
        FROM CLNT_Factura_Principal CLNT_Factura_Principal, INVT_Ficha_Principal INVT_Ficha_Principal, INVT_Lotes_Trasabilidad INVT_Lotes_Trasabilidad
        WHERE INVT_Lotes_Trasabilidad.PRODUCT_ID_CORP = INVT_Ficha_Principal.PRODUCT_ID_CORP AND CLNT_Factura_Principal.CODIGO_FACTURA = INVT_Lotes_Trasabilidad.DOC_ID_CORP AND
        ((CLNT_Factura_Principal.CODIGO_FACTURA='{n_factura}') AND (CLNT_Factura_Principal.ANULADA=FALSE))
        """
    )

    lote_factura = cursorOdbc.fetchall()

    lote_factura = [list(rows) for rows in lote_factura]
    lote_factura = pd.DataFrame(lote_factura)
    
    lote_factura = lote_factura.rename(columns={
        0:'CODIGO_FACTURA',
        1:'CODIGO_CLIENTE',
        2:'FECHA_FACTURA',
        3:'PRODUCT_ID',
        4:'PRODUCT_NAME',
        5:'PRODUCT_GROUP',
        6:'QUANTITY',
        7:'LOTE_ID',
        8:'FECHA_CADUCIDAD',
        9:'REG_SANITARIO'
    })

    lote_factura['FECHA_FACTURA'] = lote_factura['FECHA_FACTURA'].astype(str)
    lote_factura['FECHA_CADUCIDAD'] = lote_factura['FECHA_CADUCIDAD'].astype(str)

    return lote_factura



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
    
    return costototal


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
        res['disp'] = res.apply(lambda x: 'OK' if x['OH2']>x['QUANTITY'] else 'NOT', axis=1)
        res = res[res['PRODUCT_ID']!='MANTEN']

        dis = 'NOT' in list(res['disp'])
        
        if dis:
            cont.append(i)
            disp.append('NOT')
    
    sto = pd.DataFrame()
    sto['CONTRATO_ID'] = cont
    sto['DISP'] = disp

    return sto


def actualizar_imp_llegadas_odbc(request):

    # anio = str(datetime.now().year)
    # anio_sql = '%' + anio + '%'
    
    cnxn = pyodbc.connect('DSN=mba3;PWD=API')
    cursorOdbc = cnxn.cursor()
    mydb = mysql.connector.connect(
        host="172.16.28.102",
        user="standard",
        passwd="gimpromed",
        database="warehouse"
    )
    mycursorMysql = mydb.cursor()

    ##Imp Llegada
    cursorOdbc.execute(
        # "SELECT INVT_Lotes_Trasabilidad.DOC_ID_CORP, INVT_Lotes_Trasabilidad.ENTRADA_FECHA, "
        # "INVT_Lotes_Trasabilidad.PRODUCT_ID_CORP, INVT_Lotes_Trasabilidad.LOTE_ID, INVT_Lotes_Trasabilidad.FECHA_CADUCIDAD, "
        # "INVT_Lotes_Trasabilidad.AVAILABLE, INVT_Lotes_Trasabilidad.EGRESO_TEMP, INVT_Lotes_Trasabilidad.OH, INVT_Lotes_Trasabilidad.WARE_COD_CORP, CLNT_Pedidos_Principal.MEMO "
        # "FROM INVT_Lotes_Trasabilidad INVT_Lotes_Trasabilidad "
        # "LEFT JOIN CLNT_Pedidos_Principal ON INVT_Lotes_Trasabilidad.DOC_ID_CORP = CLNT_Pedidos_Principal.CONTRATO_ID_CORP "
        # #"WHERE (INVT_Lotes_Trasabilidad.ENTRADA_TIPO='OC') AND (INVT_Lotes_Trasabilidad.ENTRADA_FECHA>'01/01/2022') AND (INVT_Lotes_Trasabilidad.Tipo_Movimiento='RP')"
        # f"WHERE (INVT_Lotes_Trasabilidad.ENTRADA_TIPO='OC') AND (INVT_Lotes_Trasabilidad.ENTRADA_FECHA>'01/01/{anio}') AND (INVT_Lotes_Trasabilidad.Tipo_Movimiento='RP')"
        
        "SELECT INVT_Lotes_Trasabilidad.DOC_ID_CORP, INVT_Lotes_Trasabilidad.ENTRADA_FECHA, "
        "INVT_Lotes_Trasabilidad.PRODUCT_ID_CORP, INVT_Lotes_Trasabilidad.LOTE_ID, INVT_Lotes_Trasabilidad.FECHA_CADUCIDAD, "
        "INVT_Lotes_Trasabilidad.AVAILABLE, INVT_Lotes_Trasabilidad.EGRESO_TEMP, INVT_Lotes_Trasabilidad.OH, INVT_Lotes_Trasabilidad.WARE_COD_CORP, CLNT_Pedidos_Principal.MEMO "
        "FROM INVT_Lotes_Trasabilidad INVT_Lotes_Trasabilidad "
        "LEFT JOIN CLNT_Pedidos_Principal ON INVT_Lotes_Trasabilidad.DOC_ID_CORP = CLNT_Pedidos_Principal.CONTRATO_ID_CORP "
        "WHERE (INVT_Lotes_Trasabilidad.ENTRADA_TIPO='OC') AND (INVT_Lotes_Trasabilidad.ENTRADA_FECHA>'2023-01-01') AND (INVT_Lotes_Trasabilidad.Tipo_Movimiento='RP')"
    )
    llegada = cursorOdbc.fetchall()
    llegada = [list(rows) for rows in llegada]
    
    # delete_sql = "DELETE FROM imp_llegadas"
    delete_sql = "DELETE FROM imp_llegadas WHERE ENTRADA_FECHA>'2023-01-01'"
    mycursorMysql.execute(delete_sql)
    mydb.commit()
    print("Sucessful Deleted importaciones arrived")


    sql_insert = """INSERT INTO imp_llegadas (DOC_ID_CORP,ENTRADA_FECHA,PRODUCT_ID_CORP,LOTE_ID,FECHA_CADUCIDAD,AVAILABLE,EGRESO_TEMP,OH,WARE_COD_CORP,MEMO) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
    data_llegada = [list(rows) for rows in llegada]
    mycursorMysql.executemany(sql_insert, data_llegada)
    mydb.commit()
    print("Sucessful importaciones arrived")

    time = str(datetime.now())
    TimeStamp.objects.create(actualization_imp_llegadas=time)

    return HttpResponse('ok')


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

    # Reservas Lote
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute("SELECT * FROM reservas_lote")
        columns = [col[0] for col in cursor.description]
        reservas_lote = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
        reservas_lote = pd.DataFrame(reservas_lote)

    reservas_lote = reservas_lote.pivot_table(
        index=['PRODUCT_ID', 'LOTE_ID'], values=['EGRESO_TEMP'], aggfunc='sum'
    ).reset_index()

    stock_lote = stock_lote.merge(reservas_lote, on=['PRODUCT_ID', 'LOTE_ID'], how='left').fillna(0)
    stock_lote['DISP-MENOS-RESERVA'] = stock_lote['OH2'] - stock_lote['EGRESO_TEMP']

    return stock_lote



def revision_reservas_fun_obsoleta():

    # Datos
    df_reservas_lote    = reservas_lote()
    df_reservas_sinlote = reservas_sinlote()
    clientes            = clientes_warehouse()[['CODIGO_CLIENTE','NOMBRE_CLIENTE','CLIENT_TYPE']]
    inventario          = stock_lote_odbc()
    
    # Borrar columna 'EGRESO_TEMP' por modificación de consulta 'stock_lote_odbc'
    inventario          = inventario.drop(['EGRESO_TEMP'], axis=1)
    productos           = productos_odbc_and_django()[['product_id', 'Nombre', 'Marca']]
    productos           = productos.rename(columns={'product_id':'PRODUCT_ID'})
    
    # Lista de contratos de hospitales publicos
    reservas_publico = df_reservas_sinlote[df_reservas_sinlote['SEC_NAME_CLIENTE']=='PUBLICO']
    reservas_publico = reservas_publico['CONTRATO_ID'].unique()

    r_publico = []
    for i in reservas_publico:
        c = float(i)
        c = int(c)
        r_publico.append(c)

    # Filtros para obtener lista de contratos finales
    # Quitar contratos publicos ya por etiquetar
    reservas = df_reservas_lote[-df_reservas_lote.CONTRATO_ID.isin(r_publico)]

    # Filtrar por reservas no confirmadas 
    reservas = reservas[reservas['CONFIRMED']=='0']

    # Filtrar por cliente gimpromed y cliente hospitales publicos
    reservas = reservas.merge(clientes, on='CODIGO_CLIENTE', how='left')
    reservas = reservas[(reservas['CODIGO_CLIENTE']=='CLI01002') | (reservas['CLIENT_TYPE']=='HOSPU')]

    # Obtener lista de contratos a revisar
    lista_contratos = reservas['CONTRATO_ID'].unique()

    # Obtener lista de productos a revisar
    lista_productos = reservas['PRODUCT_ID'].unique()

    # Filtrar inventario por lista de productos en contratos
    inventario = inventario[inventario.PRODUCT_ID.isin(lista_productos)]
    #inventario['FECHA_CADUCIDAD'] = pd.to_datetime(inventario['FECHA_CADUCIDAD'])
    
    # Agrupar reservas por producto, lote y bodega - todas las reservas de la tabla "reservas_lote"
    r_agg = df_reservas_lote.pivot_table(index=['PRODUCT_ID', 'LOTE_ID', 'WARE_CODE'], values='EGRESO_TEMP', aggfunc='sum').reset_index()
    
    # Lista de reservas concatentadas
    rep_concat_lista = []

    # Iterar por contratos
    for i in lista_contratos:
        r = reservas[reservas['CONTRATO_ID']==i]
        r = r.merge(productos, on='PRODUCT_ID', how='left')
        r = r[['PRODUCT_ID','Nombre','Marca','LOTE_ID','FECHA_CADUCIDAD','WARE_CODE','EGRESO_TEMP','CONTRATO_ID','NOMBRE_CLIENTE']]
        
        r_tuple = [tuple(i) for i in r.values]
        
        for j in r_tuple:
            
            r_product_id      = j[0]
            prod              = j[0]
            r_nombre          = j[1]
            r_marca           = j[2]   
            r_lote_id         = j[3]
            r_fecha_caducidad = j[4]
            #r_fecha_caducidad = datetime.strptime(r_fecha_caducidad, '%Y-%m-%d')
            r_ware_code       = j[5]
            r_egreso_temp     = j[6]
            r_contrato_id     = j[7]     
            r_cliente         = j[8]
            
            # Reserva como dataframe
            df_reserva = pd.DataFrame()
            df_reserva['PRODUCT_ID']               = [r_product_id]
            df_reserva['PRODUCT_NAME']             = [r_nombre]
            df_reserva['GROUP_CODE']               = [r_marca]
            df_reserva['LOTE_ID']                  = [r_lote_id]
            df_reserva['FECHA_CADUCIDAD']          = [r_fecha_caducidad]
            df_reserva['WARE_CODE']                = [r_ware_code]
            df_reserva['UNDS RESERVADAS CONTRATO'] = [r_egreso_temp]
            df_reserva['CONTRATO_ID']              = [r_contrato_id]
            df_reserva['NOMBRE_CLIENTE']           = [r_cliente]

            # Inventario filtrado por item de contrato
            inv_res = inventario[inventario['PRODUCT_ID']==prod]
            inv_res = inv_res.merge(r_agg, on=['PRODUCT_ID','LOTE_ID','WARE_CODE'], how='left').fillna(0)
            inv_res = inv_res.sort_values('FECHA_CADUCIDAD')
            
            # Quitar stock en cuarentena
            inv_res = inv_res[inv_res['WARE_CODE']!='CUA']
            inv_res = inv_res[inv_res['WARE_CODE']!='CUC']
            
            # Calcular
            inv_res['UNDS DISPONIBLE'] = inv_res['OH2'] - inv_res['EGRESO_TEMP']
            inv_res['und-res-cont']    = r_egreso_temp
            inv_res['cant-res']        = inv_res['und-res-cont'] - inv_res['UNDS DISPONIBLE']
            inv_res['CANTIDAD A RESERVAR'] = (inv_res['UNDS DISPONIBLE'].where(inv_res['UNDS DISPONIBLE']<=inv_res['und-res-cont'], r_egreso_temp))

            # Restricciones
            inv_res = inv_res[inv_res['UNDS DISPONIBLE']>0]
            
            # Concatenar si el dataframe de inventario existe
            if not inv_res.empty:    
                df_res_concat = pd.concat([df_reserva, inv_res])
                rep_concat_lista.append(df_res_concat)
                
                
    reporte = pd.concat(rep_concat_lista)
    reporte = reporte[[
        'PRODUCT_ID', 'PRODUCT_NAME', 'GROUP_CODE', 'LOTE_ID', 'FECHA_CADUCIDAD', 'WARE_CODE', 'UNDS RESERVADAS CONTRATO',
        'CONTRATO_ID', 'NOMBRE_CLIENTE', 'EGRESO_TEMP', 'OH2', 'UNDS DISPONIBLE', 'CANTIDAD A RESERVAR'
    ]]

    reporte = reporte.rename(columns={
        'EGRESO_TEMP':'UNDS RESERVADAS INVENTARIO',
        'OH2': 'UNDS INVENTARIO'
    })

    reporte = reporte.set_index('PRODUCT_ID')

    return reporte


def revision_reservas_fun_obsoleta_dos():
#def revision_reservas_fun():
    # 1. Obtener datos
    df_reservas_lote    = reservas_lote()
    df_reservas_sinlote = reservas_sinlote()
    clientes            = clientes_warehouse()[['CODIGO_CLIENTE','NOMBRE_CLIENTE','CLIENT_TYPE']]
    inventario          = stock_lote_odbc()
    productos           = productos_odbc_and_django()[['product_id','Nombre','Marca']]
        
    
    # 1.1 Filtrar reservas por cliente gimpromed o cliente público
    reservas_clientes = df_reservas_lote.merge(clientes, on='CODIGO_CLIENTE', how='left')
    reservas_clientes = reservas_clientes[
        (reservas_clientes['CLIENT_TYPE'] == 'HOSPU') | 
        (reservas_clientes['CODIGO_CLIENTE'] == 'CLI01002')
        ]
    
    df_reservas_sinlote = df_reservas_sinlote[
        (df_reservas_sinlote['SEC_NAME_CLIENTE'] == 'PUBLICO') |
        (df_reservas_sinlote['SEC_NAME_CLIENTE'] == 'RESERVA') |
        (df_reservas_sinlote['SEC_NAME_CLIENTE'] == 'RESERVADO')
        ]
    
    df_reservas_sinlote = df_reservas_sinlote[df_reservas_sinlote['WARE_CODE']=='BCT']
    
    # 1.2 Filtrar y procesar reservas sin lote
    df_reservas_sinlote = df_reservas_sinlote[df_reservas_sinlote['SEC_NAME_CLIENTE'] == 'PUBLICO'].copy()
    df_reservas_sinlote['CONTRATO_ID'] = df_reservas_sinlote['CONTRATO_ID'].astype('float', errors='ignore')
    df_reservas_sinlote['CONTRATO_ID'] = df_reservas_sinlote['CONTRATO_ID'].astype('int', errors='ignore')
    df_reservas_sinlote = df_reservas_sinlote[['CONTRATO_ID', 'SEC_NAME_CLIENTE']]

    # 1.3 Merge reservas con clientes y reservas sin lote, excluyendo contratos de "PUBLICO"
    reservas = reservas_clientes.merge(df_reservas_sinlote, on='CONTRATO_ID', how='left').fillna('')
    reservas = reservas[reservas['SEC_NAME_CLIENTE'] != 'PUBLICO']
    
    # 1.4 Filtrar por reservas no confirmadas
    reservas = reservas[reservas['CONFIRMED'] == '0']
    
    # 2. Agrupar reservas por producto y lote, y añadir información de contratos
    reservas['CLIENTE-CONTRATO-UNIDADES'] = ('"' + reservas['NOMBRE_CLIENTE'].astype('str') + ': ' +
                                            reservas['CONTRATO_ID'].astype('str') + ' - UNDS: ' + 
                                            reservas['EGRESO_TEMP'].astype('str') + '"')
    
    # 2.1 Agrupar contratos por producto y lote
    df_product_contrato_group = reservas.pivot_table(index=['PRODUCT_ID', 'LOTE_ID'],
                                                    values='CLIENTE-CONTRATO-UNIDADES',
                                                    aggfunc=lambda x: ' - '.join(x)).reset_index()
    
    # 2.2 Agrupar cantidades por producto y lote
    df_product_unidades_group = reservas.pivot_table(index=['PRODUCT_ID', 'LOTE_ID'],
                                                    values='EGRESO_TEMP', aggfunc='sum').reset_index()
    
    # 2.3 Unir los dataframes de reservas agrupadas
    df_reservas_agrupadas = df_product_contrato_group.merge(df_product_unidades_group, on=['PRODUCT_ID', 'LOTE_ID'])
    df_reservas_agrupadas['LOTE_ID'] = quitar_puntos(df_reservas_agrupadas['LOTE_ID'])
    productos = productos.rename(columns={'product_id': 'PRODUCT_ID'})
    df_reservas_agrupadas = df_reservas_agrupadas.merge(productos, on='PRODUCT_ID', how='left')

    # 3. Iterar en el inventario para encontrar lotes con mayor tiempo de caducidad
    resultados = []

    for index, row in df_reservas_agrupadas.iterrows():
        stock = inventario[inventario['PRODUCT_ID'] == row['PRODUCT_ID']].copy()
        stock['LOTE_ID'] = quitar_puntos(stock['LOTE_ID'])
        stock = stock.groupby(by=['PRODUCT_ID', 'LOTE_ID', 'FECHA_CADUCIDAD'])['OH2'].sum().reset_index()
        stock = stock.sort_values(by='FECHA_CADUCIDAD').reset_index(drop=True)

        # Si hay más de un lote, evaluar si el lote actual es el último
        if len(stock) > 1:
            ubicacion_lote = stock[stock['LOTE_ID'] == row['LOTE_ID']].index[0]
            ultimo_lote_index = len(stock) - 1

            # Si el lote no es el último, añadir al reporte
            if ubicacion_lote < ultimo_lote_index:
                reserva_product_lote = reservas[
                    (reservas['PRODUCT_ID'] == row['PRODUCT_ID']) &
                    (reservas['LOTE_ID'] == row['LOTE_ID'])][[
                        'NOMBRE_CLIENTE', 'CONTRATO_ID', 'PRODUCT_ID', 'LOTE_ID', 'FECHA_CADUCIDAD', 'EGRESO_TEMP', 'WARE_CODE'
                    ]]
                resultados.append(reserva_product_lote)

    # Concatenar resultados y generar reporte final
    if resultados:
        reporte_final = pd.concat(resultados, ignore_index=True)
        reporte_final['FECHA_CADUCIDAD'] = reporte_final['FECHA_CADUCIDAD'].astype('str')
        return reporte_final

    else:
        return pd.DataFrame()



def revision_reservas_fun():
    
    # 1. Obtener datos
    df_reservas_lote    = reservas_lote()
    df_reservas_sinlote = reservas_sinlote()
    cli                 = clientes_warehouse()[['CODIGO_CLIENTE','NOMBRE_CLIENTE']]
    clientes            = clientes_warehouse()[['CODIGO_CLIENTE','CLIENT_TYPE']]
    inventario          = stock_lote_odbc()

    # 2.0 Filtrar por SEC_NAME_CLIENTE 
    # solo reserva yu reservado
    df_reservas_sinlote = df_reservas_sinlote[
        (df_reservas_sinlote['SEC_NAME_CLIENTE']=='RESERVA') |
        (df_reservas_sinlote['SEC_NAME_CLIENTE']=='RESERVADO')
        ]
    
    # 2.1 Filtrar reservas por gimpromed y cliente hospital
    df_reservas_sinlote = df_reservas_sinlote.merge(clientes, on='CODIGO_CLIENTE', how='left')
    df_reservas_sinlote = df_reservas_sinlote[
        (df_reservas_sinlote['CLIENT_TYPE'] == 'HOSPU') |
        (df_reservas_sinlote['CODIGO_CLIENTE'] == 'CLI01002') 
    ]    
    
    # 2.2 Filtrar por ware_code BCT
    df_reservas_sinlote = df_reservas_sinlote[df_reservas_sinlote['WARE_CODE'] == 'BCT']
    
    # 2.3 Obtener lista de contratos
    contratos_list = df_reservas_sinlote['CONTRATO_ID'].unique()
    contratos_list = list(map(lambda x: int(float(x)), contratos_list))

    # 2.4 Reservas lote filtradas
    reservas = df_reservas_lote[df_reservas_lote.CONTRATO_ID.isin(contratos_list)]
    
    # 2.4.1 Clientes reservas
    cli_res = reservas.copy()
    cli_res = cli_res.merge(cli, on='CODIGO_CLIENTE', how='left')[['NOMBRE_CLIENTE','CONTRATO_ID']]    
    cli_res = cli_res.drop_duplicates(subset='NOMBRE_CLIENTE')
    
    # 2.5 Filtrar en reservas con lotes por lista de contratos    
    reservas_agrupadas_cantidad = reservas.copy()
    reservas_agrupadas_cantidad = reservas_agrupadas_cantidad.groupby(by=['PRODUCT_ID','LOTE_ID'])['EGRESO_TEMP'].sum().reset_index()
    reservas_agrupadas_contratos = reservas.copy()
    reservas_agrupadas_contratos['CONTRATO_ID'] = reservas_agrupadas_contratos['CONTRATO_ID'].astype('str')
    reservas_agrupadas_contratos = reservas_agrupadas_contratos.pivot_table(
        index=[
            'PRODUCT_ID',
            'LOTE_ID'
        ], values='CONTRATO_ID', aggfunc = lambda x: ' - '.join(x)).reset_index()
    
    # 2.6 Reservas agrupadas
    reservas_agrupadas = reservas_agrupadas_cantidad.merge(reservas_agrupadas_contratos, on=['PRODUCT_ID','LOTE_ID'], how='left')
    
    # iterar y crear reporte
    resultados = []
    for index, row in reservas_agrupadas.iterrows():
        
        stock = inventario[inventario['PRODUCT_ID']==row['PRODUCT_ID']].copy()
        stock['LOTE_ID'] = quitar_puntos(stock['LOTE_ID'])
        stock = stock.groupby(by=['PRODUCT_ID','LOTE_ID','FECHA_CADUCIDAD'])['OH2'].sum()
        stock = pd.DataFrame(stock).reset_index()
        stock = stock.sort_values(by='FECHA_CADUCIDAD').reset_index(drop=True)
        
        if len(stock) > 1:
            
            row_lote_id = row['LOTE_ID'].replace('.','')
            row_lote_id = row_lote_id.rstrip()
            row_lote_id = row_lote_id.lstrip()
            
            ubicacion_lote = stock[stock['LOTE_ID']==row_lote_id].index[0]
            ultimo_lote_index = len(stock) - 1
            
            if ubicacion_lote < ultimo_lote_index:
                reserva_product_lote = df_reservas_lote[
                    (df_reservas_lote['PRODUCT_ID'] == row['PRODUCT_ID']) &
                    (df_reservas_lote['LOTE_ID'] == row['LOTE_ID'])
                ][[
                    'CONTRATO_ID', 
                    'PRODUCT_ID', 
                    'LOTE_ID', 
                    'FECHA_CADUCIDAD', 
                    'EGRESO_TEMP', 
                    'WARE_CODE'
                ]]
                
                resultados.append(reserva_product_lote)
            
    if resultados:
        reporte_final = pd.concat(resultados, ignore_index=True)
        reporte_final['FECHA_CADUCIDAD'] = reporte_final['FECHA_CADUCIDAD'].astype('str')
        reporte_final = reporte_final.merge(cli_res, on='CONTRATO_ID', how='left')
        reporte_final = reporte_final[[
            'NOMBRE_CLIENTE',
            'CONTRATO_ID',
            'PRODUCT_ID',
            'LOTE_ID',
            'FECHA_CADUCIDAD',
            'EGRESO_TEMP',
            'WARE_CODE'
        ]]
        
        return reporte_final

    else:
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
    return stock_lote



### Consulta a tabla de trasavilidad
def trazabilidad_odbc(cod, lot):

    cnxn = pyodbc.connect('DSN=mba3;PWD=API')
    # cursorOdbc = cnxn.cursor()

    # cod = 'LR10090'
    # lot = '30122234'

    query = (
        "SELECT INVT_Lotes_Trasabilidad.DOC_ID_CORP, INVT_Lotes_Trasabilidad.PRODUCT_ID_CORP, INVT_Lotes_Trasabilidad.LOTE_ID, "
        "INVT_Lotes_Trasabilidad.AVAILABLE, INVT_Lotes_Trasabilidad.COMMITED, INVT_Lotes_Trasabilidad.EGRESO_TEMP, INVT_Lotes_Trasabilidad.OH, "
        "INVT_Lotes_Trasabilidad.Ingreso_Egreso, INVT_Lotes_Trasabilidad.Tipo_Movimiento, INVT_Lotes_Trasabilidad.Id_Linea_Egreso_Movimiento, "
        "INVT_Lotes_Trasabilidad.Link_Id_Linea_Ingreso, INVT_Lotes_Trasabilidad.CONFIRMADO, INVT_Lotes_Trasabilidad.Devolucio_MP, INVT_Lotes_Trasabilidad.Lote_Agregado, "
        "INVT_Lotes_Trasabilidad.WARE_COD_CORP, "
        "INVT_Ajustes_Principal.DATE_I , CLNT_Factura_Principal.FECHA_FACTURA, CLNT_Ficha_Principal.NOMBRE_CLIENTE, INVT_Lotes_Trasabilidad.Codigo_Alt_Clnt, CLNT_Pedidos_Principal.FECHA_DESDE "
        "FROM INVT_Lotes_Trasabilidad INVT_Lotes_Trasabilidad "
        "LEFT JOIN INVT_Ajustes_Principal INVT_Ajustes_Principal "
        "ON INVT_Lotes_Trasabilidad.DOC_ID_CORP = INVT_Ajustes_Principal.DOC_ID_CORP "
        "LEFT JOIN CLNT_Factura_Principal CLNT_Factura_Principal "
        "ON INVT_Lotes_Trasabilidad.DOC_ID_CORP = CLNT_Factura_Principal.CODIGO_FACTURA "
        "LEFT JOIN CLNT_Ficha_Principal CLNT_Ficha_Principal "
        "ON INVT_Lotes_Trasabilidad.Codigo_Alt_Clnt = CLNT_Ficha_Principal.CODIGO_CLIENTE "
        "LEFT JOIN CLNT_Pedidos_Principal CLNT_Pedidos_Principal "
        "ON INVT_Lotes_Trasabilidad.DOC_ID_CORP = CLNT_Pedidos_Principal.CONTRATO_ID_CORP "
        f"WHERE (INVT_Lotes_Trasabilidad.PRODUCT_ID_CORP='{cod}-GIMPR') AND (INVT_Lotes_Trasabilidad.LOTE_ID LIKE '%{lot}%') AND (INVT_Lotes_Trasabilidad.CONFIRMADO=TRUE) "
        "ORDER BY INVT_Lotes_Trasabilidad.LINK_ID_LINEA_INGRESO"
    )
    
    df_trazabilidad = pd.read_sql_query(query, cnxn)
    
    return df_trazabilidad





### Consulta pedidos cuenca
# def pedidos_cuenca_odbc():

#     # cnxn = pyodbc.connect('DSN=mba3;PWD=API')

#     open_ssh_tunnel()
#     mysql_connect()

#     df = run_query(
#         # "SELECT orders.id,seller_code,client_code,client_name,client_identification,orders.created_at,order_products.product_id,orders.status,order_products.product_name,"
#         # "order_products.product_group_code,order_products.quantity,order_products.price FROM orders LEFT JOIN order_products "
#         # "ON orders.id = order_products.order_id where seller_code='VEN03' AND orders.status='TCR';"
        
#         "SELECT orders.id,seller_code,client_code,client_name,client_identification,orders.created_at,order_products.product_id,orders.status,order_products.product_name,"
#         "order_products.product_group_code,order_products.quantity,order_products.price FROM orders LEFT JOIN order_products "
#         "ON orders.id = order_products.order_id where seller_code='VEN03' AND orders.status='TCR';"
#     )
#     print(df)
#     # df = pd.read_sql_query(query, cnxn)
    
#     mysql_disconnect()
#     close_ssh_tunnel()
    
#     return df



# Filtrar avance de etiquetado por pedido
def etiquetado_avance_pedido(n_pedido):
    avance = EtiquetadoAvance.objects.filter(n_pedido=n_pedido).values()
    avance = pd.DataFrame(avance)
    avance = avance.rename(columns={
        # 'n_pedido':'CONTRADO_ID',
        'product_id':'PRODUCT_ID'
        })
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
        
    return stock_lote


def wms_reservas_lotes_datos():
    r_lote = reservas_lote()[['CONTRATO_ID','CODIGO_CLIENTE','PRODUCT_ID','LOTE_ID','EGRESO_TEMP']]
    r_lote = r_lote.rename(columns={
        'PRODUCT_ID':'product_id',
        'LOTE_ID':'lote_id'}
    ).drop_duplicates(subset=['product_id','lote_id'])   
    
    # cli = clientes_warehouse()[['CODIGO_CLIENTE','NOMBRE_CLIENTE']]
    # r_lote = r_lote.merge(cli, on='CODIGO_CLIENTE', how='left').drop_duplicates(subset=['product_id','lote_id'])
    
    return r_lote


def wms_reservas_lote_consulta(product_id, lote_id):
    
    with connections['gimpromed_sql'].cursor() as cursor:
        
        cursor.execute(f"SELECT * FROM reservas_lote WHERE PRODUCT_ID = '{product_id}' AND LOTE_ID = '{lote_id}' ")
        
        columns = [col[0] for col in cursor.description]
        r_lote = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
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

    cnxn = pyodbc.connect('DSN=mba3;PWD=API')
    
    query = ("SELECT CLNT_Factura_Principal.CODIGO_FACTURA, CLNT_Factura_Principal.CODIGO_CLIENTE, CLNT_Factura_Principal.FECHA_FACTURA, INVT_Ficha_Principal.PRODUCT_ID, INVT_Ficha_Principal.PRODUCT_NAME, INVT_Ficha_Principal.GROUP_CODE, INVT_Lotes_Trasabilidad.EGRESO_TEMP, INVT_Lotes_Trasabilidad.LOTE_ID, INVT_Lotes_Trasabilidad.FECHA_CADUCIDAD, INVT_Ficha_Principal.Custom_Field_1, CLNT_Factura_Principal.NUMERO_PEDIDO_SISTEMA "
    "FROM CLNT_Factura_Principal CLNT_Factura_Principal, INVT_Ficha_Principal INVT_Ficha_Principal, INVT_Lotes_Trasabilidad INVT_Lotes_Trasabilidad "
    # "WHERE INVT_Lotes_Trasabilidad.PRODUCT_ID_CORP = INVT_Ficha_Principal.PRODUCT_ID_CORP AND CLNT_Factura_Principal.CODIGO_FACTURA = INVT_Lotes_Trasabilidad.DOC_ID_CORP AND ((CLNT_Factura_Principal.CODIGO_FACTURA='FCSRI-1001000080547-GIMPR') AND (CLNT_Factura_Principal.ANULADA=FALSE))")
    f"WHERE INVT_Lotes_Trasabilidad.PRODUCT_ID_CORP = INVT_Ficha_Principal.PRODUCT_ID_CORP AND CLNT_Factura_Principal.CODIGO_FACTURA = INVT_Lotes_Trasabilidad.DOC_ID_CORP AND ((CLNT_Factura_Principal.CODIGO_FACTURA='{n_factura}') AND (CLNT_Factura_Principal.ANULADA=FALSE))")
    
    df = pd.read_sql_query(query, cnxn)
    cli = clientes_warehouse()[['CODIGO_CLIENTE','NOMBRE_CLIENTE','IDENTIFICACION_FISCAL']]
    df = df.merge(cli, on='CODIGO_CLIENTE', how='left')
    df['FECHA_FACTURA']   = df['FECHA_FACTURA'].astype(str)
    df['FECHA_CADUCIDAD'] = df['FECHA_CADUCIDAD'].astype(str)
    df['NUMERO_PEDIDO_SISTEMA'] = df['NUMERO_PEDIDO_SISTEMA'].astype(str) + '.0'
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
        
    return stock


def wms_datos_nota_entrega(nota_entrega):
    
    try:
        cnxn = pyodbc.connect('DSN=mba3;PWD=API')
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
        
        df = pd.read_sql_query(query, cnxn)
        
        prod_id_list = []
        
        for i in df['PRODUCT_ID_CORP']:
            prod_id = i.replace('-GIMPR','')
            prod_id_list.append(prod_id)
        
        df['product_id'] = prod_id_list
        df['doc_id']     = nota_entrega
        
        df = df.rename(columns={
            'DOC_ID_CORP':'doc_id_corp',
            'LOTE_ID':'lote_id',
            'EGRESO_TEMP':'unidades',
            'FECHA_CADUCIDAD':'fecha_caducidad'
        })
        
        df = df[['doc_id_corp', 'doc_id','product_id','lote_id','fecha_caducidad','unidades']]
        df = df[df['unidades']!=0]
        
        return df.to_dict(orient='records')
    
    except Exception as e:
        print(e)
    finally:
        cnxn.close()
        
        
        
def wms_ajuste_query_odbc(n_ajuste):
    
    cnxn = pyodbc.connect('DSN=mba3;PWD=API')
    cursorOdbc = cnxn.cursor()
    
    # La variable 'n' no está siendo usada en la consulta. Asegúrate de que sea necesario.
    n = 'A-00000' + str(n_ajuste) + '-GIMPR'
    
    #Transferencia Egreso
    try:

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
        
        inventario_df['product_id'] = list(map(lambda x:x[:-6], list(inventario_df['PRODUCT_ID_CORP'])))
        
        return inventario_df
        
    except Exception as e:
        print(e)
    
    finally:
        cursorOdbc.close()
        

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
        
        return email
    
# Obtener todas las proformas
def lista_proformas_odbc():
    
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute("SELECT * FROM proformas")
        columns = [col[0] for col in cursor.description]
        proformas = [dict(zip(columns, row)) for row in cursor.fetchall()]
        proformas = pd.DataFrame(proformas)
        
    return proformas

# Obtener una proforma por contrato_id
def proformas_por_contrato_id_odbc(contrato_id):
    
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(f"SELECT * FROM proformas WHERE contrato_id = '{contrato_id}'")
        columns = [col[0] for col in cursor.description]
        proformas = [dict(zip(columns, row)) for row in cursor.fetchall()]
        proformas = pd.DataFrame(proformas)
        
    return proformas


def actualizar_proformas_ajax(request):
    
    try:
        today = datetime.today() - timedelta(days=45)
        today = today.strftime('%Y-%m-%d')
        
        # MBA ODBC
        cnx_odbc_mba     = pyodbc.connect('DSN=mba3;PWD=API')
        cursor_odbc_mba  = cnx_odbc_mba.cursor()
        
        # DB WAREHOUSE
        cnx_db_warehouse = mysql.connector.connect(
            host="172.16.28.102",
            user="standard",
            passwd="gimpromed",
            database="warehouse"
        )
        
        cursor_db_warehouse = cnx_db_warehouse.cursor()
        
        sql_query = cursor_odbc_mba.execute(                        
            "SELECT CLNT_Pedidos_Principal.CONTRATO_ID, CLNT_Ficha_Principal.NOMBRE_CLIENTE, CLNT_Pedidos_Principal.FECHA_PEDIDO, CLNT_Pedidos_Principal.FECHA_HASTA, "
            "CLNT_Pedidos_Principal.SALESMAN, CLNT_Pedidos_Principal.CONFIRMED, CLNT_Pedidos_Detalle.PRODUCT_ID, CLNT_Pedidos_Detalle.QUANTITY "
            "FROM CLNT_Ficha_Principal CLNT_Ficha_Principal, CLNT_Pedidos_Detalle CLNT_Pedidos_Detalle, CLNT_Pedidos_Principal CLNT_Pedidos_Principal "
            "WHERE CLNT_Pedidos_Detalle.CONTRATO_ID_CORP = CLNT_Pedidos_Principal.CONTRATO_ID_CORP AND "
            f"CLNT_Ficha_Principal.CODIGO_CLIENTE_EMPRESA = CLNT_Pedidos_Principal.CLIENT_ID_CORP AND CLNT_Pedidos_Principal.FECHA_PEDIDO >='{today}' AND ((CLNT_Pedidos_Detalle.TIPO_DOCUMENTO='CT') AND (CLNT_Pedidos_Principal.VOID=False))"
        )
        
        sql_query = sql_query.fetchall()
        sql_query = [list(rows) for rows in sql_query]
    
        cursor_db_warehouse.execute("DELETE FROM proformas")
        cnx_db_warehouse.commit()
        
        sql_insert = """INSERT INTO proformas (contrato_id,nombre_cliente,fecha_pedido,fecha_hasta,salesman,confirmed,product_id,quantity) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        
        cursor_db_warehouse.executemany(sql_insert, sql_query)
        cnx_db_warehouse.commit()
        
        return JsonResponse({
            'tipo':'success',
            'msg': 'Proformas actualizadas exitosamente !!!'
            })
    
    except Exception as e:
        return JsonResponse({
            'tipo':'danger',
            'msg': f'Error {e} !!!'
            })
        
    finally:
        cnx_db_warehouse.close()
        cursor_odbc_mba.close()
    
    
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
        
    return anexo_product_list



# ESTRAER NÚMERO DE FACTURA
def extraer_numero_de_factura(fac):
    
    try:
        n_fac = fac.split('-')[1][6:]
        n_fac = str(int(n_fac))
        return n_fac
    except:
        return fac


## DATOS ANEXOS FACTURA
def datos_factura_compras_publicas_cabecera_odbc(n_factura):

    cnxn = pyodbc.connect('DSN=mba3;PWD=API')
    cursorOdbc = cnxn.cursor()

    cursorOdbc.execute(       
        
        "SELECT "
        "CLNT_Factura_Principal.CODIGO_FACTURA, "
        "CLNT_Factura_Principal.FECHA_FACTURA, "
        "CLNT_Factura_Principal.NUMERO_PEDIDO_SISTEMA, "
        "CLNT_Factura_Principal.CODIGO_CLIENTE, "
        "CLNT_Ficha_Principal.NOMBRE_CLIENTE, "
        "CLNT_Ficha_Principal.IDENTIFICACION_FISCAL, "
        "CLNT_Ficha_Principal.DIRECCION_PRINCIPAL_1 "
        
        "FROM "
        "CLNT_Factura_Principal "
        "INNER JOIN CLNT_Ficha_Principal ON CLNT_Factura_Principal.CODIGO_CLIENTE = CLNT_Ficha_Principal.CODIGO_CLIENTE "
        
        "WHERE "
        f"CLNT_Factura_Principal.CODIGO_FACTURA = '{n_factura}'"
        
    )

    columns = [col[0] for col in cursorOdbc.description]
    datos   = [dict(zip(columns, row)) for row in cursorOdbc.fetchall()][0]
    
    return datos


def datos_factura_compras_publicas_productos_odbc(n_factura):
    
    cnxn = pyodbc.connect('DSN=mba3;PWD=API')
    cursorOdbc = cnxn.cursor()

    cursorOdbc.execute(
        
        "SELECT "
        "CLNT_Factura_Principal.CODIGO_FACTURA, "
        "CLNT_Factura_Principal.FECHA_FACTURA, "
        "INVT_Ficha_Principal.PRODUCT_ID, "
        "INVT_Ficha_Principal.PRODUCT_NAME, "
        "INVT_Ficha_Principal.GROUP_CODE, "
        "INVT_Producto_Movimientos.QUANTITY, "
        "INVT_Ficha_Principal.Custom_Field_1, "
        "INVT_Ficha_Principal.Custom_Field_2, "
        "INVT_Lotes_Trasabilidad.LOTE_ID, "
        "INVT_Lotes_Trasabilidad.FECHA_CADUCIDAD, "
        "INVT_Producto_Lotes.Fecha_elaboracion_lote, "
        "INVT_Lotes_Trasabilidad.Precio_venta "
        
        "FROM "
        "CLNT_Factura_Principal CLNT_Factura_Principal, "
        "INVT_Ficha_Principal INVT_Ficha_Principal, "
        "INVT_Lotes_Trasabilidad INVT_Lotes_Trasabilidad, "
        "INVT_Producto_Lotes INVT_Producto_Lotes, "
        "INVT_Producto_Movimientos INVT_Producto_Movimientos "
        
        "WHERE "
        "CLNT_Factura_Principal.CODIGO_FACTURA = INVT_Producto_Movimientos.DOC_ID_CORP2 "
        "AND INVT_Lotes_Trasabilidad.PRODUCT_ID_CORP = INVT_Ficha_Principal.PRODUCT_ID_CORP "
        "AND CLNT_Factura_Principal.CODIGO_FACTURA = INVT_Lotes_Trasabilidad.DOC_ID_CORP AND "
        "INVT_Lotes_Trasabilidad.PRODUCT_ID_CORP = INVT_Producto_Lotes.PRODUCT_ID_CORP AND "
        "INVT_Lotes_Trasabilidad.LOTE_ID = INVT_Producto_Lotes.LOTE_ID AND "
        "INVT_Producto_Movimientos.PRODUCT_ID_CORP = INVT_Lotes_Trasabilidad.PRODUCT_ID_CORP AND "
        "INVT_Lotes_Trasabilidad.WARE_COD_CORP = INVT_Producto_Lotes.WARE_CODE_CORP AND "
        "INVT_Producto_Movimientos.UNIT_COST = INVT_Lotes_Trasabilidad.Precio_venta AND "
        "((INVT_Producto_Movimientos.CONFIRM=TRUE) AND (CLNT_Factura_Principal.CODIGO_FACTURA='FCSRI-1001000090896-GIMPR') AND "
        f"((INVT_Producto_Movimientos.CONFIRM=TRUE) AND (CLNT_Factura_Principal.CODIGO_FACTURA='{n_factura}') AND "
        #"(INVT_Producto_Movimientos.I_E_SIGN='-') AND (INVT_Producto_Movimientos.ADJUSTMENT_TYPE='FT') AND "
        "(CLNT_Factura_Principal.ANULADA=FALSE))"
    )

    columns = [col[0] for col in cursorOdbc.description]
    datos   = [dict(zip(columns, row)) for row in cursorOdbc.fetchall()]

    datos   = pd.DataFrame(datos)
    # print(datos)
    return datos