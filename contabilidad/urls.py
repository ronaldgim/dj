# Urls
from django.urls import path

# Views functions
from contabilidad import views

urlpatterns = [
    
    path(
        route = 'home',
        view = views.home,
        name = 'home'
    ),
]