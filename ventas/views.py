from django.shortcuts import render

import pandas as pd

# Date
from datetime import date, datetime, timedelta

# Ventas facturas odbc
from datos.views import (
    ventas_odbc_facturas, 
    de_dataframe_a_template, 
    productos_odbc_and_django, 
    clientes_warehouse, 
    lotes_facturas_odbc,
    pedidos_cuenca_odbc,
    ventas_desde_fecha
    )


# Http
from django.http import HttpResponse

# JSON
import json


# Reporte de ventas
def reporte_tipo_mba(request):

    desde = datetime.strptime('2023-01-01', '%Y-%m-%d')
    hasta = date.today()

    h = str(date.today())

    ventas = ventas_odbc_facturas()[:20]
    ventas = ventas[(ventas['FECHA']>='2023-01-01') & (ventas['FECHA']<=h)]
    prod = productos_odbc_and_django()[['product_id', 'Unidad', 'Nombre', 'Marca']]
    prod = prod.rename(columns={'product_id':'PRODUCT_ID'})
    cliente_list = clientes_warehouse()[['CODIGO_CLIENTE', 'NOMBRE_CLIENTE']]

    ventas = ventas.merge(prod, on='PRODUCT_ID', how='left')
    ventas = ventas.merge(cliente_list, on='CODIGO_CLIENTE', how='left')

    ventas = de_dataframe_a_template(ventas)

    clientes = clientes_warehouse()[['CODIGO_CLIENTE', 'NOMBRE_CLIENTE']]
    clientes = clientes.sort_values('NOMBRE_CLIENTE')

    if request.method == 'POST':
        cli = request.POST.get('cliente', '')
        desde = request.POST.get('desde', '')
        hasta = request.POST.get('hasta', '')

        d=datetime.strptime(desde, '%Y-%m-%d')
        h=datetime.strptime(hasta, '%Y-%m-%d')

        vent = ventas_odbc_facturas()
        vent = vent[(vent['FECHA']>=desde) & (vent['FECHA']<=hasta) & (vent['CODIGO_CLIENTE']==cli)]
        vent = vent.merge(prod, on='PRODUCT_ID', how='left')
        vent = vent.merge(cliente_list, on='CODIGO_CLIENTE', how='left')
        
        vent['UNIT_PRICE'] = vent['UNIT_PRICE'].round(2)
        vent['COST_TOTAL'] = vent['COST_TOTAL'].round(2)

        total_cantidad =  vent['QUANTITY'].sum()
        total_unitario = vent['UNIT_PRICE'].sum()
        total_ventas = vent['COST_TOTAL'].sum()
        
        vent = de_dataframe_a_template(vent)

        cliente = cliente_list.set_index('CODIGO_CLIENTE')
        cliente = cliente.to_dict()['NOMBRE_CLIENTE']
        cliente = cliente[cli] 

        context = {
            'ventas':vent,
            'total_cantidad':total_cantidad,
            'total_unitario':total_unitario,
            'total_ventas':total_ventas,

            'clientes':de_dataframe_a_template(clientes),

            'cliente':cliente,
            'desde':d,
            'hasta':h,
        }

        return render(request, 'ventas/reporte_ventas.html', context)

    context = {
        'ventas':ventas,
        'clientes':de_dataframe_a_template(clientes),

        'desde':desde,
        'hasta':hasta
    }

    return render(request, 'ventas/reporte_ventas.html', context)


# lote y cantidad por factura en reporte ventas
def lote_factura_ajax(request):

    fac = request.POST['fac']
    cod = request.POST['cod']

    lote_factura = lotes_facturas_odbc(fac, cod) #;print(lote_factura[0]);print(type(lote_factura[0]))

    response = json.dumps(lote_factura)

    return HttpResponse(response, content_type='appliation/json')


# Pedidos cuenca 
def pedidos_cuenca(request):
    
    hoy = datetime.now().date()
    seis_meses = hoy - timedelta(days=180)
    seis_meses = datetime.combine(seis_meses, datetime.min.time())
    tres_meses = hoy - timedelta(days=90) 
    tres_meses = datetime.combine(tres_meses, datetime.min.time())
    
    ciudades = ['AZOGUES', 'CUENCA']
    clientes = clientes_warehouse()[['CODIGO_CLIENTE', 'NOMBRE_CLIENTE', 'IDENTIFICACION_FISCAL', 'CIUDAD_PRINCIPAL']]
    clientes = clientes[clientes.CIUDAD_PRINCIPAL.isin(ciudades)]
    
    pedido = pedidos_cuenca_odbc()
    pedidos_product = pedido['product_id'].unique()

    # pedidos_product = ['B0116', '37060', '1600', 'LP16040']
    pedidos_client  = clientes['CODIGO_CLIENTE'].unique()
        
    ventas = ventas_desde_fecha(seis_meses)
    ventas = ventas[ventas.PRODUCT_ID.isin(pedidos_product)]
    ventas = ventas[ventas.CODIGO_CLIENTE.isin(pedidos_client)]
    ventas = ventas.sort_values(by='FECHA')
    ventas['FECHA'] = pd.to_datetime(ventas['FECHA'])
    ventas = ventas.merge(clientes, on='CODIGO_CLIENTE', how='left')
    
    # Ventas de hoy a 3 meses atras
    ventas_tres_meses = ventas[ventas['FECHA']>tres_meses]
    #print(ventas_tres_meses)
    
    # Ventas desde 6 meses a tres meses
    # ventas_seis_meses = ventas[ventas['FECHA']<(tres_meses - timedelta(weeks=2))]
    ventas_seis_meses = ventas[ventas['FECHA']<tres_meses]
    
    
        
    # UTILIZAR SET {} PARA SABER CUALES NO SE HAN VENDIDO EN 6 MESES
    
    # pedidos = de_dataframe_a_template(pedidos)
    
    context = {
        # 'pedido':pedido,
        'ventas':ventas
    }
    
    return render(request, 'ventas/pedidos_cuenca.html', context)


# Procesos Guantes
def procesos_guantes(request):
    print('procesos_gunates')
    
