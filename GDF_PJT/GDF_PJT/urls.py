from django.conf import settings
from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView

from app import views

urlpatterns = [
    # Ícone: navegadores pedem /gdf/favicon.ico quando a app está em subpath (evita 502 no proxy)
    path(
        'favicon.ico',
        RedirectView.as_view(url=f'{settings.STATIC_URL}img/logo.png', permanent=False),
        name='favicon',
    ),
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
    path('filiais/', views.fn_view_listar_filiais, name='Dm_Filiais'),
    path('clientes/', views.fn_view_listar_clientes, name='Dm_Clientes'),
    
    # PROCESSAMENTO FISCAL (Carga XML, Carga SPED, Relatório)
    path('CargaXml/', views.fn_view_CargaXml, name='Pro_CargaXml'),
    path('CargaSped/', views.fn_view_CargaSped, name='Pro_CargaSped'),
    path('Relatorio/', views.fn_view_Relatorio_Fiscal, name='Pro_Relatorio'),

    # FERRAMENTAS (subsolução Reproc_Painel: painel de reprocessamento, confronto SPED x NFe)
    path('Reprocessamento/Painel/', views.fn_view_Reprocessamento_Painel, name='Reproc_Painel'),

    #Dashboard
    path('dashboard/vendas/', views.fn_view_dashboard_vendas, name='Db_Vendas'),
    path('dashboard/compras/', views.fn_view_dashboard_compras, name='Db_Compras'),
    path('dashboard/custo/', views.fn_view_dashboard_custo, name='Db_Custo'),
    path(
        'dashboard/demonstrativos-contabeis/',
        views.fn_view_dashboard_demonstrativos_contabeis,
        name='Db_DemonstrContabeis',
    ),

    #Manifesto
    path('manifesto/painel/', views.fn_view_manifesto_painel, name='Mnf_Painel'),
    
    #APIs
    path('api/processar-xml/', views.fn_api_processar_xml, name='API_ProcessarXml'),
    path('api/debug-session/', views.fn_api_debug_session, name='API_DebugSession'),
    path('api/sessao/cliente/', views.fn_api_sessao_cliente, name='API_SessaoCliente'),
    path('api/cargaxml/avisos/', views.fn_api_cargaxml_avisos, name='API_CargaXmlAvisos'),
    path('api/cargaxml/jobs/', views.fn_api_cargaxml_jobs, name='API_CargaXmlJobs'),
    path('api/cargaxml/jobs/<int:job_id>/', views.fn_api_cargaxml_job_details, name='API_CargaXmlJobDetails'),
    path('api/cargaxml/resumo/', views.fn_api_cargaxml_resumo, name='API_CargaXmlResumo'),

    path('api/cargasped/resumo/', views.fn_api_cargasped_resumo, name='API_CargaSpedResumo'),
    path('api/cargasped/avisos/', views.fn_api_cargasped_avisos, name='API_CargaSpedAvisos'),
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
    path('api/relatorio/sped/<str:tipo>/<int:id_arquivo>/', views.fn_api_relatorio_sped_detalhe, name='API_RelatorioSpedDetalhe'),
    path('api/relatorio/excel/', views.fn_api_relatorio_excel, name='API_RelatorioExcel'),

    # API Reprocessamento (Painel: lotes, divergências, confronto)
    path('api/reprocessamento/lotes/', views.fn_api_reprocessamento_lotes, name='API_ReprocessamentoLotes'),
    path('api/reprocessamento/lotes/<int:id_lote>/divergencias/', views.fn_api_reprocessamento_divergencias, name='API_ReprocessamentoDivergencias'),
    path('api/reprocessamento/lotes/<int:id_lote>/condicoes-pagamento/gerar/', views.fn_api_reprocessamento_condicoes_gerar, name='API_ReprocessamentoCondicoesGerar'),
    path('api/reprocessamento/lotes/<int:id_lote>/condicoes-pagamento/', views.fn_api_reprocessamento_condicoes_listar, name='API_ReprocessamentoCondicoesListar'),
    path('api/reprocessamento/lotes/<int:id_lote>/condicoes-pagamento/enviar-sap/', views.fn_api_reprocessamento_condicoes_enviar_sap, name='API_ReprocessamentoCondicoesEnviarSap'),
    path('api/reprocessamento/lotes/<int:id_lote>/condicoes-pagamento/atualizar-retorno/', views.fn_api_reprocessamento_condicoes_atualizar_retorno, name='API_ReprocessamentoCondicoesAtualizarRetorno'),
    path('api/reprocessamento/confronto/', views.fn_api_reprocessamento_confronto, name='API_ReprocessamentoConfronto'),
    path('api/reprocessamento/divergencias/<int:id_divergencia>/detalhe/', views.fn_api_reprocessamento_divergencia_detalhe, name='API_ReprocessamentoDivergenciaDetalhe'),
    path('api/reprocessamento/divergencias/<int:id_divergencia>/reprocessar/', views.fn_api_reprocessamento_reprocessar_divergencia, name='API_ReprocessamentoReprocessarDivergencia'),
    path('api/reprocessamento/condicao-param/', views.fn_api_reprocessamento_condicao_param_listar, name='API_ReprocessamentoCondicaoParamListar'),
    path(
        'api/reprocessamento/condicao-param/exportar-excel/',
        views.fn_api_reprocessamento_condicao_param_exportar_excel,
        name='API_ReprocessamentoCondicaoParamExportarExcel',
    ),
    path(
        'api/reprocessamento/condicao-param/importar-excel/',
        views.fn_api_reprocessamento_condicao_param_importar_excel,
        name='API_ReprocessamentoCondicaoParamImportarExcel',
    ),
    path('api/reprocessamento/condicao-param/atualizar/', views.fn_api_reprocessamento_condicao_param_atualizar, name='API_ReprocessamentoCondicaoParamAtualizar'),
    path('api/sap/testar-conexao/', views.fn_api_sap_testar_conexao, name='API_SapTestarConexao'),
    path('api/sap/relatorio-custo/', views.fn_api_sap_relatorio_custo_receber, name='API_SapRelatorioCustoReceber'),
    path('integracao/rfc/', views.fn_view_Integracao_Rfc, name='Int_Rfc'),
    path('api/rfc/executar/', views.fn_api_rfc_executar, name='API_RfcExecutar'),
    path(
        'api/sap/demonstrativos-contabeis/',
        views.fn_api_sap_demonstrativos_contabeis,
        name='API_SapDemonstrativosContabeis',
    ),

        
#--------------------------------------------------------------------
    # modal path
#--------------------------------------------------------------------
    # Usuarios
    path('usuario/inserir/', views.fn_view_inserir_usuario, name='Usuario_ins'),
    path('usuario/<int:user_id>/', views.fn_view_atualizar_usuario, name='Usuario_upd'),
    
    # Empresas
    path('empresa/inserir/', views.fn_view_inserir_empresa, name='Empresa_ins'),
    path('empresa/Cert/', views.fn_view_atualizar_certificado, name='Cert_upd'),
    path('empresa/<str:cod_empresa>/filiais/', views.fn_view_listar_filiais_empresa, name='Empresa_filiais_list'),
    path('empresa/<str:cod_empresa>/', views.fn_view_atualizar_empresa, name='Empresa_upd'),

    # Filiais
    path('filial/inserir/', views.fn_view_inserir_filial, name='Filial_ins'),
    path('filial/<int:pk>/excluir/', views.fn_view_excluir_filial, name='Filial_del'),
    path('filial/<int:pk>/atualizar/', views.fn_view_atualizar_filial, name='Filial_upd'),

    # Clientes
    path('cliente/inserir/', views.fn_view_inserir_cliente, name='Cliente_ins'),
    path('cliente/Acesso/', views.fn_view_atualizar_acesso_cliente, name='Cliente_acesso_upd'),
    path('cliente/Grupos/', views.fn_view_atualizar_grupos_cliente, name='Cliente_grupos_upd'),
    path('cliente/<str:cod_cliente>/', views.fn_view_atualizar_cliente, name='Cliente_upd'),
    path('cliente/<str:cod_cliente>/sap/', views.fn_view_cliente_sap, name='Cliente_sap'),

    path('',views.fn_view_login),
]
