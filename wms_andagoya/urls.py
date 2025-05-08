from django.urls import path

# Views functions
from wms_andagoya import views

urlpatterns = [
    
    # HOME
    path(
        route='home',
        view = views.wms_andagoya_home, #OK
        name = 'wms_adnagoya_home'
    ),
]