# Urls
from django.urls import path

# Views functions
from bpa import views

urlpatterns = [

    ### IMPORTACIONES ###
    # Listado de muestreo
    path(
        route='muestreos/importaciones',
        view = views.importaciones,
        name = 'bpa_importaciones_list'
    ),
    
    #importaciones_transito
    path(
        route='muestreos/importaciones/transito',
        view = views.importaciones_transito,
        name = 'bpa_importaciones_transito_list'
    ),
    # Lista de nacionales
    path(
        route= 'nac_list',
        view = views.nacionales,
        name = 'bpa_nac_list'
    ),

    # Muestreo unidades
    path(
        route='muestreos/importaciones/unidades/<str:memo>',
        view = views.muestreo_unidades,
        name = 'muestreos_imp_unidades'
    ),

    # Muestreo cartones
    path(
        route='muestreos/importaciones/cartones/<str:memo>',
        view = views.muestreo_cartones,
        name = 'muestreos_imp_cartones'
    ),

    # Muestreo unidades transito
    path(
        route='muestreos/importaciones/transito/unidades/<str:contrato_id>',
        view = views.muestreo_unidades_transito,
        name = 'muestreos_imp_unidades_transito'
    ),
    
    #muestreo_cartones_transito
    path(
        route='muestreos/importaciones/transito/cartones/<str:contrato_id>',
        view = views.muestreo_cartones_transito,
        name = 'muestreos_imp_cartones_transito'
    ),
    
    # Revisión tecnica
    path(
        route='muestreos/revisiontecnica/<str:memo>',
        view = views.revision_tecnica,
        name = 'revision_tencnica'
    ),

    ### TRANSFERENCIAS ###
    # Tabla transito
    path(
        route='muestreos/transferencias',
        view = views.transferencias,
        name = 'transferencias_list'
    ),

    path(
        route='muestreos/transferencias/<str:doc>',
        view = views.muestreo_transferencia,
        name = 'muestreo_transferencias'
    ),

    path(
        route='muestreos/transferencias/revisiontecnica/<str:doc>',
        view = views.revision_tecnica_transferencia,
        name = 'muestreo_transferencias_revisiontecnica'
    ),

    ### REGISTROS SANITARIO ###
    # List
    path(
        route= 'reg-san/list',
        view = views.reg_san_list,
        name = 'reg_san_list'
    ),
    
    # Envio de alertas de Caducidad de R.Sanitario por Lista.
    path(
        route= 'reg-san/alerta/list/correo',
        view = views.r_san_alerta_list_correo,
        name = 'r_san_alerta_list_correo'
    ),

    ## Envio de alertas de Caducidad de R.Sanitario por documento y dias.
    path(
        route= 'reg-san/alerta/correo',
        view = views.r_san_alert,
        name = 'r_san_alerta_correo'
    ),

    # Nuevo
    path(
        route= 'reg-san/new',
        view = views.reg_san_new,
        name = 'reg_san_new'
    ),

    # Edit
    path(
        route= 'reg-san/edit/<int:id>',
        view = views.reg_san_edit,
        name = 'reg_san_edit'
    ),

    ### CARTA NO REGISTRO 
    # List
    path(
        route= 'carta-no-reg/list',
        view = views.carta_no_reg_list,
        name = 'carta_no_reg_list'
    ),
    # New
    path(
        route= 'carta-no-reg/new',
        view = views.carta_no_reg_new,
        name = 'carta_no_reg_new'
    ),

    # Edit
    path(
        route= 'carta-no-reg/edit/<int:id>',
        view = views.carta_no_reg_edit,
        name = 'carta_no_reg_edit'
    ),

]