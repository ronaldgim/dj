from django.shortcuts import render

import pandas as pd

# Date
from datetime import date, datetime, timedelta

# Models
from warehouse.models import Cliente # VentaFactura

# Ventas facturas odbc
from datos.views import (
    obtener_ventas_porcliente_warehouse,
    # ventas_odbc_facturas, 
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

    desde_default = '2024-01-01'
    hasta_default = date.today().strftime('%Y-%m-%d')

    clientes = (
        Cliente.objects
        .using('gimpromed_sql')
        .all()
        .order_by('nombre_cliente')
    )

    # Obtener parámetros GET
    cli = request.GET.get('cliente')
    desde = request.GET.get('desde')
    hasta = request.GET.get('hasta')

    ventas = []
    total_cantidad = 0
    total_ventas = 0
    cliente_nombre = None

    # Solo consultar si vienen todos los parámetros
    if cli and desde and hasta:

        ventas = obtener_ventas_porcliente_warehouse(
            codigo_cliente=cli,
            desde=desde,
            hasta=hasta
        )

        if ventas:
            total_cantidad = sum(v['QUANTITY'] for v in ventas)
            total_ventas = sum(v['PRECIO_TOTAL'] for v in ventas)

            cliente_obj = clientes.filter(codigo_cliente=cli).first()
            if cliente_obj:
                cliente_nombre = cliente_obj.nombre_cliente
        else:
            messages.warning(
                request,
                'No hay ventas de este cliente en el periodo seleccionado.'
            )
    
    context = {
        'clientes': clientes,
        'ventas': ventas,
        'total_cantidad': f"{total_cantidad:,.0f}",
        'total_ventas': f"${total_ventas:,.2f}", #round(total_ventas, 2),
        'cliente': cliente_nombre,
        'desde': desde if desde else desde_default,
        'hasta': hasta if hasta else hasta_default,
    }

    return render(request, 'ventas/reporte_ventas.html', context)


# lote y cantidad por factura en reporte ventas
def lote_factura_ajax(request):
    
    try:

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
    except Exception as e:
        return HttpResponse(f'Error: {e}')


def pedidos_cuenca_datos(n_pedido):

    hoy = datetime.now().date()
    seis_meses = hoy - timedelta(days=180) 
    seis_meses = datetime.combine(seis_meses, datetime.min.time()) 
    tres_meses = hoy - timedelta(days=90) 
    tres_meses = datetime.combine(tres_meses, datetime.min.time()) 
    
    pedido = pedidos_cuenca_odbc(n_pedido) 
    codigo_cliente = pedido['client_code'][0]
    
    ventas = ventas_desde_fecha(seis_meses, codigo_cliente) 
    
    if not ventas.empty:
        ventas = ventas.sort_values(by='FECHA')
        ventas['FECHA']  = pd.to_datetime(ventas['FECHA'])
        ventas['ALERTA'] = ventas.apply(lambda x: 'tres_meses' if x['FECHA'] < tres_meses else 'seis_meses', axis=1) 
        ventas['FECHA'] = ventas['FECHA'].astype(str)
        ventas = ventas.rename(columns={'PRODUCT_ID':'product_id'}) 
        ventas = ventas.drop_duplicates(subset=['product_id'], keep='last')
        pedido = pedido.merge(ventas, on='product_id', how='left').sort_values(by='FECHA', ascending=True, na_position='first')
        return pedido
    
    if ventas.empty:
        pedido['ALERTA'] = None
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
