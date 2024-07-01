from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

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
            # to         = ['egarces@gimpromed.com'],
            body       = plain_message,
        )
        
        email.attach_alternative(html_message, 'text/html')
        email.send()
        
        return Response(status=200)
    
    except:
        return Response(status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reg_sanitario_correo_alerta_dias(request):
    
    try:

        tabla_query = RegistroSanitario.objects.filter(activo=True).order_by('fecha_expiracion')
        
        # Avisos
        a1=120
        a2=100
        a3=90 #;a4=9
        a4=40
        
        # lista de correos 
        lista_correos = ['pespinosa@gimpromed.com', 'ncaisapanta@gimpromed.com']
        
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
                    to         = lista_correos,
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
                    to         = lista_correos,
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
                    to         = lista_correos,
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
                    # to         = lista_correos,
                    to         = lista_correos + ['ronaldm@gimpromed.com'],
                    body       = plain_message,
                )
                
                email.attach_alternative(html_message, 'text/html')
                email.send()
                
        return Response(status=200)
    
    except:
        return Response(status=500)