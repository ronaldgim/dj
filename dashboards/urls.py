# Urls
from django.urls import path

# Views functions
from dashboards import views

urlpatterns = [
    
    # FRON ADMIN ACTULIZACIONES WAREHOUSE
    path(
        route = 'pedido_data',
        view = views.pedido_data,
        name = 'pedido_data'
    )
]