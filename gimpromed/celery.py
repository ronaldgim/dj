from __future__ import absolute_import, unicode_literals
import os
from celery import Celery


# Establece la configuración predeterminada de Django para Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gimpromed.settings')

# Crea la aplicación Celery
app = Celery('gimpromed')

# Carga las configuraciones de Celery desde las configuraciones de Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Detecta automáticamente las tareas en cada app de Django
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
