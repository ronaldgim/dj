from django.contrib import admin


from users.models import UserPerfil, Permiso


@admin.register(UserPerfil)
class UserPerfilAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'departamento', 'firma_carta', 'posicion_carta')


@admin.register(Permiso)
class UserPermiso(admin.ModelAdmin):
    list_display = ('id', 'permiso', 'descripcion')