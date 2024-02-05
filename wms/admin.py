from django.contrib import admin

# Models
from wms.models import InventarioIngresoBodega, Ubicacion, Movimiento, LiberacionCuarentena, Transferencia


# INVENTARIO
@admin.register(InventarioIngresoBodega)
class InventarioIngresoBodegaAdmin(admin.ModelAdmin):
    
    list_display = ('id', 'product_id', 'lote_id', 'fecha_caducidad', 'n_referencia', 'referencia', 'bodega', 'unidades_ingresadas', 'fecha_hora')
    list_filter = ('product_id',)
    # list_display_links = []
    search_fields = ['product_id',]
    # orderin = []


# UBICACIÓN
@admin.register(Ubicacion)
class UbicacionAdmin(admin.ModelAdmin):
    
    list_display = ('id', 'bodega', 'pasillo', 'modulo', 'nivel', 'capacidad_m3')
    # list_filter = ()
    # list_display_links = []
    # search_fields = []
    # orderin = []


# MOVIMIENTO
@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'enum',
        'product_id', 
        'lote_id', 
        'tipo', 
        'estado',
        'estado_picking',
        'ubicacion', 
        'n_referencia', 
        'unidades'
        )
    
    list_filter = ('product_id',)
    # list_display_links = []
    search_fields = ['product_id',]
    # orderin = []
    
    
@admin.register(Transferencia)
class TransferenciaAdmin(admin.ModelAdmin):

    list_display = (
        'n_transferencia',
        'product_id', 
        'lote_id', 
        'unidades'
        )
    
    list_filter = ('product_id',)
    # list_display_links = []
    search_fields = ['product_id',]
    # orderin = []