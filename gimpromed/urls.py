"""gimpromed URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

# Inicio view
from datos import views

urlpatterns = [
    
    # Inicio
    path('', views.Inicio.as_view(), name='inicio'),

    # Admin
    path('admin/', admin.site.urls),
    
    # Users
    path('users/', include('users.urls')),
    
    # Datos
    path('datos/', include('datos.urls')),
    
    # Cartas
    path('cartas/', include('carta.urls')),
    
    # Etiquetado
    path('etiquetado/', include('etiquetado.urls')),
    
    # Mantenimiento
    path('mantenimiento/', include('mantenimiento.urls')),

    # Inventario
    path('inventario/', include('inventario.urls')),

    # BPA
    path('bpa/', include('bpa.urls')),
    
    # BPA
    path('compras-publicas/', include('compras_publicas.urls')),

    # REGULATORIO - LEGAL
    path('regulatorio-legal/', include('regulatorio_legal.urls')),

    # VENTAS
    path('ventas/', include('ventas.urls')),

    # WMS
    path('wms/', include('wms.urls')),
    
    # API
    path('api/', include('api.urls')),
    
    # API
    path('metro/', include('metro.urls'))
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
