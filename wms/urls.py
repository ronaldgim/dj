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
        view = views.wms_importaciones_list,
        name = 'wms_importaciones_list'
    ),

    # Lista de importaciones ingresadas
    path(
        route='importaciones/ingresadas',
        view = views.wms_imp_ingresadas,
        name = 'wms_imp_ingresadas'
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
    
    # Lista de inventario inicial por bodega
    path(
        route='inventario/inicial/list/bodegas',
        view = views.wms_inventario_inicial_list_bodega,
        name = 'wms_inventario_inicial_list_bodega'
    ),

    # Lista de inventario inicial por bodega
    path(
        route='inventario/inicial/<str:bodega>',
        view = views.wms_inventario_inicial_bodega,
        name = 'wms_inventario_inicial_bodega'
    ),
    
    # Inventario
    path(
        route='inventario',
        view = views.wms_inventario,
        name = 'wms_inventario'
    ),
    
    
    # """FUNCIONES DE MOVIMIENTO
    # """

    # Movimientos - ingreso de productos y ubicaciones
    # INVENTARIO INICIAL & IMPORTACIONES
    path(
        route='ingreso/<int:id>',
        view = views.wms_movimientos_ingreso,
        name = 'wms_ingreso'
    ),

    # Movimiento Interno
    path(
        route='mov-interno/<int:id>',
        view = views.wms_movimiento_interno,
        name = 'wms_mov_interno'
    ),

    # Liberaciones
    path(
        route='liberaciones',
        view = views.wms_lista_liberaciones,
        name = 'wms_lista_liberaciones'
    ),
    
    path(
        route='wms_liberacion',
        view = views.wms_liberacion,
        name = 'wms_liberacion'
    ),





    # Movimiento Ajuste
    path(
        route='inventario/mov-ajuste',
        view = views.wms_movimiento_ajuste,
        name = 'wms_movimiento_ajuste'
    ),







    path(
        route='ubicaciones/list/ingresos',
        view = views.wms_ubicaciones_list_ingreso,
        name = 'wms_ubicaciones_list_ingreso'
    ),
    
    
    path(
        route='mov/ingreso',
        view = views.wms_ing,
        name = 'wms_ing'
    ),
    
    
    # Ingresos
    path(
        route='mov/ingreso',
        view = views.wms_ing,
        name = 'wms_ing'
    ),







    

    

    
    # # PRUEBA INGRESOS
    # path(
    #     route='p/ing',
    #     view = views.wms_prueba_ing,
    #     name = 'prueba_ing'
    # ),
    


    # Lista de movimientos
    path(
        route='movimientos/list',
        view = views.wms_movimientos_list,
        name = 'wms_movimientos_list'
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
    
    # Picking realizados
    path(
        route='picking/realizado/list', 
        view = views.wms_productos_en_despacho_list,
        name = 'wms_productos_en_despacho_list'
    ),
]
