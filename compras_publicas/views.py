from django.shortcuts import render

# BD
from django.db import connections

# Datetime
from datetime import datetime, timedelta

# Tabla productos DJANGO
from datos.models import Product

# Pandas
import pandas as pd
import numpy as np

# Json
import json

# Pyodbc
import pyodbc
import mysql.connector

# Paginado
from django.core.paginator import Paginator

# Model
from compras_publicas.models import ProcesosSercop

# Forms
from compras_publicas.forms import ProcesosSercopForm

# Messages
from django.contrib import messages

# Django shortcuts
from django.shortcuts import render, redirect

# Clientes
from datos.views import clientes_warehouse, productos_odbc_and_django

# http response
from django.http import HttpResponse

# Funcios para pasar de dataframe a registros para el template
def de_dataframe_a_template(dataframe):

    json_records = dataframe.reset_index().to_json(orient='records') # reset_index().
    dataframe = json.loads(json_records)

    return dataframe


# Create your views here.
# tabla de facturas
def tabla_facturas(cliente):
    ''' Colusta de clientes por ruc a la base de datos '''
    with connections['gimpromed_sql'].cursor() as cursor:
        #cursor.execute("SELECT * FROM venta_facturas")
        cursor.execute(
            f"SELECT * FROM warehouse.venta_facturas WHERE CODIGO_CLIENTE = '{cliente}' AND FECHA > '2021-01-01'"
        )

        columns = [col[0] for col in cursor.description]
        facturas = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        facturas = pd.DataFrame(facturas)
    return facturas


