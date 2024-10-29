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
    quitar_puntos,
    clientes_warehouse)

# API MBA
from api_mba.mba import api_mba_sql

# Models
from regulatorio_legal.models import (
    DocumentoLote, 
    DocumentoEnviado, 
    RegistroSanitario, 
    DocumentosLegales, 
    ProductosRegistroSanitario,
    IsosRegEnviados,
    FacturaProforma
    )

# Pandas
import pandas as pd

# Forms
from regulatorio_legal.forms import (
    DocumentoLoteForm, 
    NewDocumentoLoteForm, 
    DocumentoEnviadoForm,
    DocumentosLegalesForm,
    RegistroSanitarioForm
    )

# Utilities
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from etiquetado.views import correos_notificacion_factura

# Messages
from django.contrib import messages

# Json
import json

# Email
from django.core.mail import EmailMessage
from django.conf import settings
from smtplib import SMTPException 

# Login
from django.contrib.auth.decorators import login_required

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


def doc_importacion_por_codigo_ajax(request):

    codigo = request.POST.get('codigo')
    codigo_corp = codigo + '-GIMPR'
    
    try:        
        request = api_mba_sql("SELECT INVT_Lotes_Trasabilidad.DOC_ID_CORP, INVT_Lotes_Trasabilidad.ENTRADA_FECHA, "
            "INVT_Lotes_Trasabilidad.PRODUCT_ID_CORP, INVT_Lotes_Trasabilidad.LOTE_ID, INVT_Lotes_Trasabilidad.FECHA_CADUCIDAD, "
            "INVT_Lotes_Trasabilidad.AVAILABLE, INVT_Lotes_Trasabilidad.EGRESO_TEMP, INVT_Lotes_Trasabilidad.OH, INVT_Lotes_Trasabilidad.WARE_COD_CORP, CLNT_Pedidos_Principal.MEMO "
            "FROM INVT_Lotes_Trasabilidad INVT_Lotes_Trasabilidad "
            "LEFT JOIN CLNT_Pedidos_Principal ON INVT_Lotes_Trasabilidad.DOC_ID_CORP = CLNT_Pedidos_Principal.CONTRATO_ID_CORP "
            f"WHERE (INVT_Lotes_Trasabilidad.ENTRADA_TIPO='OC') AND (INVT_Lotes_Trasabilidad.PRODUCT_ID_CORP = '{codigo_corp}') AND (INVT_Lotes_Trasabilidad.Tipo_Movimiento='RP')"
        )
        
        status = request['status']
        
        if status == 200:
            
            data = request['data']
            
            data = pd.DataFrame(data).drop_duplicates(subset='DOC_ID_CORP').fillna('-').sort_values(by='ENTRADA_FECHA', ascending=False)
            
            data = data.rename(columns={
                'DOC_ID_CORP':'O.Compra',
                'ENTRADA_FECHA':'Fecha-Llegada',
                'PRODUCT_ID_CORP':'Código',
                'LOTE_ID':'Lote',
                'FECHA_CADUCIDAD':'Fecha-Caducidad',
                'AVAILABLE':'Unidades',
                'EGRESO_TEMP':'Egreso-Temporal',
                'OH':'OH',
                'WARE_COD_CORP':'Bodega',
                'MEMO':'Memo'
            })
            
            data['Código'] = data['Código'].str.replace('-GIMPR', '')
            data['Fecha-Llegada'] = data['Fecha-Llegada'].apply(lambda x: x[0:10])
            data['Fecha-Caducidad'] = data['Fecha-Caducidad'].apply(lambda x: x[0:10])
            data['Fecha-Llegada'] = pd.to_datetime(data['Fecha-Llegada'])
            data['Fecha-Caducidad'] = pd.to_datetime(data['Fecha-Caducidad'])
            
            data = data[['O.Compra','Memo','Fecha-Llegada','Código','Lote','Fecha-Caducidad','Unidades']]
            data = data.sort_values(by=['Fecha-Llegada'], ascending=False)
            
            html_tabla = data.to_html(
                float_format='{:,.0f}'.format,
                classes='table table-responsive table-bordered m-0 p-0',
                index=False,
                justify='start',
                na_rep=''
            )

            return JsonResponse({
                'msg_data':f'{len(data)} Importaciones encontradas',
                'data':html_tabla
            })
    
    except Exception as e:
        return JsonResponse({
            'msg_data':e,
        })



