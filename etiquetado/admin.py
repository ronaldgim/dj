# from django.contrib import admin

# # Model
# from etiquetado.models import (
#     RowItem, 
#     Calculadora, 
#     EstadoEtiquetado, 
#     PedidosEstadoEtiquetado, 
#     OrdenEtiquetadoStock,
#     EstadoPicking,

#     EtiquetadoStock,
#     RegistoGuia,
#     FechaEntrega,
#     ProductArmado,
#     InstructivoEtiquetado,
#     EtiquetadoAvance
# )

# # Register your models here.
# @admin.register(RowItem)
# class RowItemAdmin(admin.ModelAdmin):
#     list_display = ('item', 'lote', 'cant')
    
# @admin.register(Calculadora)
# class CalculadoraAdmin(admin.ModelAdmin):
#     list_display = ('nombre', 'fecha')

# @admin.register(EstadoEtiquetado)
# class EstadoEtiquetadoAdmin(admin.ModelAdmin):
#     list_display = ('estado',)

# @admin.register(PedidosEstadoEtiquetado)
# class PedidosEstadoEtiquetadoAdmin(admin.ModelAdmin):
#     list_display = ('n_pedido', 'estado', 'fecha_creado', 'fecha_actualizado')

    
# @admin.register(OrdenEtiquetadoStock)
# class OrdenEtiquetadoStockAdmin(admin.ModelAdmin):
#     list_display = ('id', 'cliente', 'tipo', 'ciudad')
    
# @admin.register(EstadoPicking)
# class EstadoPickingAdmin(admin.ModelAdmin):
#     list_display = ('id', 'user', 'n_pedido', 'bodega', 'estado', 'codigo_cliente', 'cliente', 'fecha_creado', 'fecha_actualizado')
#     search_fields = ('n_pedido',)
    

# @admin.register(RegistoGuia)
# class RegistroGuiaAdmin(admin.ModelAdmin):
#     list_display = ('id', 'cliente', 'factura')

# @admin.register(FechaEntrega)
# class FechaEntregaAdmin(admin.ModelAdmin):
#     list_display = ('id', 'pedido', 'fecha_hora','estado')

# @admin.register(ProductArmado)
# class ProductArmadoAdmin(admin.ModelAdmin):
#     list_display = ('id', 'producto', 'activo')
    
    
# @admin.register(InstructivoEtiquetado)
# class InstructivoEtiquetadoAdmin(admin.ModelAdmin):
#     list_display = ('id', 'equipo', 'producto', 'creado')
    
    
# @admin.register(EtiquetadoAvance)
# class EtiquetadoAvanceAdmin(admin.ModelAdmin):
#     list_display = ('id', 'n_pedido', 'product_id', 'unidades')