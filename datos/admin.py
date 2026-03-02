# Admin
from django.contrib import admin

from django.utils.html import format_html

# Model
from datos.models import (
    Product, 
    Vehiculos, 
    AdminActualizationWarehaouse, 
    Marca, 
    Reservas,
    UsuarioSlack,
    NotificacionSlack,
    NotificacionInstanceSlack
    )

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


# =========================
# Usuario Slack
# =========================
@admin.register(UsuarioSlack)
class UsuarioSlackAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "real_name",
        "email",
        "is_active",
        "last_sync",
    )
    search_fields = ("id", "name", "real_name", "email")
    list_filter = ("is_active",)
    ordering = ("real_name",)
    readonly_fields = ("last_sync",)

    list_per_page = 25


# =========================
# Inline usuarios en notificación
# =========================
class UsuarioSlackInline(admin.TabularInline):
    model = NotificacionSlack.usuarios.through
    extra = 1


# =========================
# Notificación Slack
# =========================
@admin.register(NotificacionSlack)
class NotificacionSlackAdmin(admin.ModelAdmin):
    list_display = (
        "proceso",
        "titulo",
        "tipo_msg",
        "is_active",
        "total_usuarios",
        "creado",
    )

    list_filter = (
        "tipo_msg",
        "is_active",
    )

    search_fields = (
        "titulo",
        "mensaje",
    )

    filter_horizontal = ("usuarios",)

    inlines = []  # si luego usas through personalizado, puedes usar inline

    readonly_fields = ("creado", "actualizado")

    list_per_page = 20

    def total_usuarios(self, obj):
        return obj.usuarios.count()

    total_usuarios.short_description = "Usuarios"


# =========================
# Notificación Instance
# =========================
@admin.register(NotificacionInstanceSlack)
class NotificacionInstanceSlackAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "notificacion",
        "referencia_id",
        "status_badge",
        "envios",
        "last_sent_at",
        "creado",
    )

    list_filter = (
        "status",
        "notificacion",
    )

    search_fields = (
        "referencia_id",
    )

    readonly_fields = (
        "creado",
        "actualizado",
        "last_sent_at",
        "envios",
    )

    autocomplete_fields = ("notificacion",)

    list_select_related = ("notificacion",)

    list_per_page = 25

    # =========================
    # Badge visual de estado
    # =========================
    def status_badge(self, obj):
        colors = {
            "PENDING": "gray",
            "SENT": "blue",
            "COMPLETED": "green",
            "FAILED": "red",
        }

        color = colors.get(obj.status, "black")

        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 8px; border-radius: 5px;">{}</span>',
            color,
            obj.status
        )

    status_badge.short_description = "Estado"

    # =========================
    # Acciones masivas
    # =========================
    actions = ["marcar_completado", "reintentar"]

    def marcar_completado(self, request, queryset):
        updated = queryset.update(status=NotificacionInstanceSlack.Status.COMPLETED)
        self.message_user(request, f"{updated} registros marcados como completados")

    marcar_completado.short_description = "Marcar como COMPLETED"

    def reintentar(self, request, queryset):
        updated = queryset.update(status=NotificacionInstanceSlack.Status.PENDING)
        self.message_user(request, f"{updated} registros listos para reintento")

    reintentar.short_description = "Reintentar (PENDING)"