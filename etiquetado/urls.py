# Urls
from django.urls import path

# Views functions
from etiquetado import views

urlpatterns = [
    
    path(
        route='add_etiquetado_publico',
        view=views.add_etiquetado_publico,
        name = 'add_etiquetado_publico'
    ),
    
    # Pedidos
    path(
        route='pedidos/list',
        view = views.pedidos_list_3,
        name = 'pedidos_list'
    ),

    path(
        route='pedidos/fecha/entrega/ajax',
        view = views.fecha_entrega_ajax,
        name = 'pedidos_fecha_entrega_ajax'
    ),
    
    path(
        route='pedidos/<str:n_pedido>',
        view = views.etiquetado_pedidos,
        name = 'pedidos'
    ),
    
    path(
        route='pedidos/lote/<str:n_pedido>',
        view = views.pedido_lotes,
        name = 'pedido_lote'
    ),
    
    # Listado Etiquetao Stock
    path(
        route='stock',
        view = views.etiquetado_stock,
        name = 'stock'
    ),
    
    path(
        route='stock/bodega',
        view = views.etiquetado_stock_bodega,
        name = 'stock_bodega'
    ),

    # CALCULADORA
    path(
        route= 'calculadora/list',
        view = views.CalculadoraList.as_view(),
        name = 'calculadora_list'
    ),

    path(
        route = 'calculadora/new',
        view  = views.calculadora_new,
        name  = 'calculadora_new'
    ),
    
    path(
        route = 'calculadora/view/<int:id>',
        view  = views.calculadora_view,
        name  = 'calculadora_view'
    ),
    # FACTURAS
    path(
        route = 'facturas/list',
        view  = views.facturas_list,
        name  = 'facturas_list'
    ),
    
    path(
        route = 'factura/<str:n_factura>',
        view  = views.facturas,
        name  = 'facturas'
    ),
    
    # Estados de etiquetado
    path(
        route='pedidos/estado/list',
        view = views.pedidos_estado_list,
        name = 'pedidos_estado_list'
    ),

    # Crear estado
    path(
        route = 'estado/<str:n_pedido>/<str:id>',
        view  = views.estado_etiquetado,
        name  = 'estado_pedido'
    ),

    # Etiquetado stock
    path(
        route = 'stock/<int:id>',
        view  = views.detail_stock_etiquetado,
        name  = 'detail_stock_etiquetado'
    ),
    
    path(
        route = 'stock/bodega/<int:id>',
        view  = views.detail_stock_etiquetado_bodega,
        name  = 'detail_stock_etiquetado_bodega'
    ),

    # PICKING
    path(
        route = 'picking',
        view  = views.picking,
        name  = 'picking'
    ),
    
    path(
        route = 'picking/estado',
        view  = views.picking_estado,
        name  = 'picking_estado'
    ),
    
    path(
        route = 'picking/estado/<str:n_pedido>',
        view  = views.picking_estado_bodega,
        name  = 'picking_estado_bodega'
    ),
    
    path(
        route = 'picking/ajax_lotes_bodega',
        view  = views.ajax_lotes_bodega,
        name  = 'ajax_lotes_bodega'
    ),
    
    path(
        route = 'picking/historial',
        view  = views.picking_historial,
        name  = 'picking_historial'
    ),

    path(
        route = 'picking/historial/<int:id>',
        view  = views.picking_historial_detail,
        name  = 'picking_historial_detail'
    ),

    path(
        route = 'picking/historial/pdf',
        view  = views.picking_historial_pdf,
        name  = 'picking_historial_pdf'
    ),

    # # STOCK BODEGA
    # path(
    #     route = 'volumen/bodegas',
    #     view  = views.volumen_bodegas,
    #     name  = 'volumen_bodegas'
    # ),

    path(
        route = 'inventario/bodega',
        view  = views.inventario_bodega,
        name  = 'inventario_bodega'
    ),

    # RESERVAS
    path(
        route = 'revision/reservas',
        view  = views.revision_reservas,
        name  = 'revision_reservas'
    ),

    path(
        route = 'revision/<str:memo>',
        view  = views.revision,
        name  = 'revision'
    ),

    path(
        route = 'revision/imp/llegadas/list',
        view = views.revision_imp_llegadas_list,
        name = 'revision_imp_llegadas_list'
    ),

    path(
        route = 'revision/imp/llegadas/<str:orden_compra>',
        view = views.revision_imp_llegadas,
        name = 'revision_imp_llegadas'
    ),


    # Envio de correos
    path(
        route = 'picking/correo-facturado',
        view  = views.correo_facturado,
        name  = 'correo_facturado'
    ),

    # Dashboard pedidos andagoya y cerezos json response
    path(
        route = 'picking/picking_dashboard_json_response/<str:bodega>',
        view  = views.picking_dashboard_json_response,
        name  = 'picking_dashboard_json_response'
    ),
    
    # Dashboard pedidos andagoya y cerezos
    path(
        route = 'picking/dashboard/<str:bodega>',
        view  = views.picking_dashboard,
        name  = 'picking_dashboard'
    ),

    # Dashboard pedidos publicos
    path(
        route = 'publico/dashboard',
        view  = views.publico_dashboard,
        name  = 'publico_dashboard'
    ),

    # Dashboard completo
    path(
        route = 'publico/dashboard/completo-html',
        view  = views.dashboard_completo,
        name  = 'dashboard_completo'
    ),
    
    # Dashboard completo VUE DATA JSON
    path(
        route = 'publico/dashboard/completo-json-response',
        view  = views.dashboard_completo_json_response,
        name  = 'dashboard_completo_json_response'
    ),
    
    # Dashboard completo VUE HTML VIEW
    path(
        route = 'publico/dashboard/completo',
        view  = views.dashboard_completo_view,
        name  = 'dashboard_completo_view'
    ),

    # Dashboard armados
    path(
        route = 'publico/dashboard/armados',
        view  = views.dashboard_armados,
        name  = 'dashboard_armados'
    ),

    # detalle_dashboard_armados
    path(
        route = 'publico/dashboard/detalle_dashboard_armados',
        view  = views.detalle_dashboard_armados,
        name  = 'detalle_dashboard_armados'
    ),

    # reporte_revision_reservas
    path(
        route = 'picking/reporte_revision_reservas',
        view  = views.reporte_revision_reservas,
        name  = 'reporte_revision_reservas'
    ),

    path(
        route = 'mermaid_chart',
        view  = views.mermaid_chart,
        name  = 'mermaid_chart'
    ),


    ### CONTROL DE GUIAS
    path(
        route = 'guias/list',
        view  = views.control_guias_list,
        name  = 'guias_list'
    ),

    path(
        route = 'guias/factura/registrar/<str:n_fac>',
        view  = views.control_guias_registro,
        name  = 'guias_registro'
    ),

    path(
        route = 'guias/factura/editar/<int:id>',
        view  = views.control_guias_editar,
        name  = 'guias_editar'
    ),
    
    # lista de anexos
    path(
        route = 'anexo/list',
        view  = views.anexos_lista,
        name  = 'anexos_lista'
    ),
    
    # lista de anexos
    path(
        route = 'anexo/<int:id_anexo>',
        view  = views.anexo_detalle,
        name  = 'anexo_detalle'
    ),
    
    path(
        route = 'anexo/pdf/<int:id_anexo>',
        view  = views.anexo_detalle_pdf,
        name  = 'anexo_detalle_pdf'
    ),

    path(
        route = 'anexo_doc_editar_ajax',
        view  = views.anexo_doc_editar_ajax,
        name  = 'anexo_doc_editar_ajax'
    ),
    
    path(
        route = 'anexo_doc_actualizar_contenido_ajax',
        view  = views.anexo_doc_actualizar_contenido_ajax,
        name  = 'anexo_doc_actualizar_contenido_ajax'
    ),
    
    path(
        route = 'anexo_doc_elimiar_ajax',
        view  = views.anexo_doc_elimiar_ajax,
        name  = 'anexo_doc_elimiar_ajax'
    ),

    # entrega_estado_ajax
    path(
        route = 'entrega_estado_ajax',
        view  = views.entrega_estado_ajax,
        name  = 'entrega_estado_ajax'
    ),

    # etiquetado_stock_detalle
    path(
        route = 'etiquetado-stock-detalle/<str:product_id>',
        view  = views.etiquetado_stock_detalle,
        name  = 'etiquetado_stock_detalle'
    ),
    
    # etiquetado_stock_wms_ajax
    path(
        route = 'etiquetado_stock_wms_ajax',
        view  = views.etiquetado_stock_wms_ajax,
        name  = 'etiquetado_stock_wms_ajax'
    ),
    
    ## INSTUCTIVO DE ETIQUETADO
    # Lista Instructivo de etiquetado
    path(
        route = 'instructivo-etiquetado/list',
        view  = views.list_instructo_etiquetado,
        name  = 'list_instructo_etiquetado'
    ),
    
    ## Avance etiquetado
    path(
        route = 'etiquetado/avance',
        view  = views.etiquetado_avance,
        name  = 'etiquetado_avance'
    ),
    
    path(
        route = 'etiquetado/avance/edit',
        view  = views.etiquetado_avance_edit,
        name  = 'etiquetado_avance_edit'
    ),
    
    # set_estado_etiquetado_stock
    path(
        route = 'etiquetado/set-estado-etiquetado-stock',
        view  = views.set_estado_etiquetado_stock,
        name  = 'set_estado_etiquetado_stock'
    ),
    
    # Actualizar facturas ajax
    path(
        route = 'actualizar-facturas-ajax',
        view  = views.actualizar_facturas_ajax,
        name  = 'actualizar_facturas_ajax'
    ),
    
    # Listado de proformas
    path(
        route = 'proformas/list',
        view  = views.listado_proformas,
        name  = 'listado_proformas'
    ),
    
    # Detalle de proforma
    path(
        route = 'proforma/<str:contrato_id>',
        view  = views.detalle_proforma,
        name  = 'detalle_proforma'
    ),
    
    # path(
    #     route='mov_prueba',
    #     view = views.mov_prueba,
    #     name = 'mov_prueba'
    # ),
    
    # path(
    #     route='sleep_prueba',
    #     view = views.sleep_prueba,
    #     name = 'sleep_prueba'
    # ),
    
    
    # analisis transferencia
    path(
        route='analisis-transferencia',
        view=views.analisis_transferencia,
        name='analisis_transferencia'
    ),
    
    # pedidos_reservas_request
    path(
        route='pedidos_reservas_request',
        view=views.pedidos_reservas_request,
        name='pedidos_reservas_request'
    ),
    
    # existencias_wms_analisis_transferencia
    path(
        route='existencias_wms_analisis_transferencia',
        view=views.existencias_wms_analisis_transferencia,
        name='existencias_wms_analisis_transferencia'
    ),
    
    
    # ubicaciones
    path(
        route = 'ubicaciones-andagoya-list',
        view  = views.ubicaciones_andagoya_list,
        name  = 'ubicaciones_andagoya_list'
    ),
    
    path(
        route = 'editar-ubicacion-andagoya',
        view  = views.editar_ubicacion_andagoya,
        name  = 'editar_ubicacion_andagoya'
    ),
    
    path(
        route = 'producto-ubicacion-lista',
        view  = views.producto_ubicacion_lista,
        name  = 'producto_ubicacion_lista'
    ),
    
    path(
        route = 'editar-producto-ubicacion',
        view  = views.editar_producto_ubicacion,
        name  = 'editar_producto_ubicacion'
    ),
    
    path(
        route = 'inventario-andagoya-ubicaciones',
        view  = views.inventario_andagoya_ubicaciones,
        name  = 'inventario_andagoya_ubicaciones'
    ),
    
    path(
        route = 'transferencias-ingreso-andagoya',
        view  = views.transferencias_ingreso_andagoya,
        name  = 'transferencias_ingreso_andagoya'
    ),
    
    path(
        route = 'transferencia-ingres-andagoya-detalle/<str:n_transferencia>',
        view  = views.transferencia_ingres_andagoya_detalle,
        name  = 'transferencia_ingres_andagoya_detalle'
    ),
    
    path(
        route = 'dashboards-powerbi',
        view  = views.dashboards_powerbi,
        name  = 'dashboards_powerbi'
    ),
    
    # # DASHBOARDS VUE JS
    # path(
    #     route='picking_dashboard_vue_ban',
    #     view=views.picking_dashboard_vue_ban,
    #     name='picking_dashboard_vue_ban'
    # )
    
    path(
        route = 'pedidos-temporales/lista',
        view  = views.lista_pedidos_temporales,
        name  = 'lista_pedidos_temporales'
    ),
    
    path(
        route = 'pedidos-temporales/<int:pedido_id>',
        view  = views.pedido_temporal,
        name  = 'pedido_temporal'
    ),

    path(
        route = 'eliminar_producto_pedido_temporal',
        view  = views.eliminar_producto_pedido_temporal,
        name  = 'eliminar_producto_pedido_temporal'
    ),
    
    path(
        route = 'editar_producto_pedido_temporal',
        view  = views.editar_producto_pedido_temporal,
        name  = 'editar_producto_pedido_temporal'
    ),
    
    path(
        route = 'editar_estado_pedido_temporal',
        view  = views.editar_estado_pedido_temporal,
        name  = 'editar_estado_pedido_temporal'
    ),
    
    path(
        route = 'editar_pedido_temporal',
        view  = views.editar_pedido_temporal,
        name  = 'editar_pedido_temporal'
    ),
    
    ## transferencia
    path(
        route = 'inventario/transferencia',
        view  = views.inventario_transferencia,
        name  = 'inventario_transferencia'
    ),
    
    path(
        route = 'add_producto_transf_ajax',
        view  = views.add_producto_transf_ajax,
        name  = 'add_producto_transf_ajax'
    ),
    
    path(
        route = 'delete_producto_transf_ajax',
        view  = views.delete_producto_transf_ajax,
        name  = 'delete_producto_transf_ajax'
    ),
    
    path(
        route = 'transf_cer_and_activar_inactivar_ajax',
        view  = views.transf_cer_and_activar_inactivar_ajax,
        name  = 'transf_cer_and_activar_inactivar_ajax'
    ),
    
    path(
        route = 'get_transferencia_cer_and',
        view  = views.get_transferencia_cer_and,
        name  = 'get_transferencia_cer_and'
    ),
    
    path(
        route = 'transferencia_cer_and_email_ajax',
        view  = views.transferencia_cer_and_email_ajax,
        name  = 'transferencia_cer_and_email_ajax'
    ),
    
    
    ### WMS ANDAGOYA
    path(
        route = 'wms-andagoya/home',
        view  = views.wms_andagoya_home,
        name  = 'wms_andagoya_home'
    ),
    
    path(
        route = 'wms_andagoya_reporte_mba',
        view  = views.wms_andagoya_reporte_mba,
        name  = 'wms_andagoya_reporte_mba'
    ),
    
    path(
        route = 'reporte_error_lote_data',
        view  = views.reporte_error_lote_data,
        name  = 'reporte_error_lote_data'
    ),
    path(
        route = 'detalle_error_lote_data/<str:product_id>',
        view  = views.detalle_error_lote_data,
        name  = 'detalle_error_lote_data'
    ),
    
    path(
        route = 'reporte-error-lote',
        view  = views.reporte_error_lote,
        name  = 'reporte_error_lote'
    ),
]

