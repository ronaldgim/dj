from django.contrib import admin

# Model
from regulatorio_legal.models import (
    DocumentoLote, 
    DocumentoEnviado, 
    DocumentosLegales, 
    RegistroSanitario, 
    ProductosRegistroSanitario,
    IsosRegEnviados,
    FacturaProforma,
    DocumentoVario,
    Documento,
    )

# Register your models here.
@admin.register(DocumentoLote)
class DocumentoLoteAdmin(admin.ModelAdmin):
    list_display = ('o_compra', 'product_id', 'lote_id', 'f_caducidad', 'documento')
    search_fields = ('o_compra', 'product_id', 'lote_id')

@admin.register(DocumentoEnviado)
class DocumentoEnviadoAdmin(admin.ModelAdmin):
    list_display = ('n_factura', 'nombre_cliente', 'correo_cliente', 'fecha_hora', 'usuario')
    search_fields = ('n_factura',)
    
@admin.register(DocumentosLegales)
class DocumentosLegalesAdmin(admin.ModelAdmin):
    list_display = (
        'marca',
        'nombre_proveedor',
        'documento',
        'fecha_caducidad',
        'creado',
        'actualizado',
        'usuario'
    )

@admin.register(RegistroSanitario)
class RegistroSanitarioAdmin(admin.ModelAdmin):
    list_display = (
        'n_reg_sanitario',
        'descripcion',
        'fecha_caducidad',
        'documento',
        'creado',
        'actualizado',
        'usuario'
    )
    
@admin.register(ProductosRegistroSanitario)
class ProductosRegistroSanitarioAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'product_id'
    )
    

@admin.register(FacturaProforma)
class FacturaProformaAdmin(admin.ModelAdmin):
    list_display = (
        'tipo_comprobante',
        'n_comprobante',
        'detalle',
        'codigo_cliente',
        'nombre_cliente',
        'marca_de_agua',
        'creado',
        'actualizado',
        'usuario',
    )


@admin.register(IsosRegEnviados)
class IsosRegEnviadosAdmin(admin.ModelAdmin):
    list_display = (
        'tipo_documento',
        'descripcion',
        'documento',
        'creado',
    )

@admin.register(DocumentoVario)
class DocumentoVarioAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'cliente',
        'descripcion',
    )
@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'documento',
        'tipo',
        'procesado',
    )