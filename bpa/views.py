# Shorcuts
from django.shortcuts import render, redirect

# Datetime
from datetime import datetime, date, timedelta

# BD Connection
from django.db import connections

# Pandas
import pandas as pd
import numpy as np

# Json
import json

# Correo
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings

# Productos
from datos.models import Product
from datos.models import TimeStamp

# Transferencias
from bpa.models import Trasferencia

# PDF
from django_xhtml2pdf.utils import pdf_decorator

# Login
from django.contrib.auth.decorators import login_required


# Html
from django.utils.html import strip_tags


# Tabla Registro Sanitario
from bpa.models import RegistroSanitario, CartaNoRegistro

# Forms
from bpa.forms import RegistroSanitarioForm, CartaNoRegistroForm

# Messages
from django.contrib import messages

# Url
from django.http import HttpResponseRedirect


# TRANSFERENCIA ODBC
from datos.views import (
    doc_transferencia_odbc, 
    importaciones_llegadas_odbc, 
    productos_odbc_and_django, 
    importaciones_llegadas_por_docid_odbc,
    importaciones_tansito_list,
    importaciones_tansito_por_contratoid,
    quitar_prefijo
    )

# de dataframe to template
from compras_publicas.views import de_dataframe_a_template


# Consulta tabla de importaciones transito
def productos(): #request
    ''' Colusta de clientes por ruc a la base de datos '''
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute("SELECT * FROM productos")
        columns = [col[0] for col in cursor.description]
        prod = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
        
        prod = pd.DataFrame(prod)
        prod = prod[['Codigo', 'Nombre', 'Reg_San']]
        prod = prod.rename(columns={'Codigo':'product_id'})

    return prod


# Consulta tabla de importaciones transito
def importaciones_transito_data(): #request
    ''' Colusta de clientes por ruc a la base de datos '''
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute("SELECT * FROM imp_transito")
        columns = [col[0] for col in cursor.description]
        importaciones = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
        
        importaciones = pd.DataFrame(importaciones)

        pro = productos_odbc_and_django()[['product_id', 'Nombre','Marca','Unidad_Empaque']]
        pro = pro.rename(columns={'product_id':'PRODUCT_ID'})

        imp = importaciones.merge(pro, on='PRODUCT_ID')
        imp['CARTONES'] = (imp['QUANTITY']/imp['Unidad_Empaque']).round(0)
        imp['tipo'] = 'importaciones_transito'
        
    return imp



# DATOS DE COMPRAS
def importaciones_compras_df():
    
    imp_llegadas = importaciones_llegadas_odbc() 
    prod = productos_odbc_and_django()[['product_id', 'description','Nombre','marca2','Marca','Unidad_Empaque','Procedencia']]
    
    imp_llegadas['ENTRADA_FECHA'] = pd.to_datetime(imp_llegadas['ENTRADA_FECHA']).dt.strftime('%Y-%m-%d')
    imp_llegadas = imp_llegadas.sort_values(by='ENTRADA_FECHA', ascending=False)
    imp_llegadas['ENTRADA_FECHA'] = imp_llegadas['ENTRADA_FECHA'].astype('str')
    
    imp_llegadas = imp_llegadas.merge(prod, on='product_id', how='left')
    imp_llegadas['Procedencia'] = imp_llegadas['Procedencia'].astype('str')
    
    imp_llegadas['CARTONES'] = imp_llegadas['OH'] / imp_llegadas['Unidad_Empaque']
    imp_llegadas = imp_llegadas.drop(['LOTE_ID'], axis=1)
    
    return imp_llegadas
    

# Muestreos Importaciones
@login_required(login_url='login')
def importaciones(request):

    imp = importaciones_compras_df()
    imp = imp.drop_duplicates(subset=['DOC_ID_CORP'])
    imp['tipo'] = 'importaciones_llegadas'
    filtro_1 = imp['Procedencia'].str.contains('NACIONAL')
    filtro_2 = imp['Procedencia'].str.contains('Nacional')

    imp = imp[~filtro_1]
    imp = imp[~filtro_2]
    
    imp_llegadas = de_dataframe_a_template(imp)
    
    context = {
        'imp':imp_llegadas,
    }

    return render(request, 'bpa/muestreos/lista_importaciones.html', context)


