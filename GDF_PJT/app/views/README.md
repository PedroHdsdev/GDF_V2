# Pacote de views – app GDF

Views (telas e APIs) organizadas em pacote. Compatível com `from app import views` e `urls.py`.

## Estrutura atual

- **`_views.py`** – Implementação única de todas as views (legado monolítico).
- **`__init__.py`** – Reexporta todas as funções de `_views` para manter as URLs e o `app.api` funcionando.

## Próximo passo (quebra por domínio)

Para concluir a separação por domínio, migrar funções de `_views.py` para:

| Módulo | Funções a migrar |
|--------|-------------------|
| **auth.py** | `fn_view_login`, `fn_view_obter_subsolucao`, `fn_view_home`, `fn_view_sair` |
| **cadastros.py** | `fn_view_listar_usuarios`, `fn_view_listar_empresas`, `fn_view_listar_clientes`, `fn_view_listar_filiais`, `fn_view_inserir_filial`, `fn_view_inserir_usuario`, `fn_view_atualizar_usuario`, `_streamlit_iframe_url`, `fn_view_dashboard_*`, `fn_view_manifesto_painel`, `fn_view_inserir_empresa`, `fn_view_atualizar_empresa`, `fn_view_atualizar_certificado`, `fn_view_inserir_cliente`, `fn_view_atualizar_cliente`, `fn_view_atualizar_acesso_cliente`, `fn_view_atualizar_grupos_cliente`, `fn_view_cliente_sap` |
| **carga_xml.py** | `fn_view_CargaXml`, `fn_api_processar_xml`, `fn_api_cargaxml_*` |
| **carga_sped.py** | `fn_api_processar_sped`, `fn_api_cargasped_*`, `fn_view_CargaSped` |
| **relatorio.py** | `_serialize_model`, `fn_api_relatorio_*`, `fn_view_Relatorio_Fiscal` |
| **reprocessamento.py** | `fn_view_Reprocessamento`, `fn_view_Reprocessamento_Painel`, `fn_api_reprocessamento_*` |
| **sap.py** | `fn_api_sap_testar_conexao` |

Em cada novo módulo: colar as funções, colar só os imports necessários e remover essas funções de `_views.py`. No `__init__.py`, passar a importar desses módulos em vez de (ou além de) `_views`.
