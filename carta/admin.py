# Admin
from django.contrib import admin

# Model
from carta.models import CartaGeneral, CartaProcesos, CartaItem


# # Register your models here.
# @admin.register(CartaGeneral)
# class CartaGeneralAdmin(admin.ModelAdmin):
#     list_display = ('id', 'oficio', 'ruc', 'cliente', 'fecha_emision')
#     search_fields = ['id','ruc']


# @admin.register(CartaProcesos)
# class CartaProcesosAdmin(admin.ModelAdmin):
#     list_display = ('id', 'oficio', 'ruc', 'cliente', 'fecha_emision')
#     search_fields = ['id','ruc']


# @admin.register(CartaItem)
# class CartaItemAdmin(admin.ModelAdmin):
#     list_display = ('id', 'oficio', 'ruc', 'cliente', 'fecha_emision')
#     search_fields = ['id','ruc']