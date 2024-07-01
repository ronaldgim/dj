from django.urls import path

# JWT Django
# from rest_framework_simplejwt.views import (
#     TokenObtainPairView,
#     TokenRefreshView,
# )

from rest_framework.authtoken.views import obtain_auth_token

# Views
from api import views

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
        name = 'reg_sanitario_correo_alerta_dias'),
]
