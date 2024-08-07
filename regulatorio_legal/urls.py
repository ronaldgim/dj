# Urls
from django.urls import path

# Views functions
from regulatorio_legal import views

urlpatterns = [
    
    # Lista de Imprtaciones
    path(
        route='importaciones/list',
        view = views.importaciones_llegadas_list,
        name = 'importaciones_list'
    ),

    # doc_importacion_por_lote_ajax
    path(
        route='importacion/doc-por-lote',
        view = views.doc_importacion_por_lote_ajax,
        name = 'doc_importacion_por_lote_ajax'
    ),
    
    # doc_importacion_por_codigo_ajax
    path(
        route='importacion/doc_importacion_por_codigo_ajax',
        view = views.doc_importacion_por_codigo_ajax,
        name = 'doc_importacion_por_codigo_ajax'
    ),


    # Lista de productos en importación
    path(
        route='importaciones/<str:o_compra>/list',
        view = views.importacion_list_detail,
        name = 'importaciones_orden_list'
    ),

    # Lista de armados
    path(
        route='importaciones/armados/imp/list',
        view = views.armados_list_imp,
        name = 'armados_list_imp'
    ),


    # Ajax documento
    path(
        route='update_document',
        view = views.update_document,
        name = 'update_document'
    ),

    # New documento
    path(
        route='new_document',
        view = views.new_document,
        name = 'new_document'
    ),

    # Lista de facturas
    path(
        route='facturas',
        view = views.lista_facturas,
        name = 'r_l_facturas'
    ),

    # Factura
    path(
        route='factura/<str:n_factura>',
        view = views.factura_detalle,
        name = 'factura_detalle'
    ),
]