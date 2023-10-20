# Urls
from django.urls import path

# Views functions
from ventas import views

urlpatterns = [
    
    # Pedidos
    path(
        route='reporte_mba',
        view = views.reporte_tipo_mba,
        name = 'reporte_mba'
    ),

    # Pedidos
    path(
        route='lote_factura_ajax',
        view = views.lote_factura_ajax,
        name = 'lote_factura_ajax'
    ),
    
    # Pedidos Cuenca AJAX
    # path(
    #     route='pedidos/cuenca/ajax',
    #     view = views.pedidos_cuenca_ajax,
    #     name = 'pedidos_cuenca_ajax'
    # ),
    
    # Pedidos Cuenca
    path(
        route='pedidos/cuenca',
        view = views.pedidos_cuenca,
        name = 'pedidos_cuenca'
    ),
        
    # Procesos Guantes
    path(
        route='procesos-guantes',
        view = views.procesos_guantes,
        name = 'procesos_guantes'
    ),
]