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
from django_xhtml2pdf.utils import pdf_decorator, generate_pdf

# Login
from django.contrib.auth.decorators import login_required, permission_required

# Templeate loader
from django.template.loader import get_template, render_to_string
from django.template import Context

# Html
from django.utils.html import strip_tags

# MUESTREOS
# Función Ronald - actualizar tabla transito importaciones
# def actualizar_importaciones_transito():
import pyodbc
import mysql.connector


# Tabla Registro Sanitario
from bpa.models import RegistroSanitario, CartaNoRegistro, ImportacionesExcel

# Forms
from bpa.forms import RegistroSanitarioForm, CartaNoRegistroForm, ImportacionExcelForm

# Messages
from django.contrib import messages

# Url
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse

# TRANSFERENCIA ODBC
from datos.views import doc_transferencia_odbc, importaciones_llegadas_odbc, productos_odbc_and_django

# de dataframe to template
from compras_publicas.views import de_dataframe_a_template



# Conuslta tabla de importaciones en transito
def odbc(mydb):
# def actualizar_importaciones_transito(mydb):
    # Using a DSN, but providing a password as well
    cnxn = pyodbc.connect('DSN=mba3;PWD=API')
    # Create a cursor from the connection
    cursorOdbc = cnxn.cursor()
    ####Cstock_lotes_ mba3O######
    print ("odbc_execute")

    #####Connect to MYSQL Database#####
    mycursorMysql = mydb.cursor()


    ##Imp Transito
    cursorOdbc.execute(
        "SELECT PROV_Ficha_Principal.VENDOR_NAME, CLNT_Pedidos_Detalle.PRODUCT_ID, CLNT_Pedidos_Detalle.QUANTITY, CLNT_Pedidos_Principal.FECHA_ENTREGA, CLNT_Pedidos_Principal.MEMO "
        "FROM CLNT_Pedidos_Detalle CLNT_Pedidos_Detalle, CLNT_Pedidos_Principal CLNT_Pedidos_Principal, PROV_Ficha_Principal PROV_Ficha_Principal "
        "WHERE CLNT_Pedidos_Detalle.CONTRATO_ID_CORP = CLNT_Pedidos_Principal.CONTRATO_ID_CORP AND CLNT_Pedidos_Principal.CLIENT_ID_CORP = PROV_Ficha_Principal.CODIGO_PROVEEDOR_EMPRESA "
        "AND ((CLNT_Pedidos_Principal.FECHA_PEDIDO>'01-01-2021') AND (CLNT_Pedidos_Principal.PEDIDO_CERRADO=false) AND (CLNT_Pedidos_Detalle.EN_ORDEN=0) "
        "AND (CLNT_Pedidos_Principal.CONFIRMED=false))"
    )
    transito = cursorOdbc.fetchall()
    transito = [list(rows) for rows in transito]
    #print(transito)

    delete_sql = "DELETE FROM imp_transito"
    mycursorMysql.execute(delete_sql)
    mydb.commit()
    print("Sucessful Deleted importaciones en transito")

    sql_insert = """INSERT INTO imp_transito (VENDOR_NAME,PRODUCT_ID,QUANTITY,FECHA_ENTREGA,MEMO) VALUES (%s, %s, %s, %s, %s)"""
    data_transito = [list(rows) for rows in transito]
    mycursorMysql.executemany(sql_insert, data_transito)

    print("Sucessful importaciones en transito")
    mydb.commit()


def main_importaciones():
    mydb = mysql.connector.connect(
            host="172.16.28.102",
            user="standard",
            passwd="gimpromed",
            database="warehouse"
        )
    odbc(mydb)


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

        # r_s =[]

        # for i in prod['Reg_San'].to_list():
        #     for j in i:
        #         if j.find(':'):
        #             x =+ 1
        #             p = i[x::]
        #             r_s.append(p)

        # print(r_s)

    return prod


# Consulta tabla de importaciones transito
def importaciones_transito(): #request
    ''' Colusta de clientes por ruc a la base de datos '''
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute("SELECT * FROM imp_transito")
        columns = [col[0] for col in cursor.description]
        importaciones = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
        
        importaciones = pd.DataFrame(importaciones)
        
        pro = pd.DataFrame(Product.objects.all().values())
        pro = pro[['product_id', 'description','unidad_empaque']]
        pro = pro.rename(columns={'product_id':'PRODUCT_ID'})

        imp = importaciones.merge(pro, on='PRODUCT_ID')
        imp['CARTONES'] = (imp['QUANTITY']/imp['unidad_empaque']).round(0)
        
    return imp


