# DB
from django.db import connections

# Time
from datetime import datetime, date, timedelta

# Shorcuts
from django.shortcuts import render, redirect

from django.shortcuts import get_object_or_404

import io
import re

from django.core.mail import EmailMessage
from itertools import chain
from django.forms.models import model_to_dict
    
# Pandas
import pandas as pd
import numpy as np

# Datos Models
from datos.models import Product, Vehiculos, TimeStamp, StockConsulta, AdminActualizationWarehaouse
from wms.models import Transferencia
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
    EstadoEtiquetadoStock,
    AnexoDoc, 
    AnexoGuia,
    AddEtiquetadoPublico,
    UbicacionAndagoya,
    ProductoUbicacion,
    PedidoTemporal,
    ProductosPedidoTemporal
    )

from mantenimiento.models import Equipo
from users.models import UserPerfil, User

# Wms models
from wms.models import OrdenEmpaque

# Forms
from etiquetado.forms import (
    RowItemForm,
    PedidosEstadoEtiquetadoForm,
    RegistroGuiaForm,
    AnexoGuiaForm, 
    AnexoDocForm,
    UbicacionAndagoyaForm,
    ProductoUbicacionForm,
    PedidoTemporalForm,
    ProductosPedidoTemporalForm,
    TransfCerAndForm
)

# Json
import json

# Messages
from django.contrib import messages

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
from django.urls import reverse

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

# Etiquetado
from etiquetado.models import TransfCerAnd, ProductosTransfCerAnd

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
    
    # Proformas
    lista_proformas_odbc,
    proformas_por_contrato_id_odbc,
    
    
    # Extraer número de factura
    extraer_numero_de_factura,
    
    inventario_transferencia_data
    )


from api_mba.tablas_warehouse import (
    api_actualizar_facturas_warehouse, 
    api_actualizar_imp_transito_warehouse
    )


def lista_pedidos_agregar_dashboard_publico():

    pedidos = AddEtiquetadoPublico.objects.all()
    
    lista_pedidos = []
    for i in pedidos:
        pedido = i.contrato_id + '.0'
        lista_pedidos.append(pedido)
        
    return lista_pedidos


@csrf_exempt
@login_required(login_url='login')
def add_etiquetado_publico(request):

    data = json.loads(request.body)
    contrato = data.get('contrato')
    if contrato:
        AddEtiquetadoPublico.objects.create(contrato_id=contrato)
        return JsonResponse({'msg':'ok'})
    

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
@login_required(login_url='login')
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

@login_required(login_url='login')
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
@login_required(login_url='login')
def etiquetado_pedidos(request, n_pedido):

    try:
        
        vehiculo = Vehiculos.objects.filter(activo=True).order_by('transportista')
        
        # Dataframes
        pedido = pedido_por_cliente(n_pedido) 
        pedido = pedido[pedido['PRODUCT_ID']!='MANTEN']
        
        # Agrupar pedido por código
        pedido = pedido.groupby(by=[
            'FECHA_PEDIDO', 'CONTRATO_ID', 'CODIGO_CLIENTE', 'NOMBRE_CLIENTE',
            'PRODUCT_ID', 'PRODUCT_NAME', 'WARE_CODE',
            'CONFIRMED', 'HORA_LLEGADA', 'SEC_NAME_CLIENTE'
        ]).sum().reset_index()
        
        cabecera = pedido.merge(clientes_warehouse()[['CODIGO_CLIENTE','IDENTIFICACION_FISCAL']], on='CODIGO_CLIENTE', how='left')[[
            'WARE_CODE',
            'CONTRATO_ID',
            'NOMBRE_CLIENTE',
            'IDENTIFICACION_FISCAL',
            'FECHA_PEDIDO',
        ]]
        cabecera['FECHA_PEDIDO'] = cabecera['FECHA_PEDIDO'].astype('str')
        cabecera = de_dataframe_a_template(cabecera)[0]
        
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
        pedido['vol_total'] = pedido['Cartones'] * (pedido['Volumen'] / 1000000)
        pedido['pes_total'] = pedido['Cartones'] * pedido['Peso']
        
        p_cero = 0 in list(pedido['pes_total']) 
        
        pedido = pedido.fillna(0.0).replace(np.inf, 0.0) 

        # Mejor formato de tiempo
        pedido['t_s_1p']   = (pedido['Cartones'] * pedido['t_etiq_1p'].round(0))
        pedido['t_str_1p'] = [str(timedelta(seconds=int(i))) for i in pedido['t_s_1p']] 

        pedido['t_s_2p']   = (pedido['Cartones'] * pedido['t_etiq_2p']).round(0)
        pedido['t_str_2p'] = [str(timedelta(seconds=int(i))) for i in pedido['t_s_2p']]

        pedido['t_s_3p']   = (pedido['Cartones'] * pedido['t_etiq_3p'].round(0))
        pedido['t_str_3p'] = [str(timedelta(seconds=int(i))) for i in pedido['t_s_3p']]

        tt_str_1p = str(timedelta(seconds=int(pedido['t_s_1p'].sum())))
        tt_str_2p = str(timedelta(seconds=int(pedido['t_s_2p'].sum())))
        tt_str_3p = str(timedelta(seconds=int(pedido['t_s_3p'].sum())))

        # STOCK
        items = pedido['PRODUCT_ID'].unique()
        items = list(items) 
        bodega = pedido['WARE_CODE'].unique()[0] 
        stock = stock_disponible(bodega=bodega, items_list=items)
        
        pedido = pedido.merge(stock, on='PRODUCT_ID', how='left').fillna(0)
        pedido['disp'] = pedido['stock_disp']>pedido['QUANTITY']
        
        pedido = pedido.sort_values(by=['PRODUCT_NAME']) 
        
        # Avance
        avance = etiquetado_avance_pedido(n_pedido) 
        if not avance.empty:
            avance = avance[['PRODUCT_ID','unidades']] 
            pedido = pedido.merge(avance, on='PRODUCT_ID', how='left').fillna(0) 
            pedido = pedido.drop_duplicates(subset=['PRODUCT_ID','QUANTITY'])
        
        # Transformar Datos para presentar en template
        data = de_dataframe_a_template(pedido)

        if FechaEntrega.objects.filter(pedido=n_pedido).exists():
            fecha_entrega = FechaEntrega.objects.get(pedido=n_pedido)
        else:
            fecha_entrega='None'

        if PedidosEstadoEtiquetado.objects.filter(n_pedido=n_pedido).exists():
            estado = PedidosEstadoEtiquetado.objects.get(n_pedido=n_pedido).estado
            estado = str(estado) 
        else:
            estado = 'None'
        
        # Estado Picking
        estado_picking = EstadoPicking.objects.filter(n_pedido=n_pedido) #.first().estado
        if estado_picking.exists():
            estado_picking = True if estado_picking.first().estado == 'FINALIZADO' else False
        else:
            estado_picking = False
        
        
        # Totales de tabla
        t_total_1p_hor = pedido['t_una_p_hor'].sum()
        t_total_2p_hor = pedido['t_dos_p_hor'].sum()
        t_total_3p_hor = pedido['t_tre_p_hor'].sum()

        t_total_vol = pedido['vol_total'].sum()
        t_total_pes = pedido['pes_total'].sum()
        t_cartones = pedido['Cartones'].sum()
        t_unidades = pedido['QUANTITY'].sum()

        context = {
            'cabecera':cabecera,
            'reservas':data,

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

            'vehiculos':vehiculo,
            'fecha_entrega':fecha_entrega,
            
            'estado':estado,
            'p_cero':p_cero,
            'bodega':bodega,
            
            'estado_picking':estado_picking
        }

        return render(request, 'etiquetado/pedidos/pedido.html', context)
    
    except Exception as e:
        context = {'error':f'Error !!! carga nuevamente la página. {e}'}
        return render(request, 'etiquetado/pedidos/pedido.html', context)


@login_required(login_url='login')
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
        pedido['FECHA_CADUCIDAD'] = pedido['FECHA_CADUCIDAD'].astype('str')
        
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


@login_required(login_url='login')
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
@login_required(login_url='login')
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
@login_required(login_url='login')
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
@login_required(login_url='login')
def facturas_list(request):
    with connections['gimpromed_sql'].cursor() as cursor:

        cursor.execute("SELECT * FROM facturas")

        columns = [col[0] for col in cursor.description]

        facturas = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        facturas = pd.DataFrame(facturas)
        facturas['FECHA_FACTURA'] = facturas['FECHA_FACTURA'].astype('str')
        facturas['CODIGO_FACTURA'] = facturas['CODIGO_FACTURA'].apply(lambda x: int(x.split('-')[1][4:]))
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
    return pd.DataFrame(facturas)


@login_required(login_url='login')
def facturas(request, n_factura):

    vehiculo = Vehiculos.objects.filter(activo=True).order_by('transportista')

    # Dataframes
    n_factura = int(n_factura)
    n_factura = 'FCSRI-1001' + f'{n_factura:09d}' + '-GIMPR'
    
    factura = factura_por_cliente(n_factura)
    factura = factura[factura['PRODUCT_ID']!='MANTEN']
    
    product = productos_odbc_and_django()
    product['vol'] = product['Volumen'] / 1000000
    product = product.rename(columns={'product_id':'PRODUCT_ID'})
    
    # Merge
    factura = factura.merge(product, on='PRODUCT_ID', how='left')

    # Calculos
    factura['Cartones'] = factura['QUANTITY'] / factura['Unidad_Empaque']
    factura = factura.fillna(0).replace(np.inf, 0)
    
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
@login_required(login_url='login')
def pedidos_estado_list(request):

    add_pedidos = lista_pedidos_agregar_dashboard_publico()
    
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
        
        add_pedidos = reservas[reservas.CONTRATO_ID.isin(add_pedidos)]

        # Etiquetado especial
        especial = reservas[reservas['CONTRATO_ID']=='69236.0']

        # ETIQUETADO PARA PUBLICO
        eti_p = reservas[reservas['SEC_NAME_CLIENTE']=='PUBLICO']

        # Solo Hospitales Publicos
        tipo_clientes = ['HOSPU', 'STOCK'] #'DISTR'
        #reservas = reservas[reservas['SEC_NAME_CLIENTE']=='PUBLICO']
        reservas = reservas[reservas.CLIENT_TYPE.isin(tipo_clientes)]
        

        reservas = pd.concat([reservas, eti_p, especial,add_pedidos])
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
@login_required(login_url='login')
def estado_etiquetado(request, n_pedido, id):
    
    pedido_cabecera = de_dataframe_a_template(pedido_por_cliente(n_pedido))[0] 
    cliente = pedido_cabecera['NOMBRE_CLIENTE']
    fecha_pedido = pedido_cabecera['FECHA_PEDIDO']

    product = productos_odbc_and_django()[['product_id','Nombre','Marca','Unidad_Empaque']]
    product = product.rename(columns={'product_id':'PRODUCT_ID'})
    
    pedido = pedido_por_cliente(n_pedido)[['PRODUCT_ID','QUANTITY']]
    pedido = pedido.groupby(by=['PRODUCT_ID']).sum().reset_index() 
    pedido = pedido.merge(product, on='PRODUCT_ID', how='left').fillna(0) 
    pedido['Cartones'] = pedido['QUANTITY'] / pedido['Unidad_Empaque'] 
    
    avance = etiquetado_avance_pedido(n_pedido) 
    if not avance.empty:
        avance = avance.rename(columns={'id':'avance'})
        pedido = pedido.merge(avance, on='PRODUCT_ID', how='left')
        
    t_cartones = pedido['Cartones'].sum()
    t_unidades = pedido['QUANTITY'].sum()
    
    pedido = de_dataframe_a_template(pedido)
    
    
    if id == '-':

        form = PedidosEstadoEtiquetadoForm()

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
            
            estado_registro = PedidosEstadoEtiquetado.objects.get(id=id_estado)
            form_update = PedidosEstadoEtiquetadoForm(request.POST, instance=estado_registro)
            if form_update.is_valid():
                form_update.save()
                return redirect(f'/etiquetado/pedidos/estado/list')

    return render(request, 'etiquetado/etiquetado_estado/estado_etiquetado.html', context)


