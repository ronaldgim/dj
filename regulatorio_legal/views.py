from django.shortcuts import render

# DB
from django.db import connections

# Importaciones llegadas datafame
from datos.views import (
    importaciones_llegadas_odbc, 
    productos_odbc_and_django, 
    de_dataframe_a_template, 
    facturas_odbc, 
    factura_lote_odbc, 
    cliente_detalle_odbc,
    ultima_actualizacion,
    quitar_puntos)

# Models
from regulatorio_legal.models import DocumentoLote, DocumentoEnviado

# Pandas
import pandas as pd

# models
from users.models import User

# Utilities
from django.views.decorators.csrf import csrf_exempt
from regulatorio_legal.forms import DocumentoLoteForm, NewDocumentoLoteForm, DocumentoEnviadoForm
from django.shortcuts import redirect
from django.http import HttpResponse, HttpResponseRedirect

from django.core.mail import EmailMessage
from django.conf import settings

from etiquetado.views import correos_notificacion_factura

# Messages
from django.contrib import messages

# Json
import json

from smtplib import SMTPException 

# Lista de importaciones
def importaciones_llegadas_list(request):
    
    imp = importaciones_llegadas_odbc()
    pro = productos_odbc_and_django()
    
    imp = imp.merge(pro, on='product_id', how='left')
    
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

    # Borrar duplicados
    imp = imp.drop_duplicates(subset=['DOC_ID_CORP'])

    # Ordenar por fecha
    imp['ENTRADA_FECHA'] = pd.to_datetime(imp['ENTRADA_FECHA'])
    imp = imp.sort_values(by=['ENTRADA_FECHA'], ascending=[False])
    imp['ENTRADA_FECHA'] = imp['ENTRADA_FECHA'].astype(str)
    
    # Lista de documento lote
    d_l_list = pd.DataFrame(DocumentoLote.objects.all().values())

    # Armados
    armados = pd.DataFrame(DocumentoLote.objects.all().values())
    n_armados = armados[armados['o_compra']=='ARMADO']
    n_armados = len(n_armados['documento'])
    armados = armados[armados['o_compra']=='ARMADO'] 
    armados['DOC_ID_CORP']   = 'ARMADOS'
    armados['ENTRADA_FECHA'] = '-'
    armados['WARE_COD_CORP'] = '-'
    armados['marca2']        = 'ARMADOS'
    armados                  = armados.drop_duplicates(subset=['DOC_ID_CORP'])
    armados['documento']     = n_armados
    armados['sin_documento'] = 0.0
    armados['con_documento'] = n_armados
    armados['completado']    = ((armados['con_documento'] / armados['documento']) * 100).round(0)
    armados = armados[['DOC_ID_CORP','ENTRADA_FECHA','WARE_COD_CORP','marca2','lote_id','documento','sin_documento','con_documento','completado']]
    
    # lista de documentos lote NUMERO DE DOCUMENTOS POR IMPORTACIÓN
    n_docs = pd.DataFrame(DocumentoLote.objects.all().values()) 
    n_docs = n_docs.groupby(by=['o_compra']).count()
    n_docs = n_docs[['documento']]
    n_docs = n_docs.reset_index() 
    
    # lista de documentos lote SIN DOCUMENTO
    n_docs_2 = pd.DataFrame(DocumentoLote.objects.all().values()).replace('', 'sin documento').reset_index()
    n_docs_2 = n_docs_2[n_docs_2['documento']=='sin documento'] 
    n_docs_2 = n_docs_2.groupby(by=['o_compra']).count()
    n_docs_2 = n_docs_2[['documento']]
    n_docs_2 = n_docs_2.rename(columns={'documento':'sin_documento'}).reset_index() 

    # Calcular documentos llenoos y documentos faltante
    n_docs = n_docs.merge(n_docs_2, on='o_compra', how='left').fillna(0)
    n_docs['con_documento'] = n_docs['documento'] - n_docs['sin_documento'] 

    # Barra de comletado
    n_docs['completado'] = ((n_docs['con_documento'] / n_docs['documento']) * 100).round(0)

    n_docs = n_docs.rename(columns={'o_compra':'DOC_ID_CORP'})

    if d_l_list.empty:
        imp['lote_id'] = 0

    else: 
        d_l_list = d_l_list[['o_compra', 'lote_id']]
        d_l_list = d_l_list.drop_duplicates(subset='o_compra')        
        d_l_list = d_l_list.rename(columns={'o_compra':'DOC_ID_CORP'})
        imp = imp.merge(d_l_list, on='DOC_ID_CORP', how='left').fillna(0)

    imp = imp.merge(n_docs, on='DOC_ID_CORP', how='left').fillna(0) 
    imp = pd.concat([armados, imp])

    imp_list = de_dataframe_a_template(imp)

    context = {
        'imp':imp_list,
        'actulizacion' : ultima_actualizacion('actualization_imp_llegadas')
    }

    return render(request, 'regulatorio_legal/importaciones_llegadas_list.html', context)



