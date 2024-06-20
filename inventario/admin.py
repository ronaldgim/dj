# Admin
from django.contrib import admin

# Models
from inventario.models import Inventario, InventarioTotale, Arqueo, ArqueoFisico, ArqueosCreados

@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):

    list_display = (
        'product_id', 
        'product_name', 
        'group_code',
        'lote_id',
        #'oh', 
        'oh2',
        # 'largo',
        # 'ancho',
        # 'alto',
        # 'estado',
        # 'dias_caducar'
        'diff2'
        )
    
    list_filter = ('llenado', 'agregado')
    list_display_links = ['product_id']
    search_fields = ['product_id','lote_id']
    ordering = ['group_code']


@admin.register(InventarioTotale)
class InventarioTotalesAdmin(admin.ModelAdmin):

    list_display = (
        'product_id_t', 
        'ware_code_t',
        'location_t',
        'unidades_caja_t',
        'numero_cajas_t',
        'unidades_sueltas_t',
        'user'
        )

    list_display_links = ['product_id_t']
    search_fields = ['product_id_t',]
    ordering = ['product_id_t',]


@admin.register(ArqueosCreados)
class ArqueoAdmin(admin.ModelAdmin):

    list_display = (
        'arqueo', 
        'arqueo_enum',
        'ware_code',
        'bodega',
        'descripcion',
        'estado',
        'fecha_hora',
        'usuario'
        )
    

@admin.register(Arqueo)
class ArqueoAdmin(admin.ModelAdmin):

    list_display = (
        'id', 
        'descripcion',
        'fecha_hora',
        #'usuario'
        )

    # list_display_links = ['product_id_t']
    # search_fields = ['product_id_t',]
    # ordering = ['product_id_t',]


@admin.register(ArqueoFisico)
class ArqueoFisicoAdmin(admin.ModelAdmin):

    list_display = (
            'id_arqueo',
        )

    # list_display_links = ['product_id']
    # search_fields = ['product_id_t',]
    # ordering = ['product_id_t',]