# Muestreos Importaciones
@login_required(login_url='login')
def importaciones(request):

    imp = importaciones_transito()
    
    actualizado = pd.DataFrame(TimeStamp.objects.all().values())
    actualizado = list(actualizado['actulization_importaciones'])
    act = []
    for i in actualizado:
        if i != '':
            act.append(i)

    actualizado = act[-1]

    imp = imp.drop_duplicates(subset='MEMO')
    imp['FECHA_ENTREGA'] = pd.to_datetime(imp['FECHA_ENTREGA'])
    imp['FECHA_ENTREGA'] = imp['FECHA_ENTREGA'].astype(str)
    imp = imp.sort_values(by='FECHA_ENTREGA', ascending=False);print(imp)
    json_records = imp.reset_index().to_json(orient='records')
    imp = json.loads(json_records)

    context = {
        'imp':imp,
        'actualizado':actualizado
    }

    if request.method == 'POST':
        main_importaciones()
        
        actualizado = str(datetime.now())
        TimeStamp.objects.create(actulization_importaciones=actualizado)

        context = {
            'imp':imp,
            'actualizado':actualizado
        }

    return render(request, 'bpa/muestreos/lista_importaciones.html', context)


def nacionales_odbc():
    nacionales_list = ['SARALEJ','NILOTEX','NACIONAL','ATRAS','CARICIA']
    nac = importaciones_llegadas_odbc()
    prod = productos_odbc_and_django()[['product_id','description','marca2','unidad_empaque']] #'unidad_empaque'
    
    nac = nac.merge(prod, on='product_id', how='left')
    nac = nac[nac.marca2.isin(nacionales_list)]
    nac = nac.pivot_table(index=['product_id','description','marca2','ENTRADA_FECHA','DOC_ID_CORP'], values=['OH'], aggfunc='sum').reset_index()

    nac['ENTRADA_FECHA'] = pd.to_datetime(nac['ENTRADA_FECHA'])
    nac = nac.sort_values(by='ENTRADA_FECHA', ascending=False)
    nac['ENTRADA_FECHA'] = nac['ENTRADA_FECHA'].astype(str)


    nac = nac.rename(columns={
        'marca2':'VENDOR_NAME',
        'product_id':'PRODUCT_ID',
        'OH':'QUANTITY',
        'ENTRADA_FECHA':'FECHA_ENTREGA',
        'DOC_ID_CORP':'MEMO',

    })

    return nac



def nacionales(request):
    
    nac = nacionales_odbc()
    nac = nac.drop_duplicates(subset=['MEMO'])
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

    n = nacionales_odbc()
    data = importaciones_transito()

    data = pd.concat([data, n])

    data = data[data['MEMO']==memo]

    imp = muestreo(data, 'QUANTITY')
    imp = imp.sort_values(by='PRODUCT_ID')

    proveedor = imp['VENDOR_NAME'].iloc[0]
    n_imp = imp['MEMO'].iloc[0]
    
    json_records = imp.reset_index().to_json(orient='records')
    imp = json.loads(json_records)

    context = {
        'imp':imp,

        'proveedor':proveedor,
        'n_imp':n_imp,
    }

    return render(request, 'bpa/muestreos/muestreo_imp_unidades.html', context)


@pdf_decorator(pdfname='muestreo_importacion_cartones.pdf')
@login_required(login_url='login')
def muestreo_cartones(request, memo):

    data = importaciones_transito()
    data = data[data['MEMO']==memo]   
    
    imp = muestreo(data, 'CARTONES')
    imp = imp.sort_values(by='PRODUCT_ID')

    proveedor = imp['VENDOR_NAME'].iloc[0]
    n_imp = imp['MEMO'].iloc[0]
    
    json_records = imp.reset_index().to_json(orient='records')
    imp = json.loads(json_records)
    
    context = {
        'imp':imp,

        'proveedor':proveedor,
        'n_imp':n_imp,
    }

    return render(request, 'bpa/muestreos/muestreo_imp_cartones.html', context)


