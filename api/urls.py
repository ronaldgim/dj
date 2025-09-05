from django.urls import path

# JWT Django
# from rest_framework_simplejwt.views import (
#     TokenObtainPairView,
#     TokenRefreshView,
# )

from rest_framework.authtoken.views import obtain_auth_token

# Views
from api import views
from api import warehouse_data

urlpatterns = [
    
    # Autenticación JWT
    # path(
    #     'token/', 
    #     TokenObtainPairView.as_view(), 
    #     name='token_obtain_pair'
    #     ),
    
    # path(
    #     'api/token/refresh/', 
    #     TokenRefreshView.as_view(), 
    #     name='token_refresh'
    #     ),
    
    # Autenticación DRF
    path(
            route = 'api-token-auth',
            view  = obtain_auth_token,
            name  = 'api_token_auth'
        ),
    
    
    # reg_sanitario_correo_alerta_list
    path(
            route = 'reg_sanitario_correo_alerta_list/', 
            view = views.reg_sanitario_correo_alerta_list, 
            name = 'reg_sanitario_correo_alerta_list'
        ),
    
    # reg_sanitario_correo_alerta_dias
    path(
            route = 'reg_sanitario_correo_alerta_dias/', 
            view = views.reg_sanitario_correo_alerta_dias, 
            name = 'reg_sanitario_correo_alerta_dias'
        ),
    
    # api promociones
    path(
            route = 'precio_promocion/<str:product_id>/', 
            view = views.precio_promocion, 
            name = 'precio_promocion'
        ),
    
    # api promociones
    path(
            route = 'infimas_general/<str:codigo>/', 
            view = views.infimas_general, 
            name = 'infimas_general'
        ),
    
    
    ### WHAREHOUSE DATA
    path(
        route = 'warehouse-query',
        view  = warehouse_data.api_warehouse_query,
        name  = 'warehouse-query'
    ),
    
    # clientes wharehouse
    path(
        route = 'warehouse-clientes-list',
        view  = warehouse_data.api_clientes_list,
        name  = 'warehouse-clientes-list'
    ),
    path(
        route = 'warehouse-cliente/<str:column_name>/<str:column_value>',
        view  = warehouse_data.api_get_cliente,
        name  = 'warehouse-cliente'
    ),
    
    # productos wharehouse
        path(
        route = 'warehouse-productos-list',
        view  = warehouse_data.api_productos_list,
        name  = 'warehouse-productos-list'
    ),
    path(
        route = 'warehouse-producto/<str:codigo>',
        view  = warehouse_data.api_get_producto,
        name  = 'warehouse-producto'
    ),
]
