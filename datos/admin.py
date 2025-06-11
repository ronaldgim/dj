# Admin
from django.contrib import admin

# Model
from datos.models import Product, Vehiculos, AdminActualizationWarehaouse, Marca, Reservas


admin.site.site_header = 'GIM OPERACIONES'
# admin.site.site_title = 'ADMINISTRAICÓN DE DB'
# admin.site.index_title = 'ADMINISTRAICÓN DE DB'

# Register your models here.
# @admin.register(MarcaImportExcel)
# class MarcaExcelAdmin(admin.ModelAdmin):
#     list_display = ('archivo',)

@admin.register(AdminActualizationWarehaouse)
class AdminActualizationWarehaouseAdmin(admin.ModelAdmin):
    list_display = (
        'orden',
        'table_name',
        'datetime',
        'automatico',
        'periodicidad',
        'milisegundos',
    )

@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ('id', 'marca', 'description')
    list_filter = ('marca',)
    list_display_links = ['id', 'marca']
    search_fields = ['marca']
    ordering = ['marca']
    

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'product_id', 
        'description', 
        #'marca',
        'marca2', 
        'unidad_empaque',
        # 'largo',
        # 'ancho',
        # 'alto',
        # 'volumen',
        # 'peso',

        't_etiq_1p',
        't_etiq_2p',
        't_etiq_3p',

        'emp_primario',
        'emp_secundario',
        'emp_terciario',
        )
    
    list_filter = ('marca2',)
    list_display_links = ['product_id']
    search_fields = ['product_id', 'description']
    ordering = ['marca']


@admin.register(Vehiculos)
class VehiculosAdmin(admin.ModelAdmin):
    list_display = ('id', 'transportista', 'placa', 'ancho', 'alto', 'largo', 'volumen', 'volumen2', 'activo')
    list_display_links = ['id','transportista', 'placa']
    search_fields = ['id', 'placa']
    ordering = ['placa']


@admin.register(Reservas)
class VehiculosAdmin(admin.ModelAdmin):
    list_display = (
        'contrato_id',
        'codigo_cliente',
        'product_id',
        'quantity',
        'ware_code',
        'confirmed',
        'fecha_pedido',
        'hora_llegada',
        'sec_name_cliente',
        'unique_id',
        'alterado',
        'creado',
        'actualizado',
        'usuario',
    )
    search_fields = ['unique_id', 'contrato_id', 'product_id']
    