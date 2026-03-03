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
    
    # PROCESSAMENTO FISCAL (Carga XML, Carga SPED, Relatório — Reprocessamento será solução própria futura)
    path('CargaXml/', views.fn_view_CargaXml, name='Pro_CargaXml'),
    path('CargaSped/', views.fn_view_CargaSped, name='Pro_CargaSped'),
    path('Relatorio/', views.fn_view_Relatorio_Fiscal, name='Pro_Relatorio'),

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
    path('api/cargaxml/parametros/<int:param_id>/upload-zip/', views.fn_api_cargaxml_upload_zip, name='API_CargaXmlUploadZip'),
    path('api/cargaxml/relatorio/', views.fn_api_cargaxml_relatorio, name='API_CargaXmlRelatorio'),
    path('api/debug-session/', views.fn_api_debug_session, name='API_DebugSession'),
    path('api/sessao/cliente/', views.fn_api_sessao_cliente, name='API_SessaoCliente'),
    path('api/cargaxml/jobs/', views.fn_api_cargaxml_jobs, name='API_CargaXmlJobs'),
    path('api/cargaxml/jobs/<int:job_id>/', views.fn_api_cargaxml_job_details, name='API_CargaXmlJobDetails'),

    path('api/cargasped/parametros/', views.fn_api_cargasped_parametros, name='API_CargaSpedParams'),
    path('api/cargasped/parametros/<int:param_id>/', views.fn_api_cargasped_parametro_detail, name='API_CargaSpedParamDetail'),
    path('api/cargasped/parametros/<int:param_id>/toggle/', views.fn_api_cargasped_param_toggle, name='API_CargaSpedParamToggle'),
    path('api/cargasped/parametros/<int:param_id>/upload-zip/', views.fn_api_cargasped_upload_zip, name='API_CargaSpedUploadZip'),
    path('api/cargasped/jobs/', views.fn_api_cargasped_jobs, name='API_CargaSpedJobs'),
    path('api/cargasped/jobs/<int:job_id>/', views.fn_api_cargasped_job_details, name='API_CargaSpedJobDetails'),
    path('api/processar-sped/', views.fn_api_processar_sped, name='API_ProcessarSped'),

    path('api/relatorio/nfe/', views.fn_api_relatorio_nfe, name='API_RelatorioNFe'),
    path('api/relatorio/nfe/<int:id_nfe>/', views.fn_api_relatorio_nfe_detalhe, name='API_RelatorioNFEDetalhe'),
    path('api/relatorio/cte/', views.fn_api_relatorio_cte, name='API_RelatorioCTe'),
    path('api/relatorio/cte/<int:id_cte>/', views.fn_api_relatorio_cte_detalhe, name='API_RelatorioCTeDetalhe'),
    path('api/relatorio/nfse/', views.fn_api_relatorio_nfse, name='API_RelatorioNFSe'),
    path('api/relatorio/nfse/<int:id_nfse>/', views.fn_api_relatorio_nfse_detalhe, name='API_RelatorioNFSEDetalhe'),
    path('api/relatorio/sped/', views.fn_api_relatorio_sped, name='API_RelatorioSped'),
    path('api/relatorio/sped/<int:id_arquivo>/', views.fn_api_relatorio_sped_detalhe, name='API_RelatorioSpedDetalhe'),
    
        
#--------------------------------------------------------------------
    # modal path
#--------------------------------------------------------------------
    # Usuarios
    path('usuario/inserir/', views.fn_view_inserir_usuario, name='Usuario_ins'),
    path('usuario/<int:user_id>/', views.fn_view_atualizar_usuario, name='Usuario_upd'),
    
    # Empresas
    path('empresa/inserir/', views.fn_view_inserir_empresa, name='Empresa_ins'),
    path('empresa/grupo/inserir/', views.fn_view_inserir_grp_empresa, name='Empresa_Grp_ins'),
    path('empresa/Cert/', views.fn_view_atualizar_certificado, name='Cert_upd'),
    path('empresa/<str:cod_empresa>/', views.fn_view_atualizar_empresa, name='Empresa_upd'),

    # Clientes
    path('cliente/inserir/', views.fn_view_inserir_cliente, name='Cliente_ins'),
    path('cliente/Acesso/', views.fn_view_atualizar_acesso_cliente, name='Cliente_acesso_upd'),
    path('cliente/<str:cod_cliente>/', views.fn_view_atualizar_cliente, name='Cliente_upd'),
    
    path('',views.fn_view_login),
]
