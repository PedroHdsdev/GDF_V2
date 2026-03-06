# Arquitetura do projeto GDF_V2

Estrutura de pastas, hierarquia de arquivos, schemas do banco, fluxos de dados e lista completa de URLs.

---

## 1. Hierarquia de pastas (projeto)

```
gdf_v2/
├── DOCUMENTACAO_MD/              # Documentação (índice, workbook, arquitetura, manual, deploy, glossário)
├── GDF_PJT/                      # Projeto Django
│   ├── app/                      # Aplicação principal
│   │   ├── api/                  # APIs JSON e jobs (CargaXml, CargaSped); tasks Celery
│   │   ├── classes/              # Lógica de negócio (ClGdf, CargaXml, CargaSped, Reprocessamento, SapRfc)
│   │   ├── db_GDF/               # Modelos por schema (Public, NFe, CTe, NFSe, sped_fiscal, sped_contribuicao, reprocessamento)
│   │   ├── security/             # Decorators, validadores, middlewares de segurança
│   │   ├── utils/                # view_helpers (sessão, acesso painel, tipo pagamento, relatorio_empresas_queryset)
│   │   ├── templatetags/         # Filtros de template (security: escape HTML/JS/URL)
│   │   ├── migrations/
│   │   ├── templates/            # Base, Login, Home, Usuarios, Empresas, ClienteGdf, Processamento, Reprocessamento, Manifesto, Dashboard
│   │   ├── static/               # img, css, js
│   │   ├── views.py              # Todas as views (fn_view_* e fn_api_*)
│   │   ├── admin.py, apps.py, context_processors.py, query_optimizer.py, security_logger.py
│   │   └── ...
│   ├── GDF_PJT/                  # Settings, urls, routers, wsgi
│   ├── manage.py
│   ├── run_carga_scheduler.py    # Agendador alternativo (sem Celery) para ParametroCargaXml
│   ├── streamlit/                # Apps Streamlit (dashboards vendas/compras)
│   ├── json/                     # Ex.: Tipo_pagamento.json
│   ├── logs/
│   ├── gunicorn_config.py
│   ├── run_gunicorn.sh
│   └── venv/
```

---

## 2. Estrutura detalhada do app (`app/`)

```
app/
├── api/
│   ├── __init__.py       # Reexporta fn_api_* e jobs (processar_job_xml_background, processar_job_sped_background)
│   ├── jobs.py           # processar_job_xml_background, processar_job_sped_background (thread)
│   └── tasks.py          # Celery: scan_cargaxml_params, process_cargaxml_param
├── classes/
│   ├── __init__.py
│   ├── gdf.py            # ClGdf
│   ├── CargaXml.py       # CargaXml, EmpresaNaoCadastradaError
│   ├── CargaSped.py      # CargaSped
│   ├── Reprocessamento.py
│   └── SapRfc.py
├── db_GDF/
│   ├── __init__.py
│   ├── Public/           # models.py → schema public
│   ├── NFe/              # models.py → schema nfe
│   ├── CTe/               # models.py → schema cte
│   ├── NFSe/              # models.py → schema nfse
│   ├── sped_fiscal/
│   ├── sped_contribuicao/
│   └── reprocessamento/  # models.py → schema reprocessamento
├── security/
│   ├── __init__.py
│   ├── decorators.py     # validate_idor_empresa, validate_idor_usuario, validate_session_required
│   ├── password_validator.py
│   ├── validators.py
│   └── middlewares/
│       ├── __init__.py
│       ├── security_headers.py   # SecurityHeadersMiddleware, XSSProtectionUtility
│       ├── rate_limit.py
│       └── session_fixation.py
├── utils/
│   ├── __init__.py
│   └── view_helpers.py   # COD_CLIENTE_PROJETO, usuario_vinculado_cliente_1000, usuario_acesso_total_painel, get_subsolucoes_usuario, relatorio_empresas_queryset, descricao_tipo_pagamento
├── templatetags/
│   ├── __init__.py
│   └── security.py       # Filtros de escape (template)
├── templates/
│   ├── index_Base.html
│   ├── index_Login.html
│   ├── Home/index_Home.html
│   ├── Usuarios/index_Usuarios.html, modal_Usuario_ins.html, modal_Usuario_upd.html
│   ├── Empresas/index_Empresas.html, modal_Empresa_ins.html, modal_Empresa_upd.html, modal_GrupoEmpresa_ins.html
│   ├── ClienteGdf/index_ClienteGdf.html, modal_ClienteGdf_ins.html, modal_ClienteGdf_upd.html
│   ├── Processamento/index_CargaXml.html, index_CargaSped.html, index_Relatorio.html
│   ├── Reprocessamento/index_Painel.html
│   ├── Manifesto/index_Manifesto.html, modal_Item.html, modal_Manifesto.html
│   └── Dashboard/index_Vendas.html, index_Compras.html
├── views.py
├── admin.py, apps.py, context_processors.py, query_optimizer.py, security_logger.py
└── migrations/
```