def importacion_list_detail(request, o_compra):

    doc_lot = DocumentoLote.objects.filter(o_compra=o_compra)
    
    imp = importaciones_llegadas_odbc().reset_index()
    imp = imp[imp['DOC_ID_CORP']==o_compra]
    
    imp = imp.sort_values(by=['product_id', 'FECHA_CADUCIDAD'])
    imp['doc'] = ''
    imp = imp[['product_id','LOTE_ID', 'FECHA_CADUCIDAD', 'doc','DOC_ID_CORP']]
    imp = imp.rename(columns={
        'LOTE_ID':'lote_id',
        'FECHA_CADUCIDAD':'f_caducidad',
        'DOC_ID_CORP':'o_compra'
    })
    
    imp_tuple = [tuple(i) for i in imp.values]
    
    doc_lot_df = pd.DataFrame(doc_lot.values())
    doc_lot_df['exist'] = 'si'
    
    if doc_lot_df.empty:
        # Guardar todos los valores
        with connections['default'].cursor() as cursor:
            cursor.executemany(
                "INSERT INTO regulatorio_legal_documentolote (product_id, lote_id, f_caducidad, documento, o_compra) VALUES (%s,%s,%s,%s,%s)", imp_tuple
            )

    elif len(doc_lot_df) < len(imp):
        # hacer un merge y guardar la diferencia
        imp_data = imp.merge(doc_lot_df, on=['o_compra','product_id', 'lote_id'], how='left').fillna(0)
        imp_data = imp_data[imp_data['exist']==0]
        imp_data = de_dataframe_a_template(imp_data)
        for i in imp_data:
            doc_lot = DocumentoLote(
                product_id = i['product_id'],
                lote_id = i['lote_id'],
                f_caducidad = i['f_caducidad_x'],
                documento = '',
                o_compra = i['o_compra']
            )
            
            doc_lot.save()
            
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


def venta_facturas_query(n_factura):
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(f"SELECT * FROM warehouse.venta_facturas WHERE CODIGO_FACTURA LIKE '%{n_factura}%'")
        columns = [col[0] for col in cursor.description]
        facturas = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
        
        facturas = pd.DataFrame(facturas)
        
        return facturas


def obtener_facturas():
    """Función para obtener y procesar las facturas de la base de datos ODBC."""
    facturas = facturas_odbc()[['CODIGO_FACTURA', 'FECHA_FACTURA', 'NOMBRE_CLIENTE']]
    facturas = facturas.drop_duplicates(subset='CODIGO_FACTURA')
    facturas['codigo_factura'] = facturas['CODIGO_FACTURA'].apply(lambda x: int(x.split('-')[1][4:]))
    facturas['FECHA_FACTURA'] = facturas['FECHA_FACTURA'].astype('str')
    return facturas.sort_values(by='codigo_factura', ascending=False)


def procesar_documentos_enviados(envios_documentos, facturas):
    """Función para procesar los documentos enviados y unirlos con las facturas."""
    if not envios_documentos.empty:
        envios_documentos['user'] = envios_documentos['usuario__first_name'] + ' ' + envios_documentos['usuario__last_name']
        envios_documentos = envios_documentos.rename(columns={'n_factura': 'CODIGO_FACTURA'})
        facturas = facturas.merge(envios_documentos, on='CODIGO_FACTURA', how='left')
        facturas['fecha_hora'] = pd.to_datetime(facturas['fecha_hora']).dt.strftime('%Y/%m/%d')
    return facturas


