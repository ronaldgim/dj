from django.shortcuts import render

# BD
from django.db import connections

# Datetime
from datetime import datetime

# Tabla clientes
from etiquetado.views import clientes_table

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


# Funcios para pasar de dataframe a registros para el template
def de_dataframe_a_template(dataframe):

    json_records = dataframe.reset_index().to_json(orient='records') # reset_index().
    dataframe = json.loads(json_records)
    
    return dataframe


# Create your views here.
# tabla de facturas
def tabla_facturas():
    ''' Colusta de clientes por ruc a la base de datos '''
    with connections['gimpromed_sql'].cursor() as cursor:
        #cursor.execute("SELECT * FROM reservas WHERE CONTRATO_ID = %s", [n_pedido])
        #cursor.execute("SELECT * FROM clientes WHERE CLIENT_TYPE = %s", ['HOSPU'])
        cursor.execute("SELECT * FROM venta_facturas")
        columns = [col[0] for col in cursor.description]
        facturas = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
        
        facturas = pd.DataFrame(facturas)
    return facturas 


# Tabla producto
def tabla_productos_mba_django():
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute("SELECT * FROM productos")
        columns = [col[0] for col in cursor.description]
        products = [ # Lista de diccionarios
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
    products_mba = pd.DataFrame(products)
    products_mba = products_mba.rename(columns={'Codigo':'product_id'})
    products_django = pd.DataFrame(Product.objects.all().values())
    products = products_mba.merge(products_django, on='product_id', how='left')

    return products


# Tabla infimas
def tabla_infimas():
    
    with connections['infimas_sql'].cursor() as cursor:
        cursor.execute(
            """SELECT infimas.Fecha, entidad.Nombre, infimas.Proveedor,
            infimas.Objeto_Compra, infimas.Cantidad, infimas.Costo, infimas.Valor, infimas.Tipo_Compra, entidad.Nombre
            FROM entidad, infimas
            WHERE infimas.Codigo_Entidad = entidad.Codigo"""
        )
        columns = [col[0] for col in cursor.description]
        infimas = [ # Lista de diccionarios
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
    infimas = pd.DataFrame(infimas)
    infimas['Fecha'] = infimas['Fecha'].astype(str)
    infimas = infimas[infimas['Fecha']>'2021-01-01']
    infimas = infimas.sort_values(by=['Fecha'], ascending=[False])
    infimas = infimas[infimas['Tipo_Compra']=='Otros Bienes']
    infimas = infimas.reset_index()

    return infimas


# precios historicos
def precios_historicos(request):

    # DATOS
    facturas = tabla_facturas() # Tabla facturas
    clientes = clientes_table() # Tabla clientes
    productos = tabla_productos_mba_django() # Tabla productos
    # infimas = tabla_infimas() # Tabla infimas
    # infimas = de_dataframe_a_template(infimas)
    
    # FILTRADO DESDE AÑO 2021
    facturas = facturas[(facturas['FECHA']>'2021-01-01')]

    # FILTRAR COLUMNAS FACTURAS
    facturas = facturas[[
        'CODIGO_CLIENTE', 
        'FECHA', 
        'PRODUCT_ID',
        'QUANTITY', 
        'UNIT_PRICE']]

    # FILTRAR COLUMNAS PRODUCTOS
    productos = productos[[
        'product_id', 
        'Nombre', 
        'Marca',
        'Reg_San'
    ]]
    productos = productos.rename(columns={'product_id':'PRODUCT_ID'})

    # FILTRAR COLUMNAS DE CLIENTES
    clientes = clientes[[
        'CODIGO_CLIENTE',
        'NOMBRE_CLIENTE',
        'CLIENT_TYPE'
    ]]

    # PRECIOS HISTORICOS
    precios = facturas.merge(clientes, on='CODIGO_CLIENTE', how='left')

    # FILTRAR POR HOSPITALES PUBLICOS
    precios = precios[precios['CLIENT_TYPE']=='HOSPU']

    # AÑADIR NOMBRE Y MARCA DE PRODUCTOS
    precios = precios.merge(productos, on='PRODUCT_ID', how='left')
    precios = precios.sort_values(by=['FECHA'], ascending=[False])

    # FILTROS
    hospitales = precios['NOMBRE_CLIENTE'].unique()

    precios_template = de_dataframe_a_template(precios)

    # resumen_hospital = resumen_hospital.groupby('PRODUCT_ID').agg({'UNIT_PRICE':['min', 'max', 'mean','count']})
    if request.method == 'POST':
        precios_filter = precios
        precios_exclude = precios
        
        hospital = request.POST['hospital']
        h = str(hospital)
        # TABLE FILTRADA
        precios_filtrado = precios_filter[precios_filter['NOMBRE_CLIENTE']==h]
        precios_filtrado = precios_filtrado.sort_values(by=['FECHA'], ascending=[False])
        precios_filtrado = de_dataframe_a_template(precios_filtrado)

        precios_excluido = precios_exclude[precios_exclude['NOMBRE_CLIENTE']!=h]
        precios_excluido = de_dataframe_a_template(precios_excluido)

        context = {
            'precios_filtrado':precios_filtrado,
            'precios_excluido': precios_excluido,
            'hospitales':hospitales,
            'hospital':hospital,
            #'infimas':infimas
            }

        return render(request, 'compras_publicas/precios.html', context)

    context = {
        'precios':precios_template,
        'hospitales':hospitales,
        #'infimas':infimas
    }

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
    
    infimas = tabla_infimas()[:100] # Tabla infimas    
    infimas = de_dataframe_a_template(infimas)
    
    inf = Paginator(infimas, 1)
    
    # print(inf.count)
    # print(inf.num_pages)
    
    inf2 = inf.page(2)
    print(inf2.object_list)
    

    if request.method == 'POST':
        busqueda = request.POST['busqueda']
        infimas_df = tabla_infimas()
        infimas_df['Objeto_Compra'] = infimas_df['Objeto_Compra'].astype(str)
        infimas_df['Objeto_Compra'] = infimas_df.Objeto_Compra.str.lower()
        infimas_df = infimas_df[infimas_df['Objeto_Compra'].str.contains(busqueda)] #contains(busqueda)
        resultados = len(infimas_df)
        infimas_df = de_dataframe_a_template(infimas_df)

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

