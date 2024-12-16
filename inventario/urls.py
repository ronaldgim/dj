# Urls
from django.urls import path

# Views functions
from inventario import views

urlpatterns = [

    path(
        route = 'home',
        view = views.inventario_home,
        name = 'inventario_home'
    ),

    path(
        route = 'andagoya_get_stock',
        view = views.inventario_andagoya_get_stock,
        name = 'inventario_andagoya_get_stock',
    ),
    
    path(
        route = 'andagoya_actualizar_db',
        view = views.inventario_andagoya_actualizar_db,
        name = 'inventario_andagoya_actualizar_db',
    ),
    
    path(
        route = 'andagoya-reportes', 
        view  = views.inventario_andagoya_reportes, 
        name='inventario_andagoya_reportes'
    ),


    path(
        route='andagoya-home',
        view = views.inventario_andagoya_home,
        name = 'inventario_andagoya_home'
    ),

    # Reporte Inventario Completo EXCEL
    path(
        route='reporte/completo/excel',
        view = views.reporte_completo_excel,
        name = 'reporte_completo_excel'
    ), 

    # Reporte formato EXCEL
    path(
        route='reporte/format/excel',
        view = views.reporte_format_excel,
        name = 'reporte_format_excel'
    ), 

    # BODEGA UBICACIÓN LIST
    # QUERY DE PRODUCTOS POR BODEGA Y UBICACIÓN
    path(
        route='inv/<str:bodega>/<str:ubicacion>',
        view = views.inventario_por_bodega,
        name = 'inventario_por_bodega'
    ),
    
    # LISTA DE PRODUCTOS POR BODEGA
    path(
        route='toma-fisica/<str:bodega>/<str:location>',
        view = views.inventario_toma_fisica_andagoya_vue,
        name= 'inventario_toma_fisica_andagoya_vue'
    ),

    # GET ITEM TOMA FISICA
    path(
        route='toma-fisica/<int:item_id>',
        view = views.inventario_toma_fisica_item,
        name ="inventario_toma_fisica_item"
    ),
    
    path(
        route='toma-fisica/total-agrupado',
        view = views.inventario_toma_fisica_total_agrupado,
        name ="inventario_toma_fisica_total_agrupado"
    ),

    path(
        route='toma-fisica/buscar-producto',
        view = views.inventario_toma_fisica_buscar_producto,
        name ="inventario_toma_fisica_buscar_producto"
    ),
    
    path(
        route='toma-fisica/agregar-producto',
        view = views.inventario_toma_fisica_agregar_producto,
        name ="inventario_toma_fisica_agregar_producto"
    ),


    # Inventario Cerezos
    path(
        route='cerezos_actualizar_db',
        view = views.inventario_cerezos_actualizar_db,
        name = 'inventario_cerezos_actualizar_db'
    ),

    path(
        route='cerezos_get_stock',
        view = views.inventario_cerezos_get_stock,
        name = 'inventario_cerezos_get_stock'
    ),
    
    path(
        route='cerezos-reporte',
        view = views.inventario_cerezos_reportes,
        name = 'inventario_cerezos_reportes'
    ),

    path(
        route='cerezos-home',
        view = views.inventario_cerezos_home,
        name = 'inventario_cerezos_home'
    ),
    
    path(
        route='inv-cerezos/<str:bodega>/<str:ubicacion>',
        view = views.inventario_por_bodega_cerezos,
        name = 'inventario_por_bodega_cerezos'
    ),
    
    path(
        route='cerezos/toma-fisica/<str:bodega>/<str:location>',
        view = views.inventario_toma_fisica_cerezos_vue,
        name= 'inventario_toma_fisica_cerezos_vue'
    ),

    path(
        route='ubicaciones/wms',
        view = views.inventario_ubicaciones_wms,
        name = 'inventario_ubicaciones_wms'
    ),
    
    # GET ITEM TOMA FISICA
    path(
        route='cerezos/toma-fisica/<int:item_id>',
        view = views.inventario_cerezos_toma_fisica_item,
        name ="inventario_cerezos_toma_fisica_item"
    ),
    
    path(
        route='cerezos/toma-fisica/total-agrupado',
        view = views.inventario_cerezos_toma_fisica_total_agrupado,
        name ="inventario_cerezos_toma_fisica_total_agrupado"
    ),

    path(
        route='cerezos/toma-fisica/buscar-producto',
        view = views.inventario_cerezos_toma_fisica_buscar_producto,
        name ="inventario_cerezos_toma_fisica_buscar_producto"
    ),

    path(
        route='cerezos/toma-fisica/agregar-producto',
        view = views.inventario_cerezos_toma_fisica_agregar_producto,
        name ="inventario_cerezos_toma_fisica_agregar_producto"
    ),
    
    path(
        route='cerezos/toma-fisica/reporte-completo',
        view = views.reporte_cerezos_completo,
        name ="reporte_cerezos_completo"
    ),
    
    path(
        route='cerezos/toma-fisica/reporte-agrupado',
        view = views.reporte_cerezos_agrupado,
        name ="reporte_cerezos_agrupado"
    ),

    path(
        route='cerezos/toma-fisica/reporte-tf-mba',
        view = views.reporte_cerezos_tf_mba,
        name ="reporte_cerezos_tf_mba"
    ),
    
    # path(
    #     route='cerezos/toma-fisica/reporte-bpa',
    #     view = views.reporte_cerezos_bpa,
    #     name ="reporte_cerezos_bpa"
    # ),
    
    # # Actulizar stock lote FORM UPDDATE
    # path(
    #     route='inventario/<int:id>/<str:bodega>/<str:ubicacion>',
    #     view = views.inventario_update,
    #     name = 'inventario_update_form'
    # ), #inventario_update_totales

    # path(
    #     route='inventario/total/update/<int:id>',
    #     view = views.inventario_update_totales,
    #     name = 'inventario_total_update_form'
    # ), 

    # # Agregar stock lote FORM AGREGAR
    # path(
    #     route='inventario/new/<str:bodega>/<str:ubicacion>',
    #     view = views.inventario_agregar,
    #     name = 'inventario_agregar_form'
    # ),

    # path(
    #     route='inventario/inventario_inicial_wms',
    #     view = views.inventario_inicial_wms,
    #     name = 'inventario_inicial_wms'
    # ),



    ### ARQUEOS
    path(
            route='arqueos/new',
            view = views.nuevo_arqueo,
            name = 'nuevo_arqueo'
        ),

    # Arqueo view
    path(
            route='arqueos/view/<int:id>',
            view = views.arqueo_view,
            name = 'nuevo_view'
        ),


    path(
            route='arqueos/edit/view/<int:id>/<str:ware_code>',
            view = views.arqueo_edit_view,
            name = 'nuevo_edit_view'
        ),

    # Añadir item a arqueo
    path(
            route='arqueos/add/item',
            view = views.add_item_arqueo,
            name = 'add_item_arqueo'
        ),

    # eliminar_fila_arqueo 
    path(
            route='arqueos/eliminar-fila',
            view = views.eliminar_fila_arqueo,
            name = 'eliminar_fila_arqueo'
        ),

    # editar_fila_arqueo
    path(
            route='arqueos/editar-fila',
            view = views.editar_fila_arqueo,
            name = 'editar_fila_arqueo'
        ),
    
    # anular arqueo creado
    path(
            route='arqueos/creado-anular',
            view = views.anular_arqueo_creado,
            name = 'anular_arqueo_creado'
        ),

    # lista de arqueos
    path(
            route='arqueos/por-porbodega',
            view = views.arqueos_por_bodega,
            name = 'arqueos_por_bodega'
        ),
    
    
    path(
            route='arqueos/list',
            view = views.arqueos_list,
            name = 'arqueos_list'
        ),

    # Lista de arqueos pendientes por crear
    path(
            route='arqueos/pendientes/list',
            view = views.arqueos_pendientes_list,
            name = 'arqueos_pendientes_list'
        ),
    
    path(
            route='arqueos/bodega/view/<int:arqueo>/<str:ware_code>',
            view = views.arqueo_bodega_view,
            name = 'arqueo_bodega_view'
        ),
        
    path(
            route='arqueos/list/bodega/<str:ware_code>',
            view = views.arqueos_list_bodega,
            name = 'arqueos_list_bodega'
        ),

    path(
            route='arqueos/bodega/tomafisica/<int:arqueo>/<str:ware_code>',
            view = views.arqueo_bodega_tomafisica,
            name = 'arqueo_bodega_tomafisica'
        ),
    
    path(
            route='arqueos/cambiar_estado',
            view = views.arqueo_cambiar_estado_ajax,
            name = 'arqueo_cambiar_estado_ajax'
        ),

    path(
            route='arqueos/toma_fisica_inventario_ajax',
            view =views.toma_fisica_inventario_ajax,
            name='toma_fisica_inventario_ajax'
        ),

    path(
            route='arqueos/add_fisica_inventario_ajax',
            view =views.add_registro_tomafisica_ajax,
            name='add_registro_tomafisica_ajax'
    ),

    # add_obs2_ajax
    path(
            route='arqueos/add_obs2_ajax',
            view =views.add_obs2_ajax,
            name='add_obs2_ajax'
    ),

    ### TRAZABILIDAD
    path(
            route='trazabilidad',
            view =views.trazabilidad,
            name='trazabilidad'
    ),

]