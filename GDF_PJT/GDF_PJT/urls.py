from django.contrib import admin
from django.urls import path
from app import views

urlpatterns = [
    # Admin site
    path('admin/', admin.site.urls),

    # App views
    path('Login/', views.Login_view, name='Login'),
    path('Home/',views.Home_view, name='Home'),
    path('get_subsolucao/<str:cod_sub>/', views.get_subsolucao_view, name='get_subsolucao'),
    path('Logout/', views.Sair_View, name='Logout'),

    #Sub-soluções paths
    path('usuarios/', views.Dm_Usuarios_view, name='Dm_Usuarios'),
    path('empresas/', views.Dm_Empresas_view, name='Dm_Empresas'),
    path('clientes/', views.Dm_Clientes_view, name='Dm_Clientes'),
    path('dashboard/',views.Dashboard_view,  name='Dashboard'),
    
#--------------------------------------------------------------------
    # modal path
#--------------------------------------------------------------------
    # Usuarios
    path('usuario/inserir/', views.Usuario_ins, name='Usuario_ins'),
    path('usuario/<int:user_id>/', views.Usuario_upd, name='Usuario_upd'),

    path('',views.Login_view),
]