@login_required(login_url='login')
def importaciones_transito(request):
    prod = productos_odbc_and_django()[['product_id', 'marca2']]
    imp_transito = importaciones_tansito_list()
    imp_transito = imp_transito.drop_duplicates(subset='CONTRATO_ID').sort_values(by='CONTRATO_ID', ascending=False)
    imp_transito = imp_transito.rename(columns={'PRODUCT_ID':'product_id'})
    imp_transito = imp_transito.merge(prod, on='product_id', how='left')
    imp_transito['FECHA_ENTREGA'] = imp_transito['FECHA_ENTREGA'].astype('str')
    imp_transito['tipo'] = 'importaciones_transito'
    imp_transito = de_dataframe_a_template(imp_transito)
    
    context = {
        'imp':imp_transito
    }
    return render(request, 'bpa/muestreos/lista_importaciones_transito.html', context)


def nacionales(request):
    
    nac = importaciones_compras_df() 
    nac = nac[(nac['Procedencia'].str.contains('NACIONAL')) | (nac['Procedencia'].str.contains('Nacional'))]
    nac = nac.drop_duplicates(subset=['DOC_ID_CORP'])
    nac = de_dataframe_a_template(nac)

    context = {
        'nac':nac
    }
    
    return render(request, 'bpa/muestreos/lista_nacionales.html', context)


def muestreo(data, und):

    # Nivel 1
    condiciones_nivel = [
    (data[und] < 2),
    (data[und] >= 2) & (data[und]<=8),
    (data[und] >= 9) & (data[und]<=15),
    (data[und] >= 16) & (data[und]<=25),
    (data[und] >= 26) & (data[und]<=50),
    (data[und] >= 51) & (data[und]<=90),
    (data[und] >= 91) & (data[und]<=150),
    (data[und] >= 151) & (data[und]<=280),
    (data[und] >= 281) & (data[und]<=500),
    (data[und] >= 501) & (data[und]<=1200),
    (data[und] >= 1201) & (data[und]<=3200),
    (data[und] >= 3201) & (data[und]<=10000),
    (data[und] >= 10001) & (data[und]<=35000),
    (data[und] >= 35001) & (data[und]<=150000),
    (data[und] >= 150001) & (data[und]<=500000),
    (data[und] >= 500001) & (data[und]<=9999999),
    ]
    seleccion_nivel = ['A', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'Q']
    data['Nivel'] = np.select(condiciones_nivel, seleccion_nivel, default='N/A')

    # Muestra 1
    condiciones_muestra = [
    (data[und] < 2) & (data['Nivel'] == 'A'),
    (data['Nivel'] == 'A'),
    (data['Nivel'] == 'B'),
    (data['Nivel'] == 'C'),
    (data['Nivel'] == 'D'),
    (data['Nivel'] == 'E'),
    (data['Nivel'] == 'F'),
    (data['Nivel'] == 'G'),
    (data['Nivel'] == 'H'),
    (data['Nivel'] == 'J'),
    (data['Nivel'] == 'K'),
    (data['Nivel'] == 'L'),
    (data['Nivel'] == 'M'),
    (data['Nivel'] == 'N'),
    (data['Nivel'] == 'P'),
    (data['Nivel'] == 'Q'),
    (data['Nivel'] == 'R'),
    ]
    seleccion_muestra = [1, 2, 3, 5, 8, 13, 20, 32, 50, 80, 125, 200, 325, 500, 800, 1250, 2000]
    data['Muestra'] = np.select(condiciones_muestra, seleccion_muestra, default=0)

    # Nivel 2
    condiciones_nivel_2 = [
    (data['Muestra'] < 2),
    (data['Muestra'] >= 2) & (data['Muestra']<=8),
    (data['Muestra'] >= 9) & (data['Muestra']<=15),
    (data['Muestra'] >= 16) & (data['Muestra']<=25),
    (data['Muestra'] >= 26) & (data['Muestra']<=50),
    (data['Muestra'] >= 51) & (data['Muestra']<=90),
    (data['Muestra'] >= 91) & (data['Muestra']<=150),
    (data['Muestra'] >= 151) & (data['Muestra']<=280),
    (data['Muestra'] >= 281) & (data['Muestra']<=500),
    (data['Muestra'] >= 501) & (data['Muestra']<=1200),
    (data['Muestra'] >= 1201) & (data['Muestra']<=3200),
    (data['Muestra'] >= 3201) & (data['Muestra']<=10000),
    (data['Muestra'] >= 10001) & (data['Muestra']<=35000),
    (data['Muestra'] >= 35001) & (data['Muestra']<=150000),
    (data['Muestra'] >= 150001) & (data['Muestra']<=500000),
    (data['Muestra'] >= 500001) & (data['Muestra']<=9999999),
    ]
    seleccion_nivel_2 = ['A', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'Q']
    data['Nivel_2'] = np.select(condiciones_nivel_2, seleccion_nivel_2, default='N/A')

    # Muestra 2
    condiciones_muestra_2 = [
    (data['Muestra'] < 2) & (data['Nivel_2'] == 'A'),
    (data['Nivel_2'] == 'A'),
    (data['Nivel_2'] == 'B'),
    (data['Nivel_2'] == 'C'),
    (data['Nivel_2'] == 'D'),
    (data['Nivel_2'] == 'E'),
    (data['Nivel_2'] == 'F'),
    (data['Nivel_2'] == 'G'),
    (data['Nivel_2'] == 'H'),
    (data['Nivel_2'] == 'J'),
    (data['Nivel_2'] == 'K'),
    (data['Nivel_2'] == 'L'),
    (data['Nivel_2'] == 'M'),
    (data['Nivel_2'] == 'N'),
    (data['Nivel_2'] == 'P'),
    (data['Nivel_2'] == 'Q'),
    (data['Nivel_2'] == 'R'),
    ]
    seleccion_muestra_2 = [1, 2, 3, 5, 8, 13, 20, 32, 50, 80, 125, 200, 325, 500, 800, 1250, 2000]
    data['Muestra_2'] = np.select(condiciones_muestra_2, seleccion_muestra_2, default=0)

    return data


