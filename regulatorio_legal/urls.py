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
    
    # Marca de agua en documentos
    path(
        route='prueba_api_marca_agua',
        view = views.prueba_api_marca_agua,
        name = 'prueba_api_marca_agua'
    ),
    
    # documentos legales
    path(
        route='documentos-legales-list-marcas',
        view = views.documentos_legales_list_marcas,
        name = 'documentos_legales_list_marcas'
    ),
    
        # documentos legales
    path(
        route='documentos-legales-detail-marca/<int:id>',
        view = views.documentos_legales_detail_marca,
        name = 'documentos_legales_detail_marca'
    ),
    
    # documentos legales
    path(
        route='documento_legal_editar_marca/<int:id>',
        view = views.documento_legal_editar_marca,
        name = 'documento_legal_editar_marca'
    ),
    
    # documentos legales
    path(
        route='documento_legal_editar_detail>',
        view = views.documento_legal_editar_detail,
        name = 'documento_legal_editar_detail'
    ),
    
]