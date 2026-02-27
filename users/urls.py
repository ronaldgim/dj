# Path
from django.urls import path

# Object Views
from users.views import LoginView #, LogoutView

# Functions Views
from users import views

# Urls

urlpatterns = [
    # Login
    path(
        route = 'login/',
        view  = LoginView.as_view(),
        name  = 'login'
    ),
    
    # # Logout
    # path(
    #     route = 'logout/',
    #     view  = LogoutView.as_view(),
    #     name  = 'logout'
    # ),
    
    path('logout/', views.logout_view, name='logout'),
    
    path(
        route = 'list/',
        view  = views.users_list,
        name  = 'users_list'
    ),
    
    path(
        route = 'slack-users-list',
        view  = views.UsuarioSlackListView.as_view(),
        name  = 'slack_users_list'
    ),
    
    path(
        route = 'sync-slack-users',
        view  = views.sync_slack_users,
        name  = 'sync_slack_users'
    ),
]

