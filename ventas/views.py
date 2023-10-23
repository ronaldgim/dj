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


def pedidos_cuenca_datos(n_pedido):

    # n_pedido = request.POST['n_pedido'] 
    hoy = datetime.now().date()
    seis_meses = hoy - timedelta(days=180)
    seis_meses = datetime.combine(seis_meses, datetime.min.time())
    tres_meses = hoy - timedelta(days=90) 
    tres_meses = datetime.combine(tres_meses, datetime.min.time())
    
    productos = productos_odbc_and_django()[['product_id','Nombre','Marca']]
    pedido = pedidos_cuenca_odbc(n_pedido)
    clientes = clientes_warehouse()[['CODIGO_CLIENTE','NOMBRE_CLIENTE','CIUDAD_PRINCIPAL', 'IDENTIFICACION_FISCAL']]
    codigo_cliente = pedido['client_code'][0]
    pedidos_product = pedido['product_id'].unique()

    # Ventas
    ventas = ventas_desde_fecha(seis_meses)
    ventas = ventas[ventas.PRODUCT_ID.isin(pedidos_product)]
    ventas = ventas[ventas['CODIGO_CLIENTE']==codigo_cliente]
    ventas = ventas.sort_values(by='FECHA')
    ventas['FECHA']  = pd.to_datetime(ventas['FECHA'])
    ventas['ALERTA'] = ventas.apply(lambda x: 'tres_meses' if x['FECHA'] < tres_meses else 'seis_meses', axis=1)
    ventas['FECHA']  = ventas['FECHA'].astype(str)
    ventas = ventas.rename(columns={'PRODUCT_ID':'product_id'})
    ventas = ventas.merge(productos, on='product_id', how='left')
    ventas = ventas.merge(clientes, on='CODIGO_CLIENTE', how='left')
    ventas = ventas.merge(pedido, on='product_id', how='left')
    ventas = ventas.drop_duplicates(subset=['product_id'], keep='last')
    
    
    # Productos no vendidos
    prod_ventas = ventas['product_id'].unique()
    prod_ventas = set(prod_ventas)
    prod_pedido = set(pedidos_product)
    prod_no_vendidos = prod_pedido.difference(prod_ventas)
    prod_no_vendidos = list(prod_no_vendidos)
    no_vendidos = productos
    no_vendidos = no_vendidos[no_vendidos.product_id.isin(prod_no_vendidos)]
    no_vendidos = no_vendidos.merge(pedido, on='product_id', how='left')
    no_vendidos['ALERTA']     = 'no_vendido'

    tabla = pd.concat([no_vendidos, ventas]).reset_index(drop=True)
    
    return tabla



# Pedidos cuenca 
def pedidos_cuenca(request):
    
    if request.method == 'POST' :
        n_pedido = request.POST['n_pedido']
        try:
            pedido = pedidos_cuenca_datos(n_pedido).fillna('-') 
            cli = pedido['NOMBRE_CLIENTE'].iloc[-1]
            ciu = pedido['CIUDAD_PRINCIPAL'].iloc[-1]
            ruc = pedido['IDENTIFICACION_FISCAL'].iloc[-1]
            pedido = de_dataframe_a_template(pedido) 
            context = {
                'n_pedido':n_pedido,
                'cli':cli,
                'ciu':ciu,
                'ruc':ruc,
                'pedido':pedido
                }
            return render(request, 'ventas/pedidos_cuenca.html', context)
        
        except:
            context = {
                'error':'No hay pedido con el número: ',
                'n_pedido':n_pedido
                }
            return render(request, 'ventas/pedidos_cuenca.html', context)
            
    return render(request, 'ventas/pedidos_cuenca.html', context={})


# Procesos Guantes
def procesos_guantes(request):
    print('procesos_gunates')
    