---

## 3. Schemas e tabelas (PostgreSQL)

Um único banco (`default`) com os seguintes schemas e tabelas:

### 3.1 Schema `public`

| Tabela | Model | Descrição |
|--------|--------|-----------|
| certificado_digital | CertificadoDigital | Certificado .pfx por raiz CNPJ |
| cliente_gdf | ClienteGdf | Clientes GDF (cod_cliente, razao, cnpj) |
| grupo_empresa | GrupoEmpresa | Grupos de empresas por cliente |
| empresa | Empresa | Empresas (cod_empresa, cnpj, razao, fantasia, grp_empresa, cert, gdfcliente) |
| permissao_grupo_cliente | PermissaoGrupoCliente | Grupo Django ↔ Cliente GDF |
| usuario_empresa | UsuarioEmpresa | Usuário ↔ Empresa |
| solucao | Solucao | Soluções (módulos) |
| subsolucao | Subsolucao | Subsoluções por solução |
| acesso_solucao_cliente | AcessoSolucaoCliente | Cliente ↔ Solução |
| acesso_subsolucao_grupo | AcessoSubsolucaoGrupo | Grupo ↔ Subsolução |
| parametro_carga_xml | ParametroCargaXml | Parâmetros de carga XML agendada (diretório, horário, empresa, cliente) |
| job_carga_xml | JobCargaXml | Jobs de execução de carga XML (status, totais, mensagem) |
| parametro_carga_sped | ParametroCargaSped | Parâmetros de carga SPED |
| job_carga_sped | JobCargaSped | Jobs de carga SPED |
| conexao_sap | ConexaoSap | Conexão SAP por cliente (ashost, sysnr, client, username, passwd) |

### 3.2 Schema `nfe`

nfe_endereco, nfe_emitente, nfe_destinatario, nfe_identificacao, nfe_produto, nfe_icms, nfe_ipi, nfe_pis, nfe_cofins, nfe_total, nfe_transporte, nfe_cobranca, nfe_parcela, nfe_pagamento, nfe_informacoes_adicionais, nfe, nfe_evento, nfe_documento, nfe_documento_item.

### 3.3 Schema `cte`

cte_endereco, cte_emitente, cte_destinatario, cte_identificacao, cte_valor, cte_transporte, cte, cte_evento, cte_carga, cte_servico, cte_veiculo, cte_motorista, cte_percurso, cte_fiscal.

### 3.4 Schema `nfse`

nfse_endereco, nfse_prestador, nfse_tomador, nfse_identificacao, nfse_rps, nfse_retencao, nfse_pagamento, nfse_credenciamento, nfse_servico, nfse, nfse_evento.

### 3.5 Schema `sped_fiscal` / `sped_contribuicao`

Arquivos e registros dos SPED (EFD ICMS/IPI e EFD Contribuições).

### 3.6 Schema `reprocessamento`

| Tabela | Model | Descrição |
|--------|--------|-----------|
| reprocessamento_lote | ReprocessamentoLote | Lote de confronto (empresa, competência, status, totais NFe/divergências) |
| divergencia | Divergencia | Divergência SPED x NFe (tipo, status, chave_nfe, valor_esperado/encontrado, detalhe_json) |
| reprocessamento_job | ReprocessamentoJob | Job de confronto ou reprocessamento em massa |
| condicao_pagamento_lote | CondicaoPagamentoLote | Condições por lote (chave_nfe, condicao NFe/SAP, status envio) |
| condicao_param | CondicaoParam | Mapeamento condição NFe → SAP por cliente GDF |

---

## 4. Fluxos de dados (detalhados)

### 4.1 Login e sessão

1. Usuário acessa `/` ou `Login/` → `fn_view_login`.
2. POST com username/senha → `authenticate()` e `login(request, user)`.
3. `ClGdf().get_dados(user)`:
   - Determina cod_cliente (primeiro cliente do usuário ou 1000).
   - Carrega empresas, groups, soluções e subsoluções acessíveis.
   - Define se é usuario_cliente_1000 (empresa no cliente 1000).
