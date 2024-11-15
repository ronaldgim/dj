from django.contrib import admin

# Register your models here.
from compras_publicas.models import EvaluacionProcesos, ProcesosSercop, Producto, Anexo

@admin.register(EvaluacionProcesos)
class EvaluacionProcesosAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'codigo_proceso',
        'entidad',
        'fecha',
        'presupuesto_referencial',
        'valor_adjudicado',
        'insumos_participantes',
        'resultado_proceso',
        'empresa_ganadora'
    )

    # list_filter = (

    # )

    # search_fields = (

    # )
    
@admin.register(ProcesosSercop)
class ProcesosSercopAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'proceso',
    )
    

@admin.register(Anexo)
class AnexoAdmin(admin.ModelAdmin):
    list_display = (
        'n_pedido',
        'fecha',
        'cliente',
        'ruc',
        'direccion',
        'orden_compra',
        'observaciones'
        )



@admin.register(Producto)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'product_id',
        'nombre',
        'marca',
        'lote_id',
        'cantidad'
    )