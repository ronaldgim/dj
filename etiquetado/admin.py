from django.contrib import admin

# Model
from etiquetado.models import (
    RowItem, 
    Calculadora, 
    EstadoEtiquetado, 
    PedidosEstadoEtiquetado, 
    OrdenEtiquetadoStock,
    EstadoPicking,
    RegistoGuia,
    FechaEntrega,
    ProductArmado,
    InstructivoEtiquetado,
    EtiquetadoAvance,
    AnexoDoc,
    AnexoGuia,
    AddEtiquetadoPublico,
    UbicacionAndagoya,
    ProductoUbicacion,
    PedidoTemporal, 
    ProductosPedidoTemporal,
    TransfCerAnd,
    ProductosTransfCerAnd
)

# Register your models here.
@admin.register(RowItem)
class RowItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'item', 'lote', 'cant')
    
@admin.register(Calculadora)
class CalculadoraAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha')

@admin.register(EstadoEtiquetado)
class EstadoEtiquetadoAdmin(admin.ModelAdmin):
    list_display = ('estado',)

@admin.register(PedidosEstadoEtiquetado)
class PedidosEstadoEtiquetadoAdmin(admin.ModelAdmin):
    list_display = ('n_pedido', 'estado', 'fecha_creado', 'fecha_actualizado')
    search_fields = ('n_pedido',)
    
@admin.register(OrdenEtiquetadoStock)
class OrdenEtiquetadoStockAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'tipo', 'ciudad')
    
@admin.register(EstadoPicking)
class EstadoPickingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'n_pedido', 'bodega', 'estado', 'codigo_cliente', 'cliente', 'fecha_creado', 'fecha_actualizado')
    search_fields = ('n_pedido',)
    

@admin.register(RegistoGuia)
class RegistroGuiaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'factura')

@admin.register(FechaEntrega)
class FechaEntregaAdmin(admin.ModelAdmin):
    list_display = ('id', 'pedido', 'fecha_hora','estado')

@admin.register(ProductArmado)
class ProductArmadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'producto', 'activo')
    
    
@admin.register(InstructivoEtiquetado)
class InstructivoEtiquetadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'equipo', 'producto', 'creado')
    
    
@admin.register(EtiquetadoAvance)
class EtiquetadoAvanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'n_pedido', 'product_id', 'unidades')
    
    
@admin.register(AnexoGuia)
class AnexoGuiaAdmin(admin.ModelAdmin):
    list_display = ('id', 'bodega_nombre', 'numero_anexo','user','estado')
    

@admin.register(AnexoDoc)
class AnexoDocAdmin(admin.ModelAdmin):
    list_display = ('id', 'tipo_contenido', 'contenido', 'n_guia')
    

@admin.register(AddEtiquetadoPublico)
class AddEtiquetadoPublicoAdmin(admin.ModelAdmin):
    list_display = ('id', 'contrato_id')
    
@admin.register(UbicacionAndagoya)
class UbicacionAndagoyaAdmin(admin.ModelAdmin):
    list_display = ('id', 'bodega', 'pasillo', 'modulo', 'nivel', 'estanteria')

@admin.register(ProductoUbicacion)
class ProductoUbicacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'product_id')
    search_fields = ('product_id', )


@admin.register(PedidoTemporal)
class PedidoTemporalAdmin(admin.ModelAdmin):
    list_display = ('id', 'enum', 'cliente', 'creado')

@admin.register(ProductosPedidoTemporal)
class ProductosPedidoTemporalAdmin(admin.ModelAdmin):
    list_display = ('id', 'product_id', 'cantidad')

@admin.register(TransfCerAnd)
class TransfCerAndAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'vehiculo', 'creado')

@admin.register(ProductosTransfCerAnd)
class ProductosTransfCerAndAdmin(admin.ModelAdmin):
    list_display = ('id', 'product_id', 'lote_id', 'bodega','unidades')
