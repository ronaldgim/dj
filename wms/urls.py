# Urls
from django.urls import path

# Views functions
from wms import views

urlpatterns = [
    
    # Lista de Imprtaciones
    path(
        route='importaciones/list',
        view = views.wms_importaciones_list,
        name = 'wms_importaciones_list'
    ),

    # Detalle de importación y añadir bodega
    path(
        route='importacion/<str:o_compra>',
        view = views.wms_detalle_imp,
        name = 'wms_detalle_imp'
    ),

    # Ver detalle ya en tabla local y pedir ubicaciones
    path(
        route='importacion/bodega/<str:o_compra>',
        view = views.wms_bodega_imp,
        name = 'wms_bodega_imp'
    ),

    # Lista de importaciones ingresadas
    path(
        route='importaciones/ingresadas',
        view = views.wms_imp_ingresadas,
        name = 'wms_imp_ingresadas'
    ),

    # Movimientos - ingreso de productos y ubicaciones
    path(
        route='ingreso/<int:id>',
        view = views.wms_movimientos_ingreso,
        name = 'wms_ingreso'
    ),

    # Lista de movimientos
    path(
        route='movimientos/list',
        view = views.wms_movimientos_list,
        name = 'wms_movimientos_list'
    ),

    # Inventario
    path(
        route='inventario',
        view = views.wms_inventario,
        name = 'wms_inventario'
    ),

    # Movimiento Interno
    path(
        # route='inventario/mov-interno/<str:prod>/<str:lote>/<str:bod>/<str:pas>/<str:mod>/<str:niv>',
        route='inventario/mov-interno',
        view = views.wms_movimiento_interno,
        name = 'wms_mov_interno'
    ),

    # Listado de pedidos
    path(
        route='picking/list',  #<str:peedido', 
        view = views.wms_listado_pedidos,
        name = 'wms_listado_pedidos'
    ),

    # Egreso Picking
    path(
        route='picking/<str:pedido>', 
        view = views.wms_egreso_picking,
        name = 'wms_egreso_picking'
    ),

    # Movimiento Egreso Picking
    path(
        route='movimiento/egreso/picking', 
        view = views.wms_movimiento_egreso_picking,
        name = 'wms_movimiento_egreso_picking'
    ),

    # Eliminar Movimiento
    path(
        route='movimiento/eliminar', 
        view = views.wms_eliminar_movimiento,
        name = 'wms_eliminar_movimiento'
    ),
]
