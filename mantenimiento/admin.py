# Admin
from django.contrib import admin

# Model
from mantenimiento.models import Equipo, Estadistica

# Register your models here.
@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'description', 'ubicacion', 'frecuencia', 'mtt_por')



@admin.register(Estadistica)
class EstadisticaAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'fecha',
        'equipo',
        'p_detectados',
        'p_codificados',
        'f_seniales',
        'h_maquina',
        'h_chorro'
    )

    list_filter = ('equipo',)