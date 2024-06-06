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
    
    ## ANEXOS
    # lista de anexos
    path(
        route='anexos/list', 
        view = views.anexos_list, 
        name='anexos_list'
    ),
    
    # anexo detail
    path(
        route='anexos/<int:anexo_id>', 
        view = views.anexo_detail, 
        name='anexo_detail'
    ),
    
    #anexo_cabecera_edit_ajax
    path(
        route='anexos/anexo_cabecera_edit_ajax', 
        view = views.anexo_cabecera_edit_ajax, 
        name='anexo_cabecera_edit_ajax'
    ),
    
    #anexo_get_product_ajax
    path(
        route='anexos/anexo_edit_product_ajax', 
        view = views.anexo_edit_product_ajax, 
        name='anexo_edit_product_ajax'
    ),
    
    #anexo_get_product_ajax
    path(
        route='anexos/anexo_formato_general/<int:anexo_id>', 
        view = views.anexo_formato_general, 
        name='anexo_formato_general'
    ),
]