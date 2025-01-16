# Urls
from django.urls import path

# Views functions
from carta import views

urlpatterns = [
    
    # Cartas Inicio
    # path(
    
    # ),
        
    # Carta General
    path(
        route='general/new',
        view = views.carta_general,
        name = 'general_new'
    ),
    
    path(
        route='general/list',
        view= views.CartaGeneralList.as_view(),
        name='general_list'
    ),
        
    path(
        route='general/id/<slug:slug>',
        view = views.CartaGeneralPDF.as_view(),
        name = 'general_detail'
    ),
    
    path(
        route='general/anular/<slug:slug>',
        view = views.anular_cartageneral,
        name = 'anular_cartageneral'
    ),
    
    path(
        route='anular/general/list',
        view = views.CartaGeneralAnuladasList.as_view(),
        name ='anular_general_list'
    ),
    
    path(
        route='anular/general/<slug:slug>',
        view = views.CartaGeneralAnuladaDetailView.as_view(),
        name ='anular_general_detail'
    ),
    
    # Carta Procesos
    path(
        route='procesos/new',
        view= views.carta_procesos,
        name='procesos_new'
    ),
    
    path(
        route='procesos/list',
        view= views.CartaProcesosList.as_view(),
        name='procesos_list'
    ),
    
    path(
        route='procesos/id/<slug:slug>',
        view = views.CartaProcesosPDF.as_view(),
        name = 'procesos_detail'
    ),
    
    path(
        route='procesos/anular/<slug:slug>',
        view = views.anular_cartaprocesos,
        name = 'anular_cartaprocesos'
    ),
    
    path(
        route='anular/procesos/list',
        view =views.AnularCartaProcesosList.as_view(),
        name = 'anular_procesos_list'
    ),
    
    path(
        route='anular/procesos/<slug:slug>',
        view = views.CartaProcesosAnuladaDetailView.as_view(),
        name ='anular_procesos_detail'
    ),
    
    # Carta Items
    path(
        route='items/new',
        view= views.carta_items,
        name='items_new'
    ),
    
    path(
        route='items/list',
        view= views.CartaItemsList.as_view(),
        name='items_list'
    ),
    
    path(
        route='items/id/<slug:slug>',
        view = views.CartaItemsPDF.as_view(),
        name = 'items_detail'
    ),
    
    path(
        route='items/anular/<slug:slug>',
        view = views.anular_cartaitem,
        name = 'anular_cartaitem'
    ),
    
    path(
        route='anular/items/list',
        view =views.AnularCartaItemList.as_view(),
        name = 'anular_items_list'
    ),
    
    path(
        route='anular/items/<slug:slug>',
        view =views.CartaItemAnuladaDetailView.as_view(),
        name = 'anular_items_detail'
    ),
    
    path(
        route='buscar_cliente_por_ruc_ajax',
        view = views.buscar_cliente_por_ruc_ajax,
        name = 'buscar_cliente_por_ruc_ajax'
    ),
]