def doc_importacion_por_lote_ajax(request):

    lote_id = request.POST['lote_id']
    
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(
            f"SELECT DOC_ID_CORP FROM imp_llegadas WHERE LOTE_ID = '{lote_id}' "
            )
        columns = [col[0] for col in cursor.description]
        importacion = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        imp = pd.DataFrame(importacion)
        imp = imp.drop_duplicates()
        imp = list(imp['DOC_ID_CORP'])
        
        if len(imp)>1:
            i = '; '.join(imp)

        else:
            i = imp[0]

    return HttpResponse(i)



def importacion_list_detail(request, o_compra):

    doc_lot = DocumentoLote.objects.filter(o_compra=o_compra)
    
    imp = importaciones_llegadas_odbc()
    imp = imp[imp['DOC_ID_CORP']==o_compra]

    imp = imp.sort_values(by=['product_id', 'FECHA_CADUCIDAD'])
    imp['doc'] = ''
    imp = imp[['product_id','LOTE_ID', 'FECHA_CADUCIDAD', 'doc','DOC_ID_CORP']]
    imp = [tuple(i) for i in imp.values]

    if not doc_lot.exists():
    
        with connections['default'].cursor() as cursor:
            cursor.executemany(
                "INSERT INTO regulatorio_legal_documentolote (product_id, lote_id, f_caducidad, documento, o_compra) VALUES (%s,%s,%s,%s,%s)", imp
            )

    d_l_list = pd.DataFrame(DocumentoLote.objects.filter(o_compra=o_compra).values())
    d_l_list = d_l_list.merge(productos_odbc_and_django()[['product_id', 'Nombre', 'Marca']], on='product_id', how='left')
    d_l_list['f_caducidad'] = d_l_list['f_caducidad'].astype(str)
    
    marca = d_l_list['Marca'][0]

    d = list(d_l_list['documento'].fillna(0))
    d_list = []
    for i in d:
        if i != 0 and len(i)>0:
            i = i.split('/')[1]
        d_list.append(i)
    d_l_list['doc'] = d_list

    d_l_list = de_dataframe_a_template(d_l_list)


    context = {
        'imp':d_l_list,
        'marca':marca,
        'o_compra':o_compra,
        
    }

    return render(request, 'regulatorio_legal/detalle_importacion.html', context)



def armados_list_imp(request):
    
    armados = pd.DataFrame(DocumentoLote.objects.all().values())
    armados = armados[armados['o_compra']=='ARMADO']
    armados = armados.merge(productos_odbc_and_django()[['product_id', 'Nombre', 'Marca']], on='product_id', how='left')
    armados['f_caducidad'] = armados['f_caducidad'].astype(str)

    d = list(armados['documento'].fillna(0))
    d_list = []
    for i in d:
        if i != 0 and len(i)>0:
            i = i.split('/')[1]
        d_list.append(i)
    armados['doc'] = d_list
    
    armados = de_dataframe_a_template(armados)

    context = {
        'armados':armados
    }

    return render(request, 'regulatorio_legal/armados_list.html', context)