@pdf_decorator(pdfname='revision_tecnica.pdf')
@login_required(login_url='login')
def revision_tecnica(request, memo):

    n = nacionales_odbc()
    data = importaciones_transito()
    data = pd.concat([data,n])

    data = data[data['MEMO']==memo]   
    prod = productos()
    prod = prod.rename(columns={'product_id':'PRODUCT_ID'})
    prod_2 = pd.DataFrame(Product.objects.all().values())
    prod_2 = prod_2.rename(columns={'product_id':'PRODUCT_ID'})
    prod_2 = prod_2[['PRODUCT_ID', 'emp_primario', 'emp_secundario', 'emp_terciario']]

    imp = muestreo(data, 'CARTONES')
    imp = imp.merge(prod, on='PRODUCT_ID', how='left')
    imp = imp.merge(prod_2, on='PRODUCT_ID', how='left')
    imp = imp.sort_values(by='PRODUCT_ID')
    
    proveedor = imp['VENDOR_NAME'].iloc[0]
    n_imp = imp['MEMO'].iloc[0]
    fecha = imp['FECHA_ENTREGA'].iloc[0]
    json_records = imp.reset_index().to_json(orient='records')
    imp = json.loads(json_records)
    
    context = {
        'imp':imp,

        'proveedor':proveedor,
        'n_imp':n_imp,
        'fecha':fecha,
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
        # doc_transferencia_odbc(n)
        #print(doc_transferencia_odbc(n))

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



# @login_required(login_url='login')
# def doc_transferencia(request):   
#     if request.method == 'POST':
#         n = request.POST.get('n_transf')
#         transf = doc_transferencia_odbc(n)
#         documento = transf['doc'][0][7:-6]
#         transf = transf.groupby(['product_id', 'doc']).sum()
#         m = muestreo(transf, 'unidades')
#         m = m.merge(productos(), on='product_id', how='left')
#         m = m.rename(columns={
#             'Nombre':'description'
#         })

#         m = de_dataframe_a_template(m)

#         context = {
#             'muestreo':m,
#             'documento':documento
#         }
        
#         resp = HttpResponse(content_type='application/pdf')
#         result = generate_pdf('bpa/muestreos/muestreo_transferencias.html', file_object=resp, context=context)
#         return result
    
#     return render(request, 'bpa/muestreos/doc_transf.html')




@pdf_decorator(pdfname='muestreo_transferencia.pdf')
@login_required(login_url='login')
def muestreo_transferencia(request, doc):

    trans = pd.DataFrame(Trasferencia.objects.all().values())
    prod  = pd.DataFrame(Product.objects.all().values())
    prod  = prod[['product_id', 'description']]
    
    trans = trans.groupby(['product_id', 'documento']).sum()
    trans = trans.reset_index()

    trans = trans[trans['documento']==doc]
    docum = trans['documento'].iloc[0]

    muest = muestreo(trans, 'unidades')
    muest = muest.merge(prod, on='product_id', how='left')

    json_records = muest.reset_index().to_json(orient='records') 
    muest = json.loads(json_records)

    context = {
        'documento':docum,
        'muestreo':muest
    }

    return render(request, 'bpa/muestreos/muestreo_transferencias.html', context)


@pdf_decorator(pdfname='muestreo_transferencia.pdf')
@login_required(login_url='login')
def revision_tecnica_transferencia(request, doc):
    trans = pd.DataFrame(Trasferencia.objects.all().values())
    prod = productos()
    prod_2 = pd.DataFrame(Product.objects.all().values())
    prod_2 = prod_2[['product_id', 'emp_primario', 'emp_secundario', 'emp_terciario']]

    trans = trans.groupby(['product_id', 'documento']).sum()
    trans = trans.reset_index()

    trans = trans[trans['documento']==doc]
    docum = trans['documento'].iloc[0]

    muest = muestreo(trans, 'unidades')
    muest = muest.merge(prod, on='product_id', how='left')
    muest = muest.merge(prod_2, on='product_id', how='left')
    
    json_records = muest.reset_index().to_json(orient='records') 
    muest = json.loads(json_records)

    context = {
        'documento':docum,
        'muestreo':muest
    }

    return render(request, 'bpa/muestreos/revision_tecnica_transferencias.html', context)


# Lista de registros sanitarios
@login_required(login_url='login')
def reg_san_list(request):
    
    r_san_list = RegistroSanitario.objects.all().order_by('marca', 'fecha_expiracion')
    r_san_list_2 = RegistroSanitario.objects.all().order_by('fecha_expiracion')
    
    n_docs = len([i for i in RegistroSanitario.objects.all() if i.obs_doc == 'Docs ok'])    
    n_enviar = len([i for i in RegistroSanitario.objects.all() if i.obs_doc == 'Enviar a notaria'])   
    n_caducado = len([i for i in RegistroSanitario.objects.all() if i.estado == 'Caducado'])
    n_proximo = len([i for i in RegistroSanitario.objects.all() if i.estado == 'Próximo a caducar'])
    n_vigente = len([i for i in RegistroSanitario.objects.all() if i.estado == 'Vigente'])
    n_sin = len([i for i in RegistroSanitario.objects.all() if i.estado == 'Sin especificar' ])

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


# Envio de alertas de Caducidad de R.Sanitario por EMAIL.
def r_san_alerta_list_correo(request):
    
    tabla_query = RegistroSanitario.objects.filter(activo=True).order_by('fecha_expiracion')
    rs_list = [i for i in tabla_query if i.estado == 'Próximo a caducar']
    
    context = {
        'lista':rs_list
    }
    
    html_message  = render_to_string('emails/r_san_list.html', context)
    plain_message = strip_tags(html_message)
    
    email = EmailMultiAlternatives(
        subject    = 'Alerta - Documentos próximos a caducar.',
        from_email = settings.EMAIL_HOST_USER,
        to         = ['ronaldm@gimpromed.com','pespinosa@gimpromed.com','ncaisapanta@gimpromed.com'],
        body       = plain_message,
    )
    
    email.attach_alternative(html_message, 'text/html')
    email.send()
                    
    return HttpResponse(status=200)
        

# Enviar correos individuales por registro sanitario
def r_san_alert(request):
    
    tabla_query = RegistroSanitario.objects.filter(activo=True).order_by('fecha_expiracion')
    
    # Avisos
    a1=120
    a2=100
    a3=90
    a4=40
    
    ### PARA MEJORAR EFICIENCIA APLICAR BUSQUEDA BINARIA
    for i in tabla_query:
        if i.dias_caducar == a1:  
            # 1er Aviso
            rs_list = [i for i in tabla_query if i.dias_caducar==a1]
            context = {'lista':rs_list}
            
            html_message  = render_to_string('emails/r_san.html', context)
            plain_message = strip_tags(html_message)
            
            email = EmailMultiAlternatives(
                subject    = f'1er Aviso Próximo a Caducar - {i.registro} - {i.marca} - ({i.dias_caducar} días)',
                from_email = settings.EMAIL_HOST_USER,
                to         = ['pespinosa@gimpromed.com', 'ncaisapanta@gimpromed.com'],
                body       = plain_message,
            )
            
            email.attach_alternative(html_message, 'text/html')
            email.send()
            
        elif i.dias_caducar == a2:  
            # 2do Aviso
            rs_list = [i for i in tabla_query if i.dias_caducar==a2]
            context = {'lista':rs_list}
            
            html_message  = render_to_string('emails/r_san.html', context)
            plain_message = strip_tags(html_message)
            
            email = EmailMultiAlternatives(
                subject    = f'2do Aviso Próximo a Caducar - {i.registro} - {i.marca} - ({i.dias_caducar} días)',
                from_email = settings.EMAIL_HOST_USER,
                to         = ['pespinosa@gimpromed.com', 'ncaisapanta@gimpromed.com'],
                body       = plain_message,
            )
            
            email.attach_alternative(html_message, 'text/html')
            email.send()
            
        elif i.dias_caducar == a3:  
            # 3er Aviso
            rs_list = [i for i in tabla_query if i.dias_caducar==a3]
            context = {'lista':rs_list}
            
            html_message  = render_to_string('emails/r_san.html', context)
            plain_message = strip_tags(html_message)
            
            email = EmailMultiAlternatives(
                subject    = f'3er Aviso Próximo a Caducar - {i.registro} - {i.marca} - ({i.dias_caducar} días)',
                from_email = settings.EMAIL_HOST_USER,
                to         = ['pespinosa@gimpromed.com', 'ncaisapanta@gimpromed.com'],
                body       = plain_message,
            )
            
            email.attach_alternative(html_message, 'text/html')
            email.send()
            
        elif i.dias_caducar == a4: 
            # 4to Aviso
            rs_list = [i for i in tabla_query if i.dias_caducar==a4]
            context = {'lista':rs_list}
            
            html_message  = render_to_string('emails/r_san.html', context)
            plain_message = strip_tags(html_message)
            
            email = EmailMultiAlternatives(
                subject    = f'4to Aviso Próximo a Caducar - {i.registro} - {i.marca} - ({i.dias_caducar} días)',
                from_email = settings.EMAIL_HOST_USER,
                to         = ['ronaldm@gimpromed.com','pespinosa@gimpromed.com','ncaisapanta@gimpromed.com'],
                body       = plain_message,
            )
            
            email.attach_alternative(html_message, 'text/html')
            email.send()
            
    return HttpResponse(status=200)



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





### IMPORTACIONES EXCEL
def importacion_list(request):
    imp = ImportacionesExcel.objects.all()
    context = {
        'imp':imp
    }

    return render(request, 'bpa/imp_excel/imp_list.html', context)

def importacion_create(request):
    form = ImportacionExcelForm()

    if request.method == 'POST':
        form = ImportacionExcelForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('carta_no_reg_list')
        else:
            print(form.errors)
            messages.error(request, 'Error al cargar el archivo')
        
    context = {
        'form':form
    }

    return render(request, 'bpa/imp_excel/imp_create.html', context)

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

def importacion_detail(request, id):

    imp = ImportacionesExcel.objects.get(id=id)
    imp = 'media/' + str(imp)
    imp = pd.read_excel(imp)

    imp = imp.rename(columns={'CÓDIGO DE ITEM':'PRODUCT_ID'})
    imp['PRODUCT_ID'] = imp['PRODUCT_ID'].astype(str)

    r_lote = reservas_lote()

    ing = imp.merge(r_lote, on='PRODUCT_ID', how='left')
    ing = ing.dropna()
    

    res = imp.merge(r_lote, on='PRODUCT_ID', how='left')

