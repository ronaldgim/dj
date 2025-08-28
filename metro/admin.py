from django.contrib import admin
from metro.models import Product, Inventario, TomaFisica, Kardex


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'codigo_gim',
        'codigo_hm',
        'nombre_gim',
        # 'nombre_hm',
        # 'marca',
        # 'unidad',
        # 'u_empaque',
        'consignacion',
        # 'ubicacion',
        # 'creado',
        'actualizado',
        'usuario',
        'activo',
        'saldo',
        # 'precio_total'
        'precio_unitario_hm'
    )
    
    search_fields = ('codigo_gim', 'codigo_hm')


@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = (
        'enum',
        'nombre',
        'estado_inv',
        'estado_tf',
        'inicio_tf',
        'fin_tf',
        'creado',
        'actualizado',
        'usuario',
    )


@admin.register(TomaFisica)
class TomaFisicaAdmin(admin.ModelAdmin):
    list_display = (
        'inventario',
        'product',
        'cantidad_estanteria',
        'cantidad_bulto',
        'cantidad_total',
        'observaciones',
        'llenado',
        'agregado',
        'usuario',
        'actualizado',
    )


@admin.register(Kardex)
class KardexAdmin(admin.ModelAdmin):
    list_display = (
    'product',
    # 'tipo',
    'description',
    'nota_entrega',
    'fecha_nota',
    'movimiento_mba',
    'fecha_mba',
    'cantidad',
    # 'observaciones',
    # 'documento',
    # 'creado',
    # 'actualizado',
    'saldo'
    )
    
    search_fields = ('product__codigo_gim', 'product__codigo_hm')