@pdf_decorator(pdfname='muestreo_importacion_unidades.pdf')
@login_required(login_url='login')
def muestreo_unidades(request, memo):

    data = importaciones_llegadas_por_docid_odbc(memo)
    imp = muestreo(data, 'OH')
    imp = imp.sort_values(by='product_id')

    proveedor = imp['marca2'].iloc[0]
    proveedor2 = imp['Marca'].iloc[0]
    n_imp = imp['MEMO'].iloc[0]
    n_doc = imp['DOC_ID_CORP'].iloc[0]
    
    imp = de_dataframe_a_template(imp)

    context = {
        'imp':imp,
        'proveedor':proveedor,
        'proveedor2':proveedor2,
        'n_imp':n_imp,
        'n_doc':n_doc
    }

    return render(request, 'bpa/muestreos/muestreo_imp_unidades.html', context)


@pdf_decorator(pdfname='muestreo_importacion_cartones.pdf')
@login_required(login_url='login')
def muestreo_cartones(request, memo):
    
    data = importaciones_llegadas_por_docid_odbc(memo)
    imp = muestreo(data, 'CARTONES')
    imp = imp.sort_values(by='product_id')

    proveedor = imp['marca2'].iloc[0]
    proveedor2 = imp['Marca'].iloc[0]
    n_imp = imp['MEMO'].iloc[0]
    n_doc = imp['DOC_ID_CORP'].iloc[0]
    
    imp = de_dataframe_a_template(imp)
    
    context = {
        'imp':imp,
        'proveedor':proveedor,
        'proveedor2':proveedor2,
        'n_imp':n_imp,
        'n_doc':n_doc
    }

    return render(request, 'bpa/muestreos/muestreo_imp_cartones.html', context)


@pdf_decorator(pdfname='muestreo_importacion_unidades.pdf')
@login_required(login_url='login')
def muestreo_unidades_transito(request, contrato_id):

    data = importaciones_tansito_por_contratoid(contrato_id)
    imp = muestreo(data, 'OH')
    imp = imp.sort_values(by='product_id')

    proveedor = imp['marca2'].iloc[0]
    proveedor2 = imp['Marca'].iloc[0]
    n_imp = imp['MEMO'].iloc[0]
    n_doc = imp['CONTRATO_ID'].iloc[0]
    
    imp = de_dataframe_a_template(imp)

    context = {
        'imp':imp,
        'proveedor':proveedor,
        'proveedor2':proveedor2,
        'n_imp':n_imp,
        'n_doc':n_doc
    }

    return render(request, 'bpa/muestreos/muestreo_imp_unidades.html', context)


