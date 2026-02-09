from django.contrib import admin
from .models import Cliente, Producto, Reserva

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = (
        'codigo_cliente',
        'nombre_cliente',
        'identificacion_fiscal',
        'ciudad_principal',
        'email',
    )
    search_fields = ('nombre_cliente', 'identificacion_fiscal')
    readonly_fields = [f.name for f in Cliente._meta.fields]
    ordering = ('codigo_cliente',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.using('gimpromed_sql')  # 🔥 CLAVE

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        'codigo',
        'nombre',
        'marca',
        'unidad',
        'disponible',
        'inactivo',
    )
    search_fields = ('codigo', 'nombre', 'marca')
    list_filter = ('marca', 'procedencia', 'inactivo')
    readonly_fields = [f.name for f in Producto._meta.fields]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.using('gimpromed_sql')  # 🔥 clave

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = (
        'contrato_id',
        'fecha_pedido',
        'codigo_cliente',
        'nombre_cliente',
        'product_id',
        'quantity',
        'despachados',
        'confirmed',
    )
    search_fields = (
        'codigo_cliente',
        'nombre_cliente',
        'product_id',
        'product_name',
    )
    list_filter = (
        'fecha_pedido',
        'confirmed',
        'ware_code',
    )
    readonly_fields = [f.name for f in Reserva._meta.fields]
    date_hierarchy = 'fecha_pedido'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.using('gimpromed_sql')  # 🔥 imprescindible

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
