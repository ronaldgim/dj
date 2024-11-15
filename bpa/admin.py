# Admin
from django.contrib import admin

# Model
from bpa.models import Trasferencia, RegistroSanitario, CartaNoRegistro

# Register your models here.
@admin.register(Trasferencia)
class TransferenciaAdmin(admin.ModelAdmin):
    list_display = ('id', 'documento', 'product_id', 'lote', 'unidades')
    search_fields = ['id','documento']


@admin.register(RegistroSanitario)
class RegistroSanitario(admin.ModelAdmin):
    list_display = (
        'id',
        'marca', 
        'propietario', 
        'registro', 
        #'producto',
        'origen',
        'fecha_expedicion',
        'fecha_expiracion',
        #'cn_recomen',
        #'cn_carpeta',
        'fecha_notaria',
        'estado',
        #'obs_doc',
        'dias_caducar',
        'notaria'
    )

    search_fields = ['id', 'registro']


@admin.register(CartaNoRegistro)
class CartaNoRegistroAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'marca',
        'documento',
        'n_solicitud',
        'producto',
        'fecha_expedicion',
        'fecha_expiracion',
        'estado',
        'observacion'
    )