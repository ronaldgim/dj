from django.shortcuts import render

import pandas as pd

# Date
from datetime import date, datetime

# Ventas facturas odbc
from datos.views import ventas_odbc_facturas, de_dataframe_a_template, productos_odbc_and_django, clientes_warehouse, lotes_facturas_odbc


# Http
from django.http import HttpResponse

# JSON
import json

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


def lote_factura_ajax(request):

    fac = request.POST['fac']
    cod = request.POST['cod']

    lote_factura = lotes_facturas_odbc(fac, cod) #;print(lote_factura[0]);print(type(lote_factura[0]))

    response = json.dumps(lote_factura)
    # print(response, type(response))

    return HttpResponse(response, content_type='appliation/json')