from django.contrib import admin
from metro.models import Product, Inventario, TomaFisica


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'codigo_gim',
        'codigo_hm',
        'nombre_gim',
        'nombre_hm',
        'marca',
        'unidad',
        'u_empaque',
        'consignacion',
        'ubicacion',
        'creado',
        'actualizado',
        'usuario',
        'activo'
    )


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
