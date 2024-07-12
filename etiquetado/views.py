# DB
from django.db import connections

# Time
from datetime import datetime, date, timedelta

# Shorcuts
from django.shortcuts import render, redirect

# Pandas
import pandas as pd
import numpy as np

# Datos Models
from datos.models import Product, Vehiculos, TimeStamp
from etiquetado.models import (
    Calculadora,
    PedidosEstadoEtiquetado,
    EstadoEtiquetado,
    OrdenEtiquetadoStock,
    EstadoPicking,
    RegistoGuia,
    FechaEntrega,
    ProductArmado,
    InstructivoEtiquetado,
    EtiquetadoAvance,
    EstadoEtiquetadoStock
    )

from datos.models import StockConsulta
from mantenimiento.models import Equipo
from users.models import UserPerfil, User

# Forms
from etiquetado.forms import (
    RowItemForm,
    CalculadoraForm,
    PedidosEstadoEtiquetadoForm,
    EstadoPickingForm,
    RegistroGuiaForm,
    FechaEntregaForm,
    InstructivoEtiquetadoForm
)

# Json
import json

# Messages
from django.contrib import messages

# Models
from etiquetado.models import EtiquetadoStock

# Generic Views
from django.views.generic.list import ListView

# LoginRequired
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

# Permisos
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied

# Messages
from django.contrib import messages

# Url
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse_lazy

# PDF
from django_xhtml2pdf.utils import pdf_decorator

# Email
from django.core.mail import send_mail
from django.conf import settings


# Inventario Bodega
import pyodbc
import mysql.connector

# No utilizar csrf_token
from django.views.decorators.csrf import csrf_exempt

# Requests
import requests

# Existencias
from wms.models import Existencias
from django.db.models import Q

# Datos
from datos.views import (
    ultima_actualizacion, 
    importaciones_llegadas_odbc, 
    productos_odbc_and_django, 
    de_dataframe_a_template, 
    ventas_facturas_odbc, 
    clientes_warehouse, 
    reservas_lote, 
    stock_disponible,
    pedido_por_cliente,
    tramaco_function,
    stock_faltante_contrato,
    stock_lote_cuc_etiquetado_detalle_odbc,
    frecuancia_ventas,
    # stock_total,
    stock_lote_odbc,
    ventas_armados_facturas_odbc,
    productos_transito_odbc,
    etiquetado_avance_pedido,
    calculo_etiquetado_avance,
    lotes_bodega,
    
    whastapp_cliente_por_codigo,
    email_cliente_por_codigo,
    
    actualizar_facturas_odbc,
    
    # Proformas
    lista_proformas_odbc,
    proformas_por_contrato_id_odbc,
    importaciones_en_transito_odbc_insert_warehouse,
    
    # Extraer número de factura
    extraer_numero_de_factura
    )


# FUNCIONES
# Consulta tabla de clientes
def clientes_table(): #request
    ''' Colusta de clientes por ruc a la base de datos '''
    with connections['gimpromed_sql'].cursor() as cursor:
        #cursor.execute("SELECT * FROM reservas WHERE CONTRATO_ID = %s", [n_pedido])
        #cursor.execute("SELECT * FROM clientes WHERE CLIENT_TYPE = %s", ['HOSPU'])
        cursor.execute("SELECT * FROM clientes")
        columns = [col[0] for col in cursor.description]
        clientes = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        clientes = pd.DataFrame(clientes)
        #print(clientes)
    return clientes


# Calculadora PESOS Y VOLUMEN FUNCTION Y TIEMPOS
def calculadora_funtion(data):

    prod = pd.DataFrame(Product.objects.all().values())
    data = pd.DataFrame(data)

    data = data[['item_id', 'cant', 'lote']]
    data = data.rename(columns={'item_id':'id'})
    data = data.merge(prod, on='id', how='left')

    data['cart'] = (data['cant'] / data['unidad_empaque']).round(2)
    data['t_v']  = data['cart'] * data['volumen']
    data['t_p']  = data['cart'] * data['peso']

    data['t_1p'] = (data['cart'] * data['t_etiq_1p'].round(0)) #/ 3600
    data['t_str_1p'] = [str(timedelta(seconds=int(i))) for i in data['t_1p']]

    data['t_2p'] = (data['cart'] * data['t_etiq_2p'].round(0)) #/ 3600
    data['t_str_2p'] = [str(timedelta(seconds=int(i))) for i in data['t_2p']]

    data['t_3p'] = (data['cart'] * data['t_etiq_3p'].round(0)) #/ 3600
    data['t_str_3p'] = [str(timedelta(seconds=int(i))) for i in data['t_3p']]

    data = data[['product_id', 'description', 'marca', 'marca2', 'lote', 'cant', 'cart', 't_1p', 't_str_1p', 't_2p', 't_str_2p', 't_3p', 't_str_3p', 't_v', 't_p']]
    
    return data


# Tabla de reservas
def reservas_table():

    with connections['gimpromed_sql'].cursor() as cursor:
        # cursor.execute("SELECT * FROM reservas WHERE CONTRATO_ID = %s", [n_pedido])
        cursor.execute("SELECT * FROM reservas")

        columns = [col[0] for col in cursor.description]

        reservas = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

    return reservas


# Talba estados y maquinas
def equipos_etiquetado():
    with connections['default'].cursor() as cursor:
        # cursor.execute("SELECT * FROM reservas WHERE CONTRATO_ID = %s", [n_pedido])
        cursor.execute("SELECT * FROM etiquetado_pedidosestadoetiquetado_equipo")

        columns = [col[0] for col in cursor.description]

        equipos_etiquetado = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

    return equipos_etiquetado


# PEDIDOS
# Etiquetao Pedidos
def pedidos_list_3(request):
    #reservas_lotes_group()
    # Tablas
    reservas = pd.DataFrame(reservas_table())
    clientes = pd.DataFrame(clientes_table())
    maquina  = pd.DataFrame(equipos_etiquetado())
    equipos = pd.DataFrame(Equipo.objects.all().values())
    estados  = pd.DataFrame(EstadoEtiquetado.objects.all().values())
    pedidos_estado = pd.DataFrame(PedidosEstadoEtiquetado.objects.all().values())
    stock = pd.DataFrame(OrdenEtiquetadoStock.objects.all().values())

    # Dataframe Maquina
    equipos = equipos.rename(columns={'id':'equipo_id'})
    maquina = maquina.merge(equipos, on='equipo_id', how='left')
    maquina = maquina[['pedidosestadoetiquetado_id', 'nombre']]
    maquina = maquina.groupby(by='pedidosestadoetiquetado_id').sum().reset_index()
    maquina = maquina.rename(columns={'pedidosestadoetiquetado_id':'id'})

    # Stcok change names
    stock = stock.rename(columns={'id':'CONTRATO_ID', 'fecha_creado':'FECHA_PEDIDO', 'cliente':'NOMBRE_CLIENTE', 'tipo':'CLIENT_TYPE', 'ciudad':'CIUDAD_PRINCIPAL'})
    stock['CONTRATO_ID'] = stock['CONTRATO_ID'].astype(str)

    # Dataframe Estados
    estados = estados.rename(columns={'id':'estado_id'})

    # Dataframe Pedidos
    pedidos_estado = pedidos_estado.merge(estados, on='estado_id', how='left')
    pedidos_estado = pedidos_estado.rename(columns={'n_pedido':'CONTRATO_ID'})
    pedidos_estado = pedidos_estado.merge(maquina, on='id', how='left').fillna('-')

    # Merge Stock
    stock = stock.merge(pedidos_estado, on='CONTRATO_ID', how='left')

    # Dataframe Reservas
    reservas = reservas.merge(clientes, on='NOMBRE_CLIENTE', how='left')
    reservas = reservas.drop_duplicates(subset=['CONTRATO_ID'])
    reservas = reservas[['CONTRATO_ID', 'NOMBRE_CLIENTE', 'FECHA_PEDIDO', 'CLIENT_TYPE', 'CIUDAD_PRINCIPAL', 'WARE_CODE']]
    reservas = reservas.merge(pedidos_estado, on='CONTRATO_ID', how='left')

    reservas = pd.concat([stock, reservas])
    reservas['fecha_actualizado'] = reservas['fecha_actualizado'].astype(str)
    reservas['FECHA_PEDIDO'] = reservas['FECHA_PEDIDO'].astype(str)
    reservas = reservas.fillna('-')
    reservas = reservas.sort_values(by='FECHA_PEDIDO', ascending=False)
    #print(reservas)

    # Solo Hospitales Publicos
    #tipo_clientes = ['HOSPU']
    #reservas = reservas[reservas.CLIENT_TYPE.isin(tipo_clientes)]

    # Convertir en lista de diccionarios para pasar al template
    json_records = reservas.reset_index().to_json(orient='records') # reset_index().
    reservas = json.loads(json_records)

    context = {
        'reservas':reservas,
        # 'time_reservas':actualizado,
        'time_reservas':ultima_actualizacion('actulization_stoklote')
    }

    return render(request, 'etiquetado/pedidos/lista_pedidos.html', context)#reservas


def fecha_entrega_ajax(request):

    p = request.POST['pedido']
    pedido = FechaEntrega.objects.filter(pedido=p).exists()
    u = User.objects.get(id=request.user.id).id
    usuario = UserPerfil.objects.get(user_id=u)
    fecha = request.POST['fecha'];estado = request.POST['estado']
    #fecha_dt = datetime.strptime(fecha, "%Y-%m-%dT%H:%M")

    if request.POST['fecha'] == '':
        respuesta = {'msg_error':
                     '<div class="text-center alert alert-danger mt-3" role="alert">Ingrese una fecha y una hora !!!</div>'
                    }
        respuesta = json.dumps(respuesta)
        return HttpResponse(respuesta, content_type='appliation/json')

    else:
        fecha_dt = datetime.strptime(fecha, "%Y-%m-%dT%H:%M")

    if not pedido:

        FechaEntrega.objects.create(
            user = usuario,
            fecha_hora = fecha_dt,
            estado = request.POST['estado'],
            pedido = request.POST['pedido'],
        )
        respuesta = {'msg':f'Fecha de entrega {fecha} - {estado} guardado con exito !!! '}
        respuesta = json.dumps(respuesta)
        return HttpResponse(respuesta, content_type='appliation/json')

    else:

        obj = FechaEntrega.objects.get(pedido=p)
        obj.fecha_hora = fecha_dt
        obj.estado = request.POST['estado']
        obj.user = usuario

        obj.save()

        respuesta = {'msg':f'Fecha de entrega {fecha} - {estado} guardado con exito !!! '}
        respuesta = json.dumps(respuesta)
        return HttpResponse(respuesta, content_type='appliation/json')




# Lista de pickings
def etiquetado_pedidos(request, n_pedido):

    # meta = request.META['REMOTE_ADDR']#REMOTE_ADDR
    vehiculo = Vehiculos.objects.filter(activo=True).order_by('transportista')
    
    # Dataframes
    pedido = pedido_por_cliente(n_pedido)
    pedido = pedido[pedido['PRODUCT_ID']!='MANTEN']
    product = productos_odbc_and_django()
    product['Unidad_Empaque'] = product['Unidad_Empaque'].replace(0, 1)
    product = product.rename(columns={'product_id':'PRODUCT_ID'})

    # Merge Dataframes
    pedido = pedido.merge(product, on='PRODUCT_ID', how='left').fillna(0.0)
    
    # Calculos
    pedido['Cartones'] = (pedido['QUANTITY'] / pedido['Unidad_Empaque']).round(2)
    pedido = pedido.fillna(0.0).replace(np.inf, 0.0)
    
    pedido['t_una_p_min'] = (pedido['Cartones'] * pedido['t_etiq_1p']) / 60
    pedido['t_una_p_hor'] = pedido['t_una_p_min'] / 60
    pedido['t_dos_p_hor'] = ((pedido['Cartones'] * pedido['t_etiq_2p']) / 60) / 60
    pedido['t_tre_p_hor'] = ((pedido['Cartones'] * pedido['t_etiq_3p']) / 60) / 60

    # pedido['vol_total'] = pedido['Cartones'] * pedido['volumen']
    pedido['vol_total'] = pedido['Cartones'] * (pedido['Volumen'] / 1000000)
    # pedido['pes_total'] = pedido['Cartones'] * pedido['peso']
    pedido['pes_total'] = pedido['Cartones'] * pedido['Peso']
    
    p_cero = 0 in list(pedido['pes_total']) 
    
    pedido = pedido.fillna(0.0).replace(np.inf, 0.0) 

    # Mejor formato de tiempo
    pedido['t_s_1p'] = (pedido['Cartones'] * pedido['t_etiq_1p'].round(0)) 
    pedido['t_str_1p'] =[str(timedelta(seconds=int(i))) for i in pedido['t_s_1p']] 

    pedido['t_s_2p'] =( pedido['Cartones'] * pedido['t_etiq_2p']).round(0)
    pedido['t_str_2p'] =[str(timedelta(seconds=int(i))) for i in pedido['t_s_2p']]

    pedido['t_s_3p'] = (pedido['Cartones'] * pedido['t_etiq_3p'].round(0))
    pedido['t_str_3p'] =[str(timedelta(seconds=int(i))) for i in pedido['t_s_3p']]

    tt_str_1p = str(timedelta(seconds=int(pedido['t_s_1p'].sum())))
    tt_str_2p = str(timedelta(seconds=int(pedido['t_s_2p'].sum())))
    tt_str_3p = str(timedelta(seconds=int(pedido['t_s_3p'].sum())))

    # STOCK
    items = pedido['PRODUCT_ID'].unique()
    items = list(items) 
    bodega = pedido['WARE_CODE'].unique()[0] 

    # if bodega == 'BCT':
    #     bod= 'Cerezos'
    # elif bodega == 'BAN':
    #     bod='Andagoya'

    # STOCK DISPONIBLE POR PEDIDO
    stock = stock_disponible(bodega=bodega, items_list=items)
    stock = stock.rename(columns={'OH2':'stock_disp'})
    
    pedido = pedido.merge(stock, on='PRODUCT_ID', how='left').fillna(0)
    pedido['disp'] = pedido['stock_disp']>pedido['QUANTITY']
    
    pedido = pedido.sort_values(by=['PRODUCT_NAME']) 
    cli_ruc = clientes_table()[['NOMBRE_CLIENTE','IDENTIFICACION_FISCAL']]
    pedido = pedido.merge(cli_ruc,on='NOMBRE_CLIENTE', how='left') 
    
    # Avance
    avance = etiquetado_avance_pedido(n_pedido) 
    if not avance.empty:
        avance = avance.rename(columns={'id':'avance'})[['PRODUCT_ID','unidades']]
        pedido = pedido.merge(avance, on='PRODUCT_ID', how='left').fillna(0)
    
    # Transformar Datos para presentar en template
    data = de_dataframe_a_template(pedido)

    if FechaEntrega.objects.filter(pedido=n_pedido).exists():
        fecha_entrega = FechaEntrega.objects.get(pedido=n_pedido)#;print(fecha_entrega)
    else:
        fecha_entrega='None'

    if PedidosEstadoEtiquetado.objects.filter(n_pedido=n_pedido).exists():
        estado = PedidosEstadoEtiquetado.objects.get(n_pedido=n_pedido).estado
        estado = str(estado)
    else:
        estado = 'None'

    # Cabecera del pedido
    cliente = pedido['NOMBRE_CLIENTE'].iloc[0]
    ruc = pedido['IDENTIFICACION_FISCAL'].iloc[0]
    fecha_pedido = pedido['FECHA_PEDIDO'].iloc[0]
    
    # Totales de tabla
    t_total_1p_hor = pedido['t_una_p_hor'].sum()
    t_total_2p_hor = pedido['t_dos_p_hor'].sum()
    t_total_3p_hor = pedido['t_tre_p_hor'].sum()

    t_total_vol = pedido['vol_total'].sum()
    t_total_pes = pedido['pes_total'].sum()
    t_cartones = pedido['Cartones'].sum()
    t_unidades = pedido['QUANTITY'].sum()

    context = {
        'reservas':data,
        'pedido':n_pedido,
        'cliente':cliente,
        'ruc':ruc,
        'fecha_pedido':fecha_pedido,
        # 't_total_min':t_total_min,

        't_total_1p_hor':t_total_1p_hor,
        't_total_2p_hor':t_total_2p_hor,
        't_total_3p_hor':t_total_3p_hor,

        'tt_str_1p':tt_str_1p,
        'tt_str_2p':tt_str_2p,
        'tt_str_3p':tt_str_3p,

        't_total_vol':t_total_vol,
        't_total_pes':t_total_pes,
        't_cartones':t_cartones,
        't_unidades':t_unidades,

        # 'meta':meta,
        'vehiculos':vehiculo,

        'fecha_entrega':fecha_entrega,
        'estado':estado,

        #'bodega':bod,
        'bodega':bodega,
        'p_cero':p_cero
    }

    return render(request, 'etiquetado/pedidos/pedido.html', context)