# @csrf_exempt
def update_document(request):

    id_obj = request.POST.get('id')
    inst = DocumentoLote.objects.get(id=id_obj)

    if request.method == 'POST':
        form = DocumentoLoteForm(request.POST, request.FILES, instance=inst)
        if form.is_valid():
            form.save()
            return HttpResponse('exito')
        else:
            return HttpResponse('error')


def new_document(request):

    # Añadir documento
    if request.method == 'POST':
        form = NewDocumentoLoteForm(request.POST, request.FILES) #.clean() 
        if form.is_valid():
            form.save()
            return HttpResponse('exito')
        else:
            HttpResponse('error')



def lista_facturas(request):

    facturas = facturas_odbc()
    facturas = facturas.drop_duplicates(subset='CODIGO_FACTURA')
    
    lista_codigos_factura = list(facturas['CODIGO_FACTURA'])
    
    facturas['codigo_factura'] = list(map(lambda x: x.split(('-'))[1], lista_codigos_factura))
    facturas = facturas.sort_values(by=['codigo_factura'], ascending=[False])

    envios_documentos = pd.DataFrame(DocumentoEnviado.objects.all().values(
        'n_factura',
        'usuario__first_name',
        'usuario__last_name',
        'fecha_hora'
        ))
    
    envios_documentos['fecha_hora'] = envios_documentos['fecha_hora'].astype(str)
    envios_documentos['fecha_hora'] = envios_documentos['fecha_hora'].str.slice(0,-7)
    
    envios_documentos = envios_documentos.drop_duplicates(subset=['n_factura'], keep='last')
    
    if not envios_documentos.empty:
        envios_documentos['user'] = envios_documentos['usuario__first_name'] + ' ' + envios_documentos['usuario__last_name']
        envios_documentos = envios_documentos.rename(columns={'n_factura':'CODIGO_FACTURA'})
        facturas = facturas.merge(envios_documentos, on='CODIGO_FACTURA', how='left')

    facturas = de_dataframe_a_template(facturas)

    actualizacion = ultima_actualizacion('actulization_stoklote')

    context = {
        'facturas':facturas,
        'act':actualizacion
    }

    return render(request, 'regulatorio_legal/lista_facturas.html', context)


