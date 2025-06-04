# Render
from django.shortcuts import render

# Autentication
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from users.models import UserPerfil, Permiso
from django.contrib.auth.decorators import login_required
from datos.views import permisos

# Login View
class LoginView(auth_views.LoginView):
    template_name = 'users/login.html'


# Logout View
class LogoutView(LoginRequiredMixin, auth_views.LogoutView):
    template_name = 'users/logout.html'


@login_required(login_url='login')
@permisos(['ADMINISTRADOR'], '/wms/home', 'ingresar a Lista de usuarios')
def users_list(request):
    
    users = UserPerfil.objects.all().order_by('user__first_name', 'user__last_name')
    permisos = Permiso.objects.all().order_by('permiso')
    context = {
        'users':users,
        'permisos':permisos
    }
    return render(request, 'users/users_list.html', context)