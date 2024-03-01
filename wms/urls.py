# Urls
from django.urls import path

# Views functions
from wms import views

urlpatterns = [
    
    # """LISTA DE INGRESOS
    # """
    
    # Lista de Imprtaciones
    path(
        route='importaciones/list',
        view = views.wms_importaciones_list, #OK
        name = 'wms_importaciones_list'
    ),

    # Lista de importaciones ingresadas
    path(
        route='importaciones/ingresadas',
        view = views.wms_imp_ingresadas, #OK
        name = 'wms_imp_ingresadas'
    ),

    # Detalle de importación y añadir bodega
    path(
        route='importacion/<str:o_compra>',
        view = views.wms_detalle_imp, #OK
        name = 'wms_detalle_imp'
    ),

    # Importaciones en transito list
    path(
        route='importaciones/transito/list',
        view = views.wms_importaciones_transito_list, #OK
        name = 'wms_importaciones_transito_list'
    ),
    
    # Importaciones en transito detalle
    path(
        route='importaciones/transito/detalle/<str:contrato_id>',
        view = views.wms_importaciones_transito_detalle, #OK
        name = 'wms_importaciones_transito_detalle'
    ),
    
    # Ver detalle ya en tabla local y pedir ubicaciones
    path(
        route='importacion/bodega/<str:o_compra>',
        view = views.wms_bodega_imp, #OK
        name = 'wms_bodega_imp'
    ),
    
    # Lista de inventario inicial por bodega
    path(
        route='inventario/inicial/list/bodegas',
        view = views.wms_inventario_inicial_list_bodega, #OK
        name = 'wms_inventario_inicial_list_bodega'
    ),

    # Lista de inventario inicial por bodega
    path(
        route='inventario/inicial/<str:bodega>',
        view = views.wms_inventario_inicial_bodega, #OK
        name = 'wms_inventario_inicial_bodega'
    ),
    
    # Inventario
    path(
        route='inventario',
        view = views.wms_inventario, #OK
        name = 'wms_inventario'
    ),
    
    
    # FUNCIONES DE MOVIMIENTO

    # Movimientos - ingreso de productos y ubicaciones
    # INVENTARIO INICIAL & IMPORTACIONES
    path(
        route='ingreso/<int:id>',
        view = views.wms_movimientos_ingreso, #OK
        name = 'wms_ingreso'
    ),

    # Movimiento Interno
    path(
        route='mov-interno/<int:id>',
        view = views.wms_movimiento_interno, #OK
        name = 'wms_mov_interno'
    ),
    
    # Movimiento Interno get ubi_list
    path(
        route='mov-interno/get/ubi_list',
        view = views.wms_movimiento_interno_get_ubi_list_ajax, #OK
        name = 'wms_movimiento_interno_get_ubi_list_ajax'
    ),
    
    # Verificar ubicación para movimiento interno CN6
    path(
        route='mov-interno/get/ubi_destino/data',
        view = views.wms_verificar_ubicacion_destino_ajax, #OK
        name = 'wms_verificar_ubicacion_destino_ajax'
    ),


    # Movimiento Ajuste
    path(
        route='inventario/mov-ajuste',
        view = views.wms_movimiento_ajuste, #OK
        name = 'wms_movimiento_ajuste'
    ),

    
    path(
        route='inventario/mov-ajuste/product/ajax',
        view = views.wms_ajuste_product_ajax, #OK
        name = 'wms_ajuste_product_ajax'
    ),
    
    path(
        route='inventario/mov-ajuste/lote/ajax',
        view = views.wms_ajuste_lote_ajax, #OK
        name = 'wms_ajuste_lote_ajax'
    ),
    
    
    path(
        route='inventario/mov-ajuste/fecha/ajax',
        view = views.wms_ajuste_fecha_ajax, #OK
        name = 'wms_ajuste_fecha_ajax'
    ),
    
    
    # Lista de movimientos
    path(
        route='movimientos/list',
        view = views.wms_movimientos_list, #OK
        name = 'wms_movimientos_list'
    ),
    
    
    ### PICKING
    # Listado de pedidos
    path(
        route='picking/list',  
        view = views.wms_listado_pedidos, #OK
        name = 'wms_listado_pedidos'
    ),

     ### INGRESO AJUSTE
    #Buscar ajuste
    path(
        route='ajuste/search',  
        view = views.wms_ingreso_ajuste, #OK
        name = 'wms_ingreso_ajuste'
    ),

    path(
        route='wms-busqueda-ajuste/<int:n_ajuste>',  
        view = views.wms_busqueda_ajuste, #OK
        name = 'wms-busqueda-ajuste'
    ),


    # Egreso Picking
    path(
        route='picking/<str:n_pedido>', 
        view = views.wms_egreso_picking, #OK
        name = 'wms_egreso_picking'
    ),

    # Estado Picking AJAX
    path(
        route='picking/estado/ajax', 
        view = views.wms_estado_picking_ajax, #PRUEBA
        name = 'wms_estado_picking_ajax'
    ),
    
    # Actualizar Estado Picking AJAX
    path(
        route='picking/estado/actualizar/ajax', 
        view = views.wms_estado_picking_actualizar_ajax, #PRUEBA
        name = 'wms_estado_picking_actualizar_ajax'
    ),

    # Movimiento Egreso Picking
    path(
        route='movimiento/egreso/picking', 
        view = views.wms_movimiento_egreso_picking, #OK
        name = 'wms_movimiento_egreso_picking'
    ),

    # Eliminar Movimiento
    path(
        route='movimiento/eliminar', 
        view = views.wms_eliminar_movimiento, #OK
        name = 'wms_eliminar_movimiento'
    ),
    
    #wms_reservas_lote_consulta_ajax
    path(
        route='reservas/consulta', 
        view = views.wms_reservas_lote_consulta_ajax, #OK
        name = 'wms_reservas_lote_consulta_ajax'
    ),
    
    # Productos en despacho list
    path(
        route='picking/producto-despacho/list', 
        view = views.wms_productos_en_despacho_list, #OK
        name = 'wms_productos_en_despacho_list'
    ),
    
    # Picking en despacho list
    path(
        route='picking/picking-despacho/list', 
        view = views.wms_picking_en_despacho_list, #OK
        name = 'wms_picking_en_despacho_list'
    ),
    
    # wms_cruce_picking_factura
    path(
        route='cruce/picking/facturas', 
        view = views.wms_cruce_picking_factura,
        name = 'wms_cruce_picking_factura'
    ),
    
    # wms_cruce_check_despacho
    path(
        route='cruce/check/despacho',
        view = views.wms_cruce_check_despacho,
        name = 'wms_cruce_check_despacho'
    ),
    
    # btn actualizar toda tabla de existencias
    path(
        route='actualizar/todas/existencias',
        view = views.wms_btn_actualizar_todas_existencias,
        name = 'wms_btn_actualizar_todas_existencias'
    ),
    
    # Revisión de transferencia
    path(
        route='revision/trasferencia/ajax',
        view = views.wms_revision_transferencia_ajax,
        name = 'wms_revision_transferencia_ajax'
    ),
    
    path(
        route='revision/trasferencia',
        view = views.wms_revision_transferencia,
        name = 'wms_revision_transferencia'
    ),
    
    
    path(
        route='transferencia/input/ajax',
        view = views.wms_transferencia_input_ajax,
        name = 'wms_transferencia_input_ajax'
    ),
    
    
    path(
        route='transferencias/list',
        view = views.wms_transferencias_list,
        name = 'wms_transferencias_list'
    ),
    
    
    path(
        route='transferencia/<str:n_transf>',
        view = views.wms_transferencia_picking,
        name = 'wms_transferencia_picking'
    ),
    
    # Lista de transferencias ingresadas a Cerezos
    path(
        route='transferencia/ingreso/cerezos/list',
        view = views.wms_transferencia_ingreso_cerezos_list,
        name = 'wms_transferencia_ingreso_cerezos_list'
    ),
    
    # Lista de transferencias ingresadas a Cerezos
    path(
        route='transferencia/ingreso/cerezos/<str:n_transferencia>',
        view = views.wms_transferencia_ingreso_cerezos_detalle,
        name = 'wms_transferencia_ingreso_cerezos_detalle'
    ),
    
    
    # Ingresar a inventario todos los productos de transferencia
    path(
        route='transferencia/ingreso/cerezos/input/ajax',
        view = views.wms_transferencia_ingreso_cerezos_input_ajax,
        name = 'wms_transferencia_ingreso_cerezos_input_ajax'
    ),
    
    # Liberación ingresar a inventario todos los productos de transferencia
    path(
        route='transferencia/ingreso/cerezos/liberacion/ajax',
        view = views.wms_transferencia_ingreso_cerezos_liberacion_ajax,
        name = 'wms_transferencia_ingreso_cerezos_liberacion_ajax'
    ),
    
    
    # Movimiento de egreso transferencia
    path(
        route='transferencia/movimiento/egreso/transferencia',
        view = views.wms_movimiento_egreso_transferencia,
        name = 'wms_movimiento_egreso_transferencia'
    ),
    
    
    # Reporte RM
    path(
        route='reporte/rm',
        view = views.wms_resposicion_rm,
        name = 'wms_resposicion_rm'
    ),
    
    path(
        route='reporte/nivelunovacio/rm',
        view = views.wms_reporte_nivelunovacio_rm,
        name = 'wms_reporte_nivelunovacio_rm'
    ),
    
    
    # Notas de entrega
    path(
        route='notas-entrega/list',
        view = views.wms_nota_entrega_list,
        name = 'wms_nota_entrega_list'
    ),
    
    path(
        route='nota-entrega/input/ajax',
        view = views.wms_nota_entrega_input_ajax,
        name = 'wms_nota_entrega_input_ajax'
    ),
    
    
    path(
        route='nota-entrega/picking/<int:n_entrega>',
        view = views.wms_nota_entrega_picking,
        name = 'wms_nota_entrega_picking'
    ),
    
    path(
        route='nota-entrega/picking/ajax',
        view = views.wms_movimiento_egreso_nota_entrega,
        name = 'wms_movimiento_egreso_nota_entrega'
    ),
    
    
    # Anulación de pikcing
    path(
        route='anulacion-picking/list',
        view = views.wms_anulacion_picking_list,
        name = 'wms_anulacion_picking_list'
    ),
    
    path(
        route='anulacion-picking/detalle/<int:id_anulacion>',
        view = views.wms_anulacion_picking_detalle,
        name = 'wms_anulacion_picking_detalle'
    ),
    
    path(
        route='anulacion-picking/ajax',
        view = views.wms_anulacion_picking_ajax,
        name = 'wms_anulacion_picking_ajax'
    ),
    
    
    # Ajuste liberación ERIK
    path(
        route='ajuste-liberacion/list',
        view = views.wms_ajuste_liberacion_list,
        name = 'wms_ajuste_liberacion_list'
    ),
    
    path(
        route='ajuste-liberacion/wms_ajuste_liberacion_input_ajax',
        view = views.wms_ajuste_liberacion_input_ajax,
        name = 'wms_ajuste_liberacion_input_ajax'
    ),
    
    path(
        route='ajuste-liberacion/detalle/<str:n_liberacion>',
        view = views.wms_ajuste_liberacion_detalle,
        name = 'wms_ajuste_liberacion_detalle'
    ),
]