def pedido_lotes(request, n_pedido):
    
    pedido = reservas_lote()
    pedido['CONTRATO_ID'] = pedido['CONTRATO_ID'].astype(str) + '.0'
    pedido = pedido[pedido['CONTRATO_ID']==n_pedido]
    
    prod = productos_odbc_and_django()[['product_id','Nombre','Marca']]
    prod = prod.rename(columns={'product_id':'PRODUCT_ID'})
    
    cli = clientes_warehouse()[['CODIGO_CLIENTE','IDENTIFICACION_FISCAL','NOMBRE_CLIENTE']]
    
    if not pedido.empty:
        pedido = pedido.merge(prod, on='PRODUCT_ID', how='left')
        pedido = pedido.merge(cli, on='CODIGO_CLIENTE', how='left')
        
        bodega = pedido['WARE_CODE'][0]
        cliente = pedido['NOMBRE_CLIENTE'][0]
        ruc = pedido['IDENTIFICACION_FISCAL'][0]
        fecha = pedido['FECHA_PEDIDO'][0]
        total = pedido['EGRESO_TEMP'].sum()
        
        pedido = de_dataframe_a_template(pedido)
    
        context = {
            'n_pedido':n_pedido,
            'pedido':pedido,
            'cliente':cliente,
            'ruc':ruc,
            'fecha':fecha,
            'bodega':bodega,
            'total':total,
        }
        
    else:
        context = {
            'msg':'No hay lotes asignados !!!',
            }
    
    return render(request, 'etiquetado/pedidos/pedido_lote.html', context)


# ETIQUETADO
# Etiquetado Stock
def etiquetado_fun():

    with connections['default'].cursor() as cursor:
        cursor.execute("SELECT * FROM etiquetado_etiquetadostock")

        columns = [col[0] for col in cursor.description]

        etiquetado = [
        dict(zip(columns, row))
        for row in cursor.fetchall()
        ]

        ### TIEMPO DE ETIQUETADO
        prod = productos_odbc_and_django()[['product_id','Unidad_Empaque','t_etiq_1p','t_etiq_2p','t_etiq_3p','n_personas']]
        prod = prod.rename(columns={'product_id':'PRODUCT_ID'})
        
        etiquetado = pd.DataFrame(etiquetado)
        etiquetado = etiquetado.merge(prod, on='PRODUCT_ID',how='left')
        etiquetado['Cartones_Cuarentena'] = (etiquetado['Cuarentena'] / etiquetado['Unidad_Empaque']).round(2)

        etiquetado['t_1p'] = (etiquetado['Cartones_Cuarentena'] * etiquetado['t_etiq_1p']).round(0)
        etiquetado['t_2p'] = (etiquetado['Cartones_Cuarentena'] * etiquetado['t_etiq_2p']).round(0)
        etiquetado['t_3p'] = (etiquetado['Cartones_Cuarentena'] * etiquetado['t_etiq_3p']).round(0)

        etiquetado['t'] = etiquetado.apply(lambda x: x['t_2p'] if x['t_2p']>0 else 
        x['t_1p'] if x['t_2p']==0 and x['t_1p']>0 else
        x['t_3p'] if x['t_1p']==0 and x['t_2p']==0 and x['t_3p']>0 else 'F', axis=1)

        etiquetado['tiempo'] = etiquetado.apply(
        lambda x: 'F' if x['t']=='F' else str(timedelta(seconds=int(x['t']))), axis=1)
        
        etiquetado['t_select'] = etiquetado.apply(lambda x: x['t_1p'] if x['n_personas']=='1' else
        x['t_2p'] if x['n_personas']=='2' else
        x['t_3p'] if x['n_personas']=='3' else 'F', axis=1)

        etiquetado['tt'] = etiquetado.apply(lambda x: 'F' if x['t_select']=='F' else
        str(timedelta(seconds=int(x['t_select']))), axis=1)

        ### Nuevo ordenamiento de lista
        etiquetado = etiquetado.sort_values(by='Meses', ascending=True)
        
        ### Astado etiquetado stock
        est_stock = pd.DataFrame(EstadoEtiquetadoStock.objects.all().values())
        if not est_stock.empty:
            est_stock = est_stock.drop_duplicates(subset=['product_id'], keep='last')[['product_id','estado']]
            est_stock = est_stock.rename(columns={'product_id':'PRODUCT_ID'})
            etiquetado = etiquetado.merge(est_stock, on='PRODUCT_ID', how='left')

        ### PRODUCTOS EXCLUIDOS
        etiquetado = etiquetado[etiquetado['Cat']!='0']
        etiquetado = etiquetado[etiquetado['PRODUCT_ID']!='1113']
        etiquetado = etiquetado[etiquetado['PRODUCT_ID']!='1100']
        
        
    return etiquetado



def etiquetado_stock(request):

    eti = etiquetado_fun()
    actulizado = eti['actulizado'][5]

    etiquetado = de_dataframe_a_template(eti)

    urgente = 0.75
    correcto = 2

    context = {
        'etiquetado_stock_list':etiquetado,
        'actualizado':actulizado,

        'urgente':urgente,
        'correcto':correcto
    }

    return render(request, 'etiquetado/etiquetado_listas/stock.html', context)


# Etiquetado Stock bodega
def etiquetado_stock_bodega(request):

    eti = etiquetado_fun()
    actulizado = eti['actulizado'][5]

    urgente = 0.75
    correcto = 2

    rojo = len(eti[eti['Meses'] < urgente])
    amarillo = eti[eti['Meses'] >= urgente]
    amarillo = amarillo[amarillo['Meses'] < correcto]
    amarillo = len(amarillo)

    etiquetado = de_dataframe_a_template(eti)

    context = {
        'etiquetado_stock_list':etiquetado,
        'rojo':rojo,
        'amarillo':amarillo,
        'actualizado':actulizado,

        'urgente':urgente,
        'correcto':correcto
    }

    return render(request, 'etiquetado/etiquetado_listas/stock_bodega.html', context)


# # CALCULADORA
# # Lista Calculadora
class CalculadoraList(ListView):
    model = Calculadora
    template_name = 'etiquetado/calculadora/lista_calculadora.html'
    ordering = ['-fecha']


# Calculadora nombre
def calculadora_new(request):

    c = Calculadora(
        nombre = 'N/A',
    )

    c.save()

    return redirect(f'view/{c.id}')

    # form_cal = CalculadoraForm()

    # if request.method == 'POST':

    #     form_cal = CalculadoraForm(request.POST)

    #     if form_cal.is_valid():
    #         f = form_cal.save()
    #         return redirect(f'view/{f.id}')

    # context = {
    #     'form_cal':form_cal
    # }

    # return render(request, 'etiquetado/calculadora/calculadora.html', context)


# Calculadora registros y tramaco
def calculadora_view(request, id):

    vehiculo = Vehiculos.objects.filter(activo=True).order_by('transportista')
    object = Calculadora.objects.get(id=id)
    form_row = RowItemForm()

    context = {
        'object':object,
        'form_row':form_row,
        'vehiculos':vehiculo,

    }

    if request.method == 'GET':

        productos = object.prod.all().exists()

        if productos:

            c = Calculadora.objects.get(id=id)
            data = c.prod.all().values() 
            data = calculadora_funtion(data) 
            p_cero = 0 in list(data['t_p'])

            calculo = de_dataframe_a_template(data)

            # totales
            unidades = data['cant'].astype(int).sum()
            cartones = data['cart'].sum()

            tv_t     = data['t_v'].sum()
            tp_t     = data['t_p'].sum()

            t1p_t    = data['t_1p'].sum().round(0)
            t1p_t    = str(timedelta(seconds=t1p_t))

            t2p_t    = data['t_2p'].sum().round(0)
            t2p_t    = str(timedelta(seconds=t2p_t))

            t3p_t    = data['t_3p'].sum().round(0)
            t3p_t    = str(timedelta(seconds=t3p_t))

            context = {
                'object':c,
                'form_row':form_row,
                'calculo':calculo,
                'unidades':unidades,
                'cartones':cartones,
                't1p_t':t1p_t,
                't2p_t':t2p_t,
                't3p_t':t3p_t,
                'tv_t':tv_t,
                'tp_t':tp_t,

                'vehiculos':vehiculo,

                'p_cero':p_cero
            }


    if request.method == 'POST':

        o_url = str(object.id)
        row   = RowItemForm(request.POST)
        o     = Calculadora.objects.get(id=id)

        if row.is_valid():
            r = row.save()
            o = o.prod.add(r)
            return redirect(f'/etiquetado/calculadora/view/{o_url}')

        else:
            messages.error(request, 'Error al ingresar item y cantidad')
            return redirect(f'/etiquetado/calculadora/view/{o_url}')

    return render(request, 'etiquetado/calculadora/calculadora_update.html', context)


# FACTURAS
# Facturas list
def facturas_list(request):
    with connections['gimpromed_sql'].cursor() as cursor:

        cursor.execute("SELECT * FROM facturas")

        columns = [col[0] for col in cursor.description]

        facturas = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        facturas = pd.DataFrame(facturas)
        facturas = facturas.groupby(by=['CODIGO_FACTURA', 'FECHA_FACTURA', 'NOMBRE_CLIENTE']).sum()
        facturas = facturas.sort_values(by='FECHA_FACTURA', ascending=False)

        json_recods = facturas.reset_index().to_json(orient='records')
        facturas = json.loads(json_recods)
        context = {
            'facturas':facturas
        }

    return render(request, 'etiquetado/facturas/lista_facturas.html', context)


def factura_por_cliente(n_factura):
    with connections['gimpromed_sql'].cursor() as cursor:

        cursor.execute("SELECT * FROM facturas WHERE CODIGO_FACTURA = %s", [n_factura])
        columns = [col[0] for col in cursor.description]

        facturas = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        f = pd.DataFrame(facturas)

    return f


def facturas(request, n_factura):

    vehiculo = Vehiculos.objects.filter(activo=True).order_by('transportista')

    # Dataframes
    factura = factura_por_cliente(n_factura)
    factura = factura[factura['PRODUCT_ID']!='MANTEN']
    
    product = productos_odbc_and_django()
    product['vol'] = product['Volumen'] / 1000000
    product = product.rename(columns={'product_id':'PRODUCT_ID'})
    
    # Merge
    factura = factura.merge(product, on='PRODUCT_ID', how='left')

    # Calculos
    factura['Cartones'] = factura['QUANTITY'] / factura['Unidad_Empaque']

    factura['t_1p'] = (factura['Cartones'] * factura['t_etiq_1p']).round(0)
    factura['t_2p'] = (factura['Cartones'] * factura['t_etiq_2p']).round(0)
    factura['t_3p'] = (factura['Cartones'] * factura['t_etiq_3p']).round(0)

    factura['t_str_1p'] = [str(timedelta(seconds=i)) for i in factura['t_1p']]
    factura['t_str_2p'] = [str(timedelta(seconds=i)) for i in factura['t_2p']]
    factura['t_str_3p'] = [str(timedelta(seconds=i)) for i in factura['t_3p']]

    factura['vol_total'] = factura['Cartones'] * factura['vol']
    factura['pes_total'] = factura['Peso'] * factura['Cartones']

    t_total_1p = str(timedelta(seconds=factura['t_1p'].sum()))
    t_total_2p = str(timedelta(seconds=factura['t_2p'].sum()))
    t_total_3p = str(timedelta(seconds=factura['t_3p'].sum()))

    p_cero = 0  in list(factura['pes_total'])

    
    # Totales de tabla
    cliente = factura['NOMBRE_CLIENTE'].iloc[0]
    fecha_factura = factura['FECHA_FACTURA'].iloc[0]
    
    t_total_vol = factura['vol_total'].sum()
    t_total_pes = factura['pes_total'].sum()
    t_cartones = factura['Cartones'].sum()
    t_unidades = factura['QUANTITY'].sum()

    factura = de_dataframe_a_template(factura)


    context = {
        'factura':factura,
        'n_factura':n_factura,
        'cliente':cliente,
        'fecha_factura':fecha_factura,
        
        't_total_1p':t_total_1p,
        't_total_2p':t_total_2p,
        't_total_3p':t_total_3p,

        't_total_vol':t_total_vol,
        't_total_pes':t_total_pes,
        't_cartones':t_cartones,
        't_unidades':t_unidades,

        'vehiculos':vehiculo,

        'p_cero':p_cero
    }

    return render(request, 'etiquetado/facturas/factura.html', context)



