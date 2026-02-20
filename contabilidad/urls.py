# Urls
from django.urls import path

# Views functions
from contabilidad import views

urlpatterns = [
    
    path(
        route = 'cuentas-por-cobrar',
        view = views.lista_cuentas_por_cobrar,
        name = 'cuentas_por_cobrar'
    ),
    
    path(
        route = 'clientes-excluidos',
        view = views.lista_clientes_excluidos,
        name = 'clientes_excluidos'
    ),
    
    path(
        route = 'contabilidad_agregar_cliente_excluido',
        view = views.contabilidad_agregar_cliente_excluido,
        name = 'contabilidad_agregar_cliente_excluido'
    ),
    
    path(
        route = 'contabilidad_eliminar_cliente_excluido',
        view = views.contabilidad_eliminar_cliente_excluido,
        name = 'contabilidad_eliminar_cliente_excluido'
    ),
    
    path(
        route = 'notificaciones',
        view = views.lista_notificaciones,
        name = 'lista_notificaciones'
    ),
    
    path(
        route = 'nueva-notificacion',
        view = views.nueva_notificacion,
        name = 'nueva_notificacion'
    ),
]