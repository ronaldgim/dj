from django.contrib import admin
from users.models import UserPerfil, Permiso


@admin.register(UserPerfil)
class UserPerfilAdmin(admin.ModelAdmin):
    list_display = ('user','nombre','departamento','permisos_de_usuario')
    
    # def permisos_de_usuario(self, obj):
    #     return [f'{i.permiso}: {i.descripcion}\n' for i in obj.permisos.all()]
    
    def permisos_de_usuario(self, obj):
        return [f'{i.permiso}\n' for i in obj.permisos.all()]
    
    def nombre(self, obj):
        return obj.user.get_full_name()

@admin.register(Permiso)
class UserPermiso(admin.ModelAdmin):
    list_display = ('permiso', 'descripcion')