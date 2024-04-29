# Urls
from django.urls import path

# Views functions
from mantenimiento import views


urlpatterns = [
    
    # import
    # path(
    #     route='import',
    #     view = views.impor_data,
    #     name = 'import'
    # ),
           
    # EQUIPOS
    # Listar Equipo
    path(
        route='equipos/list',
        view = views.EquipoList.as_view(),
        name = 'equipos_list'
    ),
    
    # Crear Equipo
    path(
        route='equipos/new',
        view = views.EquipoCreate.as_view(),
        name = 'equipos_new'
    ),
    
    # SUMINISTROS
    # Listar suministros
    path(
        route='suministros/list',
        view = views.SuministroList.as_view(),
        name = 'suministros_list'
    ),
    
    path(
        route='suministros/new',
        view = views.SuministroCreate.as_view(),
        name = 'suministros_new'
    ),
    
    # ESTADISTICA
    # Listar suministros
    path(
        route='estadisticas/list',
        view = views.EstadisticaList.as_view(),
        name = 'estadisticas_list'
    ),
    
    path(
        route='estadisticas/new',
        view = views.EstadisticaCreate.as_view(),
        name = 'estadisticas_new'
    ),


    # MANTENIMIENTO
    # Listar suministros
    path(
        route='mantenimientos/list',
        view = views.MantenimientoList.as_view(),
        name = 'mantenimientos_list'
    ),
    
    path(
        route='mantenimientos/new',
        view = views.MantenimientoCreate.as_view(),
        name = 'mantenimientos_new'
    ),

    path(
        route = 'est/<int:equipo>',
        view  = views.lista_estadisticas,
        name  = 'est'
    ),
    
    ### MANTENIMIENTO PREVENTIVO
    # Lista de mantenimientos
    path(
        route = 'preventivo/list',
        view  = views.list_mpreventivos,
        name  = 'preventivo_list'
    ),
    
    # Lista de mantenimientos por realizar
    path(
        route = 'preventivo/por-realizar/list',
        view  = views.list_mpreventivos_por_realizar,
        name  = 'preventivo__por_realizar_list'
    ),
    
    # Realizar mantenimiento
    path(
        route = 'preventivo/realizar/<int:id>',
        view  = views.realizar_mpreventivo,
        name  = 'realizar_mpreventivo'
    )
]