@pdf_decorator(pdfname='muestreo_importacion_unidades.pdf')
@login_required(login_url='login')
def muestreo_cartones_transito(request, contrato_id):

    data = importaciones_tansito_por_contratoid(contrato_id)
    imp = muestreo(data, 'CARTONES')
    imp = imp.sort_values(by='product_id')

    proveedor = imp['marca2'].iloc[0]
    proveedor2 = imp['Marca'].iloc[0]
    n_imp = imp['MEMO'].iloc[0]
    n_doc = imp['CONTRATO_ID'].iloc[0]
    
    imp = de_dataframe_a_template(imp)

    context = {
        'imp':imp,
        'proveedor':proveedor,
        'proveedor2':proveedor2,
        'n_imp':n_imp,
        'n_doc':n_doc
    }

    return render(request, 'bpa/muestreos/muestreo_imp_cartones.html', context)


@pdf_decorator(pdfname='revision_tecnica.pdf')
@login_required(login_url='login')
def revision_tecnica(request, doc_id):
    
    prod = productos_odbc_and_django()[[
        'product_id',
        'Nombre',
        'Marca',
        'marca2',
        'Reg_San',
        'emp_primario', 
        'emp_secundario', 
        'emp_terciario'
    ]]


    data = importaciones_compras_df()
    data = data[data['DOC_ID_CORP']==doc_id]
    
    data = data.groupby([
        'product_id',
        'DOC_ID_CORP',
        'ENTRADA_FECHA',
        'OH',
        'WARE_COD_CORP',
        'MEMO'
        ]).sum().reset_index()
    
    data = data.merge(prod, on='product_id', how='left')
    data['Reg_San'] = data['Reg_San'].apply(quitar_prefijo)      
    
    fecha_entrada = data['ENTRADA_FECHA'].iloc[0]
    bodega_llegada = data['WARE_COD_CORP'].iloc[0]
    proveedor = data['marca2'].iloc[0]
    n_imp = data['MEMO'].iloc[0]
    
    data = de_dataframe_a_template(data)
    
    context = {
        'imp':data,
        'fecha':fecha_entrada,
        'bodega_llegada':bodega_llegada,
        'proveedor':proveedor,
        'n_imp':n_imp,
        'n_lineas':range(5)
    }

    return render(request, 'bpa/muestreos/revision_tecnica_importaciones.html', context)


@login_required(login_url='login')
def transferencias(request):
    
    trans = pd.DataFrame(Trasferencia.objects.all().values())
    trans = trans.sort_values('documento', ascending=False)
    trans['proveedor'] = 'Gimpromed Cía. Ltda.'
    trans = trans.drop_duplicates(subset=['documento'])
    trans = de_dataframe_a_template(trans)

    context = {
        'trasferencia':trans
    }

    if request.method == 'POST':
        
        n = request.POST.get('n_transf')

        try:
            
            if Trasferencia.objects.filter(documento=n).exists():
                messages.error(request, 'Ya existe un muestreo de esta transferencia, use el buscador !!!')

            else:
                transf = doc_transferencia_odbc(n)
                documento = list(map(lambda x:x[7:-6], list(transf['doc'])))
                transf['documento'] = documento
                transf = transf[['documento', 'product_id', 'lote_id', 'unidades']]
                transf = [tuple(i) for i in transf.values]
                
                with connections['default'].cursor() as cursor:
                    cursor.executemany(
                        """ INSERT INTO bpa_trasferencia (documento, product_id, lote, unidades) VALUES (%s,%s,%s,%s)""", transf
                    )

                messages.success(request, f'La transferencia número {n} se añadio correctamente !!!')
            return redirect('/bpa/muestreos/transferencias')

        except:
            messages.error(request, 'No existe ese número de transferencia !!!')

    return render(request, 'bpa/muestreos/lista_trasferencias.html', context)



