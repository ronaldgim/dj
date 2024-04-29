# Urls
from django.urls import path

# Views functions
from etiquetado import views

urlpatterns = [
    
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
        # route = 'picking/estado/<str:n_pedido>/<str:id>',
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

    
    # Dashboard pedidos andagoya
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
        route = 'publico/dashboard/completo',
        view  = views.dashboard_completo,
        name  = 'dashboard_completo'
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
]
