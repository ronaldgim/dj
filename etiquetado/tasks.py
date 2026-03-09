from celery import shared_task
from wms.models import Movimiento

# Email
from django.core.mail import send_mail
from django.conf import settings

# Time
import time

@shared_task
def enviar_correos_prueba(email):
    movs = Movimiento.objects.all()[:5]
    for i in movs:

        mensaje = f"""
        Id: {i.id}
        Código: {i.product_id}
        Lote: {i.lote_id}
        Unidades: {i.unidades}
        """

        send_mail(
            subject='Prueba Celery',
            message=mensaje,
            from_email=settings.EMAIL_HOST_USER,
            #recipient_list=['egarces@gimpromed.com'],
            recipient_list=[email],
            fail_silently=False,
        )

    return 'correos enviados'


@shared_task
def prueba_sleep():
    time.sleep(10)
    print('sleep 10 seg')
    return 'sleep 10 seg'
