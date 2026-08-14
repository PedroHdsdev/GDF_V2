# API – Endpoints JSON, Jobs e Tasks Celery

Esta pasta concentra as **APIs** (endpoints JSON), os **jobs** em thread e as **tasks Celery** do app GDF.

## Estrutura

- **`jobs.py`** – Jobs em thread (uso imediato pela view):
  - `processar_job_xml_background` – Carga de XMLs (NFe, CTe, NFSe); usa `app.classes.CargaXml`.
  - `processar_job_sped_background` – Carga de SPED; usa `app.classes.CargaSped`.

- **`tasks.py`** – Tasks Celery (carga XML agendada):
  - `scan_cargaxml_params` – dispara a cada minuto e enfileira parâmetros cujo horário é o atual.
  - `process_cargaxml_param` – processa XMLs do diretório do parâmetro (ZIPs, NFe/CTe/NFSe, move para processados/pendentes). Configuração em `settings.CELERY_BEAT_SCHEDULE`.

- **`__init__.py`** – Reexporta todas as funções de API e os jobs (para uso nas URLs e em outros módulos).

## Onde está cada API

As funções `fn_api_*` estão implementadas em **`app.views`** (ponto único: telas + APIs) e reexportadas por este pacote:

- **Carga XML**: `fn_api_processar_xml`, `fn_api_cargaxml_parametros`, `fn_api_cargaxml_parametro_detail`, `fn_api_cargaxml_upload_zip`, `fn_api_cargaxml_relatorio`, `fn_api_cargaxml_param_toggle`, `fn_api_cargaxml_avisos`, `fn_api_cargaxml_jobs`, `fn_api_cargaxml_resumo`, `fn_api_cargaxml_job_details`
- **Carga SPED**: `fn_api_processar_sped`, `fn_api_cargasped_*` (parametros, upload, jobs, resumo, avisos, etc.)
- **Sessão**: `fn_api_sessao_cliente`, `fn_api_debug_session`
- **Relatórios**: `fn_api_relatorio_nfe`, `fn_api_relatorio_cte`, `fn_api_relatorio_nfse`, `fn_api_relatorio_sped` e respectivos `_detalhe`
- **Reprocessamento**: `fn_api_reprocessamento_lotes`, `fn_api_reprocessamento_divergencias`, `fn_api_reprocessamento_confronto`, etc.
- **SAP**: `fn_api_sap_testar_conexao`

## Uso

- **URLs**: `gdf/config/urls.py` usa `from app import views`; as rotas de API usam `views.fn_api_*`.
- **Views de tela e APIs**: em `app.views` (arquivo `views.py`), usando `app.classes` (ClGdf, CargaXml, CargaSped) e `app.utils.view_helpers`.
