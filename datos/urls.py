# Urls
from django.urls import path

# Views functions
from datos import views

urlpatterns = [
       
    path(
        route='products/list',
        view=views.productos,
        name='products_list',    
    ),
    
    path(
        route='marcas/import',
        view=views.MarcaImportExcelCreateView.as_view(),
        name='marcas_import'
    ),
    
    
    path(
        route='marcas/list',
        view=views.cargar_marcas_excel,
        name='marcas_list',    
    ),
    
    path(
        route = 'productos/tabla',
        view = views.tabla_productos,
        name = 'productos_tabla'
    ),

    # EJECUTAR FUNCIÓN STOCK LOTE
    path(
        route = 'stocklote',
        view = views.stock_lote,
        name = 'stocklote'
    ),

    ### EXCEL
    path(
        route='product/<int:id>',
        view=views.product_detail,
        name='product_id',   
    ),

    path(
        route='freq-ventas',
        view=views.frecuancia_ventas,
        name='freq_ventas',   
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

]