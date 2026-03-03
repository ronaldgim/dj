from django.contrib import admin
from .models import ClienteExcluido, NotificacionCartera


@admin.register(ClienteExcluido)
class ClienteExcluidoAdmin(admin.ModelAdmin):
    list_display = ('codigo_cliente', 'creado')
    search_fields = ('codigo_cliente',)
    ordering = ('-creado',)
    list_filter = ('creado',)


@admin.register(NotificacionCartera)
class NotificacionCarteraAdmin(admin.ModelAdmin):
    list_display = (
        'enum',
        'codigo_cliente',
        'get_correos_short',
        'usuario',
        'usuario_auto',
        'creado',
    )
    search_fields = (
        'codigo_cliente',
        'correos',
        'usuario__username',
        'usuario_auto',
    )
    list_filter = ('creado', 'usuario')
    ordering = ('-creado',)
    readonly_fields = ('creado', 'actualizado', 'enum')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('usuario')

    def get_correos_short(self, obj):
        if obj.correos:
            return obj.correos[:50] + '...' if len(obj.correos) > 50 else obj.correos
        return "-"
    get_correos_short.short_description = "Correos"