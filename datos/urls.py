# Urls
from django.urls import path

# Views functions
from datos import views

urlpatterns = [
    
    # FRON ADMIN ACTULIZACIONES WAREHOUSE
    path(
        route = 'admin_actualizar_warehouse_view',
        view = views.admin_actualizar_warehouse_view,
        name = 'admin_actualizar_warehouse_view'
    ),
    
    path(
        route = 'admin_actualizar_warehouse_json_response',
        view = views.admin_actualizar_warehouse_json_response,
        name = 'admin_actualizar_warehouse_json_response'
    ),

    path(
        route = 'cambiar_conexion_de_warehouse',
        view = views.cambiar_conexion_de_warehouse,
        name = 'cambiar_conexion_de_warehouse'
    ),
    # EJECUTAR FUNCIÓN STOCK LOTE COMPLETA
    path(
        route = 'stocklote',
        view = views.stock_lote,
        name = 'stocklote'
    ),

    # ACTUALIZAR ETIQUETADO AJAX
    path(
        route='etiquetado_ajax',
        view=views.etiquetado_ajax,
        name='etiquetado_ajax',   
    ),


    path(
        route='reservas_lote_actualizar_odbc',
        view=views.reservas_lotes_actualizar_odbc,
        name='reservas_lotes_actualizar_odbc',   
    ),


    # ACTUALIZAR IMPORTACIONES LLEGADAS
    path(
        route='actualizar_imp_llegadas_odbc',
        view=views.actualizar_imp_llegadas_odbc,
        name='actualizar_imp_llegadas_odbc',   
    ),

    # ACTUALIZAR IMPORTACIONES LLEGADAS
    path(
        route='tramaco_function_ajax',
        view=views.tramaco_function_ajax,
        name='tramaco_function_ajax',   
    ),

    # Query notas de credito
    path(
        route='wms_datos_nota_entrega',
        view=views.wms_datos_nota_entrega,
        name='wms_datos_nota_entrega',   
    ),
    
    # Actualizar proformas ajax
    path(
        route='actualizar_proformas_ajax',
        view=views.actualizar_proformas_ajax,
        name='actualizar_proformas_ajax',
    ),
    
    
    #### PICKING ESTADISTICAS
    # path(
    #     route='obtener_data_picking_estadistica',
    #     view=views.obtener_data_picking_estadistica,
    #     name='obtener_data_picking_estadistica',
    # ),
    
    # path(
    #     route='actualizar_picking_stadisticas_all',
    #     view=views.actualizar_picking_stadisticas_all,
    #     name='actualizar_picking_stadisticas_all',
    # ),
    
    # path(
    #     route='pipeline_picking_estadisticas_batch/<int:year>/<int:month>',
    #     view=views.pipeline_picking_estadisticas_batch,
    #     name='pipeline_picking_estadisticas_batch',
    # ),
    
    path(
        route='registros_estadopicking_year_month/<int:year>/<int:month>',
        view=views.registros_estadopicking_year_month,
        name='registros_estadopicking_year_month',
    ),

    # CRON ENDPOINTS
    path('cron/tablas-criticas/', views.cron_tablas_criticas, name='cron_tablas_criticas'),
    path('cron/tablas-moderadas/', views.cron_tablas_moderadas, name='cron_tablas_moderadas'),
    path('cron/tablas-baja-frecuencia/', views.cron_tablas_baja_frecuencia, name='cron_tablas_baja_frecuencia'),
]