def lista_facturas(request):
    # Obtener las facturas y documentos enviados (si existen)
    facturas = obtener_facturas()
    envios_documentos = pd.DataFrame(DocumentoEnviado.objects.all().values('n_factura', 'usuario__first_name', 'usuario__last_name', 'fecha_hora'))
    facturas = procesar_documentos_enviados(envios_documentos, facturas)

    actualizacion = ultima_actualizacion('actulization_stoklote')

    if request.method == 'POST':
        # Manejo de la búsqueda de facturas
        n_factura = request.POST.get('n_factura', '').zfill(9)
        n_factura_completo = f'FCSRI-1001{n_factura}-GIMPR'

        facturas = obtener_facturas()
        facturas = facturas[facturas['CODIGO_FACTURA'] == n_factura_completo]

        # Procesar los documentos enviados asociados
        envios_documentos = pd.DataFrame(DocumentoEnviado.objects.filter(n_factura__icontains=n_factura_completo).values(
            'n_factura', 'usuario__first_name', 'usuario__last_name', 'fecha_hora'
        ))
        facturas = procesar_documentos_enviados(envios_documentos, facturas)

        # Consultar facturas adicionales y clientes desde otras fuentes
        query_facturas = venta_facturas_query(n_factura_completo)
        if not query_facturas.empty:
            query_facturas = query_facturas[['CODIGO_FACTURA', 'CODIGO_CLIENTE', 'FECHA']]
            cli = clientes_warehouse()[['CODIGO_CLIENTE', 'NOMBRE_CLIENTE']]
            query_facturas = query_facturas.merge(cli, on='CODIGO_CLIENTE', how='left').drop_duplicates(subset='CODIGO_FACTURA')
            query_facturas = query_facturas.rename(columns={'FECHA': 'FECHA_FACTURA'})
            query_facturas['codigo_factura'] = query_facturas['CODIGO_FACTURA'].apply(lambda x: x.split('-')[1])
            query_facturas['FECHA_FACTURA'] = query_facturas['FECHA_FACTURA'].astype('str')
        else:
            query_facturas = pd.DataFrame(columns=['CODIGO_FACTURA', 'CODIGO_CLIENTE', 'FECHA', 'NOMBRE_CLIENTE'])

        # Combinar y procesar todas las facturas y documentos
        facturas_list = pd.concat([facturas, query_facturas]).drop_duplicates(subset='CODIGO_FACTURA').fillna('-')
        if 'fecha_hora' in facturas_list.columns:
            facturas_list['fecha_hora'] = facturas_list['fecha_hora'].astype(str)

        facturas_list = de_dataframe_a_template(facturas_list)

        context = {
            'facturas': facturas_list,
            'len_facturas': len(facturas_list),
            'act': actualizacion
        }
        return render(request, 'regulatorio_legal/lista_facturas.html', context)

    context = {
        'facturas': de_dataframe_a_template(facturas),
        'act': actualizacion
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
    factura = factura.merge(docs, on=['PRODUCT_ID','lote_sp'], how='left').fillna(0)
    factura = factura.sort_values('PRODUCT_NAME')
    factura = factura.drop_duplicates(subset=['PRODUCT_ID','lote_sp'])
    factura['id'] = factura['id'].astype(int)  
    
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
        # who_send = User.objects.get(id=request.POST['usuario']).email
        
        if doc_len == prod_len:
            
            # Enviar correo
            try:
                
                n_archivos = 5
                n_correos = len(range(0, doc_len, n_archivos))
                
                archivos = [documentos[i:i+n_archivos] for i in range(0, doc_len, n_archivos)]
                
                correo_cliente = [request.POST['correo_cliente']]
                # correo_cliente.append(who_send)

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
                        to = correo_cliente,
                        bcc=['jgualotuna@gimpromed.com','ncaisapanta@gimpromed.com','dtrujillo@gimpromed.com'],
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
                            to = correo_cliente,
                            bcc=['jgualotuna@gimpromed.com','ncaisapanta@gimpromed.com','dtrujillo@gimpromed.com'],
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


import requests
def prueba_api_marca_agua(request):
    # Obtener el documento desde la base de datos
    doc = DocumentoLote.objects.get(id=5304).documento.path
    
    print(f"Documento a enviar: {doc}")
    
    url_api = 'https://www.gimpromed.com/app/api/procesarPdf'
    
    # Cargar el archivo y los datos que se enviarán
    with open(doc, 'rb') as pdf_file:
        # Definir el payload con datos adicionales
        data = {
            'texto': """
GIMPROMED CIA. LTDA.
AUTORIZA EL USO DE
ESTE DOCUMENTO A:
COMERCIALIZADORA Y
CONSULTORA DE IMPLEMENTOS MAYKCARS S.A
PARA PARTICIPAR EN EL:
PROCESO No.
SIE-HTMC-2023-202
HOSPITAL DE ESPECIALIDADES
TEODORO MALDONADO CARBO DISTRITNAL DE NUMERO 1
USO VALIDO HASTA:
MARZO 2024
""",
            'espacio': '100'
        }
        
        # Enviar el archivo PDF y los datos adicionales a la API externa
        files = {
            'pdf': pdf_file  # Aquí 'pdf' es el nombre del campo que la API espera
        }
        
        try:
            r = requests.post(url_api, data=data, files=files)
            
            # Verificar si la solicitud fue exitosa
            if r.status_code == 200:
                # Imprimir la respuesta o la URL de descarga si la API lo proporciona
                print(f"Respuesta de la API: {r.text}")
                try:
                    response_json = r.json()  # Intentar convertir la respuesta a JSON
                    url_descarga = response_json.get('url_descarga', 'URL no disponible')
                    
                    # Retornar un mensaje o redirigir al usuario a la URL de descarga
                    return HttpResponse(f"El archivo fue procesado exitosamente. Descarga aquí: {url_descarga}")
                except ValueError:
                    # Si la respuesta no es JSON, retornar el texto de la respuesta
                    return HttpResponse(f"Respuesta de la API: {r.text}")
            else:
                # Si hubo un error con la solicitud
                return HttpResponse(f"Error al procesar el archivo. Código de estado: {r.status_code}")
        
        except requests.exceptions.RequestException as e:
            # Manejar cualquier excepción de la solicitud
            return HttpResponse(f"Error al conectarse a la API: {str(e)}")


@login_required(login_url='login')
def documentos_legales_list_marcas(request):
    
    documentos = DocumentosLegales.objects.all()
    
    if documentos.exists():
    
        estados = pd.DataFrame([{'estado':i.estado, 'marca':i.marca} for i in documentos])
        query_df = pd.DataFrame(documentos.values(
            'id', 'marca', 'nombre_proveedor', 'documento', 'fecha_caducidad', 'usuario__first_name', 'usuario__last_name'
        ))
        query_df['fecha_caducidad'] = query_df['fecha_caducidad'].astype('str')
        
        marcas_doc = []
        marcas_count = []
        for i in documentos:
            reg_san = i.registros_sanitarios.all()
            for j in reg_san:
                productos = len(j.productos.all())
                
                marcas_doc.append(i.marca)
                marcas_count.append(productos)
        
        productos_por_marca_docs = pd.DataFrame({
            'marca': [i for i in marcas_doc],
            'documentos_agregados': [i for i in marcas_count]
        })

        productos_por_marca_total = productos_odbc_and_django()[['product_id','Marca']]
        productos_por_marca_total = productos_por_marca_total.rename(columns={'Marca':'marca','product_id':'total_productos'})
        productos_por_marca_total = productos_por_marca_total.groupby(by='marca').count().reset_index()
        
        if not productos_por_marca_docs.empty:
            productos_por_marca_final = productos_por_marca_docs.merge(query_df, on='marca', how='left')
            productos_por_marca_final = productos_por_marca_final.merge(estados, on='marca', how='left')
        else:
            productos_por_marca_final = query_df

        productos_por_marca_final = productos_por_marca_final.groupby(by=[
            'id','marca','nombre_proveedor','documento','fecha_caducidad','usuario__first_name','usuario__last_name','estado'
        ]).sum().reset_index().sort_values(by='marca')
        
        if not productos_por_marca_final.empty:
            productos_por_marca_final = productos_por_marca_final.merge(productos_por_marca_total, on='marca', how='left')
            productos_por_marca_final['porcentaje'] = (productos_por_marca_final['documentos_agregados'] / productos_por_marca_final['total_productos'] * 100)
            productos_por_marca_final = de_dataframe_a_template(productos_por_marca_final)
    
    else:
        productos_por_marca_final = pd.DataFrame()
    
    marcas = productos_odbc_and_django()
    marcas = list(marcas['Marca'].unique())
    
    form = DocumentosLegalesForm()
    
    if request.method == 'POST':
        form = DocumentosLegalesForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save()
            return HttpResponseRedirect(f'/regulatorio-legal/documentos-legales-detail-marca/{doc.id}')
            
        else:
            messages.error(request, form.errors)
            return HttpResponseRedirect(f'/regulatorio-legal/documentos-legales-list-marcas')
        
    
    context = {
        'documentos': productos_por_marca_final,
        'marcas': marcas,
        'form': form
    }
    
    return render(request, 'regulatorio_legal/documentos_legales_list_marcas.html', context)


def documentos_legales_detail_marca(request, id):
    
    documento = DocumentosLegales.objects.get(id=id)

    # PROCESAR LISTA DE PRODUCTOS
    productos_list = productos_odbc_and_django()[['product_id','Nombre','Marca']]
    productos_list = productos_list[productos_list['Marca']==documento.marca]
    productos = set(productos_list['product_id'].unique())
    
    # FILTRAR POR PRODUCTOS YA OCUPADOS DE ESA MARCA
    productos_reg_san = set(ProductosRegistroSanitario.objects.all().values_list('product_id', flat=True))
    
    # LISTADO DE PRODUCTOS PARA SELECCIONAR
    # NUEVOS REG SANITARIO
    productos_list_select = pd.DataFrame(productos.difference(productos_reg_san), columns=['product_id'])
    productos_list_select = sorted(
        de_dataframe_a_template(productos_list_select.merge(productos_list, on='product_id', how='left')),
        key= lambda x: x['product_id']
        )
    
    
    if request.method == 'POST':

        productos_list_post = request.POST.getlist('productos')
        
        form = RegistroSanitarioForm(request.POST, request.FILES)
        
        if form.is_valid():
            reg = form.save()                        
            for i in productos_list_post:
                prod = ProductosRegistroSanitario.objects.create(product_id=i)
                reg.productos.add(prod)
                documento.registros_sanitarios.add(reg)
                
            messages.success(request, f'Registro sanitario añadido exitosamente !!!')
        else:
            messages.error(request, form.errors)
    
    context  = {
        'documento': documento,
        'productos_list_select':productos_list_select, 
    }
    
    return render(request, 'regulatorio_legal/documentos_legales_detail_marca.html', context)


def documento_legal_editar_marca(request, id):
    
    documento = DocumentosLegales.objects.get(id=id)
    if request.method == 'GET':
        form = DocumentosLegalesForm(instance=documento)
        return HttpResponse(form.as_p())
    
    if request.method == 'POST':
        form = DocumentosLegalesForm(request.POST, request.FILES, instance=documento)
        if form.is_valid():
            form.save()
            messages.success(request, 'Documento legal actualizado exitosamente !!!')
            return HttpResponseRedirect(f'/regulatorio-legal/documentos-legales-detail-marca/{documento.id}')
        else:
            messages.error(request, form.errors)
            return HttpResponseRedirect(f'/regulatorio-legal/documentos-legales-detail-marca/{documento.id}') 


def documento_legal_editar_detail(request):    
    
    if request.method == 'GET':
        reg_id = int(request.GET.get('reg_id'))
        reg_sanitario = RegistroSanitario.objects.get(id=reg_id)
        form = RegistroSanitarioForm(instance=reg_sanitario)
        documento = reg_sanitario.documentoslegales_set.all().first()
        
        productos_todos = productos_odbc_and_django()[['product_id','Nombre','Marca']]
        productos_todos = productos_todos[productos_todos['Marca']==documento.marca]
        
        productos_registro_sanitario = pd.DataFrame(reg_sanitario.productos.values())
        if not productos_registro_sanitario.empty:
            productos_registro_sanitario['checked'] = 'checked'
            productos = productos_todos.merge(productos_registro_sanitario, on='product_id', how='left')
            productos = sorted(de_dataframe_a_template(productos), key=lambda x: x['product_id'])

        else:
            productos = productos_todos
            productos = sorted(de_dataframe_a_template(productos), key=lambda x: x['product_id'])
        
        return JsonResponse({
            'form': form.as_p(),
            'productos_list':productos
        })
    
    elif request.method == 'POST':
        
        reg_id = int(request.POST.get('reg_id'))
        reg_sanitario = RegistroSanitario.objects.get(id=reg_id)
        form = RegistroSanitarioForm(request.POST, request.FILES, instance=reg_sanitario)
        documento = reg_sanitario.documentoslegales_set.all().first()
        
        try:
            
            # Eliminar todos los productos
            reg_sanitario.productos.all().delete()
            
            # Actualizar productos
            reg_sanitario.productos.clear()
            
            # Agregar los productos
            for i in request.POST.getlist('productos'):
                prod = ProductosRegistroSanitario.objects.create(product_id=i)
                reg_sanitario.productos.add(prod)
            
            if form.is_valid():
                form.save()
                messages.success(request, 'Registro sanitario actualizado exitosamente !!!')
                return HttpResponseRedirect(f'/regulatorio-legal/documentos-legales-detail-marca/{documento.id}')
            else:
                messages.error(request, form.errors)
                return HttpResponseRedirect(f'/regulatorio-legal/documentos-legales-detail-marca/{documento.id}')
        except Exception as e:
            messages.error(request, str(e))
            return HttpResponseRedirect(f'/regulatorio-legal/documentos-legales-detail-marca/{documento.id}')
        
        
        
### ENVIO DE ISOS Y REGISTROS CON MARCA DE AGUA
def data_factura_proforma_warehouse(tipo_comprobante, n_comprobante):
    
    if tipo_comprobante == 'factura':
        
        # ARMAR FACTURA
        n_comprobante   = 'FCSRI-1001' + f'{int(n_comprobante):09d}' + '-GIMPR'
        
        with connections['gimpromed_sql'].cursor() as cursor:
            cursor.execute(f"SELECT * FROM facturas WHERE CODIGO_FACTURA = '{n_comprobante}'")
            columns = [col[0] for col in cursor.description]
            data = [dict(zip(columns, row)) for row in cursor.fetchall()]
            data = pd.DataFrame(data)
            
            data = data.rename(columns={'PRODUCT_ID':'product_id','QUANTITY':'quantity'})
            data = data.merge(clientes_warehouse()[['CODIGO_CLIENTE','NOMBRE_CLIENTE']], on='NOMBRE_CLIENTE', how='left')
            detalle = str(data[['product_id','quantity']].to_dict('records'))
            
            return {
                'detalle':detalle,
                'codigo_cliente':data['CODIGO_CLIENTE'].unique()[0],
                'nombre_cliente':data['NOMBRE_CLIENTE'].unique()[0],                
            }

        
    elif tipo_comprobante == 'proforma':
        with connections['gimpromed_sql'].cursor() as cursor:
            cursor.execute(f"SELECT * FROM proformas WHERE contrato_id = '{n_comprobante}'")
            columns = [col[0] for col in cursor.description]
            data = [dict(zip(columns, row)) for row in cursor.fetchall()]
            data = pd.DataFrame(data)
            
            data = data.rename(columns={'nombre_cliente':'NOMBRE_CLIENTE'})
            data = data.merge(clientes_warehouse()[['CODIGO_CLIENTE','NOMBRE_CLIENTE']], on='NOMBRE_CLIENTE', how='left')
            detalle = str(data[['product_id','quantity']].to_dict('records'))
            
            return {
                'detalle':detalle,
                'codigo_cliente':data['CODIGO_CLIENTE'].unique()[0],
                'nombre_cliente':data['NOMBRE_CLIENTE'].unique()[0],
            }




def facturas_proformas_list(request):
    
    if request.method == 'GET':
    
        factura_proforma_list = FacturaProforma.objects.all().order_by('-id')
        
    elif request.method == 'POST':
        
        tipo_comprobante = request.POST.get('tipo_comprobante') #'proforma'
        n_comprobante = request.POST.get('n_comprobante') #'45692'

        data = data_factura_proforma_warehouse(tipo_comprobante, n_comprobante)
        
        try:
        
            factura_proforma = FacturaProforma.objects.create(
                tipo_comprobante = tipo_comprobante,
                n_comprobante = n_comprobante,
                detalle = data['detalle'],
                codigo_cliente = data['codigo_cliente'],
                nombre_cliente = data['nombre_cliente'],
                usuario_id = request.user.id,
            )
            
            if factura_proforma:
                pass
                #redirect
            else:
                return JsonResponse({
                    'alert':'danger',
                    'msg': f'Error al añadir {tipo_comprobante} con número {n_comprobante}',
            })
                
        except Exception as e:
            return JsonResponse({
                    'alert':'danger',
                    'msg': f'Error ("{e}")',
            })
        
    context = {
        'factura_proforma_list': factura_proforma_list,
    }
    
    return render(request, 'regulatorio_legal/lista_facturas_proformas.html', context)


def facturas_proformas_detalle(request, id):
    
    if request.method == 'GET':
        factura_proforma = FacturaProforma.objects.get(id=id)
        detalle = json.loads(factura_proforma.detalle.replace("'", '"'))
        detalle = pd.DataFrame(detalle)
        detalle = detalle.groupby(by='product_id').sum().reset_index()
        detalle = detalle.merge(productos_odbc_and_django()[['product_id','Nombre','Marca']])
        
        # ISOS
        marcas = detalle['Marca'].unique()
        isos_query =  DocumentosLegales.objects.filter(marca__in = list(marcas))        
        doc_isos = pd.DataFrame(isos_query.values('id','marca','nombre_proveedor','documento'))
        
        doc_isos_estados = pd.DataFrame([{'id':i.id, 'estado':i.estado} for i in isos_query])
        doc_isos = doc_isos.merge(doc_isos_estados, on='id', how='left')
        isos = pd.DataFrame(marcas, columns=['marca']).merge(doc_isos, on='marca', how='left').fillna('')
        
        # REGISTROS SANITARIOS
        productos = detalle['product_id'].unique()        
        registros_sanitarios = RegistroSanitario.objects.filter(productos__product_id__in = list(productos)).distinct()
        
        context = {
            'factura_proforma': factura_proforma,
            'detalle':de_dataframe_a_template(detalle),
            'isos':de_dataframe_a_template(isos),
            'registros_sanitarios':registros_sanitarios
        }
        return render(request, 'regulatorio_legal/detalle_factura_proforma.html', context)