4. Sessão preenchida: cod_cliente, t_solucoes, is_superuser, usuario_cliente_1000.
5. Redirect para `Home/`. A Home monta o menu conforme `t_solucoes` (subsoluções).

### 4.2 Carga de XML (manual)

1. Usuário na tela CargaXml escolhe empresa, tipo (NFe/CTe/NFSe) e envia arquivos (XML ou ZIP).
2. POST para `api/processar-xml/` → `fn_api_processar_xml`.
3. Arquivos salvos em diretório temporário; criado `JobCargaXml` (status RUNNING, gdfcliente, parametro opcional, usuario_execucao).
4. Iniciada thread com `processar_job_xml_background(job_id, temp_dir, type_xml, origem_dados, user_id, cod_cliente, empresa_id)`.
5. No thread: listagem de .xml na pasta → `CargaXml().set_upload_xml(...)` → gravação em NFe/CTe/NFSe; atualização do job (total_sucesso, total_erro, status SUCCESS/ERROR, mensagem, finished_at); remoção da pasta temp.
6. Front consulta `api/cargaxml/jobs/` e `api/cargaxml/jobs/<id>/` para exibir status e detalhes.

### 4.3 Carga XML agendada (Celery)

1. `scan_cargaxml_params` (beat, ex.: a cada minuto) lista `ParametroCargaXml` ativos cujo horário (hour, minute) é o atual e ainda não executou nesse minuto → enfileira `process_cargaxml_param.delay(param.id)`.
2. Worker executa `process_cargaxml_param`: lê diretório do parâmetro, extrai ZIPs, coleta XMLs, detecta tipo (NFe/CTe/NFSe), para cada XML chama `CargaXml().set_nfe/set_cte/set_nfse`, move arquivo para processados ou pendentes; cria/atualiza `JobCargaXml` e `param.ultima_execucao`.

### 4.4 Carga SPED

1. Usuário envia .txt na tela CargaSped → `fn_api_processar_sped` → cria `JobCargaSped` e thread com `processar_job_sped_background`.
2. Thread: `CargaSped().processar_pasta_temp(...)` → gravação em sped_fiscal/sped_contribuicao; atualização do job.

### 4.5 Relatório fiscal

1. Usuário na tela Relatório define filtros (empresa/grupo, período, tipo: NFe/CTe/NFSe/SPED).
2. Front chama `api/relatorio/nfe/`, `api/relatorio/cte/`, etc. (GET com query params).
3. View usa `relatorio_empresas_queryset(request)` para restringir empresas ao cliente da sessão; aplica filtros de data e empresa; retorna JSON com lista.
4. Detalhe: `api/relatorio/nfe/<id_nfe>/`, etc. → retorna um documento completo (identificação, emitente, destinatário, produtos, totais, etc.).

### 4.6 Reprocessamento (SPED x NFe)

1. Painel: listagem de lotes (`api/reprocessamento/lotes/`); criação de novo confronto (`api/reprocessamento/confronto/` com empresa, competência, escopo).
2. Backend usa classe `Reprocessamento`: compara registros SPED com NFe no banco; cria/atualiza `ReprocessamentoLote` e `Divergencia`.
3. Divergências: listagem por lote (`api/reprocessamento/lotes/<id_lote>/divergencias/`); detalhe e reprocessar item (`api/reprocessamento/divergencias/<id>/detalhe/`, `.../reprocessar/`).
4. Condições de pagamento: gerar (`api/reprocessamento/lotes/<id_lote>/condicoes-pagamento/gerar/`), listar, atualizar retorno SAP, enviar ao SAP (`.../enviar-sap/`). Envio usa `SapRfc.enviar_condicoes_pagamento_sap`. Parâmetros de mapeamento NFe→SAP: `api/reprocessamento/condicao-param/` e `.../atualizar/`.

---

## 5. Diagrama de dependências (módulos)

```
views.py
  ├── app.security.decorators (validate_idor_empresa, validate_idor_usuario, validate_session_required)
  ├── app.utils.view_helpers (relatorio_empresas_queryset, usuario_acesso_total_painel, descricao_tipo_pagamento, etc.)
  ├── app.classes (ClGdf, CargaXml, CargaSped, Reprocessamento, SapRfc)
  ├── app.db_GDF.Public.models (Empresa, ClienteGdf, JobCargaXml, JobCargaSped, ParametroCargaXml, etc.)
  ├── app.db_GDF.reprocessamento.models (ReprocessamentoLote, Divergencia, CondicaoPagamentoLote, CondicaoParam)
  └── app.api (jobs: processar_job_xml_background, processar_job_sped_background)

api/jobs.py
  ├── app.classes.CargaXml, CargaSped
  └── app.db_GDF.Public.models (JobCargaXml, JobCargaSped, Empresa)

api/tasks.py (Celery)
  ├── app.classes.CargaXml (set_nfe, set_cte, set_nfse; EmpresaNaoCadastradaError)
  └── app.db_GDF.Public.models (ParametroCargaXml, JobCargaXml)

classes/* (ClGdf, CargaXml, CargaSped, Reprocessamento, SapRfc)
  └── app.db_GDF.*.models (Public, NFe, CTe, NFSe, reprocessamento)
```