# Detalle vista Andagoya
@login_required(login_url='login')
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
@login_required(login_url='login')
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
Nuestro horario de atención es: Lunes a Viernes de 8:00 am a 13:30 pm y de 14:00 pm a 16:30 pm.
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
    
    if n_whatsapp and n_whatsapp.startswith('+593') and len(n_whatsapp) == 13:

        # Send whatsapp
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

        # si se envia whatsapp set value
        if response.status_code == 200: 
            picking_estado.whatsapp = True
    
        # si no hay número o el numero el incorrecto
    elif not n_whatsapp or not n_whatsapp.startswith('+593'):
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
        
        # # HABILITAR ACTUALIZACIÓN
        # actualizado = pd.DataFrame(TimeStamp.objects.all().values())
        # actualizado = list(actualizado['actulization_stoklote'])
        # act = []
        # for i in actualizado:
        #     if i != '':
        #         act.append(i)
        # actualizado = act[-1][0:19]

        # act = datetime.strptime(actualizado, '%Y-%m-%d %H:%M:%S') #%H:%M:%S
        # aho = datetime.now()

        # d = aho-act
        # d = pd.Timedelta(d)
        # d = d.total_seconds()
        # t_s = 60

        # if d > t_s:
        #     dd = None
        # else:
        #     dd = 'disabled'

        reservas_actualizado = AdminActualizationWarehaouse.objects.get(table_name='reservas').datetime

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


        # if request.method == 'POST':
        #     if d > t_s:
        #         import pyodbc
        #         import mysql.connector

        #         try:
        #             mydb = mysql.connector.connect(
        #                     host="172.16.28.102",
        #                     user="standard",
        #                     passwd="gimpromed",
        #                     database="warehouse"
        #             )

        #             cnxn = pyodbc.connect('DSN=mba3;PWD=API')
        #             cursorOdbc = cnxn.cursor()
        #             cursor_write = mydb.cursor()

        #             cursorOdbc.execute(
        #             "SELECT CLNT_Pedidos_Principal.FECHA_PEDIDO, CLNT_Pedidos_Principal.CONTRATO_ID, CLNT_Ficha_Principal.NOMBRE_CLIENTE, "
        #             "CLNT_Pedidos_Detalle.PRODUCT_ID, CLNT_Pedidos_Detalle.PRODUCT_NAME, CLNT_Pedidos_Detalle.QUANTITY, CLNT_Pedidos_Detalle.Despachados, CLNT_Pedidos_Principal.WARE_CODE, CLNT_Pedidos_Principal.CONFIRMED, CLNT_Pedidos_Principal.HORA_LLEGADA, CLNT_Pedidos_Principal.SEC_NAME_CLIENTE "
        #             "FROM CLNT_Ficha_Principal CLNT_Ficha_Principal, CLNT_Pedidos_Detalle CLNT_Pedidos_Detalle, CLNT_Pedidos_Principal CLNT_Pedidos_Principal "
        #             "WHERE CLNT_Pedidos_Principal.CONTRATO_ID_CORP = CLNT_Pedidos_Detalle.CONTRATO_ID_CORP AND CLNT_Ficha_Principal.CODIGO_CLIENTE = CLNT_Pedidos_Principal.CLIENT_ID "
        #             "AND ((CLNT_Pedidos_Principal.PEDIDO_CERRADO=false) AND (CLNT_Pedidos_Detalle.TIPO_DOCUMENTO='PE')) ORDER BY CLNT_Pedidos_Principal.CONTRATO_ID DESC"
        #             )

        #             reservas = cursorOdbc.fetchall()

        #             sql_delete="DELETE FROM reservas"
        #             cursor_write.execute(sql_delete)

        #             sql_insert_reservas = """INSERT INTO reservas (FECHA_PEDIDO, CONTRATO_ID, NOMBRE_CLIENTE,
        #             PRODUCT_ID, PRODUCT_NAME, QUANTITY, Despachados, WARE_CODE, CONFIRMED, HORA_LLEGADA, SEC_NAME_CLIENTE) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"""
        #             data_reservas = [list(rows) for rows in reservas]
        #             res = cursor_write.executemany(sql_insert_reservas, data_reservas)
        #             mydb.commit()

        #             time = str(datetime.now())
        #             TimeStamp.objects.create(actulization_stoklote=time)

        #             return redirect('picking_estado') #render(request, 'etiquetado/picking_estado/picking_estado.html', context)

        #         except:
        #             print('NO SE ACTULIZO')
                    
        #         finally:
        #             cnxn.close()
        #             cursorOdbc.close()
                    
        #     else:
        #         print('menos 1 min - RESERVAS')

        context = {
            'reservas':reservas,
            # 'disabled':dd,
            'actualizado':reservas_actualizado
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

    estado_picking = EstadoPicking.objects.filter(n_pedido=n_pedido).exists()
    if estado_picking:
        est = EstadoPicking.objects.get(n_pedido=n_pedido)
        estado = est.estado
        estado_id = est.id
    else:
        estado = 'SIN ESTADO'
        estado_id = ''

    pedido = pedido_por_cliente(n_pedido)
    
    ubicaciones_andagoya = productos_ubicacion_lista_template()

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
    
    data = de_dataframe_a_template(pedido)
    
    for i in data:
        product_id = i['PRODUCT_ID']
        for j in ubicaciones_andagoya:
            if j['product_id'] == product_id:
                i['ubicaciones'] = j['ubicaciones']
                break
    
    context = {
        'reservas':data,
        'pedido':n_pedido,

        'cabecera':data[0],
        'fecha_pedido': pedido['FECHA_PEDIDO'].iloc[0],
        
        'f_pedido':f_pedido,
        't_cartones':t_cartones,
        't_unidades':t_unidades,
        'detalle':p_str,
        'estados':['EN PROCESO'],
        'estado':estado,
        'estado_id':estado_id
    }

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
@login_required(login_url='login')
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
    
    try:

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

    except Exception as e:
        print(e)
    finally:
        cursor.close()
        cnxn.close()


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
@login_required(login_url='login')
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
        
        api_actualizar_imp_transito_warehouse()

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


@login_required(login_url='login')
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
@login_required(login_url='login')
def revision_imp_llegadas_list(request):
    
    imp = importaciones_llegadas_odbc()
    pro = productos_odbc_and_django()

    imp = imp.merge(pro, on='product_id', how='left').fillna('')

    imp = imp[[
        'DOC_ID_CORP',
        'ENTRADA_FECHA',
        'WARE_COD_CORP',
        'Marca',
        'marca2',
    ]]
    
    imp['MARCA'] = imp.apply(lambda row: row['Marca'] if not row['marca2'] else row['marca2'], axis=1)
    
    imp['ENTRADA_FECHA'] = imp['ENTRADA_FECHA'].astype('str')

    imp = imp.drop_duplicates(subset=['DOC_ID_CORP'])
    imp = imp.sort_values(['ENTRADA_FECHA'], ascending=[False])[:50]
    imp_list = de_dataframe_a_template(imp)
    
    actualizado = ultima_actualizacion('actualization_reserva_lote')

    context = {
        'imp':imp_list,
        'actualizado':actualizado
    }

    return render(request, 'etiquetado/revision_reservas/importaciones_llegadas_list.html', context)


@login_required(login_url='login')
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


def pedidos_warhouse_data():
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute("SELECT CONTRATO_ID, NUM_PRINT FROM pedidos")
        columns = [col[0] for col in cursor.description]
        pedidos = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
        pedidos = pd.DataFrame(pedidos)

    return pedidos


# Dashboards de pedidos
def estado_pedidos_dashboard_fun(bodega):

    reservas = pd.DataFrame(reservas_table())
    reservas = reservas[reservas['WARE_CODE']==bodega]
    num_print = pedidos_warhouse_data()
    reservas = reservas.merge(num_print, on='CONTRATO_ID', how='left')

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
    solca_thu = reservas[reservas['NOMBRE_CLIENTE']=='SOLCA TUNGURAHUA']
    junta_gye = reservas[reservas['NOMBRE_CLIENTE']=='JUNTA DE BENEFICENCIA DE GUAYA']

    # Fistrado de datos
    reservas = reservas[reservas['NOMBRE_CLIENTE']!='GIMPROMED CIA. LTDA.']
    reservas = reservas[reservas['CLIENT_TYPE']!='HOSPU']

    # Añadir clientes
    reservas = pd.concat([reservas, solca_uio, solca_gye, junta_gye, solca_thu])

    # Filtrar por finalizado y reservas
    reservas = reservas[reservas['estado']!='FINALIZADO']
    reservas = reservas[reservas['SEC_NAME_CLIENTE']!='RESERVA']

    # Llenar None y ordenar
    reservas = reservas.fillna('-')
    reservas = reservas.sort_values(by=['FECHA_PEDIDO', 'HORA_LLEGADA'])

    return reservas


def picking_dashboard_json_response(request, bodega):

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

    ayer = hoy - timedelta(days=1)
    pedidos_ayer = reservas[reservas['FECHA_PEDIDO']==ayer]
    pedidos_ayer_n = len(pedidos_ayer)

    pedidos_mas3 = reservas[reservas['FECHA_PEDIDO']<ayer]#[['CONTRATO_ID','FECHA_PEDIDO']];print(pedidos_mas3)
    pedidos_mas3_n = len(pedidos_mas3)

    # Definir columna de dia para añadir color
    if len(reservas) > 0:
        reservas['fecha_estado'] = reservas.apply(lambda x: 'hoy' if x['FECHA_PEDIDO']==hoy else 'ayer' if x['FECHA_PEDIDO']==ayer else 'mas3' if x['FECHA_PEDIDO']<ayer else 'mas3', axis=1)

    # Config
    reservas['FECHA_PEDIDO'] = reservas['FECHA_PEDIDO'].astype(str)
    reservas = de_dataframe_a_template(reservas)

    context = {
        'reservas':reservas,
        'hoy':pedidos_hoy_n,
        'ayer':pedidos_ayer_n,
        'mas3':pedidos_mas3_n,
        'bodega':b
    }
    
    return JsonResponse(context, safe=False)
    #return render(request, 'dashboards/dashboard.html', context)


def picking_dashboard(request, bodega):
    return render(request, 'dashboards/dashboard_vue.html')



def publico_dashboard_fun():
    
    reservas = pd.DataFrame(reservas_table())
    reservas = reservas[reservas['PRODUCT_ID']!='MANTEN']

    add_pedidos = lista_pedidos_agregar_dashboard_publico()
    nuevos_pedidos = reservas[reservas.CONTRATO_ID.isin(add_pedidos)]
    
    pro = productos_odbc_and_django()[['product_id', 'Unidad_Empaque', 't_etiq_1p', 't_etiq_2p', 't_etiq_3p']]
    estado = pd.DataFrame(PedidosEstadoEtiquetado.objects.all().values('n_pedido','estado__estado','fecha_creado'))
    estado = estado.rename(columns={'n_pedido':'CONTRATO_ID','estado__estado':'estado'})
    estado['fecha_creado'] = estado['fecha_creado'].astype(str)

    reservas = reservas[reservas['SEC_NAME_CLIENTE']=='PUBLICO']
    
    if not nuevos_pedidos.empty:
        reservas = pd.concat([reservas, nuevos_pedidos])
    
    reservas = reservas.rename(columns={'PRODUCT_ID':'product_id'})
    reservas = reservas.merge(pro, on='product_id', how='left')
    reservas['FECHA_PEDIDO'] = reservas['FECHA_PEDIDO'].astype(str)

    list_reservas = reservas.drop_duplicates(subset=['CONTRATO_ID'])

    reservas['cartones'] = (reservas['QUANTITY'] / reservas['Unidad_Empaque']).round(2)
    reservas = reservas.fillna(0).replace(np.inf, 0)
    reservas['t_1p'] = (reservas['cartones'] * reservas['t_etiq_1p']).round(0)
    reservas['t_2p'] = (reservas['cartones'] * reservas['t_etiq_2p']).round(0)
    reservas['t_3p'] = (reservas['cartones'] * reservas['t_etiq_3p']).round(0)
    
    reservas['FECHA_PEDIDO'] = reservas['FECHA_PEDIDO'].astype('str')
    
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
    
    data = reservas
    data['FECHA_PEDIDO'] = data['FECHA_PEDIDO'].astype('str')
    data['HORA_LLEGADA'] = data['HORA_LLEGADA'].astype('str')
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
    #fecha_entrega = fecha_entrega.rename(columns={'pedido':'CONTRATO_ID', 'estado':'estado_entrega'})
    fecha_entrega = fecha_entrega.rename(columns={'pedido':'CONTRATO_ID', 'estado':'estado_entrega', 'fecha_hora':'fecha_entrega'})
    
    list_reservas = list_reservas.merge(fecha_entrega, on='CONTRATO_ID', how='left') #;print(list_reservas)

    try:
        hoy = datetime.now() #;print(hoy)
        #list_reservas['dias_faltantes'] = (list_reservas['fecha_hora'] - hoy).dt.days  
        list_reservas['dias_faltantes'] = (list_reservas['fecha_entrega'] - hoy).dt.days  
        list_reservas['dias_faltantes'] = list_reservas['dias_faltantes'].astype('int')
    except:
        pass
    
    hoy_2 = date.today()
    
    #list_reservas['fecha_entrega'] = list_reservas['fecha_hora'].dt.date  #;print(list_reservas['fecha_entrega'])

    try:
        if len(list_reservas) > 0:
            list_reservas['dias_faltantes'] = (list_reservas['fecha_entrega'] - hoy_2).dt.days
    except:
        pass

    #list_reservas = list_reservas.sort_values(by=['fecha_hora'])
    list_reservas = list_reservas.sort_values(by=['fecha_entrega'])
    
    #list_reservas['fecha_hora'] = list_reservas['fecha_hora'].astype(str)
    list_reservas['fecha_entrega'] = list_reservas['fecha_entrega'].astype('str')
    
    list_reservas = list_reservas.replace('NaT','-')
    list_reservas = list_reservas.fillna('-')  #;print(type(list_reservas['dias_faltantes'][1])) ;print(list_reservas)
    
    #list_reservas['fh'] = pd.to_datetime(list_reservas['fecha_hora'], errors='coerce')
    list_reservas['fh'] = pd.to_datetime(list_reservas['fecha_entrega'], errors='coerce')
    
    list_reservas['dia'] = list_reservas['fh'].dt.day_name(locale='es_EC.utf-8')
    list_reservas['dia_numero'] = list_reservas['fh'].dt.day
    list_reservas['dia_numero'] = list_reservas['dia_numero'].astype('str')
    try:
        list_reservas['dia'] = list_reservas['dia'].str.replace('Miã©rcoles','Miércoles')
    except:
        pass
    list_reservas['mes'] = list_reservas['fh'].dt.month_name(locale='es_EC.utf-8')
    list_reservas = list_reservas.merge(avance_df, on='CONTRATO_ID', how='left')
    
    # Clientes
    cli = clientes_table()[['CODIGO_CLIENTE','CIUDAD_PRINCIPAL']]    
    if not list_reservas.empty:
        list_reservas = list_reservas.merge(cli, on='CODIGO_CLIENTE', how='left')
    
    # Estados
    lista_de_reservas_estado = list_reservas['CONTRATO_ID'].unique()
    estados = pd.DataFrame(EstadoPicking.objects.filter(n_pedido__in=lista_de_reservas_estado).values('n_pedido','estado'))
    estados = estados.rename(columns={'n_pedido':'CONTRATO_ID','estado':'estado_picking_x'})
    if not estados.empty:
        list_reservas = list_reservas.merge(estados, on='CONTRATO_ID', how='left')
    
    return list_reservas


def pedidos_temporales_fun():
    
    try:
        pedidos = PedidoTemporal.objects.filter(estado='PENDIENTE')
        clientes_df = clientes_warehouse()[['NOMBRE_CLIENTE', 'CIUDAD_PRINCIPAL']]
        
        if pedidos.exists():
            # return pd.DataFrame()
            data = []
            for i in pedidos:
                pedidos_data = calculos_pedido(i.productos.values())
                data.append({
                    'id_pedido_temporal':str(i.id),
                    'CONTRATO_ID': i.enum,
                    'NOMBRE_CLIENTE': i.cliente,
                    'fecha_entrega': i.entrega,
                    't_1p_str': pedidos_data['tt_str_1p'],
                    't_2p_str': pedidos_data['tt_str_2p'],
                    't_3p_str': pedidos_data['tt_str_3p'],
                    'fecha_hora':i.creado,
                    'TIEMPOS':pedidos_data['TIEMPOS'],
                })
            
            df = pd.DataFrame(data)
            df['TIPO_PEDIDO'] = 'TEMPORAL'
            df['dias_faltantes'] = (df['fecha_entrega'] - datetime.now()).dt.days
            df['dia'] = df['fecha_entrega'].dt.day_name(locale='es_EC.utf-8')
            df['dia_numero'] = df['fecha_entrega'].dt.day
            df['dia_numero'] = df['dia_numero'].astype('str')
            df['mes'] = df['fecha_entrega'].dt.month_name(locale='es_EC.utf-8')
            #df['fecha_hora'] = df['fecha_entrega'].astype('str')
            df['fecha_entrega'] = df['fecha_entrega'].astype('str')
            df['avance'] = None
            df['FECHA_PEDIDO'] = df['fecha_hora'].dt.date
            
            if not df.empty:
                df = df.merge(clientes_df, on='NOMBRE_CLIENTE', how='left') 
                return df
        else:
            return pd.DataFrame()
    except:
        return pd.DataFrame()


def publico_dashboard(request):

    pedidos_temporales = pedidos_temporales_fun().dropna(axis=1, how='all')
    list_reservas = publico_dashboard_fun()

    pub = list_reservas[list_reservas['estado']!='FINALIZADO']
    contratos = list(pub['CONTRATO_ID'].unique())
    sto = stock_faltante_contrato(contratos, 'BCT')
    
    if not sto.empty:
        pub = pub.merge(sto, on='CONTRATO_ID', how='left')

    fin = list_reservas[list_reservas['estado']=='FINALIZADO']
    
    if not pub.empty and not pedidos_temporales.empty:
        pub = pd.concat([pub, pedidos_temporales], ignore_index=True).sort_values('fecha_entrega') 
    else:
        pub = pub
    
    pub = de_dataframe_a_template(pub)
    fin = de_dataframe_a_template(fin)

    context = {
        'list_reservas':pub,
        'fin':fin,
        'n_pedidos':len(pub),
        'por_facturar':len(fin)
    }

    return render(request, 'dashboards/etiquetado_publico.html', context)


def dashboard_completo(request):

    # PEDIDOS CEREZOS
    pedidos_cerezos = estado_pedidos_dashboard_fun('BCT')
    contratos_pedidos = list(pedidos_cerezos['CONTRATO_ID'].unique())
    sto_pedidos = stock_faltante_contrato(contratos_pedidos, 'BCT')
    
    if not sto_pedidos.empty:
        pedidos_cerezos = pedidos_cerezos.merge(sto_pedidos, on='CONTRATO_ID', how='left')

    # Filtrado por fecha
    hoy = date.today()
    ayer = hoy - timedelta(days=1)
    meses_2 = hoy - timedelta(days=30)

    pedidos_cerezos = pedidos_cerezos[pedidos_cerezos['FECHA_PEDIDO']>meses_2]

    pedidos_cerezos_hoy = len(pedidos_cerezos[pedidos_cerezos['FECHA_PEDIDO']==hoy])
    pedidos_cerezos_ayer = len(pedidos_cerezos[pedidos_cerezos['FECHA_PEDIDO']==ayer])
    pedidos_cerezos_mas3 = len(pedidos_cerezos[pedidos_cerezos['FECHA_PEDIDO']<ayer])

    if len(pedidos_cerezos) > 0:
        pedidos_cerezos['fecha_estado'] = pedidos_cerezos.apply(lambda x: 'hoy' if x['FECHA_PEDIDO']==hoy else 'ayer' if x['FECHA_PEDIDO']==ayer else 'mas3' if x['FECHA_PEDIDO']<ayer else 'mas3', axis=1)

    pedidos_cerezos['FECHA_PEDIDO'] = pedidos_cerezos['FECHA_PEDIDO'].astype(str)
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

    return render(request, 'dashboards/dashboard_completo.html', context)


def dashboard_completo_json_response(request):
    
    # PEDIDOS CEREZOS
    pedidos_cerezos = estado_pedidos_dashboard_fun('BCT')
    contratos_pedidos = list(pedidos_cerezos['CONTRATO_ID'].unique())
    sto_pedidos = stock_faltante_contrato(contratos_pedidos, 'BCT')
    
    if not sto_pedidos.empty:
        pedidos_cerezos = pedidos_cerezos.merge(sto_pedidos, on='CONTRATO_ID', how='left')

    # Filtrado por fecha
    hoy = date.today()
    ayer = hoy - timedelta(days=1)
    meses_2 = hoy - timedelta(days=30)

    pedidos_cerezos = pedidos_cerezos[pedidos_cerezos['FECHA_PEDIDO']>meses_2]

    pedidos_cerezos_hoy = len(pedidos_cerezos[pedidos_cerezos['FECHA_PEDIDO']==hoy])
    pedidos_cerezos_ayer = len(pedidos_cerezos[pedidos_cerezos['FECHA_PEDIDO']==ayer])
    pedidos_cerezos_mas3 = len(pedidos_cerezos[pedidos_cerezos['FECHA_PEDIDO']<ayer])

    if len(pedidos_cerezos) > 0:
        pedidos_cerezos['fecha_estado'] = pedidos_cerezos.apply(lambda x: 'hoy' if x['FECHA_PEDIDO']==hoy else 'ayer' if x['FECHA_PEDIDO']==ayer else 'mas3' if x['FECHA_PEDIDO']<ayer else 'mas3', axis=1)

    pedidos_cerezos['FECHA_PEDIDO'] = pedidos_cerezos['FECHA_PEDIDO'].astype(str)
    pedidos_cerezos = de_dataframe_a_template(pedidos_cerezos)

    # ETIQUETADO STOCK
    etiquetado = etiquetado_fun() 
    urgente = 0.75
    correcto = 2
    n_urgente = len(etiquetado[etiquetado['Meses']<urgente])
    amarillo = etiquetado[etiquetado['Meses']>=urgente]
    amarillo = amarillo[amarillo['Meses']<correcto]
    n_pronto = len(amarillo)

    etiquetado = de_dataframe_a_template(etiquetado)

    # ETIQUETADO PUBLICO
    publico = publico_dashboard_fun()
    publico = publico[publico['estado']!='FINALIZADO']
    contratos_publicos = list(publico['CONTRATO_ID'].unique())
    sto_publico = stock_faltante_contrato(contratos_publicos, 'BCT') 
    
    if not sto_publico.empty:
        publico = publico.merge(sto_publico, on='CONTRATO_ID', how='left')
    
    pedidos_temporales = pedidos_temporales_fun().dropna(axis=1, how='all')
    
    if not publico.empty and not pedidos_temporales.empty:
        publico = pd.concat([publico, pedidos_temporales])
        publico['fecha_entrega'] = publico['fecha_entrega'].astype('str')
        publico = publico.sort_values(by='fecha_entrega')
    else:
        publico = publico       
    
    publicos_n = len(publico)
    publico = de_dataframe_a_template(publico)
    
    context = {
        # CONFIG
        'urgente':urgente,
        'correcto':correcto,
        
        # PEDIDOS CEREZOS
        'pedidos_cerezos':pedidos_cerezos,
        'pedidos_cerezos_hoy':pedidos_cerezos_hoy,
        'pedidos_cerezos_ayer':pedidos_cerezos_ayer,
        'pedidos_cerezos_mas3':pedidos_cerezos_mas3,

        # ETIQUETADO STOCK
        'etiquetado':etiquetado,
        'n_urgente':n_urgente,
        'n_pronto':n_pronto,

        # PUBLICO
        'publico':publico,
        'n_publico':publicos_n
    }
    
    return JsonResponse(context)


def dashboard_completo_view(request):
    return render(request, 'dashboards/dashboard_completo_vue.html')


def detalle_dashboard_armados(request):
    
    prod = request.POST['prod']
    ventas = ventas_armados_facturas_odbc(prod)
    cli = clientes_warehouse()[['CODIGO_CLIENTE','NOMBRE_CLIENTE']]

    ventas = ventas.merge(cli, on='CODIGO_CLIENTE', how='left')
    ventas = ventas.rename(columns={
        'QUANTITY':'VENTAS',
        'NOMBRE_CLIENTE':'CLIENTE'
    })
    ventas['VENTAS'] = ventas['VENTAS'].astype('int')

    # Dataframe to complete the dates
    un_anio = datetime.now() - timedelta(days=375)
    periodo_gim = pd.date_range(start=datetime.now(), end=un_anio, periods=12)
    df = pd.DataFrame()
    df.index = periodo_gim
    df['FECHA'] = periodo_gim
    df['CLIENTE'] = 'GIM'
    df['CODIGO_CLIENTE'] = 'GIM0001'
    df['VENTAS'] = 0
    df = df.sort_values(by='FECHA')
    
    ventas = pd.concat([ventas, df]).sort_values(by='FECHA')
    
    ventas['PERIODO'] = ventas['FECHA'].dt.to_period('M')
    
    ventas = ventas.pivot_table(
        index=['CLIENTE'], 
        values=['VENTAS'], 
        columns=['PERIODO'], 
        aggfunc='sum',
        margins=True, 
        margins_name='TOTAL', 
        sort=False
    )
        
    ventas = ventas.sort_values(by=('VENTAS','TOTAL'), ascending=False).fillna('-').replace(0,'-')
    
    ventas = ventas.to_html(
        classes='table table-responsive table-bordered m-0 p-0', 
        float_format='{:.0f}'.format,
        )
    
    return HttpResponse(ventas)


@login_required(login_url='login')
def dashboard_armados(request):
    
    productos = productos_odbc_and_django()[['product_id', 'Nombre', 'Marca', 'Unidad_Empaque', 't_armado']]

    productos_armados = pd.DataFrame(ProductArmado.objects.filter(activo=True).values(
        'producto__product_id',
        # 'producto__description',
        # 'producto__marca',
        ))
    productos_armados = productos_armados.rename(columns={'producto__product_id':'product_id'})
    productos_armados = productos_armados.merge(productos, on='product_id', how='left') #;print(productos)
    productos_armados = productos_armados.rename(columns={'product_id':'PRODUCT_ID'})
    #print(productos_armados)
    
    
    ventas = frecuancia_ventas() #; print(ventas)
    stock = stock_lote_odbc()[['PRODUCT_ID', 'OH2']] #; print(stock)#[['PRODUCT_ID', 'EGRESO_TEMP', 'DISP-MENOS-RESERVA', 'OH2']] 
    # stock = stock.pivot_table(index='PRODUCT_ID', values=['OH2','DISP-MENOS-RESERVA','EGRESO_TEMP'], aggfunc='sum')
    stock = stock.pivot_table(index='PRODUCT_ID', values=['OH2'], aggfunc='sum')

    # #reservas = pd.DataFrame(reservas_table())[['PRODUCT_ID','QUANTITY']]
    # #reservas = reservas.rename(columns={'QUANTITY':'EGRESO_TEMP'})
    # #reservas = reservas.pivot_table(index='PRODUCT_ID', values=['EGRESO_TEMP'], aggfunc='sum').reset_index()
    
    # #stock = stock.merge(reservas, on='PRODUCT_ID', how='left').fillna(0)

    reservas_sin_lote = pd.DataFrame(reservas_table())
    reservas_sin_lote = reservas_sin_lote.pivot_table(index=['PRODUCT_ID'], values=['QUANTITY'], aggfunc='sum').reset_index()
    # reservas_sin_lote = reservas_sin_lote.rename(columns={'QUANTITY':'RESERVAS-SIN-LOTE'})
    reservas_sin_lote = reservas_sin_lote.rename(columns={'QUANTITY':'EGRESO_TEMP'})


    # armados = productos.merge(ventas, on='PRODUCT_ID', how='left').fillna(0)
    armados = productos_armados.merge(ventas, on='PRODUCT_ID', how='left').fillna(0)
    armados = armados.merge(stock, on='PRODUCT_ID', how='left').fillna(0)
    armados = armados.merge(reservas_sin_lote, on='PRODUCT_ID', how='left').fillna(0)

    # # armados['RESERVAS'] = armados.apply(lambda x: x['EGRESO_TEMP'] if x['EGRESO_TEMP']==x['RESERVAS-SIN-LOTE'] else x['RESERVAS-SIN-LOTE'], axis=1)
    
    ### PRODUCTOS EN TRANSITO
    transito = productos_transito_odbc()
    if not transito.empty:
        transito = transito.pivot_table(index=['PRODUCT_ID'], values=['OH'], aggfunc='sum').reset_index()
        armados = armados.merge(transito, on='PRODUCT_ID', how='left').fillna(0)
        armados['OH2'] = armados['OH2'] + armados['OH']

    armados['mensual'] = (armados['ANUAL'] / 12).round(0)
    # armados['dip-meno-res-2'] = (armados['OH2'] - armados['RESERVAS']).round(0)
    armados['dip-meno-res-2'] = (armados['OH2'] - armados['EGRESO_TEMP']).round(0)
    
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
        # 'Nombre':'PRODUCT_NAME',
        # 'Marca':'GROUP_CODE'
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
    
    armados = armados.sort_values(by=['meses','mensual','Nombre'], ascending=[True, True, False])
    armados = armados[armados['Marca']!=0]
    
    # Solicitudes de armado
    solicitudes = OrdenEmpaque.objects.exclude(estado='Finalizado').count()
    
    # armados = armados.merge(productos, on='PRODUCT_ID', how='left') ;print(armados)
    armados = de_dataframe_a_template(armados)

    context = {
        'armados':armados,
        'urgente':len(urgente),
        'pronto' :len(pronto),
        'actualizado':ultima_actualizacion('actulization_stoklote'),
        'solicitudes':solicitudes
    }
    
    return render(request, 'dashboards/dashboard_armados.html', context)



def reporte_revision_reservas(request):

    from datos.views import revision_reservas_fun
    
    reporte = revision_reservas_fun()

    # Excel
    if not reporte.empty:
        hoy = datetime.today().strftime('%Y-%m-%d_%H-%M-%S')
        nombre_archivo = f'Reporte-Reservas_{hoy}.xlsx'
        content_disposition = f'attachment; filename="{nombre_archivo}"'

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = content_disposition

        with pd.ExcelWriter(response, engine='openpyxl') as writer:
            
            reporte.to_excel(writer, sheet_name='Reporte-Reservas', index=False)
            
            workbook = writer.book
            worksheet = writer.sheets['Reporte-Reservas']
            
            worksheet.column_dimensions['A'].width = 30 # CONTRATO
            worksheet.column_dimensions['B'].width = 16 # PRODUCT_ID
            worksheet.column_dimensions['C'].width = 20 # LOTE_RESERVAS
            worksheet.column_dimensions['D'].width = 20 # FECHA_RESERVA
            worksheet.column_dimensions['E'].width = 20 # RESERVA_RESERVADO
            worksheet.column_dimensions['F'].width = 20 # BODEGA_RESERVA
            worksheet.column_dimensions['G'].width = 23 # LOTE_DISPONIBLE
            worksheet.column_dimensions['H'].width = 23 # FECHA_DISPONIBLE
            worksheet.column_dimensions['I'].width = 23 # BODEGA_DISPONIBLE
            worksheet.column_dimensions['J'].width = 23 # EXISTENCIA_DISPONIBLE
            worksheet.column_dimensions['K'].width = 23 # RESERVA_DISPONIBLE_ACTUAL
            worksheet.column_dimensions['L'].width = 23 # RESERVA_DISPONIBLE_NUEVA
            worksheet.column_dimensions['M'].width = 23 # DISPONIBLE_DISPONIBLE
            worksheet.column_dimensions['N'].width = 50 # OBSERVACIONES
            
        return response

    else:
        messages.success(request, 'Reservas actualizadas, no hay items que mover !!!')
        return HttpResponseRedirect('/etiquetado/revision/imp/llegadas/list')


##### MERMAID CHART JS HTML DRAWS 
def mermaid_chart(request):
    return render(request, 'etiquetado/revision_reservas/mermaid.html')


## CONTROL DE GUIAS Y COUIER
login_required(login_url='login')
def control_guias_list(request):
    
    ventas_fac = ventas_facturas_odbc()[['NOMBRE_CLIENTE', 'CODIGO_FACTURA', 'FECHA_FACTURA']]
    clientes = clientes_warehouse()[['NOMBRE_CLIENTE','CIUDAD_PRINCIPAL', 'CLIENT_TYPE']]
    
    # Ventas factura
    ventas_fac = ventas_fac.drop_duplicates(subset=['CODIGO_FACTURA'])
    ventas_fac['FECHA'] = pd.to_datetime(ventas_fac['FECHA_FACTURA'])
    ventas_fac = ventas_fac.sort_values(by=['FECHA'], ascending=[False])    
    ventas_fac = ventas_fac.merge(clientes, on='NOMBRE_CLIENTE', how='left')
    ventas_fac['FECHA'] = ventas_fac['FECHA'].astype(str)
    
    # Solca
    solca_quito = ventas_fac[ventas_fac['NOMBRE_CLIENTE']=='SOLCA QUITO']   
    
    # Filtros
    ventas_fac = ventas_fac[ventas_fac['CIUDAD_PRINCIPAL']!='QUITO']
    ventas_fac = ventas_fac[ventas_fac['CIUDAD_PRINCIPAL']!='SANGOLQUI']
    
    # Concat
    ventas_fac = pd.concat([ventas_fac, solca_quito], ignore_index=True)    
    
    # Guias Registradas
    reg_guia = pd.DataFrame(RegistoGuia.objects.all().values(
        'id',
        'factura',
        'factura_c', 
        'user__user__first_name',
        'user__user__last_name',
        'transporte'
        ))    
    reg_guia['user_reg'] = reg_guia['user__user__first_name'] + ' ' + reg_guia['user__user__last_name']
    reg_guia = reg_guia.rename(columns={'factura_c':'CODIGO_FACTURA'})
    
    # Merge
    ventas_fac = ventas_fac.merge(reg_guia, on='CODIGO_FACTURA', how='left')#.fillna(0)
    ventas_fac['id'] = ventas_fac['id'].fillna(0).astype('int')
    ventas_fac = ventas_fac.sort_values(by=['CODIGO_FACTURA'], ascending=False).fillna('Sin Registrar')
    
    # Anexos
    anexos = AnexoGuia.objects.all()
    anexo_num = []
    anexo_factura = []
    
    for i in anexos:
        for j in i.contenido.all():
            anexo_num.append(i.numero_anexo)
            anexo_factura.append(j.contenido)
    
    if anexos.exists():
        anexos_df = pd.DataFrame({
            'anexo_num':anexo_num,
            'factura':anexo_factura
        })
        ventas_fac = ventas_fac.merge(anexos_df, on='factura', how='left').fillna('-')
    
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

    try:
        fac_slice = int(fac['CODIGO_FACTURA'].split('-')[1][4:])
        fac['fac_slice'] = str(fac_slice)
    except:
        fac['fac_slice'] = fac['CODIGO_FACTURA']


    if request.method == 'POST':
        form = RegistroGuiaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/etiquetado/guias/list')
        else:
            messages.error(request, f'Error {form.errors}')
            return redirect('/etiquetado/guias/list')

    context = {
        'fac':fac
    }

    return render(request, 'guias/facturas_registro.html', context)


login_required(login_url='login')
def control_guias_editar(request, id):

    reg = RegistoGuia.objects.get(id=id)

    if request.method == 'POST':
        form = RegistroGuiaForm(request.POST, instance=reg)
        if form.is_valid():
            form.save()
            return redirect('/etiquetado/guias/list')
        else:
            messages.error(request, f'Error {form.errors}')
            return redirect('/etiquetado/guias/list')

    context = {
        'fac':reg
    }

    return render(request, 'guias/editar.html', context)

@login_required(login_url='login')
def anexos_lista(request):
    
    anexos = AnexoGuia.objects.all()
    form   = AnexoGuiaForm()
    
    facturas_registradas = list(RegistoGuia.objects.values_list('factura', flat=True))
    facturas_warehouse = ventas_facturas_odbc()['CODIGO_FACTURA'].unique()
    facturas_warehouse = list(map(lambda x: str(int(x.split('-')[1][4:])), facturas_warehouse))
    facturas_list = set(facturas_registradas + facturas_warehouse)
    
    if request.method == 'POST':
        form = dict(request.POST)
        if form: 
            
            f_bodega_nombre = form.get('bodega_nombre')[0]
            f_bodega_codigo = '01' if f_bodega_nombre == 'Andagoya' else '02'
            f_user          = form.get('user')[0]
            f_facturas_list = form.get('facturas')
            
            # Guardar Anexo
            anexo = AnexoGuia(
                bodega_nombre = f_bodega_nombre,
                bodega_codigo = f_bodega_codigo,
                user_id       = int(f_user),
            )
            
            anexo.save()
            
            if anexo.id:
            
                for i in f_facturas_list:
                    guia = RegistoGuia.objects.filter(factura=i)
                    
                    if guia.exists():
                        anexo_doc = AnexoDoc(
                            transporte     = guia.first().transporte,
                            n_guia         = guia.first().n_guia,
                            tipo_contenido = 'Factura' if guia.first().factura_c.startswith('FCSRI-') else '',
                            contenido      = i
                        )
                        anexo_doc.save()
                        
                    elif not guia.exists():
                        anexo_doc = AnexoDoc(
                            contenido = i
                        )
                        
                        anexo_doc.save()
                        
                    anexo.contenido.add(anexo_doc)
                    
                    if all(doc.n_guia for doc in anexo.contenido.all()):
                        anexo.estado = 'Completo'
                        anexo.save()
                    else:
                        anexo.estado = 'Incompleto'
                        anexo.save()
                    
                messages.success(request, 'Anexo agregado exitosamente')
            
        else:
            messages.error(request, f'Error intente nuevamente')
            return redirect('anexos_lista')
    
    context = {
        'anexos':anexos,
        'form':form,
        'facturas_list':facturas_list
    }
    return render(request, 'guias/anexos_lista.html', context)


@login_required(login_url='login')
def anexo_detalle(request, id_anexo):
    
    anexo = AnexoGuia.objects.get(id=id_anexo)
    context = {
        'anexo':anexo,
    }
    
    return render(request, 'guias/anexo_ver.html', context)

#from django_xhtml2pdf.utils import pdf_decorator
@login_required(login_url='login')
@pdf_decorator(pdfname='anexo.pdf')
def anexo_detalle_pdf(request, id_anexo):
    
    anexo = AnexoGuia.objects.get(id=id_anexo)
    context = {
        'anexo':anexo,
    }
    
    return render(request, 'guias/anexo_pdf.html', context)


def anexo_doc_editar_ajax(request):
    if request.method == 'GET':
        id_anexo_fila = request.GET.get('id_anexo_fila')
        if id_anexo_fila:
            anexo_doc = AnexoDoc.objects.get(id=int(id_anexo_fila))
            form = AnexoDocForm(instance=anexo_doc)
            return HttpResponse(form.as_p())
        else:
            form  = AnexoDocForm()
            return HttpResponse(form.as_p())
    
    elif request.method == 'POST':
        id_anexo_fila = request.POST.get('id_anexo_fila') 
        id_anexo = request.POST.get('anexo')
        if id_anexo_fila != 'undefined':
            anexo_doc = AnexoDoc.objects.get(id=int(id_anexo_fila))
            form = AnexoDocForm(request.POST, instance=anexo_doc)
            if form.is_valid():
                form.save()
                
                anexo = AnexoGuia.objects.get(id=int(id_anexo))
                if all(doc.n_guia for doc in anexo.contenido.all()):
                        anexo.estado = 'Completo'
                        anexo.save()
                else:
                    anexo.estado = 'Incompleto'
                    anexo.save()
                
                messages.success(request, 'Fila editada exitosamente')
                return redirect(f'/etiquetado/anexo/{id_anexo}')
            else:
                messages.error(request, f'Error: {form.errors}')
                return redirect(f'/etiquetado/anexo/{id_anexo}')
        
        else:
            anexo = AnexoGuia.objects.get(id=int(id_anexo))
            form = AnexoDocForm(request.POST)
            if form.is_valid():
                form = form.save()
                anexo.contenido.add(form)
                
                if all(doc.n_guia for doc in anexo.contenido.all()):
                        anexo.estado = 'Completo'
                        anexo.save()
                else:
                    anexo.estado = 'Incompleto'
                    anexo.save()
                        
                messages.success(request, 'Fila agregada exitosamente')
                return redirect(f'/etiquetado/anexo/{id_anexo}')
            else:
                messages.error(request, f'Error: {form.errors}')
                return redirect(f'/etiquetado/anexo/{id_anexo}')


def anexo_doc_actualizar_contenido_ajax(request):
    
    if request.method == 'POST':
        
        id_anexo_doc = request.POST.get('id_anexo_doc')
        id_anexo = request.POST.get('id_anexo')
        
        anexo_doc = AnexoDoc.objects.get(id=int(id_anexo_doc))        
        registro_guia = RegistoGuia.objects.filter(factura=anexo_doc.contenido)
        
        if registro_guia.exists():
    
            rg = registro_guia.first()
            anexo_doc.transporte = rg.transporte
            anexo_doc.n_guia = rg.n_guia
            anexo_doc.tipo_contenido = 'Factura' if rg.factura_c.startswith('FCSRI') else ''
            anexo_doc.save()
            
            anexo = AnexoGuia.objects.get(id=int(id_anexo))
            if all(doc.n_guia for doc in anexo.contenido.all()):
                anexo.estado = 'Completo'
                anexo.save()
            else:
                anexo.estado = 'Incompleto'
                anexo.save()
            
            return JsonResponse({
                'tipo':'success',
                'msg':'Registro actualizado correctamente !!!'
                })
            
        else:
            return JsonResponse({
                'tipo':'danger',
                'msg':'Aún no hay registro de anexo creado !!!'
                })


def anexo_doc_elimiar_ajax(request):
    if request.method == 'POST':
        id_anexo_fila = request.POST.get('id_anexo_fila')
        anexo_doc = AnexoDoc.objects.get(id=int(id_anexo_fila))
        anexo_doc.delete()
        return JsonResponse({'msg':'Elimado exitosamente'})



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


@login_required(login_url='login')
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
    
    update = api_actualizar_facturas_warehouse()
    
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
@login_required(login_url='login')
def listado_proformas(request):
    
    proformas = lista_proformas_odbc()
    proformas = proformas.drop_duplicates(subset=['contrato_id'])
    #proformas['fecha_pedido'] = pd.to_datetime(proformas['fecha_pedido']).dt.strftime("%Y-%m-%d")
    proformas['fecha_pedido'] = proformas['fecha_pedido'].astype('str')
    proformas = proformas.sort_values(by='fecha_pedido', ascending=False)
    proformas = de_dataframe_a_template(proformas)
    
    context = {
        'proformas':proformas
    }

    return render(request, 'etiquetado/proformas/listado.html', context)


# Detalle de proforma
@login_required(login_url='login')
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



from .transferencia_data import sugerencia, andagoya_saldos, pedidos_reservas

def analisis_transferencia(request):
    
    saldos_ban = andagoya_saldos()
    sugerencia_ban = sugerencia()
    
    context = {
        'saldos_ban': de_dataframe_a_template(saldos_ban),
        'sugerencia_ban': de_dataframe_a_template(sugerencia_ban)
    }
    
    
    return render(request, 'etiquetado/analisis_transferencia/analisis_transferencia.html', context)


def pedidos_reservas_request(request):
    
    if request.method == 'POST':
        
        data = pedidos_reservas(request.POST.get('prod_id')) 
        if not data.empty:
            data = de_dataframe_a_template(data)
            return JsonResponse({'data':data})
        
        else:
            return JsonResponse({'error':'No hay datos'})
    

def existencias_wms_analisis_transferencia(request):
    
    if request.method == 'POST':
        existencias = (
            Existencias.objects
            .filter(product_id=request.POST.get('prod_id'))
            .order_by(
                '-estado',
                'product_id',
                'fecha_caducidad',
                'lote_id',
                'ubicacion__bodega',
                'ubicacion__nivel'
                )
        )
        
        if existencias.exists():
            # convertir queryset django a json
            existencias = existencias.values(
                'product_id',
                'lote_id',
                'fecha_caducidad',
                'ubicacion__bodega',
                'ubicacion__pasillo',
                'ubicacion__modulo',
                'ubicacion__nivel',
                'estado',
                'unidades'
                )
            existencias = list(existencias)
            
            return JsonResponse({
                'data':existencias,
                'error':False
            })
            
        else:
            return JsonResponse({'error':'No hay datos'})



# def update_andagoya_ubis():
#     excel = pd.read_excel('C:\Erik\Egares Gimpromed\Desktop\ReposiciónAndagoya/datos_actuales/UBI-ANDAGOYA.xlsx')#.fillna(0)
#     excel['codigo'] = excel['codigo'].astype('str')
#     excel = excel.sort_values(by='codigo')
#     #excel['estanteria'] = excel.apply(lambda x: True if x['estanteria'] == 11 else False, axis=1)
#     #print(excel)
    
#     for index, row in excel.iterrows():
#         codigo = row['codigo']
#         ubicacion = row['ubicación'].split('-')
        
#         if len(ubicacion) == 2:
#             ubi = UbicacionAndagoya.objects.filter(
#                 Q (bodega=ubicacion[0]) &
#                 Q (pasillo=ubicacion[1]) &
#                 Q (modulo='') &
#                 Q (nivel='') 
#             )
            
#         elif len(ubicacion) == 4:
#             ubi = UbicacionAndagoya.objects.filter(
#                 Q (bodega=ubicacion[0]) &
#                 Q (pasillo=ubicacion[1]) &
#                 Q (modulo=ubicacion[2]) &
#                 Q (nivel=ubicacion[3]) 
#             )
        
#         prod_id = ProductoUbicacion.objects.get(product_id=codigo)
#         prod_id.ubicaciones.add(ubi.first())



# UbicacionAndagoya
# ProductoUbicacion
@login_required(login_url='login')
def ubicaciones_andagoya_list(request):
    #update_andagoya_ubis()
    ubicaciones = UbicacionAndagoya.objects.all().order_by('bodega','pasillo','modulo','nivel')
    form = UbicacionAndagoyaForm()
    
    if request.method == 'POST':
        form = UbicacionAndagoyaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('ubicaciones_andagoya_list')
        else:
            messages.error(request, f'Error: {form.errors}')
            return redirect('ubicaciones_andagoya_list')
    
    context = {
        'ubicaciones':ubicaciones,
        'form': form,
    }
    
    return render(request, 'etiquetado/ubicaciones_andagoya/ubicaciones_list.html', context)



def editar_ubicacion_andagoya(request):
    
    if request.method == 'GET':
        id = request.GET.get('id')
        ubicacion = UbicacionAndagoya.objects.get(id=id)
        form = UbicacionAndagoyaForm(instance=ubicacion).as_div()
        
        return JsonResponse({
            'form': form,
            'ubi_id':ubicacion.id
        })

    if request.method == 'POST':
        id = request.POST.get('ubi_id')
        ubicacion = UbicacionAndagoya.objects.get(id=id)  # Ensure `ubicacion` is retrieved here
        form = UbicacionAndagoyaForm(request.POST, instance=ubicacion)
        if form.is_valid():
            form.save()
            return redirect('ubicaciones_andagoya_list')
        else:
            messages.error(request, f'Error: {form.errors}')
            return redirect('ubicaciones_andagoya_list')


def productos_ubicacion_lista_template():
    productos_mba = productos_odbc_and_django()[['product_id', 'Nombre', 'Marca']]
    productos = ProductoUbicacion.objects.all()
    
    productos_df = pd.DataFrame(productos.values())
    if not productos_df.empty:
        productos_completo = productos_df.merge(productos_mba, on='product_id', how='left').sort_values(by=['Marca','product_id'], ascending=[True, True]).fillna('-')
        productos_completo = de_dataframe_a_template(productos_completo)   
        
        for i in productos_completo:
            product_id = i['product_id']        
            for j in productos:
                if j.product_id == product_id:
                    i['ubicaciones'] = list(j.ubicaciones.all().order_by('bodega','pasillo','modulo','nivel'))
                    
        return productos_completo
    else:
        return []


@login_required(login_url='login')
def producto_ubicacion_lista(request):
    
    productos_mba = productos_odbc_and_django()[['product_id', 'Nombre', 'Marca']]
    productos = ProductoUbicacion.objects.all()
    form = ProductoUbicacionForm()
    
    productos_completo = productos_ubicacion_lista_template()
    
    productos_form = set(productos.values_list('product_id', flat=True))
    productos_form_mba = set(productos_mba['product_id'].unique())
    productos_input = list(productos_form_mba.difference(productos_form))
    
    prods = productos_odbc_and_django()[['product_id', 'Nombre', 'Marca']]
    prods = prods[prods['product_id'].isin(productos_input)]
    prods = de_dataframe_a_template(prods)
    
    if request.method == 'POST':
        form = ProductoUbicacionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto y ubicacion guardado exitosamente')
            return redirect('producto_ubicacion_lista')
        else:
            messages.error(request, f'Error: {form.errors}')
            return redirect('producto_ubicacion_lista')
    
    context = {
        'prods': prods,
        'ubs':UbicacionAndagoya.objects.all(),
        'productos_completo': productos_completo,
        'form': form,
    }
    
    return render(request, 'etiquetado/ubicaciones_andagoya/producto_ubicacion_list.html', context)



def editar_producto_ubicacion(request):
    
    if request.method == 'GET':

        # Obtener el producto por ID
        producto_id = request.GET.get('id')
        producto = get_object_or_404(ProductoUbicacion, id=producto_id)

        todas_ubicaciones = UbicacionAndagoya.objects.values() 
        ubicaciones_seleccionadas = producto.ubicaciones.all().values()

        # Devolver todas las ubicaciones y las seleccionadas en formato JSON
        return JsonResponse({
            'todas_ubicaciones': list(todas_ubicaciones),
            'producto_ubicaciones': list(ubicaciones_seleccionadas),
        })
    
    if request.method == 'POST':
        
        prod = ProductoUbicacion.objects.get(product_id=request.POST.get('product_id')) 
        form = ProductoUbicacionForm(request.POST, instance=prod)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto y ubicacion actualizado exitosamente')
            return redirect('producto_ubicacion_lista')
        else:
            messages.error(request, f'Error: {form.errors}')
            return redirect('producto_ubicacion_lista')
        

def stock_lote_andagoya_ban_cua(): 
    
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(
        """
            SELECT * 
            FROM 
                warehouse.stock_lote 
            WHERE 
                WARE_CODE = 'BAN' OR WARE_CODE = 'CUA'
        """)
        columns = [col[0] for col in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        data = pd.DataFrame(data)
        data['LOTE_ID'] = data['LOTE_ID'].str.replace('.', '', regex=False)
        data = data.groupby(by=[
            'PRODUCT_ID',
            'PRODUCT_NAME',
            'GROUP_CODE',
            'LOTE_ID',
            'WARE_CODE',
            'Fecha_elaboracion_lote',
            'FECHA_CADUCIDAD'
        ])['OH2'].sum().reset_index()
        
        data['Fecha_elaboracion_lote'] = data['Fecha_elaboracion_lote'].astype('str')
        data['FECHA_CADUCIDAD'] = data['FECHA_CADUCIDAD'].astype('str')
        
    return data


@login_required(login_url='login')
def inventario_andagoya_ubicaciones(request):
    # Obtenemos la lista de ubicaciones
    stock = stock_lote_andagoya_ban_cua()
    stock = de_dataframe_a_template(stock)
    
    ubicaciones = productos_ubicacion_lista_template()
    
    for i in stock:
        for j in ubicaciones:
            if j['product_id'] == i['PRODUCT_ID']:
                i['ubicaciones'] = list(j['ubicaciones'])
    
    context = {
        'stock': stock,
    }
    
    return render(request, 'etiquetado/ubicaciones_andagoya/inventario_andagoya_ubicaciones.html', context)


@login_required(login_url='login')
def transferencias_ingreso_andagoya(request):
    
    desde = datetime.today() - timedelta(days=15)
    transferencias = Transferencia.objects.filter(
        fecha_hora__gte=desde,
        bodega_salida = 'BCT'
    ).order_by('-fecha_hora').values()
    
    transferencias = pd.DataFrame(transferencias).drop_duplicates(subset='n_transferencia')
    
    context = {
        'transferencias':de_dataframe_a_template(transferencias)
    } 
    
    return render(request, 'etiquetado/ubicaciones_andagoya/transferencias.html', context)


@login_required(login_url='login')
def transferencia_ingres_andagoya_detalle(request, n_transferencia):
    
    transferencia = Transferencia.objects.filter(n_transferencia=n_transferencia).values()
    transferencia = pd.DataFrame(transferencia)
    transferencia = transferencia.groupby(by=['product_id'])['unidades'].sum().reset_index()
    
    # transferencia['fecha_caducidad'] = transferencia['fecha_caducidad'].astype('str')
    productos = productos_odbc_and_django()[['product_id','Nombre','Marca','Unidad_Empaque']]
    transferencia = transferencia.merge(productos, on='product_id', how='left')
    transferencia['cartones'] = transferencia['unidades'] / transferencia['Unidad_Empaque']
    
    t_unidades = transferencia['unidades'].sum()
    t_cartones = transferencia['cartones'].sum()
    
    transferencia = de_dataframe_a_template(transferencia)
    
    ubicaciones = productos_ubicacion_lista_template()
    
    for i in transferencia:
        for j in ubicaciones:
            if j['product_id'] == i['product_id']:
                i['ubicaciones'] = list(j['ubicaciones'])
    
    context = {
        'n_transferencia':n_transferencia,
        't_unidades':t_unidades,
        't_cartones':t_cartones,
        'transferencia': transferencia
    }
    
    return render(request, 'etiquetado/ubicaciones_andagoya/transferencia_detalle.html', context)




# from .tasks import enviar_correos_prueba, prueba_sleep
# def mov_prueba(request):

#     result = enviar_correos_prueba.delay(email='egarces@gimpromed.com')
#     return HttpResponse(f'{request.user} - {result}')
# def sleep_prueba(request):
#     result = prueba_sleep.delay()
#     return HttpResponse(f'{request.user} - {result}')


@login_required(login_url='login')
def dashboards_powerbi(request):
    return render(request, 'etiquetado/powerbi/dashboard_uno.html')



### PEDIDOS TEMPORALES
@login_required(login_url='login')
def lista_pedidos_temporales(request):
    
    pedidos = PedidoTemporal.objects.all()
    # productos = productos_odbc_and_django()[['product_id','Nombre','Marca']]
    clientes = clientes_warehouse()[['NOMBRE_CLIENTE','IDENTIFICACION_FISCAL']]
    
    if request.method == 'POST':
        form = PedidoTemporalForm(request.POST)
        if form.is_valid():
            pedido = form.save()
            messages.success(request, 'Pedido guardado exitosamente')
            return redirect(reverse('pedido_temporal', kwargs={'pedido_id': pedido.id}))
        else:
            messages.error(request, form.errors)
    
    context = {
        'pedidos': pedidos,
        # 'productos': de_dataframe_a_template(productos),
        'clientes': de_dataframe_a_template(clientes),
    }
    
    return render(request, 'etiquetado/pedidos_temporales/lista_pedidos_temporales.html', context)



def calculos_pedido(productos_values):
    
    productos_df = productos_odbc_and_django()
    productos = pd.DataFrame(productos_values).rename(columns={'id':'id_product_temporal'})
    
    if not productos.empty:
    
        pedido = productos.merge(productos_df, on='product_id', how='left')
        pedido = pedido.rename(columns={
            'product_id':'PRODUCT_ID',
            'Nombre':'PRODUCT_NAME',
            'cantidad':'QUANTITY'})
        
        # Calculos
        pedido['Cartones'] = (pedido['QUANTITY'] / pedido['Unidad_Empaque']).round(2)
        #pedido = pedido.fillna(0.0).replace(np.inf, 0.0)
        
        pedido['t_una_p_min'] = (pedido['Cartones'] * pedido['t_etiq_1p']) / 60
        pedido['t_una_p_hor'] = pedido['t_una_p_min'] / 60
        pedido['t_dos_p_hor'] = ((pedido['Cartones'] * pedido['t_etiq_2p']) / 60) / 60
        pedido['t_tre_p_hor'] = ((pedido['Cartones'] * pedido['t_etiq_3p']) / 60) / 60
        pedido['vol_total'] = pedido['Cartones'] * (pedido['Volumen'] / 1000000)
        pedido['pes_total'] = pedido['Cartones'] * pedido['Peso']
        
        p_cero = 0 in list(pedido['pes_total']) 
        
        #pedido = pedido.fillna(0.0).replace(np.inf, 0.0) 

        # Mejor formato de tiempo
        pedido['t_s_1p']   = (pedido['Cartones'] * pedido['t_etiq_1p'].round(0))
        pedido['t_str_1p'] = [str(timedelta(seconds=int(i))) for i in pedido['t_s_1p']] 

        pedido['t_s_2p']   = (pedido['Cartones'] * pedido['t_etiq_2p']).round(0)
        pedido['t_str_2p'] = [str(timedelta(seconds=int(i))) for i in pedido['t_s_2p']]

        pedido['t_s_3p']   = (pedido['Cartones'] * pedido['t_etiq_3p'].round(0))
        pedido['t_str_3p'] = [str(timedelta(seconds=int(i))) for i in pedido['t_s_3p']]

        tt_str_1p = str(timedelta(seconds=int(pedido['t_s_1p'].sum())))
        tt_str_2p = str(timedelta(seconds=int(pedido['t_s_2p'].sum())))
        tt_str_3p = str(timedelta(seconds=int(pedido['t_s_3p'].sum())))
        
        cero_in_t1 = 0 in list(pedido['t_s_1p'])
        cero_in_t2 = 0 in list(pedido['t_s_2p'])
        cero_in_t3 = 0 in list(pedido['t_s_3p'])
        
        t_total_vol = pedido['vol_total'].sum()
        t_total_pes = pedido['pes_total'].sum()
        t_cartones = pedido['Cartones'].sum()
        t_unidades = pedido['QUANTITY'].sum()

        pedido = {
            'productos': de_dataframe_a_template(pedido)
            }
        
        if not cero_in_t2:
            pedido['TIEMPOS'] = 't2'
        elif cero_in_t2 and not cero_in_t1:
            pedido['TIEMPOS'] = 't1'
        elif cero_in_t1 and cero_in_t2 and not cero_in_t3:
            pedido['TIEMPOS'] = 't3'
        elif cero_in_t1 and cero_in_t2 and cero_in_t3:
            pedido['TIEMPOS'] = 'F'
        
        pedido['tt_str_1p'] = tt_str_1p
        pedido['tt_str_2p'] = tt_str_2p
        pedido['tt_str_3p'] = tt_str_3p
        
        pedido['t_total_vol'] = t_total_vol
        pedido['t_total_pes'] = t_total_pes
        pedido['t_cartones'] = t_cartones
        pedido['t_unidades'] = t_unidades
        
        pedido['p_cero'] = p_cero

        return pedido
    
    else:
        return {}


@login_required(login_url='login')
def pedido_temporal(request, pedido_id):
    
    vehiculo = Vehiculos.objects.filter(activo=True).order_by('transportista')
    pedido = PedidoTemporal.objects.get(id=pedido_id)
    productos = productos_odbc_and_django()[['product_id','Nombre','Marca']]
    clientes = clientes_warehouse()[['NOMBRE_CLIENTE','IDENTIFICACION_FISCAL']]
    
    if pedido.productos.exists():
        productos_pedido = calculos_pedido(pedido.productos.values())   
    else:
        productos_pedido = {'productos': []}
    
    if request.method == 'POST':
        form = ProductosPedidoTemporalForm(request.POST)
        if form.is_valid():
            producto = form.save()
            pedido.productos.add(producto)
            messages.success(request, 'Producto agregado al pedido exitosamente')
            return redirect(reverse('pedido_temporal', kwargs={'pedido_id': pedido.id}))
        else:
            messages.error(request, form.errors)

    context = {
        'vehiculos':vehiculo,
        'pedido':pedido,
        'productos': de_dataframe_a_template(productos),
        'clientes': de_dataframe_a_template(clientes),
        'productos_pedido': productos_pedido,
    }
    
    return render(request, 'etiquetado/pedidos_temporales/pedido_temporal.html', context)



def eliminar_producto_pedido_temporal(request):
    
    if request.method == 'POST':
        id_producto_temporal = request.POST.get('id_producto_temporal')
        
        try:
            producto_temporal = ProductosPedidoTemporal.objects.get(id=id_producto_temporal)
            producto_temporal.delete()
            return JsonResponse({'msg':'Producto eliminado exitosamente'})
        except:
            return JsonResponse({'msg':'Error al eliminar el producto'})


def editar_producto_pedido_temporal(request):

    if request.method == 'GET':
        producto_temporal = ProductosPedidoTemporal.objects.get(id=request.GET.get('id_producto_temporal'))
        return JsonResponse({
            'product_id':producto_temporal.product_id,
            'cantidad':producto_temporal.cantidad,
        })
    
    if request.method == 'POST':
        producto_temporal = ProductosPedidoTemporal.objects.get(id=request.POST.get('id_producto_temporal'))
        pedido = PedidoTemporal.objects.filter(productos__id=producto_temporal.id).first() 
        form = ProductosPedidoTemporalForm(request.POST, instance=producto_temporal)
        if form.is_valid():
            form.save()
            messages.success(request, f'Producto {producto_temporal.product_id} editado exitosamente')
            return redirect(reverse('pedido_temporal', kwargs={'pedido_id': pedido.id}))
        else:
            messages.error(request, 'Error al editar el producto')
            return redirect(reverse('pedido_temporal', kwargs={'pedido_id': pedido.id}))


def editar_estado_pedido_temporal(request):
    
    if request.method == 'POST':
        pedido_id = request.POST.get('pedido_id', None)
        estado_texto = request.POST.get('estado', None)
        estado = 'CERRADO' if estado_texto == 'CERRAR PEDIDO' else 'PENDIENTE'
        
        if pedido_id and estado:
            pedido = PedidoTemporal.objects.get(id=pedido_id)
            pedido.estado = estado
            pedido.save()
        return JsonResponse({
            'estado': estado,
        })


def editar_pedido_temporal(request):
    
    if request.method == 'GET':
        pedido = PedidoTemporal.objects.get(id=request.GET.get('pedido_id'))
        return JsonResponse({
            'cliente':pedido.cliente,
            'ruc':pedido.ruc,
            'entrega':pedido.entrega.date(),
        })
    
    if request.method == 'POST':
        pedido = PedidoTemporal.objects.get(id=request.POST.get('pedido_id'))
        form = PedidoTemporalForm(request.POST, instance=pedido)
        if form.is_valid():
            form.save()
            messages.success(request, f'Pedido {pedido.enum} editado exitosamente !!!')
            return redirect(reverse('pedido_temporal', kwargs={'pedido_id': pedido.id}))
        else:
            messages.error(request, form.errors)
            return redirect(reverse('pedido_temporal', kwargs={'pedido_id': pedido.id}))


### INVETARIO TRANSFERENCIA
def inventario_transferencia(request):
    
    transf_list = TransfCerAnd.objects.all().order_by('-id')[:5]
    transf_activas = TransfCerAnd.objects.filter(activo=True).order_by('-id')
    data = inventario_transferencia_data()
    
    querysets_transf = [transferencia.productos.all() for transferencia in transf_activas]
    if querysets_transf and len(querysets_transf) > 1:
        todos_productos = list(chain(*querysets_transf))
        productos_dict = [model_to_dict(producto) for producto in todos_productos]
        data_transf = pd.DataFrame(productos_dict)
        data_transf = data_transf.groupby(by=['product_id','lote_id','bodega'])[['cartones','saldos','unidades','reservas']].sum().reset_index()
        data_transf = data_transf.rename(columns={'product_id':'PRODUCT_ID','lote_id':'LOTE_ID','bodega':'LOCATION'})
        data = data.merge(data_transf, on=['PRODUCT_ID','LOTE_ID','LOCATION'], how='left').sort_values(
            by=['PRODUCT_ID','FECHA_CADUCIDAD','BODEGA'], ascending=[True,True,True]
        )
        
    elif len(querysets_transf) == 1 and querysets_transf[0].exists():
        todos_productos = list(chain(*querysets_transf))
        productos_dict = [model_to_dict(producto) for producto in todos_productos]
        data_transf = pd.DataFrame(productos_dict)
        data_transf = data_transf.rename(columns={'product_id':'PRODUCT_ID','lote_id':'LOTE_ID','bodega':'LOCATION'})
        data = data.merge(data_transf, on=['PRODUCT_ID','LOTE_ID','LOCATION'], how='left').sort_values(
            by=['unidades','PRODUCT_ID','FECHA_CADUCIDAD','BODEGA'], ascending=[True,True,True,True]
        )
        data['id'] = data['id'].astype('str')
        
    data = de_dataframe_a_template(data)
    
    if request.method == 'POST':
        form = TransfCerAndForm(request.POST)
        if form.is_valid():
            n_trans = form.save()
            trasf = TransfCerAnd.objects.exclude(id=n_trans.id)
            trasf.update(activo=False)
            
            return HttpResponseRedirect('/etiquetado/inventario/transferencia')
    
    context = {
        'data':data,
        'transf_list':transf_list,
        'transf_activas':transf_activas,
        'len_transf_activas':len(transf_activas),
        'form':TransfCerAndForm()
    }
    
    return render(request, 'etiquetado/analisis_transferencia/inventario_transferencia.html', context)


def transferencia_cer_and_data(id_transf):
    
    transf = TransfCerAnd.objects.get(id=id_transf)
    prods = pd.DataFrame(transf.productos.all().order_by('bodega','product_id','unidades').values())
    
    if not prods.empty:

        totales = {
            'product_id':'TOTAL',
            'lote_id':'',
            'fecha_caducidad':'',
            'bodega':'',
            'cartones' : prods['cartones'].sum(),
            'saldos' : prods['saldos'].sum(),
            'unidades' : prods['unidades'].sum(),
            'volumen' : round(prods['volumen'].sum(), 5),
            'peso' : round(prods['peso'].sum(), 5),
            'reservas':'',
            'detalle':'',
            'Nombre':'',
            'Marca':''
        }
        
        productos = productos_odbc_and_django()[['product_id','Nombre','Marca']]
        prods = prods.merge(productos, on='product_id', how='left')
        prods.insert(0, 'No.', range(1, len(prods) + 1))
        
        df_final = pd.concat([prods, pd.DataFrame([totales])], ignore_index=True).fillna('')        
        df_final = df_final[['No.','product_id','Nombre','Marca','bodega','lote_id','cartones','saldos','unidades','volumen','reservas','detalle']]
        
        return df_final
    
    else:
        return pd.DataFrame()


def get_transferencia_cer_and(request):
    
    id_transf = int(request.GET.get('id_transf'))
    data = transferencia_cer_and_data(id_transf) 
    
    if not data.empty:
        return JsonResponse({
            'data':de_dataframe_a_template(data)
        })
        
    return JsonResponse({'msg':'ok'})


def transferencia_cer_and_email_ajax(request):
    
    id_transf = int(request.GET.get('id_transf'))
    transf = TransfCerAnd.objects.get(id=id_transf)
    data = transferencia_cer_and_data(id_transf)
    
    if not data.empty:
        
        try:
            email = EmailMessage(
                    subject='TRANSFERENCIA CEREZOS-ANDAGOYA',
                    body=f"""
# TRANSFERENCIA: {transf.enum}
# NOMBRE: {transf.nombre.upper()} 
# VEHÍCULO: {transf.vehiculo.placa}
# FECHA: {transf.creado}""",
                    from_email=settings.EMAIL_HOST_USER,
                    to=[
                        'dreyes@gimpromed.com',
                        'ncastillo@gimpromed.com',
                        'jgualotuna@gimpromed.com',
                        'bcerezos@gimpromed.com',
                        'egarces@gimpromed.com',
                    ]
                )
            
            columnas_amarillas = ['product_id', 'lote_id', 'unidades']
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                data.to_excel(writer, sheet_name='Reporte', index=False)
                
                # Opcional: Dar formato al Excel
                workbook = writer.book
                worksheet = writer.sheets['Reporte']
                
                # Añadir formato para encabezados
                header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'border': 1,
                    'fg_color': '#D7E4BC'  # Color verde claro para encabezados normales
                })
                
                # Crear formato para encabezados de columnas amarillas
                yellow_header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'border': 1,
                    'fg_color': '#FFEB9C'  # Color amarillo para encabezados especiales
                })
                
                # Crear formato para celdas amarillas
                yellow_cell_format = workbook.add_format({
                    'fg_color': '#FFEB9C'  # Color amarillo para celdas
                })
                
                # Aplicar formato a los encabezados y determinar índices de columnas amarillas
                indices_columnas_amarillas = []
                
                for col_num, column in enumerate(data.columns):
                    # Determinar si esta columna debe ser amarilla
                    if column in columnas_amarillas:
                        worksheet.write(0, col_num, column, yellow_header_format)
                        indices_columnas_amarillas.append(col_num)
                    else:
                        worksheet.write(0, col_num, column, header_format)
                    
                    # Ajustar el ancho de la columna
                    column_width = max(data[column].astype(str).map(len).max(), len(str(column)))
                    worksheet.set_column(col_num, col_num, column_width + 2)
                
                # Aplicar formato amarillo a todas las celdas de las columnas seleccionadas
                for col_index in indices_columnas_amarillas:
                    # Aplicar formato a todas las filas de la columna (desde la fila 1 hasta la última)
                    worksheet.conditional_format(1, col_index, len(data) - 1, col_index, {
                        'type': 'no_blanks',
                        'format': yellow_cell_format
                    })
            buffer.seek(0)
            
            excel_data = buffer.getvalue()
            
            nombre_archivo = f"{transf.enum}_{transf.creado}.xlsx"
            email.attach(nombre_archivo, excel_data, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            
            email.send(fail_silently=False)
            transf.email = True
            transf.save()
            return JsonResponse({'msg':'ok'})
        except Exception as e:
            transf.email = False
            transf.save()
            return JsonResponse({'msg':'fail','msg-e':f'{e}'})
    
    return JsonResponse({'msg':'no_data'})


def transf_cer_and_activar_inactivar_ajax(request):
    
    id_transf = request.POST.get('id_transf')
    
    transf = TransfCerAnd.objects.get(id=id_transf)
    
    if transf.activo:
        transf.activo = False
        transf.save()
    else:
        transf.activo = True
        transf.save()
    
    return JsonResponse({'msg':'ok'})


def add_producto_transf_ajax(request):
    
    productos = productos_odbc_and_django()
    
    transferencia = TransfCerAnd.objects.filter(activo=True).first()
    vol_list_products = list(transferencia.productos.all().values_list('volumen', flat=True))
    vol_prods_transf =  sum(vol_list_products).__round__(5) if vol_list_products else 0
    
    peso_list_products = list(transferencia.productos.all().values_list('peso', flat=True))
    peso_prods_transf =  sum(peso_list_products).__round__(5) if peso_list_products else 0
    
    def texto_a_numero(texto):
    # Eliminar cualquier carácter que no sea un dígito
        solo_numeros = re.sub(r'\D', '', texto)
        return int(solo_numeros)
    
    if request.method == 'POST':
        
        producto_id = request.POST.get('producto_id')
        lote_id = request.POST.get('lote_id')
        fecha_caducidad = request.POST.get('fecha_caducidad')
        bodega = request.POST.get('bodega')
        und_disp = texto_a_numero(request.POST.get('und_disp'))
        cartones = int(request.POST.get('cartones'))
        saldos = int(request.POST.get('saldos'))
        detalle = request.POST.get('detalle')
        
        prods = productos[productos['product_id']==producto_id].to_dict('records')[0]
        prod_ue = int(prods.get('Unidad_Empaque'))  
        prod_vol = int(prods.get('Volumen')) if int(prods.get('Unidad_Empaque')) == 0 else 0.025
        prod_peso = float(prods.get('Peso')) if float(prods.get('Peso')) > 0 else 0
        
        unidades = (cartones * prod_ue) + saldos
        volumen = (unidades / prod_ue) * prod_vol
        peso = (unidades / prod_ue) * prod_peso
        reservas = und_disp - unidades
        
        new_product = ProductosTransfCerAnd(
            product_id = producto_id,
            lote_id = lote_id,
            fecha_caducidad = fecha_caducidad,
            bodega = bodega,
            cartones = cartones,
            saldos = saldos,
            unidades = unidades,
            volumen = volumen,
            peso = peso,
            reservas = reservas,
            detalle = detalle
        )
        
        new_product.save()
        transferencia.productos.add(new_product)
        
        # volumen transf 
        transferencia.volumen_total = vol_prods_transf + volumen
        transferencia.peso_total = peso_prods_transf + peso
        transferencia.save()
        
        return JsonResponse({'msg':'ok'})


def delete_producto_transf_ajax(request):
    
    if request.method == 'POST':
        
        id_prod = int(float(request.POST.get('id_prod')))
        ProductosTransfCerAnd.objects.get(id=id_prod).delete()
        
        transferencia = TransfCerAnd.objects.filter(activo=True).first()
        
        list_products = list(transferencia.productos.all().values_list('volumen', flat=True))
        vol_prods_transf =  sum(list_products).__round__(5) if list_products else 0.0
        
        peso_list_products = list(transferencia.productos.all().values_list('peso', flat=True))
        peso_prods_transf =  sum(peso_list_products).__round__(5) if peso_list_products else 0
        
        transferencia.volumen_total = vol_prods_transf
        transferencia.peso_total = peso_prods_transf
        
        transferencia.save()
        
        return JsonResponse({'msg':'ok'})


def wms_andagoya_home(request):
    return render(request, 'etiquetado/wms_andagoya/home.html')