@pdf_decorator(pdfname='muestreo_transferencia.pdf')
@login_required(login_url='login')
def muestreo_transferencia(request, doc):

    trans = pd.DataFrame(Trasferencia.objects.filter(documento=doc).values())    
    prod = productos_odbc_and_django()[['product_id','Nombre']]
    
    trans = trans.groupby(['product_id', 'documento']).sum()
    trans = trans.reset_index()

    docum = trans['documento'].iloc[0]

    muest = muestreo(trans, 'unidades')
    muest = muest.merge(prod, on='product_id', how='left')

    muest = de_dataframe_a_template(muest)
    
    context = {
        'documento':docum,
        'muestreo':muest
    }

    return render(request, 'bpa/muestreos/muestreo_transferencias.html', context)


@pdf_decorator(pdfname='muestreo_transferencia.pdf')
@login_required(login_url='login')
def revision_tecnica_transferencia(request, doc):
    
    trans = pd.DataFrame(Trasferencia.objects.filter(documento=doc).values())
    trans_odbc = doc_transferencia_odbc(doc)[['product_id','bodega_salida']]
    prod = productos_odbc_and_django()[[
        'product_id',
        'Nombre',
        'Reg_San',
        'emp_primario', 
        'emp_secundario', 
        'emp_terciario']]

    trans = trans.groupby(['product_id', 'documento']).sum()
    trans = trans.reset_index()

    muest = muestreo(trans, 'unidades')
    muest = muest.merge(prod, on='product_id', how='left')
    muest = muest.merge(trans_odbc, on='product_id', how='left')
    muest['Reg_San'] = muest['Reg_San'].apply(quitar_prefijo)
    
    docum = muest['documento'].iloc[0]
    b_salida = muest['bodega_salida'].iloc[0]
    
    if b_salida == 'BCT':
        bodega_salida = 'Cerezos'
        bodega_entrada = 'Andagoya'
    elif b_salida == 'CUC':
        bodega_salida = 'Cuarentena Cerezos'
        bodega_entrada = 'Cuarentena Andagoya'
    
    muest = de_dataframe_a_template(muest)

    context = {
        'muestreo':muest,
        'documento':docum,
        'bodega_salida':bodega_salida,
        'bodega_entrada':bodega_entrada,
        'n_lineas':range(5)
    }

    return render(request, 'bpa/muestreos/revision_tecnica_transferencias.html', context)


# Lista de registros sanitarios
@login_required(login_url='login')
def reg_san_list(request):
    
    r_san_list = RegistroSanitario.objects.all().order_by('marca', 'fecha_expiracion')
    r_san_list_2 = RegistroSanitario.objects.all().order_by('fecha_expiracion')
    
    n_docs     = len([i for i in RegistroSanitario.objects.all() if i.obs_doc == 'Docs ok'])    
    n_enviar   = len([i for i in RegistroSanitario.objects.all() if i.obs_doc == 'Enviar a notaria'])   
    n_caducado = len([i for i in RegistroSanitario.objects.all() if i.estado  == 'Caducado'])
    n_proximo  = len([i for i in RegistroSanitario.objects.all() if i.estado  == 'Próximo a caducar'])
    n_vigente  = len([i for i in RegistroSanitario.objects.all() if i.estado  == 'Vigente'])
    n_sin      = len([i for i in RegistroSanitario.objects.all() if i.estado  == 'Sin especificar' ])

    context = {
        'r_san_list':r_san_list,
        'r_san_list_2':r_san_list_2,
        
        'n_docs':n_docs,
        'n_enviar':n_enviar,
        'n_caducado':n_caducado,
        'n_proximo':n_proximo,
        'n_vigente':n_vigente,
        'n_sin':n_sin
    }

    return render(request, 'bpa/registro_sanitario/list.html', context)


# Nuevo Registro Sanitario
@login_required(login_url='login')
def reg_san_new(request):

    if request.user.has_perm('bpa.add_registrosanitario'):
        form = RegistroSanitarioForm()

        if request.method == 'POST':
            form = RegistroSanitarioForm(request.POST)
            reg = str(request.POST.get('registro'))
            if form.is_valid():
                form.save()
                messages.success(request, f'El registro sanitario {reg} se añadio correctamiente !!!')
                return redirect('reg_san_list')
            else:
                messages.error(request, 'Error al añadir un nuevo registro sanitario !!!')
                return HttpResponseRedirect('/bpa/reg-san/list')
    else:
        messages.error(request, 'No tienes los permisos necesarios !!!')
        return HttpResponseRedirect('/bpa/reg-san/list')

    context = {
        'form':form,
    }

    return render(request, 'bpa/registro_sanitario/r_san_new.html', context)


