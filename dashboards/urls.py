# Urls
from django.urls import path

# Views functions
from dashboards import views

urlpatterns = [
    
    path(
        route = 'data_publicos_dashboard_completo',
        view = views.data_publicos_dashboard_completo,
        name = 'data_publicos_dashboard_completo'
    ),
    
    path(
        route = 'publico',
        view = views.dashboard_publico,
        name = 'dashboard_publico'
    ),
    
    path(
        route = 'completo',
        view = views.dashboard_completo,  #pedido_data, 
        name = 'dashboard_completo'
    )
]