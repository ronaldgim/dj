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
]