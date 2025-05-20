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
    
    # inventarios
    path(
        route = 'inventarios-list',
        view = views.metro_inventarios_list,
        name = 'metro_inventarios_list'
    ),
    
    path(
        route = 'inventario-edit/<int:id>',
        view = views.metro_inventario_edit,
        name = 'metro_inventario_edit'
    ),
    
    
    # path(
    #     route = 'toma-fisica/<int:inventario_id>',
    #     view = views.TomaFisicaView.as_view(),
    #     name = 'metro_toma_fisica'
    # ),
    
    # path(
    #     route = 'toma-fisica-data/<int:inventario_id>',
    #     view = views.metro_toma_fisica_data,
    #     name = 'metro_toma_fisica_data'
    # ),
    
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
]