# Tabla infimas
def tabla_infimas():

    one_year = datetime.now().date()
    days = 365
    one_year_ago = one_year - timedelta(days=days)

    with connections['infimas_sql'].cursor() as cursor:
        cursor.execute(
            # """SELECT infimas.Fecha, entidad.Nombre, infimas.Proveedor,
            # infimas.Objeto_Compra, infimas.Cantidad, infimas.Costo, infimas.Valor, infimas.Tipo_Compra, entidad.Nombre
            # FROM entidad, infimas
            # WHERE infimas.Codigo_Entidad = entidad.Codigo"""

            f"""SELECT infimas.Fecha, entidad.Nombre, infimas.Proveedor,
            infimas.Objeto_Compra, infimas.Cantidad, infimas.Costo, infimas.Valor,
            infimas.Tipo_Compra, entidad.Nombre

            FROM entidad, infimas
            WHERE infimas.Codigo_Entidad = entidad.Codigo
            AND infimas.Fecha > '{one_year_ago}'
            AND infimas.Tipo_Compra = 'Otros Bienes'
            """
        )
        columns = [col[0] for col in cursor.description]
        infimas = [ # Lista de diccionarios
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
    infimas = pd.DataFrame(infimas)
    infimas['Fecha'] = infimas['Fecha'].astype(str)
    # infimas = infimas[infimas['Fecha']>'2023-01-01']
    infimas = infimas.sort_values(by=['Fecha'], ascending=[False])
    # infimas = infimas[infimas['Tipo_Compra']=='Otros Bienes']
    infimas = infimas.reset_index()

    return infimas



def clientes_hospitales_publicos():

    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(
        "SELECT CODIGO_CLIENTE, NOMBRE_CLIENTE, CLIENT_TYPE FROM warehouse.clientes WHERE CLIENT_TYPE = 'HOSPU'"
    )

        columns = [col[0] for col in cursor.description]
        hpublicos = [ # Lista de diccionarios
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

    return hpublicos


def facturas_por_product(producto):

    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(
        f"SELECT * FROM warehouse.venta_facturas WHERE PRODUCT_ID = '{producto}' AND FECHA > '2021-01-01'"
    )

        columns = [col[0] for col in cursor.description]
        producto = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
        
        producto = pd.DataFrame(producto)
        prod = productos_odbc_and_django()[['product_id','Nombre','Marca']]
        prod = prod.rename(columns={'product_id':'PRODUCT_ID'})
        cli  = clientes_warehouse()[['CODIGO_CLIENTE','NOMBRE_CLIENTE']]
        
        producto = producto.merge(prod, on='PRODUCT_ID', how='left')
        producto = producto.merge(cli, on='CODIGO_CLIENTE', how='left')
        
        producto = producto.rename(columns={
            'PRODUCT_ID':'Código',
            'FECHA':'Fecha',
            'QUANTITY':'Cantidad',
            'UNIT_PRICE':'Precio Unitario',
            'NOMBRE_CLIENTE':'Cliente'
        })
        
        producto = producto[['Código','Nombre','Marca','Cliente','Fecha','Cantidad','Precio Unitario']]

    return producto


def facturas_por_product_ajax(request):
    
    product_id = request.POST['producto']
    ventas = facturas_por_product(product_id)
    ventas['Precio Unitario'] = ventas['Precio Unitario'].astype(float)
    ventas['Cantidad'] = ventas['Cantidad'].apply(lambda x:'{:,.0f}'.format(x))
    ventas['Precio Unitario'] = ventas['Precio Unitario'].apply(lambda x:'$ {:,.2f}'.format(x))
    ventas = ventas.sort_values(by='Fecha', ascending=False)
    
    ventas = ventas.to_html(
        #classes='table', 
        table_id='v_table',
        index=False,
        justify='start',
        border=0
    )
    
    return HttpResponse(ventas)

    


# precios historicos
def precios_historicos(request):

    hospitales = clientes_hospitales_publicos()
    
    context = {
        'hospitales':hospitales,
    }
    
    if request.method == 'POST':
        try:        
            hospitales = clientes_hospitales_publicos()
            prod = productos_odbc_and_django()
            prod = prod.rename(columns={'product_id':'PRODUCT_ID'})
            
            hospital = request.POST['hospital']
            
            facturas = tabla_facturas(hospital)
            clientes = clientes_warehouse()[['CODIGO_CLIENTE', 'NOMBRE_CLIENTE']]
            
            precios_filtrado = facturas.merge(clientes, on='CODIGO_CLIENTE', how='left')
            precios_filtrado = precios_filtrado.merge(prod, on='PRODUCT_ID', how='left')
            precios_filtrado = precios_filtrado.sort_values(by=['FECHA'], ascending=[False])
            
            h = precios_filtrado['NOMBRE_CLIENTE'].iloc[0]
            
            precios_filtrado = de_dataframe_a_template(precios_filtrado)        

            context = {
                'h':h,
                'precios_filtrado':precios_filtrado,
                'hospitales':hospitales,
                }
        except:
            messages.error(request, 'Error, intente nuevamente !!!')
            
        return render(request, 'compras_publicas/precios.html', context)

    return render(request, 'compras_publicas/precios.html', context)



from django.http import JsonResponse

def my_ajax_view(request):
    data = {
        "key1": "value1",
        "key2": "value2",
    }

    # data = tabla_infimas()
    # data = data.to_json(orient='table')
    # data = json.loads(data)

    # print(data)
    return JsonResponse(data)


# Infimas
def infimas(request):

    infimas = tabla_infimas() #[:10] # Tabla infimas
    infimas = de_dataframe_a_template(infimas)

    paginator   = Paginator(infimas, 50)
    page_number = request.GET.get('page')

    if page_number == None:
        page_number = 1

    infimas = paginator.get_page(page_number)

    if request.method == 'POST':
        busqueda = request.POST['busqueda']
        infimas_df = tabla_infimas()
        infimas_df['Objeto_Compra'] = infimas_df['Objeto_Compra'].astype(str)
        infimas_df['Objeto_Compra'] = infimas_df.Objeto_Compra.str.lower()
        infimas_df = infimas_df[infimas_df['Objeto_Compra'].str.contains(busqueda)] #contains(busqueda)
        resultados = len(infimas_df)
        infimas_df = de_dataframe_a_template(infimas_df)

        # paginator = Paginator(infimas_df, 200)
        # page_number = 1 #request.POST.get('page')
        # infimas_df = paginator.get_page(page_number)

        context = {
            'infimas':infimas_df,
            'busqueda':busqueda,
            'resultados':resultados,
            }

        return render(request, 'compras_publicas/infimas.html', context)

    context = {
        'infimas':infimas
        }

    return render(request, 'compras_publicas/infimas.html', context)


def procesos_sercop_sql():
    with connections['procesos_sercop'].cursor() as cursor:
        cursor.execute("""
            SELECT * 
            FROM procesos_sercop.procesos
            LEFT JOIN procesos_sercop.fechas
            ON procesos_sercop.procesos.Codigo = procesos_sercop.fechas.Codigo
            """)

        columns  = [col[0] for col in cursor.description]
        procesos = [dict(zip(columns, row)) for row in cursor.fetchall()]

        procesos = pd.DataFrame(procesos)

        return procesos



def procesos_sercop(request):

    procesos = pd.DataFrame(ProcesosSercop.objects.all().order_by('-fecha_hora').values())
    procesos_sql = procesos_sercop_sql()
    procesos_sql = procesos_sql.rename(columns={'Codigo':'proceso'})

    procesos = procesos.merge(procesos_sql, on='proceso', how='left')
    procesos = procesos.sort_values(by=['fecha_hora','Fecha_Puja','Hora_Puja'], ascending=[False,False,True])
    
    procesos = de_dataframe_a_template(procesos)

    form = ProcesosSercopForm()

    if request.method == 'POST':
        form = ProcesosSercopForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'El proceso se agrego correctamente !!!')
            return redirect('/compras-publicas/procesos-sercop')

        else:
            messages.error(request, form.errors)
            return redirect('/compras-publicas/procesos-sercop')

    context = {
        'procesos':procesos,
        'form':form
    }

    return render(request, 'compras_publicas/procesos_sercop.html', context)
