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

    
    # IMPORTACIONES EXCEL
    path(
        route= 'imp_list',
        view = views.importacion_list,
        name = 'imp_list'
    ),

    path(
        route= 'imp_create',
        view = views.importacion_create,
        name = 'imp_create'
    ),

    path(
        route= 'imp_detail/<int:id>',
        view = views.importacion_detail,
        name = 'imp_detail'
    ),

    # # Transferencias ODBC
    # path(
    #     route= 'transf/muestreo',
    #     view = views.doc_transferencia,
    #     name = 'trasf_muestreo'
    # ),

]