# Detallar factura, enviar correo y guardar envio
def factura_detalle(request, n_factura):
    
    factura = factura_lote_odbc(n_factura)
    n_fac = factura['CODIGO_FACTURA'].iloc[0]
    fac = n_fac.split('-')[1]
    cliente = factura['CODIGO_CLIENTE'].iloc[0]
    cli = cliente_detalle_odbc(cliente)['NOMBRE_CLIENTE']
    ff = factura['FECHA_FACTURA'].iloc[0]
    correo = correos_notificacion_factura(cli)[0]

    docs = pd.DataFrame(DocumentoLote.objects.all().values())
    docs = docs.rename(columns={'product_id':'PRODUCT_ID','lote_id':'LOTE_ID'})[['id','PRODUCT_ID','LOTE_ID','documento']]

    # QUITAR PUNTOS DE LOS LOTES
    lotes_factura = factura['LOTE_ID']
    factura['lote_sp'] = quitar_puntos(lotes_factura)
    
    # QUITAR PUNTOS DE LOS LOTES
    lotes_docs = docs['LOTE_ID'] 
    docs['lote_sp'] = quitar_puntos(lotes_docs)
    
    # MERGE FACTURA Y DOCUMENTOS
    # factura = factura.merge(docs, on=['PRODUCT_ID','LOTE_ID'], how='left').fillna(0) 
    factura = factura.merge(docs, on=['PRODUCT_ID','lote_sp'], how='left').fillna(0) #;print(factura)
    factura = factura.sort_values('PRODUCT_NAME')
    #factura = factura.drop_duplicates(subset=['PRODUCT_ID','LOTE_ID'])
    factura = factura.drop_duplicates(subset=['PRODUCT_ID','lote_sp'])
    factura['id'] = factura['id'].astype(int)  #; print(factura)
    
    # JSON DETALLE DE FACTURA Y DOCUMENTOS
    detalle = factura[['PRODUCT_ID', 'lote_sp', 'documento']].to_dict('list')
    detalle = json.dumps(detalle)    

    documentos = factura['documento'].dropna() 
    documentos = list(documentos) 
    
    doc_len = len(documentos)
    prod_len = len(factura['PRODUCT_ID'])

    d = list(factura['documento'].fillna(0))
    d_list = []
    for i in d:
        if i != 0 and len(i)>0:
            i = i.split('/')[1]
        d_list.append(i)
    factura['doc'] = d_list

    factura = de_dataframe_a_template(factura)

    if request.method == 'POST':
        
        # Quien envia el correo
        who_send = User.objects.get(id=request.POST['usuario']).email
        
        if doc_len == prod_len:
            
            # Enviar correo
            try:
                
                n_archivos = 10
                n_correos = len(range(0, doc_len, n_archivos))
                
                archivos = [documentos[i:i+n_archivos] for i in range(0, doc_len, n_archivos)]
                
                correo_cliente = [request.POST['correo_cliente']]
                correo_cliente.append(who_send)

                if n_correos == 1:   
                    
                    email = EmailMessage(
                        subject=f'Documentos de factura N°. {fac}',
                        body=f"""
Señores {cli}, \n
Su pedido de documentos con respecto a la factura {fac} es enviado de acuerdo a lo solicitado.\n
GIMPROMED Cia. Ltda.\n
****Esta notificación ha sido enviada automáticamente - No responder****
                        """,
                        from_email=settings.EMAIL_HOST_USER,
                        # to=['egarces@gimpromed.com','jgualotuna@gimpromed.com','ncaisapanta@gimpromed.com'],
                        # to=['egarces@gimpromed.com'],
                        to = correo_cliente,
                        headers={'Message-ID':'Documentos'}
                    )

                    for i in documentos:
                        docs = 'media/' + i
                        email.attach_file(docs)

                    email.send()

                    form = DocumentoEnviadoForm(request.POST)
                    if form.is_valid():
                        form.save()

                    messages.success(request, 'Correo enviado con exito !!!')
                    return HttpResponseRedirect('/regulatorio-legal/facturas')

                else:
                    for i in range(0, n_correos):
                        corr = i+1
                   
                        email = EmailMessage(
                            subject=f'Documentos de factura N°. {fac} - Parte {corr}',
                            body=f"""
Señores {cli}, \n
Su pedido de documentos con respecto a la factura {fac} es enviado de acuerdo a lo solicitado.\n
GIMPROMED Cia. Ltda.\n
****Esta notificación ha sido enviada automáticamente - No responder****
                            """,
                            from_email=settings.EMAIL_HOST_USER,
                            #to=['egarces@gimpromed.com','jgualotuna@gimpromed.com','ncaisapanta@gimpromed.com'],
                            #to=['egarces@gimpromed.com'],
                            to = correo_cliente,
                            headers={'Message-ID':'Documentos'}
                        )

                        
                        for j in archivos[i]:
                            docs = 'media/' + j
                            email.attach_file(docs)
                            
                        email.send()

                    form = DocumentoEnviadoForm(request.POST)
                    if form.is_valid():
                        form.save()

                    messages.success(request, f'Se enviarón {n_correos} correos !!!')
                    return HttpResponseRedirect('/regulatorio-legal/facturas')
            
            except SMTPException as e:
                messages.error(request, f'Error al enviar el correo, {e} !!!')
                
        else:
            messages.error(request, 'No se ha subido todos los documentos !!!')

    context = {
        'factura':factura,

        'fac':fac,
        'cli':cli,
        'ff':ff,

        'correo_cli':correo,

        'n_fac':n_fac,
        'codigo_cliente':cliente,
        'detalle':detalle
    }

    return render(request, 'regulatorio_legal/factura_detalle.html', context)