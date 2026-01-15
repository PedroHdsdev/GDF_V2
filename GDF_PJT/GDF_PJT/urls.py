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
    path('Usuarios/', views.Dm_Usuarios_view, name='Dm_Usuarios'),
    path('Empresas/', views.Dm_Empresas_view, name='Dm_Empresas'),
    path('Clientes/', views.Dm_Clientes_view, name='Dm_Clientes'),
    path('Dashboard/',views.Dashboard_view,  name='Dashboard'),
    
#--------------------------------------------------------------------
    # modal path
#--------------------------------------------------------------------

    # modal path
    path('usuario_ins/', views.Usuario_ins, name='usuario_ins'),
    path('usuario_upd/', views.Usuario_upd, name='usuario_upd'),
    path('userGroup_ins/', views.UserGroup_ins, name='userGroup_ins'),

    path('usuario_ins/', views.Usuario_ins, name='usuario_ins'),
    path('usuario_upd/', views.Usuario_upd, name='usuario_upd'),
    path('userGroup_ins/', views.UserGroup_ins, name='userGroup_ins'),

    path('usuario_ins/', views.Usuario_ins, name='usuario_ins'),
    path('usuario_upd/', views.Usuario_upd, name='usuario_upd'),
    path('userGroup_ins/', views.UserGroup_ins, name='userGroup_ins'),
    path('',views.Login_view),
]