# Estado de etiquetado
# Lista de actulización BODEGA
def pedidos_estado_list(request):

    davimed_list = ['77317.0','77318.0','77319.0','77320.0','78956.0']

    if request.user.has_perm('etiquetado.view_pedidosestadoetiquetado'):

        # Tablas
        reservas = pd.DataFrame(reservas_table())
        clientes = pd.DataFrame(clientes_table())
        maquina  = pd.DataFrame(equipos_etiquetado())
        equipos = pd.DataFrame(Equipo.objects.all().values())
        estados  = pd.DataFrame(EstadoEtiquetado.objects.all().values())
        pedidos_estado = pd.DataFrame(PedidosEstadoEtiquetado.objects.all().values())
        stock = pd.DataFrame(OrdenEtiquetadoStock.objects.all().values())

        # Dataframe Maquina
        equipos = equipos.rename(columns={'id':'equipo_id'})
        maquina = maquina.merge(equipos, on='equipo_id', how='left')
        maquina = maquina[['pedidosestadoetiquetado_id', 'nombre']]
        maquina = maquina.groupby(by='pedidosestadoetiquetado_id').sum().reset_index()
        maquina = maquina.rename(columns={'pedidosestadoetiquetado_id':'id'})

        stock   = stock.rename(columns={'id':'CONTRATO_ID', 'fecha_creado':'FECHA_PEDIDO', 'cliente':'NOMBRE_CLIENTE', 'tipo':'CLIENT_TYPE', 'ciudad':'CIUDAD_PRINCIPAL'})
        stock['CONTRATO_ID'] = stock['CONTRATO_ID'].astype(str)

        # Dataframe Estados
        estados = estados.rename(columns={'id':'estado_id'})

        # Dataframe Pedidos
        pedidos_estado = pedidos_estado.merge(estados, on='estado_id', how='left')
        pedidos_estado = pedidos_estado.rename(columns={'n_pedido':'CONTRATO_ID'})
        pedidos_estado = pedidos_estado.merge(maquina, on='id', how='left').fillna('-')

        # Merge Stock
        stock = stock.merge(pedidos_estado, on='CONTRATO_ID', how='left')

        # Dataframe Reservas
        reservas = reservas.merge(clientes, on='NOMBRE_CLIENTE', how='left')
        reservas = reservas.drop_duplicates(subset=['CONTRATO_ID'])
        reservas = reservas[['CONTRATO_ID', 'NOMBRE_CLIENTE', 'FECHA_PEDIDO', 'CLIENT_TYPE', 'CIUDAD_PRINCIPAL','SEC_NAME_CLIENTE']]
        reservas = reservas.merge(pedidos_estado, on='CONTRATO_ID', how='left')
        reservas = pd.concat([stock, reservas])
        reservas['fecha_actualizado'] = reservas['fecha_actualizado'].astype(str)
        reservas['FECHA_PEDIDO'] = reservas['FECHA_PEDIDO'].astype(str)
        reservas = reservas.fillna('-')
        reservas = reservas.sort_values(by='FECHA_PEDIDO', ascending=False)

        # davimed
        davimed = reservas[reservas.CONTRATO_ID.isin(davimed_list)]
        # davimed

        # Etiquetado especial
        especial = reservas[reservas['CONTRATO_ID']=='69236.0']

        # ETIQUETADO PARA PUBLICO
        eti_p = reservas[reservas['SEC_NAME_CLIENTE']=='PUBLICO']

        # Solo Hospitales Publicos
        tipo_clientes = ['HOSPU', 'STOCK'] #'DISTR'
        #reservas = reservas[reservas['SEC_NAME_CLIENTE']=='PUBLICO']
        reservas = reservas[reservas.CLIENT_TYPE.isin(tipo_clientes)]
        

        reservas = pd.concat([reservas, eti_p, especial,davimed])
        reservas = reservas.drop_duplicates(subset=['CONTRATO_ID'])

        # Convertir en lista de diccionarios para pasar al template
        reservas = de_dataframe_a_template(reservas)
        # print(reservas)
        context = {
            'reservas':reservas
        }

    else:
        messages.error(request, 'No tienes los permisos necesarios !!!')
        return HttpResponseRedirect('/')


    return render(request, 'etiquetado/etiquetado_estado/lista_estado_pedidos.html', context)#reservas


# Crear registro de avance
def etiquetado_avance(request):
    
    n_pedido = request.POST['n_pedido']
    product_id = request.POST['product_id']
    unidades = request.POST['unidades'].replace('.','')
    unidades = int(unidades)
    
    av = EtiquetadoAvance(
        n_pedido   = n_pedido,
        product_id = product_id,
        unidades   = unidades
    )
    
    av.save()
    
    return HttpResponse(None)

# Editar registro de avance
def etiquetado_avance_edit(request):
    
    id_request = request.POST['id']
    id_request = id_request.split(',')[0]
    id_request = int(id_request)
    
    unidades = request.POST['unidades']   
    unidades = int(unidades)
    
    av = EtiquetadoAvance.objects.get(id=id_request) 
    av.unidades = unidades
    
    av.save()
    
    return HttpResponse(None)


# Crear estado
def estado_etiquetado(request, n_pedido, id):
    
    if id == '-':

        form = PedidosEstadoEtiquetadoForm()

        # Dataframes
        pedido = pedido_por_cliente(n_pedido)[['PRODUCT_ID','PRODUCT_NAME','QUANTITY','NOMBRE_CLIENTE','FECHA_PEDIDO']]
        avance = etiquetado_avance_pedido(n_pedido)
        if not avance.empty:
            avance = avance.rename(columns={'id':'avance'})
            pedido = pedido.merge(avance, on='PRODUCT_ID', how='left')
        
        product = productos_odbc_and_django()[['product_id','marca','Unidad_Empaque']]
        product = product.rename(columns={'product_id':'PRODUCT_ID'})

        # Merge Dataframes
        pedido = pedido.merge(product, on='PRODUCT_ID', how='left').sort_values(by='PRODUCT_ID').fillna(0)

        # Calculos
        pedido['Cartones'] = pedido['QUANTITY'] / pedido['Unidad_Empaque']
        
        # Totales de tabla
        cliente = pedido['NOMBRE_CLIENTE'].iloc[0]
        fecha_pedido = pedido['FECHA_PEDIDO'].iloc[0]
        
        t_cartones = pedido['Cartones'].sum()
        t_unidades = pedido['QUANTITY'].sum()

        pedido = de_dataframe_a_template(pedido)

        context = {
            'reservas':pedido,
            'pedido':n_pedido,
            'cliente':cliente,
            'fecha_pedido':fecha_pedido,
            
            't_cartones':t_cartones,
            't_unidades':t_unidades,

            # Form
            'form':form
        }

        if request.method == 'POST':
            form = PedidosEstadoEtiquetadoForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect(f'/etiquetado/pedidos/estado/list')
            else:
                messages.error(request, 'Error !!! Actulize su lista de pedidos')
    else:

        id_estado = int(float(id))
        estado_registro = PedidosEstadoEtiquetado.objects.get(id=id_estado)
        form_update = PedidosEstadoEtiquetadoForm(instance=estado_registro)

        # Dataframes
        pedido = pedido_por_cliente(n_pedido)[['PRODUCT_ID','PRODUCT_NAME','QUANTITY','NOMBRE_CLIENTE','FECHA_PEDIDO']]
        avance = etiquetado_avance_pedido(n_pedido)
        if not avance.empty:
            avance = avance.rename(columns={'id':'avance'})
            pedido = pedido.merge(avance, on='PRODUCT_ID', how='left')
        
        product = productos_odbc_and_django()[['product_id','marca','unidad_empaque']] 
        product = product.rename(columns={'product_id':'PRODUCT_ID'})

        # Merge Dataframes
        pedido = pedido.merge(product, on='PRODUCT_ID', how='left').sort_values(by='PRODUCT_ID').fillna('')

        # Calculos
        pedido['Cartones'] = pedido['QUANTITY'] / pedido['unidad_empaque']
        
        # Totales de tabla
        cliente = pedido['NOMBRE_CLIENTE'].iloc[0]
        fecha_pedido = pedido['FECHA_PEDIDO'].iloc[0]
                
        t_cartones = pedido['Cartones'].sum()
        t_unidades = pedido['QUANTITY'].sum()
        
        pedido = de_dataframe_a_template(pedido)

        context = {
            'reservas':pedido,
            'pedido':n_pedido,
            'cliente':cliente,
            'fecha_pedido':fecha_pedido,
                        
            't_cartones':t_cartones,
            't_unidades':t_unidades,

            # Form
            'form':form_update
        }

        if request.method == 'POST':
            #id_estado = int(float(id))
            estado_registro = PedidosEstadoEtiquetado.objects.get(id=id_estado)
            form_update = PedidosEstadoEtiquetadoForm(request.POST, instance=estado_registro)
            if form_update.is_valid():
                form_update.save()
                return redirect(f'/etiquetado/pedidos/estado/list')

    return render(request, 'etiquetado/etiquetado_estado/estado_etiquetado.html', context)


# Detalle vista Andagoya
def detail_stock_etiquetado(request, id):

    stock = OrdenEtiquetadoStock.objects.get(id=id)

    # Dataframes
    orden = stock.prod.all().values()
    data = calculadora_funtion(orden)

    json_records = data.to_json(orient='records')
    calculo = json.loads(json_records)

    unidades = data['cant'].astype(int).sum()
    cartones = data['cart'].sum()
    t1p_t    = data['t_1p'].sum()
    t2p_t    = data['t_2p'].sum()
    t3p_t    = data['t_3p'].sum()
    tv_t     = data['t_v'].sum()
    tp_t     = data['t_p'].sum()

    context = {
        'object':stock,
        'calculo':calculo,

        'unidades':unidades,
        'cartones':cartones,
        't1p_t':t1p_t,
        't2p_t':t2p_t,
        't3p_t':t3p_t,
        'tv_t':tv_t,
        'tp_t':tp_t,
    }

    return render(request, 'etiquetado/etiquetado_estado/orden_stock.html', context)


# Detalle y actualización vista Cerezos
def detail_stock_etiquetado_bodega(request, id):
    
    if PedidosEstadoEtiquetado.objects.filter(n_pedido=id).exists():

        id_str = str(id)

        stock = OrdenEtiquetadoStock.objects.get(id=id)
        instancia_inicial = PedidosEstadoEtiquetado.objects.get(n_pedido=id)
        form_update = PedidosEstadoEtiquetadoForm(instance=instancia_inicial)

        productos = pd.DataFrame(Product.objects.all().values())

        data = pd.DataFrame(stock.prod.all().values())
        data = data[['item_id', 'lote', 'cant']]
        data = data.rename(columns={'item_id':'id'})
        data = data.merge(productos, on='id', how='left')
        data['cart'] = data['cant'] / data['unidad_empaque']

        json_records = data.to_json(orient='records')
        calculo = json.loads(json_records)

        # Totales
        unidades = data['cant'].astype(int).sum()
        cartones = data['cart'].sum()


        context = {
            'object':stock,
            'id_str':id_str,
            'form':form_update,
            'calculo':calculo,
            'unidades':unidades,
            'cartones':cartones
        }

        if request.method == 'POST':
            estado_inicial = PedidosEstadoEtiquetado.objects.get(n_pedido=id)
            form_update = PedidosEstadoEtiquetadoForm(request.POST, instance=estado_inicial)
            if form_update.is_valid():
                form_update.save()
                return redirect(f'/etiquetado/pedidos/estado/list')
            else:
                messages.error(request, 'Error !!! Actulize su lista de pedidos')


    else:

        # Form Create
        form = PedidosEstadoEtiquetadoForm()

        # Data
        stock = OrdenEtiquetadoStock.objects.get(id=id)
        productos = pd.DataFrame(Product.objects.all().values())
        id_str = str(id)

        data = pd.DataFrame(stock.prod.all().values())
        data = data[['item_id', 'lote', 'cant']]
        data = data.rename(columns={'item_id':'id'})
        data = data.merge(productos, on='id', how='left')
        data['cart'] = data['cant'] / data['unidad_empaque']

        json_records = data.to_json(orient='records')
        calculo = json.loads(json_records)

        # Totales
        unidades = data['cant'].astype(int).sum()
        cartones = data['cart'].sum()

        context = {
            'object':stock,
            'id_str':id_str,
            'form':form,
            'calculo':calculo,
            'unidades':unidades,
            'cartones':cartones
        }

        if request.method == 'POST':

            form = PedidosEstadoEtiquetadoForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect(f'/etiquetado/pedidos/estado/list')
            else:
                messages.error(request, 'Error !!! Actulize su lista de pedidos')

    return render(request, 'etiquetado/etiquetado_estado/orden_stock_bodega.html', context)


def n_factura_consulta():
    
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(
            f"SELECT CODIGO_FACTURA, NUMERO_PEDIDO_SISTEMA CODIGO_FACTURA FROM warehouse.facturas"
        )
        
        fac = [tuple(row) for row in cursor.fetchall()]
        fac = pd.DataFrame(fac
            ,columns=[
                'CODIGO_FACTURA',
                'n_pedido'
            ]
            )
        
        fac['n_pedido'] = fac['n_pedido'].astype('str') + '.0'
        
    return fac


def n_factura_volumen_cartones(n_pedido):
    
    n_pedido = int(n_pedido)
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(
            f"SELECT NUMERO_PEDIDO_SISTEMA, PRODUCT_ID, QUANTITY FROM warehouse.facturas WHERE NUMERO_PEDIDO_SISTEMA = '{n_pedido}'"
        )
        
        fac = [tuple(row) for row in cursor.fetchall()]
        fac = pd.DataFrame(fac
            ,columns=[
                'n_pedido',
                'product_id',
                'unidades_pedido'
            ]
            )
        
        prod = productos_odbc_and_django()[['product_id','Unidad_Empaque','Volumen']]
        
        if not fac.empty:
        
            fac = fac.merge(prod, on='product_id', how='left').fillna(0)
            fac['vol'] = fac['Volumen'] / 1000000
            fac['car'] = fac['unidades_pedido'] / fac['Unidad_Empaque']
            
            vol = round(fac['vol'].sum(), 1)
            car = round(fac['car'].sum(), 1)
            
            if car < 1: car = 1.0
            
            return vol, car
        
        else:
            vol, car = 0, 0
            return vol, car


def correos_notificacion_factura(nombre_cliente):
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(f"SELECT EMAIL, Email_Fiscal FROM warehouse.clientes WHERE NOMBRE_CLIENTE='{nombre_cliente}'"
        )
        correos = cursor.fetchall()[0]

        email = correos[0]
        email_fiscal = correos[1]
        email_fiscal = email_fiscal.split(',')

        correos = []
        if email:

            if email.find(','):
                e = email.split(',')
                correos.append(e[0])

            else:
                correos.append(email)

        else:
            correos = email_fiscal
    return correos





