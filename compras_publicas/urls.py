# Urls
from django.urls import path

# Views functions
from compras_publicas import views

urlpatterns = [

    path(
        route='precios-historicos',
        view = views.precios_historicos,
        name = 'precios_historicos'
    ),

    path(
        route='infimas', #?page=1
        view = views.infimas,
        name = 'infimas'
    ),

    path('ajax/my_view/', views.my_ajax_view, name='my_ajax_view'),
]