from django.contrib import admin

# Models
from wms.models import (
    InventarioIngresoBodega, 
    Ubicacion, 
    Movimiento, 
    LiberacionCuarentena, 
    Transferencia,
    AjusteLiberacion,
    TransferenciaStatus,
    NotaEntrega,
    NotaEntregaStatus,
    AnulacionPicking,
    ProductoArmado,
    OrdenEmpaque,
    Existencias,
    FacturaAnulada,
    ImportacionFotos,
    CostoImportacion,
    OrdenSalida
    )

# EXISTENCIAS
@admin.register(Existencias)
class ExistenciasAdmin(admin.ModelAdmin):
    
    list_display = ('id', 'product_id', 'lote_id')
    list_filter = ('product_id',)
    search_fields = ['product_id',]
    
    
    
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
        'referencia',
        'estado',
        'estado_picking',
        'ubicacion', 
        'n_referencia', 
        'usuario',
        'fecha_hora',
        'n_factura',
        'unidades'
        )
    
    # list_filter = ('product_id',)
    # list_display_links = []
    search_fields = ['product_id','n_referencia']
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
    
    
    
@admin.register(LiberacionCuarentena)
class TransferenciaAdmin(admin.ModelAdmin):

    list_display = (
        'doc_id',
        'product_id', 
        'lote_id', 
        'egreso_temp'
        )
    
    # list_filter = ('product_id',)
    # list_display_links = []
    # search_fields = ['product_id',]
    # orderin = []
    
    
@admin.register(AjusteLiberacion)
class AjusteLiberacionAdmin(admin.ModelAdmin):

    list_display = (
        'doc_id_corp',
        'doc_id',
        'product_id', 
        'lote_id', 
        'egreso_temp',
        'unidades_cuc'
        )
    # list_filter = ('doc_id_corp', 'doc_id', 'product_id')
    search_fields = ['doc_id_corp', 'doc_id', 'product_id']
    
@admin.register(TransferenciaStatus)
class TransferenciaStatusAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'n_transferencia', 
        'estado', 
        'unidades_mba',
        'unidades_wms',
        'avance'
        )
    
    
@admin.register(NotaEntrega)
class NotaEntregaAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'doc_id', 
        'product_id', 
        'lote_id',
        'unidades',
        )
    
@admin.register(NotaEntregaStatus)
class NotaEntregaStatusAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'nota_entrega', 
        'estado', 
        'unidades_mba',
        'unidades_wms',
        'avance'
        )
    
@admin.register(AnulacionPicking)
class AnulacionPickingAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'picking_anulado', 
        'picking_nuevo', 
        'estado',
        'usuario',
        'fecha_hora'
        )
    
@admin.register(ProductoArmado)
class ProductoArmadoAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'product_id',
        'nombre',
        'marca',
        'lote_id',
        'fecha_elaboracion',
        'fecha_caducidad',
        'precio_venta',
        'ubicacion',
        'unidades'
        )
    
@admin.register(OrdenEmpaque)
class OrdenEmpaqueAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'enum',
        'ruc',
        'cliente',
        'bodega',
        'prioridad',
        'estado',
        'nuevo_producto',
        'usuario',
        'creado',
        'actualizado',
        'observaciones'
        )

@admin.register(FacturaAnulada)
class FacturaAnuladaAdmin(admin.ModelAdmin):
    
    list_display = (
        'id',
        'n_factura',
        'n_picking',
        'cliente',
        'creado',
        'actualizado',
        'usuario',
        )

@admin.register(ImportacionFotos)
class ImportacionFotosAdmin(admin.ModelAdmin):
    list_display = (
        'importacion',
        'foto',
        'creado',
        'usuario',
    )


@admin.register(CostoImportacion)
class CostoImportacionAdmin(admin.ModelAdmin):
    list_display = (
        'product_id',
        'nombre',
        'marca',
        'importacion',
        'gim'
    )

@admin.register(OrdenSalida)
class OrdenSalidaAdmin(admin.ModelAdmin):
    list_display = (
        'n_factura',
        'codigo_cliente',
        'ruc_cliente',
        'cliente',
        'fecha_salida'
    )