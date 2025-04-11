from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# Models
from datos.models import EmailApiLog

# Email
from django.core.mail import EmailMultiAlternatives

# Tabla Registro Sanitario
from bpa.models import RegistroSanitario

# Html
from django.utils.html import strip_tags

# Templeate loader
from django.template.loader import render_to_string

# Settings
from django.conf import settings

from django.db import connections


# APIS

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reg_sanitario_correo_alerta_list(request):
    
    try:
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
        
        EmailApiLog.objects.create(
            nombre='Email proximos a vencer en 180 días',
            description = ' - '.join([str(i) for i in rs_list]),
            error = 'N/A',
            enviado = True
        )
        
        return Response(status=200)
    
    except Exception as e:
        
        EmailApiLog.objects.create(
            nombre='Email proximos a vencer en 180 días',
            description = ' - '.join([str(i) for i in rs_list]),
            error = str(e),
            enviado = True
        )
        return Response(status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reg_sanitario_correo_alerta_dias(request):
    try:
        # Inicializa las variables
        text_log = ''
        rs_list = []

        # Obtener datos de la base de datos
        tabla_query = RegistroSanitario.objects.filter(activo=True).order_by('fecha_expiracion')

        # Avisos
        avisos = {
            120: '1er Aviso',
            100: '2do Aviso',
            90: '3er Aviso',
            40: '4to Aviso'
        }
        
        
        # Lista de correos
        lista_correos = ['pespinosa@gimpromed.com', 'ncaisapanta@gimpromed.com']
        
        for aviso_dias, aviso_nombre in avisos.items():
            rs_list = [i for i in tabla_query if i.dias_caducar == aviso_dias]
            if rs_list:
                context = {'lista': rs_list}
                html_message = render_to_string('emails/r_san.html', context)
                plain_message = strip_tags(html_message)
                
                if aviso_dias == 40:
                    destinatarios = lista_correos + ['ronaldm@gimpromed.com']
                else:
                    destinatarios = lista_correos
                
                email = EmailMultiAlternatives(
                    subject=f'{aviso_nombre} Próximo a Caducar - {rs_list[0].registro} - {rs_list[0].marca} - ({aviso_dias} días)',
                    from_email=settings.EMAIL_HOST_USER,
                    to=destinatarios,
                    body=plain_message,
                )
                
                email.attach_alternative(html_message, 'text/html')
                email.send()
                
                text_log = f'{aviso_nombre}: {aviso_dias} dias'

                EmailApiLog.objects.create(
                    nombre=f'Email {text_log}',
                    description=' - '.join([str(i) for i in rs_list]),
                    error='N/A',
                    enviado=True
                )
        
        return Response(status=200)

    except Exception as e:
        EmailApiLog.objects.create(
            nombre=f'Email {text_log}',
            description=' - '.join([str(i) for i in rs_list]),
            error=str(e),
            enviado=False
        )
        return Response(status=500)



#### API PRECIOS
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def precio_promocion(request, product_id):
        
    with connections['gimpromed_sql'].cursor() as cursor:
        
        cursor.execute(f"SELECT * FROM precios.promociones WHERE Ref = '{product_id}'")
        columns = [col[0] for col in cursor.description]
        promocion = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ] 
        
        return Response(promocion, status=200)


#### API PRECIOS
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def infimas_general(request, codigo):
    
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(f"SELECT * FROM procesos_sercop.infimas_general WHERE Codigo = '{codigo}'")
        columns = [col[0] for col in cursor.description]
        infimas = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ] 
        
        return Response(infimas, status=200)