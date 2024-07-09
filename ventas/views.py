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
    ventas_desde_fecha,
    
    # Permisos costum @decorador
    permisos
    )


# Http
from django.http import HttpResponse

# JSON
import json

# Messages
from django.contrib import messages

# Login
from django.contrib.auth.decorators import login_required


# Reporte de ventas
@login_required(login_url='login')
@permisos(['VENTAS'], '/', 'ingresar a Ventas')
def reporte_tipo_mba(request):

    desde = datetime.strptime('2023-01-01', '%Y-%m-%d')
    hasta = date.today()

    h = str(date.today())

    clientes = clientes_warehouse()[['CODIGO_CLIENTE', 'NOMBRE_CLIENTE']]
    clientes = clientes.sort_values('NOMBRE_CLIENTE')

    if request.method == 'POST':
        cli = request.POST.get('cliente', '')
        desde = request.POST.get('desde', '')
        hasta = request.POST.get('hasta', '')

        d=datetime.strptime(desde, '%Y-%m-%d')
        h=datetime.strptime(hasta, '%Y-%m-%d')
        
        vent = ventas_odbc_facturas(desde, hasta, cli).sort_values(by='FECHA', ascending=False)
        vent['FECHA'] = vent['FECHA'].astype('str')
        
        if not vent.empty:
            
            prod = productos_odbc_and_django()[['product_id', 'Unidad', 'Nombre', 'Marca']]
            prod = prod.rename(columns={'product_id':'PRODUCT_ID'})
            cliente_list = clientes_warehouse()[['CODIGO_CLIENTE', 'NOMBRE_CLIENTE']]
            
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
        
        elif vent.empty:
            
            messages.error(request, 'No hay ventas de este cliente en el periodo seleccionado !!!')
            
            context = {
                'clientes':de_dataframe_a_template(clientes),
                'desde':d,
                'hasta':h
            }
            
            return render(request, 'ventas/reporte_ventas.html', context)
            

    context = {
        # 'ventas':ventas,
        'clientes':de_dataframe_a_template(clientes),

        'desde':desde,
        'hasta':hasta
    }

    return render(request, 'ventas/reporte_ventas.html', context)


# lote y cantidad por factura en reporte ventas
def lote_factura_ajax(request):

    fac = request.POST['fac']
    cod = request.POST['cod']

    lote_factura = lotes_facturas_odbc(fac, cod) 
    df = pd.DataFrame(lote_factura)[['lote', 'fecha_caducidad', 'unidades']]
    df = df.to_html(        
        classes='table table-responsive table-bordered m-0 p-0', 
        table_id= 'lotes',
        float_format='{:.0f}'.format,
        index=False,
        justify='start')
    
    return HttpResponse(df)


def pedidos_cuenca_datos(n_pedido):

    hoy = datetime.now().date()
    seis_meses = hoy - timedelta(days=180)
    seis_meses = datetime.combine(seis_meses, datetime.min.time())
    tres_meses = hoy - timedelta(days=90) 
    tres_meses = datetime.combine(tres_meses, datetime.min.time())
    
    pedido = pedidos_cuenca_odbc(n_pedido)
    codigo_cliente = pedido['client_code'][0]

    # Ventas
    ventas = ventas_desde_fecha(seis_meses, codigo_cliente)
    ventas = ventas.sort_values(by='FECHA')
    ventas['FECHA']  = pd.to_datetime(ventas['FECHA'])
    ventas['ALERTA'] = ventas.apply(lambda x: 'tres_meses' if x['FECHA'] < tres_meses else 'seis_meses', axis=1) #;print(ventas)
    ventas['FECHA'] = ventas['FECHA'].astype(str)
    ventas = ventas.rename(columns={'PRODUCT_ID':'product_id'})
    ventas = ventas.drop_duplicates(subset=['product_id'], keep='last')
    
    pedido = pedido.merge(ventas, on='product_id', how='left').sort_values(by='FECHA', ascending=True, na_position='first')
    
    return pedido



# Pedidos cuenca 
def pedidos_cuenca(request):
    
    if request.method == 'POST' :
        n_pedido = request.POST['n_pedido']
        try:
            pedido = pedidos_cuenca_datos(n_pedido)
            
            cli = pedido['client_name'][0] 
            ruc = pedido['client_identification'][0] 
            
            pedido = de_dataframe_a_template(pedido) 
            context = {
                'n_pedido':n_pedido,
                'cli':cli,
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
