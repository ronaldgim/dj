# Urls
from django.urls import path

# Views functions
from compras_publicas import views

urlpatterns = [

    path(
        route='precios-historicos',
        view = views.precios_historicos,
        name = 'precios_historicos'
    ),
    
    path(
        route='facturas_por_product_ajax',
        view = views.facturas_por_product_ajax,
        name = 'facturas_por_product_ajax'
    ),

    path(
        route='infimas', #?page=1
        view = views.infimas,
        name = 'infimas'
    ),

    path(
        route='ajax/my_view/', 
        view = views.my_ajax_view, 
        name='my_ajax_view'
    ),
    
    # Procesos SERPCOP
    path(
        route='procesos-sercop', 
        view = views.procesos_sercop, 
        name='procesos_sercop'
    ),
]