# Envio de correo con ajax
def correo_facturado(request):
    
    # Numero de factura
    n_pedido = request.GET['ped']
    n_factura = extraer_numero_de_factura(request.GET['fac'])
    id_picking = request.GET['id_button']
    
    # Objeto Django
    picking_estado = EstadoPicking.objects.get(id=id_picking)
    picking_estado.facturado_por_id = User.objects.get(id=request.user.id).id
    picking_estado.hora_facturado = datetime.now()
    
    # Volumen Carton    
    vol, car = n_factura_volumen_cartones(n_pedido)
    if vol > 0 and car > 0:
        vol_car = f'Volumen: {vol} m3 / Cartones: {car}'
    else:
        vol_car = ''

    # Correos
    correo_vendedor = User.objects.get(id=request.user.id)
    correo_vendedor = correo_vendedor.email
    
    emails = email_cliente_por_codigo(picking_estado.codigo_cliente)
    
    if emails == None: 
        picking_estado.facturado = False
        
    elif not emails == None:
        emails.append(correo_vendedor)
        picking_estado.facturado = True
        
    # Bodega
    bod = request.GET['bod']
    if bod == 'BAN':
        b = 'Andagoya'
    elif bod == 'BCT':
        b = 'Cerezos'
    else:
        b = ''

    # Mensaje email
    mensaje = f"""
Señores {picking_estado.cliente} \n
Su pedido con factura # {n_factura}, se encuentra listo para ser retirado en:
Bodega: {b}. \n
{vol_car} \n
Nuestro horario de atención es: Lunes a Viernes de 7:30 am a 13:30 pm y de 14:30 pm a 16:30 pm.
Estamos para servirle.\n
GIMPROMED Cia. Ltda.\n
****Esta notificación ha sido enviada automáticamente - No responder****
"""

    # Send mail
    send_mail(
        subject='Notificación Pedido FACTURADO',
        message= mensaje,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list= emails,
        fail_silently=True,
    )
    
    # ENVIAR WHATSAPP
    n_whatsapp = whastapp_cliente_por_codigo(picking_estado.codigo_cliente)
    
    whatsapp_json = {
        'senores': picking_estado.cliente,
        'recipient': n_whatsapp,
        'factura':n_factura,
        'bodega':b,
        'n_cartones':str(car)
    }
    
    response = requests.post(
        url='http://gimpromed.com/app/api/send-whatsapp',
        data= whatsapp_json
    )
    
    if response.status_code == 200: 
        picking_estado.whatsapp = True
    else:
        if n_whatsapp.startswith('+593'):
            picking_estado.wh_fail_number = True
    
    picking_estado.save()
    
    if picking_estado.facturado == True or picking_estado.whatsapp == True:
        return JsonResponse({
            'tipo':'succes',
            'msg':f'El pedido # {picking_estado.n_pedido} de {picking_estado.cliente} fue facturado y notificado exitosamente !!!'
        })
    elif picking_estado.facturado == False and picking_estado.whatsapp == False:
        return JsonResponse({
            'tipo':'error',
            'msg':'Error intente nuevamente !!!'
        })


# PICKING AJAX
# Vista Todos (lista)
@login_required(login_url='login')
def picking(request):
    
    hoy = datetime.now()
    un_mes = hoy - timedelta(days=10)

    clientes = clientes_table()[['CODIGO_CLIENTE','CIUDAD_PRINCIPAL','CLIENT_TYPE']]
    clientes = clientes.rename(columns={'CODIGO_CLIENTE':'codigo_cliente'})
    
    estados = pd.DataFrame(EstadoPicking.objects.filter(fecha_creado__gte=un_mes).order_by('-id').values(
        'id','n_pedido','estado','fecha_pedido','cliente','fecha_creado','fecha_actualizado','bodega','facturado',
        'user__user__first_name','user__user__last_name','codigo_cliente','whatsapp', 'wh_fail_number'
    ))

    estados['fecha_creado'] = estados['fecha_creado'].astype(str)
    estados['fecha_actualizado'] = estados['fecha_actualizado'].astype(str)
    
    estados = estados.merge(clientes, on='codigo_cliente', how='left')
    estados = estados.drop_duplicates(subset=['n_pedido'])
    estados = estados.sort_values(by=['n_pedido'], ascending=[False])
    
    facturas = n_factura_consulta()
    if not facturas.empty:
        estados = estados.merge(facturas, on='n_pedido', how='left')
        estados = estados.drop_duplicates(subset=['n_pedido'])
    
    reservas = de_dataframe_a_template(estados)
    
    context = {
        'reservas':reservas
    }

    return render(request, 'etiquetado/picking_estado/picking.html', context)


# Vista personal de picking (lista)
@login_required(login_url='login')
def picking_estado(request):
    
    if request.user.has_perm('etiquetado.view_estadopicking'):
        # HABILITAR ACTUALIZACIÓN
        actualizado = pd.DataFrame(TimeStamp.objects.all().values())
        actualizado = list(actualizado['actulization_stoklote'])
        act = []
        for i in actualizado:
            if i != '':
                act.append(i)
        actualizado = act[-1][0:19]

        act = datetime.strptime(actualizado, '%Y-%m-%d %H:%M:%S') #%H:%M:%S
        aho = datetime.now()

        d = aho-act
        d = pd.Timedelta(d)
        d = d.total_seconds()
        t_s = 60

        if d > t_s:
            dd = None
        else:
            dd = 'disabled'

        # Tablas
        reservas = pd.DataFrame(reservas_table())
        clientes = pd.DataFrame(clientes_table())
        estados  = pd.DataFrame(EstadoPicking.objects.all().values())
        users    = pd.DataFrame(User.objects.all().values())
        perfil   = pd.DataFrame(UserPerfil.objects.all().values())

        meses_2 = date.today() - timedelta(days=60) #;print(type(meses_2))
        reservas = reservas[reservas['FECHA_PEDIDO']>meses_2]
        reservas = reservas[reservas['SEC_NAME_CLIENTE']!='RESERVA']

        # Config Users
        users = users.rename(columns={'id':'user_id'})
        perfil = perfil.merge(users, on='user_id', how='left')
        perfil = perfil.rename(columns={'user_id':'perfil_id', 'id':'user_id'})

        # Estado Merge Perfil
        estados = estados.merge(perfil, on='user_id', how='left')
        estados = estados.rename(columns={'n_pedido':'CONTRATO_ID'})
        estados['fecha_creado'] = estados['fecha_creado'].astype(str)
        estados['fecha_actualizado'] = estados['fecha_actualizado'].astype(str)
        estados = estados.rename(columns={'id_x':'id'})

        # Merges Clientes
        reservas = reservas.merge(clientes, on='NOMBRE_CLIENTE', how='left')
        reservas = reservas.drop_duplicates(subset=['CONTRATO_ID'])
        reservas = reservas.merge(estados, on='CONTRATO_ID', how='left')
        reservas = reservas.fillna('-')

        # Config
        reservas['FECHA_PEDIDO'] = reservas['FECHA_PEDIDO'].astype(str)

        # Filtrar solo por bodega Andagoya
        reservas = reservas[reservas['WARE_CODE']=='BAN']
        
        # Convertir en lista de diccionarios para pasar al template        
        reservas = de_dataframe_a_template(reservas)


        if request.method == 'POST':
            if d > t_s:
                import pyodbc
                import mysql.connector

                try:
                    mydb = mysql.connector.connect(
                            host="172.16.28.102",
                            user="standard",
                            passwd="gimpromed",
                            database="warehouse"
                    )

                    cnxn = pyodbc.connect('DSN=mba3;PWD=API')
                    cursorOdbc = cnxn.cursor()
                    cursor_write = mydb.cursor()

                    cursorOdbc.execute(
                    "SELECT CLNT_Pedidos_Principal.FECHA_PEDIDO, CLNT_Pedidos_Principal.CONTRATO_ID, CLNT_Ficha_Principal.NOMBRE_CLIENTE, "
                    "CLNT_Pedidos_Detalle.PRODUCT_ID, CLNT_Pedidos_Detalle.PRODUCT_NAME, CLNT_Pedidos_Detalle.QUANTITY, CLNT_Pedidos_Detalle.Despachados, CLNT_Pedidos_Principal.WARE_CODE, CLNT_Pedidos_Principal.CONFIRMED, CLNT_Pedidos_Principal.HORA_LLEGADA, CLNT_Pedidos_Principal.SEC_NAME_CLIENTE "
                    "FROM CLNT_Ficha_Principal CLNT_Ficha_Principal, CLNT_Pedidos_Detalle CLNT_Pedidos_Detalle, CLNT_Pedidos_Principal CLNT_Pedidos_Principal "
                    "WHERE CLNT_Pedidos_Principal.CONTRATO_ID_CORP = CLNT_Pedidos_Detalle.CONTRATO_ID_CORP AND CLNT_Ficha_Principal.CODIGO_CLIENTE = CLNT_Pedidos_Principal.CLIENT_ID "
                    "AND ((CLNT_Pedidos_Principal.PEDIDO_CERRADO=false) AND (CLNT_Pedidos_Detalle.TIPO_DOCUMENTO='PE')) ORDER BY CLNT_Pedidos_Principal.CONTRATO_ID DESC"
                    )

                    reservas = cursorOdbc.fetchall()

                    sql_delete="DELETE FROM reservas"
                    cursor_write.execute(sql_delete)

                    sql_insert_reservas = """INSERT INTO reservas (FECHA_PEDIDO, CONTRATO_ID, NOMBRE_CLIENTE,
                    PRODUCT_ID, PRODUCT_NAME, QUANTITY, Despachados, WARE_CODE, CONFIRMED, HORA_LLEGADA, SEC_NAME_CLIENTE) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"""
                    data_reservas = [list(rows) for rows in reservas]
                    res = cursor_write.executemany(sql_insert_reservas, data_reservas)
                    mydb.commit()

                    time = str(datetime.now())
                    TimeStamp.objects.create(actulization_stoklote=time)

                    return redirect('picking_estado') #render(request, 'etiquetado/picking_estado/picking_estado.html', context)

                except:
                    print('NO SE ACTULIZO')
            else:
                print('menos 1 min - RESERVAS')

        context = {
            'reservas':reservas,
            'disabled':dd,
            'actualizado':actualizado
        }

    else:
        messages.error(request, 'No tienes los permisos necesarios !!!')
        return HttpResponseRedirect('/')

    return render(request, 'etiquetado/picking_estado/picking_estado.html', context)


# Funcion lista de correos
def lista_correos(n_cliente):
    cli = clientes_table()
    cli = cli[cli['NOMBRE_CLIENTE']==n_cliente]
    cli = cli.set_index('NOMBRE_CLIENTE')
    cli = cli.to_dict()
    cli = cli.get('SALESMAN')
    vendedor = cli.get(n_cliente)
    if vendedor == 'VEN01':
        l_mail = ['dmontalvo@gimpromed.com', 'mlopez@gimpromed.com']
    elif vendedor == 'VEN02':
        l_mail = ['dmontalvo@gimpromed.com']
    elif vendedor == 'VEN08':
        l_mail = ['mlopez@gimpromed.com']
    else:
        l_mail = []
    return l_mail


# From
@login_required(login_url='login')
@csrf_exempt
def picking_estado_bodega(request, n_pedido):
# def picking_estado_bodega(request, n_pedido, id):
    
    # if id == '-':
        # Form
        # form = EstadoPickingForm()
        
    estado_picking = EstadoPicking.objects.filter(n_pedido=n_pedido).exists()
    if estado_picking:
        est = EstadoPicking.objects.get(n_pedido=n_pedido)
        estado = est.estado
        estado_id = est.id
    else:
        estado = 'SIN ESTADO'
        estado_id = ''

    pedido = pedido_por_cliente(n_pedido)
    
    cliente = clientes_table()[['CODIGO_CLIENTE','CLIENT_TYPE']]
    pedido = pedido.merge(cliente, on='CODIGO_CLIENTE', how='left')
    p_json = (pedido[['PRODUCT_ID', 'QUANTITY']]).to_dict()
    p_str = json.dumps(p_json)

    product = productos_odbc_and_django()[['product_id','Unidad_Empaque','Marca']]
    product = product.rename(columns={'product_id':'PRODUCT_ID','Marca':'marca2'})

    # Merge
    pedido = pedido.merge(product, on='PRODUCT_ID', how='left')
    
    # Calculos
    pedido['Cartones'] = pedido['QUANTITY'] / pedido['Unidad_Empaque'] 
    f_pedido = str(pedido['FECHA_PEDIDO'].iloc[0])
    t_cartones = pedido['Cartones'].sum()
    t_unidades = pedido['QUANTITY'].sum()

    # Trasformar datos para pasar al template
    json_records = pedido.sort_values(by='PRODUCT_ID').reset_index().to_json(orient='records')
    data = []
    data = json.loads(json_records)

    # Datos
    cliente        = pedido['NOMBRE_CLIENTE'].iloc[0]
    fecha_pedido   = pedido['FECHA_PEDIDO'].iloc[0]
    tipo_cliente   = pedido['CLIENT_TYPE'].iloc[0]
    bodega         = pedido['WARE_CODE'].iloc[0]
    codigo_cliente = pedido['CODIGO_CLIENTE'].iloc[0]
    
    estados_list_inicial = ['EN PROCESO']

    context = {
        'reservas':data,
        'pedido':n_pedido,
        'cliente':cliente,
        'fecha_pedido':fecha_pedido,
        'tipo_cliente':tipo_cliente,
        'bodega':bodega,
        'codigo_cliente':codigo_cliente,
        'f_pedido':f_pedido,

        't_cartones':t_cartones,
        't_unidades':t_unidades,

        'detalle':p_str,

        #'form':form,

        'estados':estados_list_inicial,
        
        'estado':estado,
        'estado_id':estado_id
    }

    #     if request.method == 'POST':
    #         form = EstadoPickingForm(request.POST)
    #         if form.is_valid():
    #             form.save()
                
    #             return redirect(f'/etiquetado/picking/estado')
    #         else:
    #             messages.error(request, 'Error !!! Actulize su listado de picking')

    # else:
        
    #     id_estado = int(float(id))
    #     estado_registro = EstadoPicking.objects.get(id=id_estado)
    #     form_update = EstadoPickingForm(instance=estado_registro)

    #     # Dataframes
    #     pedido = pedido_por_cliente(n_pedido)
    #     cliente = clientes_table()[['CODIGO_CLIENTE','CLIENT_TYPE']]
    #     pedido = pedido.merge(cliente, on='CODIGO_CLIENTE', how='left')
    #     p_json = (pedido[['PRODUCT_ID', 'QUANTITY']]).to_dict()
    #     p_str = json.dumps(p_json)

    #     product = productos_odbc_and_django()[['product_id','Unidad_Empaque','Marca']]
    #     product = product.rename(columns={'product_id':'PRODUCT_ID','Marca':'marca2'})

    #     # Merge
    #     pedido = pedido.merge(product, on='PRODUCT_ID', how='left')

    #     # Calculos
    #     pedido['Cartones'] = pedido['QUANTITY'] / pedido['Unidad_Empaque']
    #     f_pedido = str(pedido['FECHA_PEDIDO'].iloc[0])
    #     t_cartones = pedido['Cartones'].sum()
    #     t_unidades = pedido['QUANTITY'].sum()
        
    #     # Trasformar datos para pasar al template
    #     json_records = pedido.sort_values(by='PRODUCT_ID').reset_index().to_json(orient='records')
    #     data = []
    #     data = json.loads(json_records)


    #     # Datos
    #     cliente        = pedido['NOMBRE_CLIENTE'].iloc[0]
    #     fecha_pedido   = pedido['FECHA_PEDIDO'].iloc[0]
    #     tipo_cliente   = pedido['CLIENT_TYPE'].iloc[0]
    #     bodega         = pedido['WARE_CODE'].iloc[0]
    #     codigo_cliente = pedido['CODIGO_CLIENTE'].iloc[0]
        
    #     estados_list_finalizado = ['EN PROCESO', 'EN PAUSA', 'INCOMPLETO', 'EN TRANSITO', 'FINALIZADO']

    #     context = {
    #         'reservas':data,
    #         'pedido':n_pedido,
    #         'cliente':cliente,
    #         'fecha_pedido':fecha_pedido,
    #         'tipo_cliente':tipo_cliente,
    #         'bodega':bodega,
    #         'codigo_cliente':codigo_cliente,
    #         'f_pedido':f_pedido,

    #         't_cartones':t_cartones,
    #         't_unidades':t_unidades,

    #         'detalle':p_str,

    #         'form':form_update,

    #         'estados':estados_list_finalizado
    #     }

    #     if request.method == 'POST':
    #         estado_registro = EstadoPicking.objects.get(id=id_estado)
    #         form_update = EstadoPickingForm(request.POST, instance=estado_registro)

    #         h = datetime.now() 
    #         #est = request.POST.get('estado') 

    #         if form_update.is_valid():
    #             form_update.clean()
    #             form_update.save()
                
    #             if  form_update.clean()['estado'] == 'FINALIZADO':
    #                 estado_registro.fecha_actualizado = h
    #                 estado_registro.save()

    #             return redirect(f'/etiquetado/picking/estado')
    #         else:
    #             messages.warning(request, 'Error !!! Actulize su lista de pedidos')

    return render(request, 'etiquetado/picking_estado/picking_estado_bodega.html', context)


