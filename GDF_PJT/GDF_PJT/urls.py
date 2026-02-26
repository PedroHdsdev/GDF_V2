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

    #Manifesto
    path('manifesto/painel/', views.fn_view_manifesto_painel, name='Mnf_Painel'),
    
    #APIs
    path('api/processar-xml/', views.fn_api_processar_xml, name='API_ProcessarXml'),
    path('api/cargaxml/parametros/', views.fn_api_cargaxml_parametros, name='API_CargaXmlParams'),
    path('api/cargaxml/parametros/<int:param_id>/', views.fn_api_cargaxml_parametro_detail, name='API_CargaXmlParamDetail'),
    path('api/cargaxml/parametros/<int:param_id>/toggle/', views.fn_api_cargaxml_param_toggle, name='API_CargaXmlParamsToggle'),
    path('api/cargaxml/relatorio/', views.fn_api_cargaxml_relatorio, name='API_CargaXmlRelatorio'),
    path('api/debug-session/', views.fn_api_debug_session, name='API_DebugSession'),
    path('api/cargaxml/jobs/', views.fn_api_cargaxml_jobs, name='API_CargaXmlJobs'),
    path('api/cargaxml/jobs/<int:job_id>/', views.fn_api_cargaxml_job_details, name='API_CargaXmlJobDetails'),
    
        
#--------------------------------------------------------------------
    # modal path
#--------------------------------------------------------------------
    # Usuarios
    path('usuario/inserir/', views.fn_view_inserir_usuario, name='Usuario_ins'),
    path('usuario/<int:user_id>/', views.fn_view_atualizar_usuario, name='Usuario_upd'),
    
    # Empresas
    path('empresa/inserir/', views.fn_view_inserir_empresa, name='Empresa_ins'),
    path('empresa/Cert/', views.fn_view_atualizar_certificado, name='Cert_upd'),
    path('empresa/<str:cod_empresa>/', views.fn_view_atualizar_empresa, name='Empresa_upd'),

    # Clientes
    path('cliente/inserir/', views.fn_view_inserir_cliente, name='Cliente_ins'),
    path('cliente/Acesso/', views.fn_view_atualizar_acesso_cliente, name='Cliente_acesso_upd'),
    path('cliente/<str:cod_cliente>/', views.fn_view_atualizar_cliente, name='Cliente_upd'),
    
    path('',views.fn_view_login),
]
