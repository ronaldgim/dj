# Urls
from django.urls import path

# Views functions
from inventario import views

urlpatterns = [

    # Actulizar stock lote TABLA
    path(
        route='actualizar/inventario',
        view = views.actualizar_stock_inventario,
        name = 'actualizar_stock'
    ),

    path(
        route='bodegas',
        view = views.inventario_home,
        name = 'inv_home'
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
    path(
        route='inv/<str:bodega>/<str:ubicacion>',
        view = views.inventario_por_bodega,
        name = 'inventario_por_bodega'
    ),

    # Actulizar stock lote FORM UPDDATE
    path(
        route='inventario/<int:id>/<str:bodega>/<str:ubicacion>',
        view = views.inventario_update,
        name = 'inventario_update_form'
    ), #inventario_update_totales

    path(
        route='inventario/total/update/<int:id>',
        view = views.inventario_update_totales,
        name = 'inventario_total_update_form'
    ), 

    # Agregar stock lote FORM AGREGAR
    path(
        route='inventario/new/<str:bodega>/<str:ubicacion>',
        view = views.inventario_agregar,
        name = 'inventario_agregar_form'
    ),


    ### DATOS ###
    # Stock por caducar
    path(
        route='porcaducar/',
        view = views.stock_por_caducar,
        name = 'porcaducar'
    ),

    # Volumen
    path(
        route='volumen/',
        view = views.volumen_bodegas,
        name = 'volumen'
    ),


    ### ARQUEOS
    path(
            route='arqueos/new',
            view = views.nuevo_arqueo,
            name = 'nuevo_arqueo'
        ),

    ### ARQUEO VIEW
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

    # Trazabilidad
    path(
            route='trazabilidad',
            view =views.trazabilidad,
            name='trazabilidad'
    ),

]