# AJAX - LOTES DE PRODUCTO POR BODEGA
def ajax_lotes_bodega(request):
    
    product_id = request.POST['product_id']
    bodega     = request.POST['bodega']
    
    lotes = lotes_bodega(bodega, product_id)
    
    if not lotes.empty:
        lotes['Unds'] = lotes['Unds'].apply(lambda x:'{:,.0f}'.format(x))
    
    lotes= lotes.to_html(
        #float_format='{:,.0f}'.format,
        classes='table table-responsive table-bordered m-0 p-0', 
        table_id= 'lotes',
        index=False,
        justify='start'
    )
    
    return HttpResponse(lotes)



# Picking Historial
def picking_historial(request):

    picking_hist = EstadoPicking.objects.filter().exclude(id__in=[1,]).order_by('-n_pedido', 'fecha_actualizado')
    picking_hist_len = (EstadoPicking.objects.filter().exclude(id__in=[1,]).order_by('-n_pedido')).count()

    context = {
        'picking_hist':picking_hist,
        'picking_hist_len':picking_hist_len
    }

    return render(request, 'etiquetado/picking_estado/picking_historial.html', context)


# Picking HIstorial Detail
@login_required(login_url='login')
def picking_historial_detail(request, id):

    vehiculos = Vehiculos.objects.all()

    picking = EstadoPicking.objects.get(id=id)

    detalle = json.loads(picking.detalle)
    detalle = pd.DataFrame(detalle)
    detalle = detalle.rename(columns={'PRODUCT_ID':'product_id'})
    producto = pd.DataFrame(Product.objects.all().values())

    # tiempo = picking.fecha_actualizado - picking.fecha_creado

    detalle = detalle.merge(producto, on='product_id', how='left')
    detalle['Cartones'] = detalle['QUANTITY'] / detalle['unidad_empaque']
    detalle['T1'] = detalle['Cartones'] * detalle['t_etiq_1p']
    detalle['T2'] = detalle['Cartones'] * detalle['t_etiq_2p']
    detalle['T3'] = detalle['Cartones'] * detalle['t_etiq_3p']
    detalle['volumen_detalle'] = detalle['Cartones'] * detalle['volumen']
    detalle['peso_detalle'] = detalle['Cartones'] * detalle['peso']
    detalle = detalle[['product_id', 'description', 'marca', 'QUANTITY', 'Cartones', 'T1', 'T2', 'T3', 'volumen_detalle', 'peso_detalle']]

    t_und = detalle['QUANTITY'].sum()
    t_car = detalle['Cartones'].sum()
    t_t1 = detalle['T1'].sum()
    t_t2= detalle['T2'].sum()
    t_t3 = detalle['T3'].sum()
    t_vol = detalle['volumen_detalle'].sum()
    t_peso = detalle['peso_detalle'].sum()

    json_records = detalle.reset_index().to_json(orient='records')
    detalle = json.loads(json_records)


    context = {
        'vehiculos':vehiculos,

        'cliente':picking.cliente,
        'estado':picking.estado,
        'fecha_pedido':picking.fecha_pedido,
        'tipo_cliente':picking.tipo_cliente,
        'creado':picking.fecha_creado,
        'finalizado':picking.fecha_actualizado,
        'pedido':picking.n_pedido,
        'user':picking.user,
        # 'tiempo':tiempo,

        'detalle':detalle,
        't_und' : t_und,
        't_car' : t_car,
        't_t1' : t_t1,
        't_t2' : t_t2,
        't_t3' : t_t3,
        't_vol' : t_vol,
        't_peso' : t_peso,

    }
    return render(request, 'etiquetado/picking_estado/picking_detail.html', context)


# Picking Historial
@pdf_decorator(pdfname='picking.pdf')
@login_required(login_url='login')
def picking_historial_pdf(request):

    picking_hist = EstadoPicking.objects.filter().exclude(id__in=[1,]).order_by('-n_pedido')
    picking_hist_len = (EstadoPicking.objects.filter().exclude(id__in=[1,]).order_by('-n_pedido')).count()

    users    = pd.DataFrame(User.objects.all().values())
    perfil   = pd.DataFrame(UserPerfil.objects.all().values())

    # Hora reporte
    time = str(datetime.now())

    # Resumen Usuarios
    users = users.rename(columns={'id':'user_id'})
    perfil = perfil.merge(users, on='user_id', how='left')
    perfil = perfil.rename(columns={'user_id':'peril_id', 'id':'user_id'})

    resumen = pd.DataFrame(EstadoPicking.objects.filter().exclude(id__in=[1,]).values())
    resumen = resumen.groupby('user_id').count()
    resumen = resumen.merge(perfil, on='user_id', how='left')
    resumen = resumen[['user_id', 'n_pedido', 'first_name', 'last_name']]
    resumen = resumen.sort_values(by='n_pedido', ascending=False)

    json_records = resumen.reset_index().to_json(orient='records')
    resumen = json.loads(json_records)

    # Resumen Estados
    r_pausa = (EstadoPicking.objects.filter(estado='EN PAUSA').exclude(id__in=[1,])).count()
    r_proceso = (EstadoPicking.objects.filter(estado='EN PROCESO').exclude(id__in=[1,])).count()
    r_incompleto = (EstadoPicking.objects.filter(estado='INCOMPLETO').exclude(id__in=[1,])).count()
    r_finalizado = (EstadoPicking.objects.filter(estado='FINALIZADO').exclude(id__in=[1,])).count()

    # Resumen Tipo cliente
    r_tipocliente = pd.DataFrame(EstadoPicking.objects.filter().exclude(id__in=[1,]).values())
    r_tipocliente = r_tipocliente.groupby('tipo_cliente').count()
    r_tipocliente = r_tipocliente[['n_pedido']]
    r_tipocliente = r_tipocliente.sort_values(by='n_pedido', ascending=False)

    json_records = r_tipocliente.reset_index().to_json(orient='records')
    r_tipocliente = json.loads(json_records)


    context = {
        'picking_hist':picking_hist,
        'picking_hist_len':picking_hist_len,
        'resumen':resumen,
        'time':time,

        'r_pausa': r_pausa,
        'r_proceso':r_proceso,
        'r_incompleto':r_incompleto,
        'r_finalizado':r_finalizado,

        'r_tipocliente':r_tipocliente,
    }

    return render(request, 'etiquetado/picking_estado/picking_historial_pdf.html', context)



