# Render
from django.shortcuts import render

# Autentication
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin


# Views

# Login View
class LoginView(auth_views.LoginView):
    template_name = 'users/login.html'


# Logout View
class LogoutView(LoginRequiredMixin, auth_views.LogoutView):
    template_name = 'users/logout.html'