---

## 6. URLs completas (GDF_PJT/urls.py)

### Autenticação e Home

| URL | Name | View |
|-----|------|------|
| `/` | (login) | fn_view_login |
| `Login/` | Login | fn_view_login |
| `Home/` | Home | fn_view_home |
| `get_subsolucao/<cod_sub>/` | get_subsolucao | fn_view_obter_subsolucao |
| `Logout/` | Logout | fn_view_sair |

### Cadastros (subsoluções)

| URL | Name | View |
|-----|------|------|
| `usuarios/` | Dm_Usuarios | fn_view_listar_usuarios |
| `usuario/inserir/` | Usuario_ins | fn_view_inserir_usuario |
| `usuario/<user_id>/` | Usuario_upd | fn_view_atualizar_usuario |
| `empresas/` | Dm_Empresas | fn_view_listar_empresas |
| `empresa/inserir/` | Empresa_ins | fn_view_inserir_empresa |
| `empresa/grupo/inserir/` | Empresa_Grp_ins | fn_view_inserir_grp_empresa |
| `empresa/Cert/` | Cert_upd | fn_view_atualizar_certificado |
| `empresa/<cod_empresa>/` | Empresa_upd | fn_view_atualizar_empresa |
| `clientes/` | Dm_Clientes | fn_view_listar_clientes |
| `cliente/inserir/` | Cliente_ins | fn_view_inserir_cliente |
| `cliente/Acesso/` | Cliente_acesso_upd | fn_view_atualizar_acesso_cliente |
| `cliente/Grupos/` | Cliente_grupos_upd | fn_view_atualizar_grupos_cliente |
| `cliente/<cod_cliente>/` | Cliente_upd | fn_view_atualizar_cliente |
| `cliente/<cod_cliente>/sap/` | Cliente_sap | fn_view_cliente_sap |

### Processamento e Relatório

| URL | Name | View |
|-----|------|------|
| `CargaXml/` | Pro_CargaXml | fn_view_CargaXml |
| `CargaSped/` | Pro_CargaSped | fn_view_CargaSped |
| `Relatorio/` | Pro_Relatorio | fn_view_Relatorio_Fiscal |

### Reprocessamento e Manifesto / Dashboard

| URL | Name | View |
|-----|------|------|
| `Reprocessamento/Painel/` | Reproc_Painel | fn_view_Reprocessamento_Painel |
| `dashboard/vendas/` | Db_Vendas | fn_view_dashboard_vendas |
| `dashboard/compras/` | Db_Compras | fn_view_dashboard_compras |
| `manifesto/painel/` | Mnf_Painel | fn_view_manifesto_painel |

### APIs – Carga XML

| URL | Name | View |
|-----|------|------|
| `api/processar-xml/` | API_ProcessarXml | fn_api_processar_xml |
| `api/cargaxml/parametros/` | API_CargaXmlParams | fn_api_cargaxml_parametros |
| `api/cargaxml/parametros/<param_id>/` | API_CargaXmlParamDetail | fn_api_cargaxml_parametro_detail |
| `api/cargaxml/parametros/<param_id>/toggle/` | API_CargaXmlParamsToggle | fn_api_cargaxml_param_toggle |
| `api/cargaxml/parametros/<param_id>/upload-zip/` | API_CargaXmlUploadZip | fn_api_cargaxml_upload_zip |
| `api/cargaxml/relatorio/` | API_CargaXmlRelatorio | fn_api_cargaxml_relatorio |
| `api/cargaxml/avisos/` | API_CargaXmlAvisos | fn_api_cargaxml_avisos |
| `api/cargaxml/jobs/` | API_CargaXmlJobs | fn_api_cargaxml_jobs |
| `api/cargaxml/jobs/<job_id>/` | API_CargaXmlJobDetails | fn_api_cargaxml_job_details |
| `api/cargaxml/resumo/` | API_CargaXmlResumo | fn_api_cargaxml_resumo |
| `api/sessao/cliente/` | API_SessaoCliente | fn_api_sessao_cliente |
| `api/debug-session/` | API_DebugSession | fn_api_debug_session |

