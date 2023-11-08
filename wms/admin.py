from django.contrib import admin

# Models
from wms.models import InventarioIngresoBodega, Ubicacion, Movimiento


# INVENTARIO
@admin.register(InventarioIngresoBodega)
class InventarioIngresoBodegaAdmin(admin.ModelAdmin):
    
    list_display = ('product_id', 'lote_id', 'fecha_caducidad', 'n_referencia', 'referencia', 'bodega', 'unidades_ingresadas', 'fecha_hora')
    # list_filter = ()
    # list_display_links = []
    # search_fields = []
    # orderin = []


# UBICACIÓN
@admin.register(Ubicacion)
class UbicacionAdmin(admin.ModelAdmin):
    
    list_display = ('bodega', 'pasillo', 'modulo', 'nivel', 'capacidad_m3')
    # list_filter = ()
    # list_display_links = []
    # search_fields = []
    # orderin = []


# MOVIMIENTO
@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):

    list_display = ('product_id', 'lote_id', 'tipo', 'ubicacion', 'n_referencia', 'unidades')
    
    # list_filter = ()
    # list_display_links = []
    # search_fields = []
    # orderin = []