# Registro Sanitario detail - edit
@login_required(login_url='login')
def reg_san_edit(request, id):
    
    r_san_instance = RegistroSanitario.objects.get(id=id)
    form = RegistroSanitarioForm(instance=r_san_instance)

    id_edit = str(id)
    reg = str(request.POST.get('registro'))

    if request.user.has_perm('bpa.change_registrosanitario'):
        disabled = ''
    else:
        disabled = 'disabled'

    if request.method == 'POST':

        form = RegistroSanitarioForm(request.POST, instance=r_san_instance)
        if form.is_valid():
            form.save()
            messages.success(request, f'El registro sanitario {reg} se edito correctamiente !!!')
            return redirect('reg_san_list')

        else:
            messages.error(request, f'Error al editar el registro sanitario {reg} !!!')
            return HttpResponseRedirect(f'/bpa/reg-san/edit/{id_edit}')

    context = {
        'form':form,
        'disabled':disabled
    }

    return render(request, 'bpa/registro_sanitario/r_san_edit.html', context)


# Carta de no registro
@login_required(login_url='login')
def carta_no_reg_list(request):

    r_san_list = CartaNoRegistro.objects.all()

    n_caducado = len([i for i in CartaNoRegistro.objects.all() if i.estado == 'Caducado'])
    n_proximo = len([i for i in CartaNoRegistro.objects.all() if i.estado == 'Próximo a caducar'])
    n_vigente = len([i for i in CartaNoRegistro.objects.all() if i.estado == 'Vigente'])
    n_sin = len([i for i in CartaNoRegistro.objects.all() if i.estado == 'Sin especificar' ])

    context = {
        'r_san_list':r_san_list,

        'n_caducado':n_caducado,
        'n_proximo':n_proximo,
        'n_vigente':n_vigente,
        'n_sin':n_sin,
    }

    return render(request, 'bpa/carta_no_reg/list.html', context)


# Nuevo Registro Sanitario
@login_required(login_url='login')
def carta_no_reg_new(request):

    if request.user.has_perm('bpa.add_cartanoregistro'):
        form = CartaNoRegistroForm()

        if request.method == 'POST':
            form = CartaNoRegistroForm(request.POST)
            reg = str(request.POST.get('registro'))
            if form.is_valid():
                form.save()
                messages.success(request, f'El registro sanitario {reg} se añadio correctamiente !!!')
                return redirect('reg_san_list')
            else:
                messages.error(request, 'Error al añadir un nuevo registro sanitario !!!')
                return HttpResponseRedirect('/bpa/reg-san/list')
    else:
        messages.error(request, 'No tienes los permisos necesarios !!!')
        return HttpResponseRedirect('/bpa/reg-san/list')

    context = {
        'form':form,
    }

    return render(request, 'bpa/carta_no_reg/carta_no_r_san_new.html', context)


# Carta No Registro Sanitario detail - edit
@login_required(login_url='login')
def carta_no_reg_edit(request, id):
    
    r_san_instance = CartaNoRegistro.objects.get(id=id)
    form = CartaNoRegistroForm(instance=r_san_instance)

    id_edit = str(id)
    reg = str(request.POST.get('marca'))

    if request.user.has_perm('bpa.change_registrosanitario'):
        disabled = ''
    else:
        disabled = 'disabled'
    

    if request.method == 'POST':

        form = CartaNoRegistroForm(request.POST, instance=r_san_instance)
        if form.is_valid():
            form.save()
            messages.success(request, f'La carta de no registro sanitario {reg} se edito correctamiente !!!')
            return redirect('carta_no_reg_list')

        else:
            messages.error(request, f'Error al editar la carta de no registro sanitario {reg} !!!')
            return HttpResponseRedirect(f'/bpa/carta-no-reg/edit/{id_edit}')


    context = {
        'form':form,
        'disabled':disabled
    }

    return render(request, 'bpa/carta_no_reg/carta_no_r_san_edit.html', context)


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