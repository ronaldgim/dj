# Urls
from django.urls import path

# Views functions
from metro import views

urlpatterns = [

    # productos
    path(
        route = 'products-list',
        view = views.metro_products_list,
        name = 'metro_products_list'
    ),
    
    path(
        route = 'products-edit/<int:id>',
        view = views.metro_product_edit,
        name = 'metro_product_edit'
    ),
    
    path(
        route = 'metro_cambiar_orden_productos_ajax',
        view = views.metro_cambiar_orden_productos_ajax,
        name = 'metro_cambiar_orden_productos_ajax'
    ),
    
    # inventarios
    path(
        route = 'inventarios-list',
        view = views.metro_inventarios_list,
        name = 'metro_inventarios_list'
    ),
    
    path(
        route = 'inventario-edit-patch/<int:id>',
        view = views.metro_inventario_patch,
        name = 'metro_inventario_patch'
    ),
    
    path(
        route = 'inventario-informe/<int:id>',
        view = views.metro_inventario_informe,
        name = 'metro_inventario_informe'
    ),
    
    path(
        route = 'inventario-informe-excel/<int:id>',
        view = views.metro_inventario_informe_excel,
        name = 'metro_inventario_informe_excel'
    ),
    
    path(
        route = 'toma-fisica-list',
        view = views.metro_toma_fisica_list,
        name = 'metro_toma_fisica_list'
    ),
    
    path(
        route = 'toma-fisica/<int:inventario_id>',
        view = views.metro_toma_fisica,
        name = 'metro_toma_fisica'
    ),
    
    path(
        route = 'toma-fisica-edit/<int:id>',
        view = views.metro_toma_fisica_edit,
        name = 'metro_toma_fisica_edit'
    ),
    
    path(
        route = 'inventario-revision/<int:id>',
        view = views.metro_inventario_revision,
        name = 'metro_inventario_revision'
    ),
    
    path(
        route = 'metro_cambiar_orden_revision_ajax',
        view = views.metro_cambiar_orden_revision_ajax,
        name = 'metro_cambiar_orden_revision_ajax'
    ),
    
    path(
        route = 'revision-check/<int:id>',
        view = views.revision_check,
        name = 'revision_check'
    ),
    
    path(
        route = 'consignacion',
        view = views.metro_consignacion,
        name = 'metro_consignacion'
    ),
    
    path(
        route = 'kardex/<int:product_id>',
        view = views.metro_kardex,
        name = 'metro_kardex'
    ),
]