### APIs – Carga SPED

| URL | Name | View |
|-----|------|------|
| `api/processar-sped/` | API_ProcessarSped | fn_api_processar_sped |
| `api/cargasped/parametros/` | API_CargaSpedParams | fn_api_cargasped_parametros |
| `api/cargasped/parametros/<param_id>/` | API_CargaSpedParamDetail | fn_api_cargasped_parametro_detail |
| `api/cargasped/parametros/<param_id>/toggle/` | API_CargaSpedParamToggle | fn_api_cargasped_param_toggle |
| `api/cargasped/parametros/<param_id>/upload-zip/` | API_CargaSpedUploadZip | fn_api_cargasped_upload_zip |
| `api/cargasped/resumo/` | API_CargaSpedResumo | fn_api_cargasped_resumo |
| `api/cargasped/avisos/` | API_CargaSpedAvisos | fn_api_cargasped_avisos |
| `api/cargasped/jobs/` | API_CargaSpedJobs | fn_api_cargasped_jobs |
| `api/cargasped/jobs/<job_id>/` | API_CargaSpedJobDetails | fn_api_cargasped_job_details |

### APIs – Relatório

| URL | Name | View |
|-----|------|------|
| `api/relatorio/nfe/` | API_RelatorioNFe | fn_api_relatorio_nfe |
| `api/relatorio/nfe/<id_nfe>/` | API_RelatorioNFEDetalhe | fn_api_relatorio_nfe_detalhe |
| `api/relatorio/cte/` | API_RelatorioCTe | fn_api_relatorio_cte |
| `api/relatorio/cte/<id_cte>/` | API_RelatorioCTeDetalhe | fn_api_relatorio_cte_detalhe |
| `api/relatorio/nfse/` | API_RelatorioNFSe | fn_api_relatorio_nfse |
| `api/relatorio/nfse/<id_nfse>/` | API_RelatorioNFSEDetalhe | fn_api_relatorio_nfse_detalhe |
| `api/relatorio/sped/` | API_RelatorioSped | fn_api_relatorio_sped |
| `api/relatorio/sped/<tipo>/<id_arquivo>/` | API_RelatorioSpedDetalhe | fn_api_relatorio_sped_detalhe |

### APIs – Reprocessamento e SAP

| URL | Name | View |
|-----|------|------|
| `api/reprocessamento/lotes/` | API_ReprocessamentoLotes | fn_api_reprocessamento_lotes |
| `api/reprocessamento/lotes/<id_lote>/divergencias/` | API_ReprocessamentoDivergencias | fn_api_reprocessamento_divergencias |
| `api/reprocessamento/lotes/<id_lote>/condicoes-pagamento/gerar/` | API_ReprocessamentoCondicoesGerar | fn_api_reprocessamento_condicoes_gerar |
| `api/reprocessamento/lotes/<id_lote>/condicoes-pagamento/` | API_ReprocessamentoCondicoesListar | fn_api_reprocessamento_condicoes_listar |
| `api/reprocessamento/lotes/<id_lote>/condicoes-pagamento/enviar-sap/` | API_ReprocessamentoCondicoesEnviarSap | fn_api_reprocessamento_condicoes_enviar_sap |
| `api/reprocessamento/lotes/<id_lote>/condicoes-pagamento/atualizar-retorno/` | API_ReprocessamentoCondicoesAtualizarRetorno | fn_api_reprocessamento_condicoes_atualizar_retorno |
| `api/reprocessamento/confronto/` | API_ReprocessamentoConfronto | fn_api_reprocessamento_confronto |
| `api/reprocessamento/divergencias/<id_divergencia>/detalhe/` | API_ReprocessamentoDivergenciaDetalhe | fn_api_reprocessamento_divergencia_detalhe |
| `api/reprocessamento/divergencias/<id_divergencia>/reprocessar/` | API_ReprocessamentoReprocessarDivergencia | fn_api_reprocessamento_reprocessar_divergencia |
| `api/reprocessamento/condicao-param/` | API_ReprocessamentoCondicaoParamListar | fn_api_reprocessamento_condicao_param_listar |
| `api/reprocessamento/condicao-param/atualizar/` | API_ReprocessamentoCondicaoParamAtualizar | fn_api_reprocessamento_condicao_param_atualizar |
| `api/sap/testar-conexao/` | API_SapTestarConexao | fn_api_sap_testar_conexao |

---

*Última atualização: Março 2026*
