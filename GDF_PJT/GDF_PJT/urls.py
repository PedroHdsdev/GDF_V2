from django.contrib import admin
from django.urls import path
from app import views

urlpatterns = [
    # Admin site
    path('admin/', admin.site.urls),

    # App views
    path('Login/', views.fn_view_login, name='Login'),
    path('Home/',views.fn_view_home, name='Home'),
    path('get_subsolucao/<str:cod_sub>/', views.fn_view_obter_subsolucao, name='get_subsolucao'),
    path('Logout/', views.fn_view_sair, name='Logout'),

    #Sub-soluções paths
    #ADM
    path('usuarios/', views.fn_view_listar_usuarios, name='Dm_Usuarios'),
    path('empresas/', views.fn_view_listar_empresas, name='Dm_Empresas'),
    path('clientes/', views.fn_view_listar_clientes, name='Dm_Clientes'),
    
    #PROCESSAMENTO
    path('CargaXml/', views.fn_view_CargaXml, name='Pro_CargaXml'),
    path('Reprocessamento/', views.fn_view_Reprocessamento, name='Pro_Reproc.'),

    #Dashboard
    path('dashboard/vendas/', views.fn_view_dashboard_vendas, name='Db_Vendas'),
    path('dashboard/compras/', views.fn_view_dashboard_compras, name='Db_Compras'),
    
        
#--------------------------------------------------------------------
    # modal path
#--------------------------------------------------------------------
    # Usuarios
    path('usuario/inserir/', views.fn_view_inserir_usuario, name='Usuario_ins'),
    path('usuario/<int:user_id>/', views.fn_view_atualizar_usuario, name='Usuario_upd'),
    
    # Empresas
    path('empresa/inserir/', views.fn_view_inserir_empresa, name='Empresa_ins'),
    path('empresa/<str:cod_empresa>/', views.fn_view_atualizar_empresa, name='Empresa_upd'),
    path('empresa/Cert/', views.fn_view_atualizar_certificado, name='Cert_upd'),

    # Clientes
    path('cliente/inserir/', views.fn_view_inserir_cliente, name='Cliente_ins'),
    path('cliente/Acesso/', views.fn_view_atualizar_acesso_cliente, name='Cliente_acesso_upd'),
    path('cliente/<str:cod_cliente>/', views.fn_view_atualizar_cliente, name='Cliente_upd'),
    
    path('',views.fn_view_login),
]