def inventario_bodega_consulta():

    cnxn = pyodbc.connect('DSN=mba3;PWD=API')
    cursor = cnxn.cursor()
    stock = cursor.execute(
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

    stock = stock.fetchall()
    stock = pd.DataFrame.from_records(
        stock,
        columns=[
            'PRODUCT_ID',
            'PRODUCT_NAME',
            'GROUP_CODE',
            'UM',
            'OH',
            'OH2',
            'COMMITED',
            'QUANTITY',
            'LOTE_ID',
            'FECHA_ELABORACION',
            'FECHA_CADUCIDAD',
            'WARE_CODE',
            'LOCATION'
        ])

    stock['FECHA_ELABORACION'] = stock['FECHA_ELABORACION'].astype(str)
    stock['FECHA_CADUCIDAD'] = stock['FECHA_CADUCIDAD'].astype(str)

    stock = stock.sort_values(by=['GROUP_CODE', 'PRODUCT_ID'])

    stock_id = []

    for i in range(0, len(stock['PRODUCT_ID'])+1):
        if i != 0:
            stock_id.append(i)

    stock['ID'] = stock_id

    stock = stock[[
            'ID',
            'PRODUCT_ID',
            'PRODUCT_NAME',
            'GROUP_CODE',
            'UM',
            'OH',
            'OH2',
            'COMMITED',
            'QUANTITY',
            'LOTE_ID',
            'FECHA_ELABORACION',
            'FECHA_CADUCIDAD',
            'WARE_CODE',
            'LOCATION'
        ]]

    stock = [tuple(x) for x in stock.values]

    return stock



@login_required(login_url='login')
def inventario_bodega(request):

    act_list = pd.DataFrame(TimeStamp.objects.all().values())
    act_list = list(act_list['actulization_stockconsulta'])
    act = []
    for i in act_list:
        if i != '':
            act.append(i)
    act_last = act[-1][:-7]

    act_dt = datetime.strptime(act_last, '%Y-%m-%d %H:%M:%S')
    aho = datetime.now()

    d = aho-act_dt
    d = pd.Timedelta(d)
    d = d.total_seconds()
    t_s = 60

    stock = StockConsulta.objects.all().order_by('fecha_cadu_lote')


    if request.method == 'POST':

        # Filtrar
        if request.POST.get('bodega') != 'todas':
            bodega = str(request.POST.get('bodega'))
            stock = StockConsulta.objects.filter(ware_code=bodega).order_by('fecha_cadu_lote')
            context = {
                'stock':stock,
                'actulizado':act_last,
                'bodega':request.POST.get('bodega')
                }
            return render(request, 'etiquetado/inventario/stock.html', context)

        # Actulizar
        elif request.POST.get('bodega') == 'todas':
            if d>t_s:

                with connections['default'].cursor() as cursor:
                    cursor.execute(
                        "TRUNCATE TABLE datos_stockconsulta"
                    )

                with connections['default'].cursor() as cursor:
                    stock_list = inventario_bodega_consulta()
                    cursor.executemany(
                        "INSERT INTO datos_stockconsulta (id, product_id, product_name, group_code, um, oh, oh2, commited, quantity, lote_id, fecha_elab_lote, fecha_cadu_lote, ware_code, location) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", stock_list
                    )

                    messages.success(request,'Stock actulizado !!!')

                ahora = str(datetime.now())

                TimeStamp.objects.create(actulization_stockconsulta=ahora)

                return redirect('inventario_bodega')

            else:
                print('menos 1 min - INVENTARIO')

    context = {
        'stock':stock,
        'actulizado':act_last,
        }

    return render(request, 'etiquetado/inventario/stock.html', context)


# Revisión de Reservas en importaciones
from bpa.views import importaciones_transito #, main_importaciones

def revision_reservas(request):

    imp = importaciones_transito()

    actualizado = pd.DataFrame(TimeStamp.objects.all().values())
    actualizado = list(actualizado['actulization_importaciones'])
    act = []
    for i in actualizado:
        if i != '':
            act.append(i)

    actualizado = act[-1]

    imp = imp.drop_duplicates(subset='MEMO')
    imp = imp.sort_values(by='MEMO')
    json_records = imp.reset_index().to_json(orient='records')
    imp = json.loads(json_records)

    context = {
        'imp':imp,
        'actualizado':actualizado
    }

    if request.method == 'POST':
        #main_importaciones()
        importaciones_en_transito_odbc_insert_warehouse()

        actualizado = str(datetime.now())
        TimeStamp.objects.create(actulization_importaciones=actualizado)

        context = {
            'imp':imp,
            'actualizado':actualizado
        }

    return render(request, 'etiquetado/revision_reservas/revision_reservas_list.html', context)


# def reservas_lote(): #request
#     ''' Colusta de clientes por ruc a la base de datos '''
#     with connections['gimpromed_sql'].cursor() as cursor:
#         cursor.execute("SELECT * FROM reservas_lote")
#         columns = [col[0] for col in cursor.description]
#         reservas_lote = [
#             dict(zip(columns, row))
#             for row in cursor.fetchall()
#         ]
#         reservas_lote = pd.DataFrame(reservas_lote)
#     return reservas_lote


def revision(request, memo):

    data = importaciones_transito()#;print(data)
    data = data[data['MEMO']==memo]
    r_lote = reservas_lote() #;print(r_lote)
    clientes = clientes_table()
    clientes = clientes[['CODIGO_CLIENTE', 'NOMBRE_CLIENTE']]

    imp = data.merge(r_lote, on='PRODUCT_ID', how='left')
    imp = imp.dropna(subset=['QUANTITY'])
    imp = imp.drop_duplicates(subset=['PRODUCT_ID'])

    proveedor = imp['VENDOR_NAME'][0]
    memo = imp['MEMO'][0]

    res = data.merge(r_lote, on='PRODUCT_ID', how='left')
    res = res.dropna(subset=['CONTRATO_ID'])
    res = res[['PRODUCT_ID', 'description', 'CONTRATO_ID', 'CODIGO_CLIENTE', 'WARE_CODE', 'EGRESO_TEMP', 'LOTE_ID','FECHA_CADUCIDAD']]
    res = res.merge(clientes, on='CODIGO_CLIENTE', how='left')
    res = res.sort_values(by=['PRODUCT_ID', 'FECHA_CADUCIDAD'])
    res['CONTRATO_ID'] = res['CONTRATO_ID'].astype(str)
    res_imp = res.drop_duplicates(subset='PRODUCT_ID')
    res_imp = res_imp[['PRODUCT_ID']]

    imp = imp.merge(res_imp, on='PRODUCT_ID', how='right')
    imp = imp[['VENDOR_NAME', 'PRODUCT_ID', 'description', 'QUANTITY']]
    imp = imp.sort_values(by=['PRODUCT_ID'])

    json_records_imp = imp.reset_index().to_json(orient='records')
    imp = json.loads(json_records_imp)

    json_records_res = res.reset_index().to_json(orient='records')
    res = json.loads(json_records_res)

    context = {
        'proveedor':proveedor,
        'memo':memo,
        'imp':imp,
        'res':res
    }

    return render(request, 'etiquetado/revision_reservas/revision_detail.html', context)


# importaciones llegadas
def revision_imp_llegadas_list(request):
    
    imp = importaciones_llegadas_odbc()
    pro = productos_odbc_and_django()

    # r_lote = reservas_lote()
    # clientes = clientes_table()[['CODIGO_CLIENTE', 'CLIENT_TYPE']]
    # r_lote = r_lote.merge(clientes, on='CODIGO_CLIENTE', how='left')
    # r_lote = r_lote[r_lote['CLIENT_TYPE']=='HOSPU'];print(r_lote)

    imp = imp.merge(pro, on='product_id', how='left') #;print(imp)
    #print(imp);print(imp.keys())

    imp = imp[[
        'DOC_ID_CORP',
        'ENTRADA_FECHA',
        # 'LOTE_ID',
        # 'FECHA_CADUCIDAD',
        # 'AVAILABLE',
        # 'EGRESO_TEMP',
        # 'OH',
        'WARE_COD_CORP',

        # 'product_id',
        # 'Nombre',
        'marca2'
    ]]

    imp = imp.drop_duplicates(subset=['DOC_ID_CORP'])
    imp = imp.sort_values(['ENTRADA_FECHA'], ascending=[False])[:50]

    #print(imp);print(imp.keys())
    imp_list = de_dataframe_a_template(imp)

    actualizado = ultima_actualizacion('actualization_reserva_lote')

    context = {
        'imp':imp_list,
        'actualizado':actualizado
    }

    return render(request, 'etiquetado/revision_reservas/importaciones_llegadas_list.html', context)



def revision_imp_llegadas(request, orden_compra):

    try:
        data = importaciones_llegadas_odbc()
        data = data[data['DOC_ID_CORP']==orden_compra]
        data = data[['DOC_ID_CORP', 'ENTRADA_FECHA', 'product_id', 'LOTE_ID', 'FECHA_CADUCIDAD', 'OH', 'WARE_COD_CORP']]
        data = data.rename(columns={
            'DOC_ID_CORP':'imp_orden_compra',
            'ENTRADA_FECHA':'imp_fecha_llegada',
            'LOTE_ID':'imp_lote_id',
            'FECHA_CADUCIDAD':'imp_fecha_caducidad',
            'OH':'imp_unidades',
            'WARE_COD_CORP':'imp_bodega'
        })

        # LISTA DE PRODUCTOS EN RESERVAS QUE VIENEN EN LA IMPORTACIÓN
        data_product_id = data['product_id'].unique()
        data_product_id = np.sort(data_product_id)

        r_lote = reservas_lote()
        r_lote = r_lote.merge(clientes_table()[['CODIGO_CLIENTE', 'NOMBRE_CLIENTE', 'CLIENT_TYPE']], on='CODIGO_CLIENTE', how='left')
        r_lote = r_lote[r_lote['CLIENT_TYPE']=='HOSPU'] #;print(r_lote)
        r_lote = r_lote.rename(columns={'PRODUCT_ID':'product_id'})
        r_lote = r_lote.sort_values(by=['product_id', 'FECHA_CADUCIDAD'])
        r_lote['CONTRATO_ID'] = r_lote['CONTRATO_ID'].astype(str)
        r_lote = r_lote[r_lote.product_id.isin(data_product_id)]
        # r_lote = r_lote.merge(clientes_table()[['CODIGO_CLIENTE', 'NOMBRE_CLIENTE']], on='CODIGO_CLIENTE', how='left')
        r_lote = r_lote.merge(productos_odbc_and_django()[['product_id', 'Nombre', 'marca2']], on='product_id', how='left')

        # LISTA DE PRODUCTOS EN IMPORTACIÓN CON RESERVAS
        reserva_product_id = r_lote['product_id'].unique()

        imp = data[data.product_id.isin(reserva_product_id)]
        imp = imp.sort_values(by=['product_id', 'imp_fecha_caducidad'])
        imp = imp.merge(productos_odbc_and_django()[['product_id', 'Nombre', 'marca2']], on='product_id', how='left')

        # print(data)
        # print(r_lote)
        # print(imp)

        o_comp = imp['imp_orden_compra'][0]
        marca = imp['marca2'][0]

        imp = de_dataframe_a_template(imp)
        r_lote = de_dataframe_a_template(r_lote)

        context = {
            'o_comp':o_comp,
            'marca':marca,
            'imp':imp,
            'res':r_lote
        }
        return render(request, 'etiquetado/revision_reservas/revision_imp_llegadas.html', context)
    except:
        messages.error(request,'No hay reservas en esta orden de compra')
        return redirect('/etiquetado/revision/imp/llegadas/list')


# Dashboards de pedidos
def estado_pedidos_dashboard_fun(bodega):

    reservas = pd.DataFrame(reservas_table())
    reservas = reservas[reservas['WARE_CODE']==bodega]

    estados = pd.DataFrame(EstadoPicking.objects.all().values())
    clientes = clientes_table()[['NOMBRE_CLIENTE','CIUDAD_PRINCIPAL','CLIENT_TYPE']]
    users    = pd.DataFrame(User.objects.all().values())[['id', 'first_name','last_name']]
    perfil   = pd.DataFrame(UserPerfil.objects.all().values())[['id', 'user_id']]

    # Config Users
    users = users.rename(columns={'id':'user_id'})
    perfil = perfil.merge(users, on='user_id', how='left')
    perfil = perfil.rename(columns={'user_id':'perfil_id', 'id':'user_id'})
    perfil['operario'] = perfil['first_name'] + ' ' + perfil['last_name']

    # Estado Merge Perfil
    estados = estados.merge(perfil, on='user_id', how='left')
    estados = estados.rename(columns={'n_pedido':'CONTRATO_ID'})
    estados['fecha_creado'] = estados['fecha_creado'].astype(str)
    estados['fecha_actualizado'] = estados['fecha_actualizado'].astype(str)
    estados = estados.rename(columns={'id_x':'id'})

    # Merges Clientes
    reservas = reservas.merge(clientes, on='NOMBRE_CLIENTE', how='left')
    reservas = reservas.drop_duplicates(subset=['CONTRATO_ID'])
    reservas = reservas.merge(estados, on='CONTRATO_ID', how='left')

    # AÑADIR CLIENTES
    solca_uio = reservas[reservas['NOMBRE_CLIENTE']=='SOLCA QUITO']
    solca_gye = reservas[reservas['NOMBRE_CLIENTE']=='SOLCA MATRIZ GUAYAQUIL']
    junta_gye = reservas[reservas['NOMBRE_CLIENTE']=='JUNTA DE BENEFICENCIA DE GUAYA']

    # Fistrado de datos
    reservas = reservas[reservas['NOMBRE_CLIENTE']!='GIMPROMED CIA. LTDA.']
    reservas = reservas[reservas['CLIENT_TYPE']!='HOSPU']

    # Añadir clientes
    reservas = pd.concat([reservas, solca_uio, solca_gye, junta_gye])

    # Filtrar por finalizado y reservas
    reservas = reservas[reservas['estado']!='FINALIZADO']
    reservas = reservas[reservas['SEC_NAME_CLIENTE']!='RESERVA']

    # Llenar None y ordenar
    reservas = reservas.fillna('-')
    reservas = reservas.sort_values(by=['FECHA_PEDIDO', 'HORA_LLEGADA'])

    return reservas


def picking_dashboard(request, bodega):

    if bodega == 'BAN':
        b = 'ANDAGOYA'
    elif bodega == 'BCT':
        b = 'CEREZOS'

    reservas = estado_pedidos_dashboard_fun(bodega)
    
    # STOCK FALTANTE POR CONTRATO
    contratos = list(reservas['CONTRATO_ID'].unique())
    sto = stock_faltante_contrato(contratos, bodega)
    
    if not sto.empty:
        reservas = reservas.merge(sto, on='CONTRATO_ID', how='left')
    
    # Fistrado por fecha
    hoy = date.today()

    # Reserva de hoy a 2 meses
    meses_2 = hoy - timedelta(days=30)
    reservas = reservas[reservas['FECHA_PEDIDO']>meses_2]

    # Numero de pedidos
    pedidos_hoy = reservas[reservas['FECHA_PEDIDO']==hoy]
    pedidos_hoy_n = len(pedidos_hoy)
    # pedidos_hoy_fin = len(pedidos_hoy[pedidos_hoy['estado']=='FINALIZADO'])
    # pedidos_hoy_pro = len(pedidos_hoy[pedidos_hoy['estado']=='EN PROCESO'])
    # pedidos_hoy_inc = len(pedidos_hoy[pedidos_hoy['estado']=='INCOMPLETO'])
    # pedidos_hoy_pau = len(pedidos_hoy[pedidos_hoy['estado']=='EN PAUSA'])
    # pedidos_hoy_pen = pedidos_hoy_n - (pedidos_hoy_fin+pedidos_hoy_pro+pedidos_hoy_inc+pedidos_hoy_pau)

    ayer = hoy - timedelta(days=1)
    pedidos_ayer = reservas[reservas['FECHA_PEDIDO']==ayer]
    pedidos_ayer_n = len(pedidos_ayer)
    # pedidos_ayer_fin = len(pedidos_ayer[pedidos_ayer['estado']=='FINALIZADO'])
    # pedidos_ayer_pro = len(pedidos_ayer[pedidos_ayer['estado']=='EN PROCESO'])
    # pedidos_ayer_inc = len(pedidos_ayer[pedidos_ayer['estado']=='INCOMPLETO'])
    # pedidos_ayer_pau = len(pedidos_ayer[pedidos_ayer['estado']=='EN PAUSA'])
    # pedidos_ayer_pen = pedidos_ayer_n - (pedidos_ayer_fin+pedidos_ayer_pro+pedidos_ayer_inc+pedidos_ayer_pau)


    pedidos_mas3 = reservas[reservas['FECHA_PEDIDO']<ayer]#[['CONTRATO_ID','FECHA_PEDIDO']];print(pedidos_mas3)
    pedidos_mas3_n = len(pedidos_mas3)
    # pedidos_mas3_fin = len(pedidos_mas3[pedidos_mas3['estado']=='FINALIZADO'])
    # pedidos_mas3_pro = len(pedidos_mas3[pedidos_mas3['estado']=='EN PROCESO'])
    # pedidos_mas3_inc = len(pedidos_mas3[pedidos_mas3['estado']=='INCOMPLETO'])
    # pedidos_mas3_pau = len(pedidos_mas3[pedidos_mas3['estado']=='EN PAUSA'])
    # pedidos_mas3_pen = pedidos_mas3_n - (pedidos_mas3_fin+pedidos_mas3_pro+pedidos_mas3_inc+pedidos_mas3_pau)

    # Definir columna de dia para añadir color
    if len(reservas) > 0:
        reservas['fecha_estado'] = reservas.apply(lambda x: 'hoy' if x['FECHA_PEDIDO']==hoy else 'ayer' if x['FECHA_PEDIDO']==ayer else 'mas3' if x['FECHA_PEDIDO']<ayer else 'mas3', axis=1)
    # print(reservas);print(reservas.keys())
    # print(reservas)
    # Config
    reservas['FECHA_PEDIDO'] = reservas['FECHA_PEDIDO'].astype(str)
    reservas = de_dataframe_a_template(reservas)

    context = {
        'reservas':reservas,
        'hoy':pedidos_hoy_n,
        # 'hoy_fin':pedidos_hoy_fin,
        # 'hoy_pro':pedidos_hoy_pro,
        # 'hoy_inc':pedidos_hoy_inc,
        # 'hoy_pau':pedidos_hoy_pau,
        # 'hoy_pen':pedidos_hoy_pen,

        'ayer':pedidos_ayer_n,
        # 'ayer_fin':pedidos_ayer_fin,
        # 'ayer_pro':pedidos_ayer_pro,
        # 'ayer_inc':pedidos_ayer_inc,
        # 'ayer_pau':pedidos_ayer_pau,
        # 'ayer_pen':pedidos_ayer_pen,

        'mas3':pedidos_mas3_n,
        # 'mas3_fin':pedidos_mas3_fin,
        # 'mas3_pro':pedidos_mas3_pro,
        # 'mas3_inc':pedidos_mas3_inc,
        # 'mas3_pau':pedidos_mas3_pau,
        # 'mas3_pen':pedidos_mas3_pen,

        'bodega':b
    }

    return render(request, 'etiquetado/pedidos/dashboard.html', context)


def publico_dashboard_fun():

    reservas = pd.DataFrame(reservas_table())
    reservas = reservas[reservas['PRODUCT_ID']!='MANTEN']
    
    # davimed #
    davimed_list = ['77317.0','77318.0','77319.0','77320.0', '78956.0']
    davimed = reservas[reservas.CONTRATO_ID.isin(davimed_list)]
    # davimed #
    
    pro = productos_odbc_and_django()[['product_id', 'Unidad_Empaque', 't_etiq_1p', 't_etiq_2p', 't_etiq_3p']]
    estado = pd.DataFrame(PedidosEstadoEtiquetado.objects.all().values('n_pedido','estado__estado','fecha_creado'))
    estado = estado.rename(columns={'n_pedido':'CONTRATO_ID','estado__estado':'estado'})
    estado['fecha_creado'] = estado['fecha_creado'].astype(str)

    reservas = reservas[reservas['SEC_NAME_CLIENTE']=='PUBLICO']
    
    # davimed #
    if not davimed.empty:
        reservas = pd.concat([reservas,davimed])
    # davimed #
    
    reservas = reservas.rename(columns={'PRODUCT_ID':'product_id'})
    reservas = reservas.merge(pro, on='product_id', how='left')
    reservas['FECHA_PEDIDO'] = reservas['FECHA_PEDIDO'].astype(str)

    list_reservas = reservas.drop_duplicates(subset=['CONTRATO_ID'])

    reservas['cartones'] = (reservas['QUANTITY'] / reservas['Unidad_Empaque']).round(2)
    reservas = reservas.fillna(0).replace(np.inf, 0)
    reservas['t_1p'] = (reservas['cartones'] * reservas['t_etiq_1p']).round(0)
    reservas['t_2p'] = (reservas['cartones'] * reservas['t_etiq_2p']).round(0)
    reservas['t_3p'] = (reservas['cartones'] * reservas['t_etiq_3p']).round(0)
    


    
    ### CONF TIEMPOS
    contratos = reservas['CONTRATO_ID'].unique()
    
    # Avance de etiquetado
    avance_df = pd.DataFrame()
    avance_df['CONTRATO_ID'] = contratos
    avance_df['avance'] = [calculo_etiquetado_avance(i) for i in contratos]
    
    # Mostrar tiempos
    cont = []
    tiempos = []

    for i in contratos:
        res = reservas[reservas['CONTRATO_ID']==i] #;print(res);print(len(res))
        cero_in_t1 = 0 in list(res['t_1p'])
        cero_in_t2 = 0 in list(res['t_2p'])
        cero_in_t3 = 0 in list(res['t_3p'])

        cont.append(i)

        if not cero_in_t2:
            # añadir t2
            tiempos.append('t2')

        elif cero_in_t2 and not cero_in_t1:
            # añadir t1
            tiempos.append('t1')

        elif cero_in_t1 and cero_in_t2 and not cero_in_t3:
            #añadri t3
            tiempos.append('t3')
        elif cero_in_t1 and cero_in_t2 and cero_in_t3:
            # Añadir F
            tiempos.append('F')

    tiempos_df = pd.DataFrame()
    tiempos_df['CONTRATO_ID'] = cont
    tiempos_df['TIEMPOS'] = tiempos

    data = reservas.groupby('CONTRATO_ID').sum()
    data = data.reset_index()[['CONTRATO_ID', 't_1p', 't_2p', 't_3p']]

    data = data.fillna(0.0) #; data = data.replace([np.inf, -np.inf], 0.0, inplace=True)
    
    if not tiempos_df.empty:
        data = data.merge(tiempos_df, on='CONTRATO_ID', how='left')

    list_reservas = list_reservas.merge(data, on='CONTRATO_ID', how='left')
    list_reservas['t_1p_str'] = [str(timedelta(seconds=int(i))) for i in list_reservas['t_1p']]
    list_reservas['t_2p_str'] = [str(timedelta(seconds=int(i))) for i in list_reservas['t_2p']]
    list_reservas['t_3p_str'] = [str(timedelta(seconds=int(i))) for i in list_reservas['t_3p']]

    list_reservas = list_reservas.merge(estado, on='CONTRATO_ID', how='left')
    #list_reservas = list_reservas[list_reservas['estado']!='FINALIZADO'] #;print(list_reservas)

    # Merge fecha entrega
    fecha_entrega = pd.DataFrame(FechaEntrega.objects.all().values()) #[['user','fecha_hora','estado','pedido']] #;print(fecha_entrega)
    fecha_entrega = fecha_entrega.rename(columns={'pedido':'CONTRATO_ID', 'estado':'estado_entrega'})

    list_reservas = list_reservas.merge(fecha_entrega, on='CONTRATO_ID', how='left') #;print(list_reservas)

    # hoy = datetime.now() #;print(hoy)
    # list_reservas['dias_faltantes'] = (list_reservas['fecha_hora'] - hoy).dt.days  #;print(type(list_reservas['dias_faltantes'][0]))
    # list_reservas['dias_faltantes'] = list_reservas['dias_faltantes'].astype(int)
    
    hoy_2 = date.today()
    
    list_reservas['fecha_entrega'] = list_reservas['fecha_hora'].dt.date  #;print(list_reservas['fecha_entrega'])

    try:
        if len(list_reservas) > 0:
            list_reservas['dias_faltantes'] = (list_reservas['fecha_entrega'] - hoy_2).dt.days
    except:
        pass

    list_reservas = list_reservas.sort_values(by=['fecha_hora'])
    list_reservas['fecha_hora'] = list_reservas['fecha_hora'].astype(str)
    list_reservas = list_reservas.replace('NaT','-')
    list_reservas = list_reservas.fillna('-')  #;print(type(list_reservas['dias_faltantes'][1])) ;print(list_reservas)
    
    list_reservas['fh'] = pd.to_datetime(list_reservas['fecha_hora'], errors='coerce')
    list_reservas['dia'] = list_reservas['fh'].dt.day_name(locale='es_EC.utf-8')
    try:
        list_reservas['dia'] = list_reservas['dia'].str.replace('Miã©rcoles','Miércoles')
    except:
        pass
    list_reservas['mes'] = list_reservas['fh'].dt.month_name(locale='es_EC.utf-8')

    list_reservas = list_reservas.merge(avance_df, on='CONTRATO_ID', how='left')
    
    return list_reservas


def publico_dashboard(request):

    list_reservas = publico_dashboard_fun()
    
    pub = list_reservas[list_reservas['estado']!='FINALIZADO']
    contratos = list(pub['CONTRATO_ID'].unique())
    sto = stock_faltante_contrato(contratos, 'BCT')

    if not sto.empty:
        pub = pub.merge(sto, on='CONTRATO_ID', how='left')

    fin = list_reservas[list_reservas['estado']=='FINALIZADO']

    pub = de_dataframe_a_template(pub)
    fin = de_dataframe_a_template(fin)

    context = {
        'list_reservas':pub,
        'fin':fin,
        'n_pedidos':len(pub),
        'por_facturar':len(fin)
    }

    return render(request, 'etiquetado/etiquetado_estado/dashboard.html', context)


def dashboard_completo(request):

    # PEDIDOS CEREZOS
    pedidos_cerezos = estado_pedidos_dashboard_fun('BCT')
    contratos_pedidos = list(pedidos_cerezos['CONTRATO_ID'].unique())
    sto_pedidos = stock_faltante_contrato(contratos_pedidos, 'BCT')
    
    if not sto_pedidos.empty:
        pedidos_cerezos = pedidos_cerezos.merge(sto_pedidos, on='CONTRATO_ID', how='left')

    # Fistrado por fecha
    hoy = date.today()
    ayer = hoy - timedelta(days=1)
    meses_2 = hoy - timedelta(days=30)

    pedidos_cerezos = pedidos_cerezos[pedidos_cerezos['FECHA_PEDIDO']>meses_2]

    pedidos_cerezos_hoy = len(pedidos_cerezos[pedidos_cerezos['FECHA_PEDIDO']==hoy])
    pedidos_cerezos_ayer = len(pedidos_cerezos[pedidos_cerezos['FECHA_PEDIDO']==ayer])
    pedidos_cerezos_mas3 = len(pedidos_cerezos[pedidos_cerezos['FECHA_PEDIDO']<ayer])

    if len(pedidos_cerezos) > 0:
        pedidos_cerezos['fecha_estado'] = pedidos_cerezos.apply(lambda x: 'hoy' if x['FECHA_PEDIDO']==hoy else 'ayer' if x['FECHA_PEDIDO']==ayer else 'mas3' if x['FECHA_PEDIDO']<ayer else 'mas3', axis=1)

    pedidos_cerezos['FECHA_PEDIDO'] = pedidos_cerezos['FECHA_PEDIDO'].astype(str)#;print(pedidos_cerezos)
    pedidos_cerezos = de_dataframe_a_template(pedidos_cerezos)


    # ETIQUETADO STOCK
    etiquetado = etiquetado_fun()
    urgente = 0.75
    correcto = 2
    rojo = len(etiquetado[etiquetado['Meses']<urgente])
    amarillo = etiquetado[etiquetado['Meses']>=urgente]
    amarillo = amarillo[amarillo['Meses']<correcto]
    amarillo = len(amarillo)

    etiquetado = de_dataframe_a_template(etiquetado)

    # ETIQUETADO PUBLICO
    publico = publico_dashboard_fun()
    publico = publico[publico['estado']!='FINALIZADO']
    contratos_publicos = list(publico['CONTRATO_ID'].unique())
    sto_publico = stock_faltante_contrato(contratos_publicos, 'BCT')
    
    
    if not sto_publico.empty:
        publico = publico.merge(sto_publico, on='CONTRATO_ID', how='left')
    
    publicos_n = len(publico)
    publico = de_dataframe_a_template(publico)

    context = {
        # PEDIDOS CEREZOS
        'pedidos_cerezos':pedidos_cerezos,
        'pedidos_cerezos_hoy':pedidos_cerezos_hoy,
        'pedidos_cerezos_ayer':pedidos_cerezos_ayer,
        'pedidos_cerezos_mas3':pedidos_cerezos_mas3,

        # ETIQUETADO STOCK
        'etiquetado':etiquetado,
        'urgente':urgente,
        'correcto':correcto,
        'rojo':rojo,
        'amarillo':amarillo,

        # PUBLICO
        'publico':publico,
        'publico_n':publicos_n
    }

    return render(request, 'etiquetado/pedidos/dashboard_completo.html', context)



def detalle_dashboard_armados(request):
    
    prod = request.POST['prod']
    ventas = ventas_armados_facturas_odbc(prod)
    cli = clientes_warehouse()[['CODIGO_CLIENTE','NOMBRE_CLIENTE']]

    ventas = ventas.merge(cli, on='CODIGO_CLIENTE', how='left')
    ventas = ventas.rename(columns={
        'QUANTITY':'VENTAS',
        'NOMBRE_CLIENTE':'CLIENTE'
    })
    ventas['VENTAS'] = ventas['VENTAS'].astype(int)

    # Dataframe to complete the dates
    un_anio = datetime.now() - timedelta(days=365)
    periodo_gim = pd.date_range(start=datetime.now(), end=un_anio, periods=11)
    df = pd.DataFrame()
    df.index = periodo_gim
    df['FECHA'] = periodo_gim
    df['CLIENTE']='GIM'
    df['CODIGO_CLIENTE'] = 'GIM0001'
    df['VENTAS'] = 0

    ventas = pd.concat([ventas, df])
    
    ventas['PERIODO'] = ventas['FECHA'].dt.to_period('M')

    ventas = ventas.pivot_table(
        index=['CLIENTE'], values=['VENTAS'], columns=['PERIODO'], aggfunc='sum',
        margins=True, margins_name='TOTAL', sort=False
    )

    ventas = ventas.sort_values(by=('VENTAS','TOTAL'), ascending=False).fillna('-').replace(0,'-')
    
    ventas = ventas.to_html(
        classes='table table-responsive table-bordered m-0 p-0', 
        float_format='{:.0f}'.format,
        )
    
    return HttpResponse(ventas)


def dashboard_armados(request):
    
    productos = ProductArmado.objects.filter(activo=True).values('producto__product_id')
    productos = pd.DataFrame(productos)
    productos = productos.rename(columns={'producto__product_id':'PRODUCT_ID'})
    prod = productos_odbc_and_django()[['product_id', 'Nombre', 'Marca', 'Unidad_Empaque', 't_armado']]
    prod = prod.rename(columns={'product_id':'PRODUCT_ID'})
    productos = productos.merge(prod, on='PRODUCT_ID', how='left')

    ventas = frecuancia_ventas() 
    stock = stock_lote_odbc()[['PRODUCT_ID', 'EGRESO_TEMP', 'DISP-MENOS-RESERVA', 'OH2']] 
    stock = stock.pivot_table(index='PRODUCT_ID', values=['OH2','DISP-MENOS-RESERVA','EGRESO_TEMP'], aggfunc='sum')

    reservas_sin_lote = pd.DataFrame(reservas_table())
    reservas_sin_lote = reservas_sin_lote.pivot_table(
        index=['PRODUCT_ID'], values=['QUANTITY'], aggfunc='sum'
    ).reset_index()
    reservas_sin_lote = reservas_sin_lote.rename(columns={'QUANTITY':'RESERVAS-SIN-LOTE'})

    armados = productos.merge(ventas, on='PRODUCT_ID', how='left').fillna(0)
    armados = armados.merge(stock, on='PRODUCT_ID', how='left').fillna(0)
    armados = armados.merge(reservas_sin_lote, on='PRODUCT_ID', how='left').fillna(0)

    armados['RESERVAS'] = armados.apply(lambda x: x['EGRESO_TEMP'] if x['EGRESO_TEMP']==x['RESERVAS-SIN-LOTE'] else x['RESERVAS-SIN-LOTE'], axis=1)

    
    ### PRODUCTOS EN TRANSITO
    transito = productos_transito_odbc()
    if not transito.empty:
        transito = transito.pivot_table(index=['PRODUCT_ID'], values=['OH'], aggfunc='sum').reset_index()
        armados = armados.merge(transito, on='PRODUCT_ID', how='left').fillna(0)
        armados['OH2'] = armados['OH2'] + armados['OH']

    armados['mensual'] = (armados['ANUAL'] / 12).round(0)
    armados['dip-meno-res-2'] = (armados['OH2'] - armados['RESERVAS']).round(0)
    armados['meses']   = (armados['dip-meno-res-2'] / armados['mensual']).round(2)
    #armados['armar']   = (armados['mensual'] - armados['dip-meno-res-2'])
    # Si dip-meno-res-2 mayor ponga 0 sino haga la resta
    armados['armar']   = armados.apply(
        lambda x: 0 if x['dip-meno-res-2'] > x['mensual'] else (x['mensual'] - x['dip-meno-res-2']), axis=1
    )

    armados = armados.rename(columns={
        'producto__description':'PRODUCT_NAME',
        'producto__marca2':'GROUP_CODE',
        'dip-meno-res-2':'disponible',
        'Nombre':'PRODUCT_NAME',
        'Marca':'GROUP_CODE'
    })
    
    armados['cartones'] = (armados['armar'] / armados['Unidad_Empaque']).round(2)#.replace(np.inf, 0).replace(-np.inf, 0).replace(-0,0)
    armados['tiempo_s'] = (armados['cartones'] * armados['t_armado']).round(0)
    armados = armados.fillna(0).replace(np.inf, 0)
    armados['tiempo_s'] = armados['tiempo_s'].astype(int)
    
    armados['tiempo'] = [str(timedelta(seconds=int(i))) for i in armados['tiempo_s']]

    armados['tiempo_str'] = armados.apply(
        lambda x: 'F' if x['t_armado'] == 0 else x['tiempo'], axis=1
    )

    urgente = armados[armados['meses']< 0.5]
    pronto  = armados[armados['meses']>=0.5]
    pronto  = pronto[pronto['meses']< 1]
    
    armados = armados.sort_values(by=['meses','mensual','PRODUCT_NAME'], ascending=[True, True, False])
    
    armados = de_dataframe_a_template(armados)

    context = {
        'armados':armados,
        'urgente':len(urgente),
        'pronto' :len(pronto),
        'actualizado':ultima_actualizacion('actulization_stoklote')
        
    }
    
    return render(request, 'etiquetado/pedidos/dashboard_armados.html', context)



def reporte_revision_reservas(request):

    from datos.views import revision_reservas_fun

    reporte = revision_reservas_fun()
    
    # Excel
    if not reporte.empty:
        hoy = datetime.today()
        hoy = str(hoy)
        n = 'Reporte-Reservas_' + hoy + '.xlsx'
        nombre = 'attachment; filename=' + '"' + n + '"'

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = nombre

        reporte.to_excel(response)

        return response

    else:
        messages.success(request, 'Reservas actualizadas, no hay items que mover !!!')
        return HttpResponseRedirect('/etiquetado/revision/imp/llegadas/list')



    
## CONTROL DE GUIAS Y COUIER
login_required(login_url='login')
def control_guias_list(request):
    
    ventas_fac = ventas_facturas_odbc()[['NOMBRE_CLIENTE', 'CODIGO_FACTURA', 'FECHA_FACTURA']]
    
    perfil = pd.DataFrame(UserPerfil.objects.all().values())
    user = pd.DataFrame(User.objects.all().values())
    user = user.rename(columns={'id':'user_id'})
    perfil = perfil.merge(user, on='user_id', how='left')[['id', 'first_name', 'last_name']]
    perfil = perfil.rename(columns={'id':'user_id'}) #;print(perfil)

    reg_guia = pd.DataFrame(RegistoGuia.objects.all().values())[['id','factura_c', 'user_id','transporte']]
    reg_guia['user_id'] = reg_guia['user_id'].astype(int)
    ventas_fac = ventas_fac.drop_duplicates(subset=['CODIGO_FACTURA'])
    ventas_fac['FECHA'] = pd.to_datetime(ventas_fac['FECHA_FACTURA'])
    ventas_fac = ventas_fac.sort_values(by=['FECHA'], ascending=[False])

    desde = '01-04-2023 00:00:01';desde = datetime.strptime(desde, '%d-%m-%Y %H:%M:%S')
    # meses_3 = datetime.today() - timedelta(days=90);print(meses_3)
    ventas_fac = ventas_fac[ventas_fac['FECHA']>desde]

    clientes = clientes_warehouse()[['NOMBRE_CLIENTE','CIUDAD_PRINCIPAL', 'CLIENT_TYPE']]

    ventas_fac = ventas_fac.merge(clientes, on='NOMBRE_CLIENTE', how='left')
    ventas_fac = ventas_fac[ventas_fac['CIUDAD_PRINCIPAL']!='QUITO']
    ventas_fac = ventas_fac[ventas_fac['CIUDAD_PRINCIPAL']!='SANGOLQUI']

    # junta = ventas_fac[ventas_fac['NOMBRE_CLIENTE']=='JUNTA DE BENEFICENCIA DE GUAYA']
    # solca = ventas_fac[ventas_fac['NOMBRE_CLIENTE']=='SOLCA MATRIZ GUAYAQUIL']
    # solca_tungurahua = ventas_fac[ventas_fac['NOMBRE_CLIENTE']=='SOLCA TUNGURAHUA']

    # ventas_fac = ventas_fac[ventas_fac['CLIENT_TYPE']!='HOSPU']
    # ventas_fac = pd.concat([ventas_fac, junta, solca, solca_tungurahua])
    ventas_fac['FECHA'] = ventas_fac['FECHA'].astype(str)

    #ventas_fac = ventas_fac[~ventas_fac.CODIGO_FACTURA.isin(reg_guia)]
    reg_guia = reg_guia.rename(columns={'factura_c':'CODIGO_FACTURA'})
    ventas_fac = ventas_fac.merge(reg_guia, on='CODIGO_FACTURA', how='left').fillna(0)
    ventas_fac = ventas_fac.merge(perfil, on='user_id', how='left')
    ventas_fac['id'] = ventas_fac['id'].astype(int)
    # print(ventas_fac)

    ventas_fac['user_reg'] = ventas_fac['first_name'] + ' ' + ventas_fac['last_name']
    ventas_fac = ventas_fac.sort_values(by=['CODIGO_FACTURA'], ascending=False).fillna('Sin Registrar')
    
    reg = list(ventas_fac['user_reg'].unique())
    
    ventas_fac = de_dataframe_a_template(ventas_fac)
    
    if request.method=='POST':
        desde = request.POST['desde']
        hasta = request.POST['hasta']
        
        rep = RegistoGuia.objects.filter(fecha_conf__range=[desde, hasta]).values(
            'cliente',
            'factura',
            'factura_c',
            'ciudad',
            'fecha_factura',
            'transporte',
            'fecha_conf',
            'n_guia',
            'confirmado',
            'user__user__first_name',
            'user__user__last_name'
        )
        
        rep_df = pd.DataFrame(rep)
        
        rep_df['Registrado por'] = rep_df['user__user__first_name'] + ' ' + rep_df['user__user__last_name']
        rep_df = rep_df.rename(columns={
            'cliente':'Cliente',            
            'factura':'N°. Factura',
            'factura_c':'N°. Factura GIM',
            'fecha_factura':'Fecha Factura',
            
            'transporte':'Transporte',
            'n_guia':'N°. Guia',
            'ciudad':'Ciudad',
            'fecha_conf':'Fecha Confirmado',
            'confirmado':'Confirmado por',
        })
        
        rep_df = rep_df[[
            'Cliente',
            'N°. Factura',
            'N°. Factura GIM',
            'Fecha Factura',
            'Transporte',
            'N°. Guia',
            'Ciudad',
            'Fecha Confirmado',
            'Confirmado por',
            'Registrado por'
        ]]

        rep_df['Fecha Factura'] = rep_df['Fecha Factura'].astype(str)
        rep_df['Fecha Confirmado'] = rep_df['Fecha Confirmado'].astype(str)
        
        hoy = str(datetime.today())
        n = 'Reporte-Guias_'+hoy+'.xlsx'
        nombre = 'attachment; filename=' + '"' + n + '"'
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        response['Content-Disposition'] = nombre
        rep_df.to_excel(response, index=False)
        
        return response

    context = {
        'ventas_fac':ventas_fac,
        'reg':reg
    }

    return render(request, 'guias/facturas_lista.html', context)

login_required(login_url='login')
def control_guias_registro(request, n_fac):

    form = RegistroGuiaForm()

    fac = ventas_facturas_odbc()
    fac = fac.drop_duplicates(subset=['CODIGO_FACTURA'])
    fac = fac[fac['CODIGO_FACTURA']==n_fac]

    clientes = clientes_warehouse()[['NOMBRE_CLIENTE','CIUDAD_PRINCIPAL']]

    fac = fac.merge(clientes, on='NOMBRE_CLIENTE', how='left')
    fac = fac[['NOMBRE_CLIENTE', 'CIUDAD_PRINCIPAL', 'CODIGO_FACTURA', 'FECHA_FACTURA']]
    fac = fac.to_dict(orient='records')[0]

    if request.method == 'POST':
        form = RegistroGuiaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/etiquetado/guias/list')

    context = {
        'fac':fac
    }

    return render(request, 'guias/facturas_registro.html', context)

login_required(login_url='login')
def control_guias_editar(request, id):

    reg = RegistoGuia.objects.get(id=id);print(reg)

    if request.method == 'POST':
        form = RegistroGuiaForm(request.POST, instance=reg)
        if form.is_valid():
            form.save()
            return redirect('/etiquetado/guias/list')

    context = {
        'fac':reg
    }

    return render(request, 'guias/editar.html', context)


def entrega_estado_ajax(request):

    n_pedido = request.POST['pedido']
    entrega_estado = request.POST['entrega_estado']
    usr = request.user.id
    usr = UserPerfil.objects.get(user_id=usr)#.id 

    obj = FechaEntrega.objects.get(pedido=n_pedido)
    obj.est_entrega = entrega_estado
    obj.reg_entrega = usr
    obj.save()
    return HttpResponse('ok')


def etiquetado_stock_detalle(request, product_id):

    stock = stock_lote_cuc_etiquetado_detalle_odbc()
    product = productos_odbc_and_django()
    ventas = frecuancia_ventas()[frecuancia_ventas()['PRODUCT_ID']==product_id]
    ventas['MENSUAL'] = round(ventas['ANUAL'] / 12, 0)
    ventas = ventas.to_dict(orient='records')[0]
    product = product.rename(columns={'product_id':'PRODUCT_ID'})[[
        'PRODUCT_ID', 'Unidad_Empaque', 'volumen', 'peso', 't_etiq_1p', 't_etiq_2p', 't_etiq_3p'
    ]]

    stock = stock[stock['PRODUCT_ID']==product_id]

    stock = stock.merge(product, on='PRODUCT_ID', how='left')
    stock['i'] = [i+1 for i in range(0, len(stock))]
    
    stock['FECHA_CADUCIDAD'] = stock['FECHA_CADUCIDAD'].astype(str)
    codigo = stock['PRODUCT_ID'].iloc[0]
    nombre = stock['PRODUCT_NAME'].iloc[0]
    marca = stock['GROUP_CODE'].iloc[0]
    
    stock['cartones'] = (stock['OH2'] / stock['Unidad_Empaque']).round(2)
    stock['vol'] = stock['cartones'] * stock['volumen']
    stock['pes'] = stock['cartones'] * stock['peso']

    stock['t1'] = (stock['cartones'] * stock['t_etiq_1p']).round(0)
    stock['t2'] = (stock['cartones'] * stock['t_etiq_2p']).round(0)
    stock['t3'] = (stock['cartones'] * stock['t_etiq_3p']).round(0)

    vol_total = stock['vol'].sum()
    pes_total = stock['pes'].sum()

    t1_total = stock['t1'].sum()
    t2_total = stock['t2'].sum()
    t3_total = stock['t3'].sum()
    t_unidades = stock['OH2'].sum()
    t_cartones = stock['cartones'].sum()

    stock['t_str_1p'] = [str(timedelta(seconds=i)) for i in stock['t1']]
    stock['t_str_2p'] = [str(timedelta(seconds=i)) for i in stock['t2']]
    stock['t_str_3p'] = [str(timedelta(seconds=i)) for i in stock['t3']]

    tt_str_1p = str(timedelta(seconds=t1_total))
    tt_str_2p = str(timedelta(seconds=t2_total))
    tt_str_3p = str(timedelta(seconds=t3_total))
    
    stock = de_dataframe_a_template(stock)
    
    context = {
        'stock':stock,
        'codigo':codigo,
        'nombre':nombre,
        'marca':marca,
        'ventas':ventas,

        'tt_str_1p':tt_str_1p,
        'tt_str_2p':tt_str_2p,
        'tt_str_3p':tt_str_3p,

        'vol_total':vol_total,
        'pes_total':pes_total,
        't_unidades':t_unidades,
        't_cartones':t_cartones
    }

    return render(request, 'etiquetado/pedidos/etiquetado_cuarentena.html', context)
    

# BUSCAR UBICACIÓN EN WMS DE PRODUCTO EN CUARENTENA
def etiquetado_stock_wms_ajax(request):
    
    try:
        existencia = Existencias.objects.filter(
            Q(product_id=request.POST.get('product_id'))&Q(lote_id=request.POST.get('lote_id'))
        ).values(
            'unidades',
            'estado',
            'ubicacion__bodega',
            'ubicacion__pasillo',
            'ubicacion__modulo',
            'ubicacion__nivel'
            )
        existencia = pd.DataFrame(existencia)
        existencia['ubicación'] = (
            existencia['ubicacion__bodega'] + '-' +
            existencia['ubicacion__pasillo'] + '-' +
            existencia['ubicacion__modulo'] + '-' +
            existencia['ubicacion__nivel']
            )
        existencia['unidades'] = existencia['unidades'].apply(lambda x:'{:,.0f}'.format(x))
        existencia = existencia[['estado','ubicación','unidades']]
        existencia = existencia.to_html(
            float_format='{:,.0f}'.format,
            classes='table table-responsive table-bordered m-0 p-0',
            table_id= 'reservas_table',
            index=False,
            justify='start'
        )
        
        return HttpResponse(existencia)
    except:
        return HttpResponse('Error !!!')
    
    

### INSTRUCTIVO ETIQUETADO
def list_instructo_etiquetado(request):
    
    inst = InstructivoEtiquetado.objects.all().order_by('producto__product_id')
    
    context = {
        'inst':inst
    }
    
    return render(request, 'etiquetado/instructivo_etiquetado/list.html', context)


def set_estado_etiquetado_stock(request):
    
    prod = request.POST['product_id']
    est  = request.POST['estado']
    
    obj = EstadoEtiquetadoStock(
        product_id = prod,
        estado     = est
    )
    
    obj.save()
    
    return HttpResponse('Cambio de estado exitoso !!!')


def actualizar_facturas_ajax(request):
    
    update = actualizar_facturas_odbc()
    #import time
    #time.sleep(3)
    #update = 'ok'
    
    if update == 'ok':
    
        return JsonResponse({
            'tipo':'success',
            'msg':'Actualización exitosa'
        })
    elif update == 'fail':
        
        return JsonResponse({
            'tipo' : 'danger',
            'msg':'Error en actualización'
        })
    

# Listado de proformas
def listado_proformas(request):
    
    proformas = lista_proformas_odbc()
    proformas = proformas.drop_duplicates(subset=['contrato_id'])
    proformas['fecha_pedido'] = pd.to_datetime(proformas['fecha_pedido']).dt.strftime("%Y-%m-%d")
    proformas = proformas.sort_values(by='fecha_pedido', ascending=False)
    proformas = de_dataframe_a_template(proformas)
    
    context = {
        'proformas':proformas
    }

    return render(request, 'etiquetado/proformas/listado.html', context)


# Detalle de proforma
def detalle_proforma(request, contrato_id):
    
    vehiculo = Vehiculos.objects.filter(activo=True).order_by('transportista')
    prod = productos_odbc_and_django()[['product_id','Nombre','Marca','Unidad_Empaque','Volumen','Peso','t_etiq_1p','t_etiq_2p','t_etiq_3p']]
    proforma = proformas_por_contrato_id_odbc(contrato_id)
    proforma = proforma[proforma['product_id']!='MANTEN']
    
    proforma = proforma.merge(prod, on='product_id', how='left')
    
    # Calculos
    proforma['cartones'] = proforma['quantity'] / proforma['Unidad_Empaque']
    proforma = proforma.fillna(0.0).replace(np.inf, 0.0)
    proforma['volumen'] = proforma['cartones'] * (proforma['Volumen']/1000000)
    proforma['peso'] = proforma['cartones'] * proforma['Peso']
    
    # Tiempos
    proforma['t_1p'] = (proforma['cartones'] * proforma['t_etiq_1p']).round(0)
    proforma['t_2p'] = (proforma['cartones'] * proforma['t_etiq_2p']).round(0)
    proforma['t_3p'] = (proforma['cartones'] * proforma['t_etiq_3p']).round(0)
    
    proforma['t_1p_str'] = [str(timedelta(seconds=(i))) for i in proforma['t_1p']]
    proforma['t_2p_str'] = [str(timedelta(seconds=(i))) for i in proforma['t_2p']]
    proforma['t_3p_str'] = [str(timedelta(seconds=(i))) for i in proforma['t_3p']]
    
    # Totales
    t_unidades = proforma['quantity'].sum()
    t_cartones = proforma['cartones'].sum()
    t_1p = str(timedelta(seconds=int(proforma['t_1p'].sum())))
    t_2p = str(timedelta(seconds=int(proforma['t_2p'].sum())))
    t_3p = str(timedelta(seconds=int(proforma['t_3p'].sum())))
    t_volumen = proforma['volumen'].sum()
    t_peso = proforma['peso'].sum()
    
    # Cabecera
    cliente = proforma['nombre_cliente'].iloc[0]
    fecha_proforma = proforma['fecha_pedido'].iloc[0]
    
    # Cero en peso
    p_cero = 0 in list(proforma['peso'])
    proforma = de_dataframe_a_template(proforma)
    
    context = {
        'proforma':proforma,
        
        # totales
        't_unidades':t_unidades,
        't_cartones':t_cartones,
        't_1p':t_1p,
        't_2p':t_2p,
        't_3p':t_3p,
        't_volumen':t_volumen,
        't_peso':t_peso,
        
        # cabecera
        'contrato_id':contrato_id,
        'cliente':cliente,
        'fecha_proforma':fecha_proforma,
        'p_cero':p_cero,
        
        # Vehiculos
        'vehiculos':vehiculo,
    }
    
    return render(request, 'etiquetado/proformas/proforma.html', context)