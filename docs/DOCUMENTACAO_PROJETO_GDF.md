# Documentação do projeto GDF_V2

Documentação técnica detalhada do sistema GDF_V2: visão geral, stack, módulos, banco de dados, segurança, integrações e funcionalidades.

---

## 1. Visão geral

O **GDF_V2** é um sistema **multi-tenant** (ERP) que centraliza:

- **Cadastros:** clientes GDF, empresas, grupos de empresa, usuários, grupos de permissão (Django), soluções e subsoluções.
- **Documentos fiscais:** NFe (modelo 55), CTe (57/67), NFSe (carga via XML) e SPED (EFD ICMS/IPI e EFD Contribuições).
- **Relatórios:** consulta a NFe, CTe, NFSe e SPED por empresa (ou grupo), período e filtros; detalhe por documento.
- **Reprocessamento:** confronto SPED x NFe, geração de divergências, condições de pagamento e envio ao SAP via RFC.
- **Integração SAP:** conexão RFC (PyRFC), teste de conexão e envio de condições de pagamento por lote.
- **Segurança:** controle por soluções/subsoluções, validação IDOR (empresa/usuário), rate limit, session fixation, headers de segurança (XSS, HSTS, etc.) e validação de senha forte.

**Stack principal:** Django 6.x (Python 3.10+), PostgreSQL (um banco, múltiplos schemas), Celery + Redis (carga XML agendada), PyRFC (SAP). Front: templates Django, JavaScript; dashboards externos em Streamlit (JWT para iframe).

---

## 2. Módulos principais (app Django)

### 2.1 views.py (ponto único de telas e APIs)

Todas as views ficam em **um único arquivo**: `app/views.py`. Convenção:

- **`fn_view_*`** – Renderizam HTML (telas). Recebem `request`; usam `ClGdf`, helpers e context; retornam `render()` ou `redirect`.
- **`fn_api_*`** – APIs JSON. Recebem `request`; validam sessão/IDOR quando necessário; retornam `JsonResponse`.

Principais funções:

| Função | Tipo | Descrição |
|--------|------|-----------|
| `fn_view_login` | view | Tela de login; após sucesso preenche sessão (cod_cliente, t_solucoes, usuario_cliente_1000) via ClGdf.get_dados. |
| `fn_view_home` | view | Home com menu dinâmico por subsoluções do usuário. |
| `fn_view_sair` | view | Logout. |
| `fn_view_listar_usuarios` / `fn_view_inserir_usuario` / `fn_view_atualizar_usuario` | view | Listagem e CRUD de usuários (Dm_Usuarios). |
| `fn_view_listar_empresas` / `fn_view_inserir_empresa` / `fn_view_atualizar_empresa` / `fn_view_inserir_grp_empresa` / `fn_view_atualizar_certificado` | view | Listagem e CRUD de empresas, grupos e certificado (Dm_Empresas). |
| `fn_view_listar_clientes` / `fn_view_inserir_cliente` / `fn_view_atualizar_cliente` / `fn_view_atualizar_acesso_cliente` / `fn_view_atualizar_grupos_cliente` / `fn_view_cliente_sap` | view | CRUD clientes GDF e conexão SAP (Dm_Clientes). |
| `fn_view_CargaXml` | view | Tela Carga XML (Pro_CargaXml). |
| `fn_view_CargaSped` | view | Tela Carga SPED (Pro_CargaSped). |
| `fn_view_Relatorio_Fiscal` | view | Tela Relatório fiscal (Pro_Relatorio). |
| `fn_view_Reprocessamento_Painel` | view | Painel de reprocessamento (Reproc_Painel). |
| `fn_view_dashboard_vendas` / `fn_view_dashboard_compras` | view | Telas que carregam iframe Streamlit com JWT (Db_Vendas, Db_Compras). |
| `fn_view_manifesto_painel` | view | Painel de manifesto (Mnf_Painel). |
| `fn_api_processar_xml` | api | Recebe XML/ZIP; cria JobCargaXml; dispara thread com processar_job_xml_background. |
| `fn_api_cargaxml_parametros` / `fn_api_cargaxml_parametro_detail` / `fn_api_cargaxml_upload_zip` / `fn_api_cargaxml_param_toggle` | api | CRUD parâmetros de carga XML agendada; upload ZIP por parâmetro. |
| `fn_api_cargaxml_jobs` / `fn_api_cargaxml_job_details` / `fn_api_cargaxml_resumo` / `fn_api_cargaxml_avisos` / `fn_api_cargaxml_relatorio` | api | Listagem de jobs, detalhe, resumo, avisos e relatório de carga XML. |
| `fn_api_processar_sped` | api | Recebe arquivo SPED; cria JobCargaSped; dispara processar_job_sped_background. |
| `fn_api_cargasped_*` | api | Parâmetros, jobs, detalhes, resumo, avisos (espelho da carga XML). |
| `fn_api_relatorio_nfe` / `fn_api_relatorio_cte` / `fn_api_relatorio_nfse` / `fn_api_relatorio_sped` | api | Listagem de documentos com filtros (empresa, grupo, período). |
| `fn_api_relatorio_nfe_detalhe` / `fn_api_relatorio_cte_detalhe` / `fn_api_relatorio_nfse_detalhe` / `fn_api_relatorio_sped_detalhe` | api | Detalhe de um documento (id). |
| `fn_api_reprocessamento_lotes` / `fn_api_reprocessamento_divergencias` / `fn_api_reprocessamento_confronto` | api | Lotes, divergências do lote, disparo do confronto SPED x NFe. |
| `fn_api_reprocessamento_divergencia_detalhe` / `fn_api_reprocessamento_reprocessar_divergencia` | api | Detalhe de divergência e reprocessar item. |
| `fn_api_reprocessamento_condicoes_gerar` / `fn_api_reprocessamento_condicoes_listar` / `fn_api_reprocessamento_condicoes_atualizar_retorno` / `fn_api_reprocessamento_condicoes_enviar_sap` | api | Condições de pagamento do lote: gerar, listar, atualizar retorno SAP, enviar ao SAP. |
| `fn_api_reprocessamento_condicao_param_listar` / `fn_api_reprocessamento_condicao_param_atualizar` | api | Parâmetros de mapeamento condição NFe → SAP por cliente. |
| `fn_api_sap_testar_conexao` | api | Testa conexão RFC para o cliente da sessão. |
| `fn_api_sessao_cliente` / `fn_api_debug_session` | api | Sessão (trocar cliente) e debug. |

### 2.2 api/ – APIs e jobs em background

- **api/__init__.py** – Reexporta as funções `fn_api_*` e os jobs para uso em `views` (views importa de `app.api` onde necessário).
- **api/jobs.py**
  - **processar_job_xml_background(job_id, temp_dir, type_xml, origem_dados, user_id, cod_cliente, empresa_id)**  
    Executado em thread. Lista XMLs em `temp_dir`, chama `CargaXml().set_upload_xml(...)` e atualiza `JobCargaXml` (total_sucesso, total_erro, status, mensagem, finished_at).
  - **processar_job_sped_background(job_id, temp_dir, tipo_sped, user_id, cod_cliente, empresa_id)**  
    Análogo para SPED: usa `CargaSped().processar_pasta_temp(...)` e atualiza `JobCargaSped`.
- **api/tasks.py** (Celery)
  - **scan_cargaxml_params** – Tarefa agendada (a cada minuto). Para cada `ParametroCargaXml` ativo cujo horário coincide com o atual, enfileira `process_cargaxml_param`.
  - **process_cargaxml_param(param_id)** – Lê o diretório do parâmetro, extrai ZIPs, detecta tipo (NFe/CTe/NFSe), grava via `CargaXml` (set_nfe/set_cte/set_nfse), move arquivos para `processados/` ou `pendentes/`. Cria e atualiza `JobCargaXml` e `param.ultima_execucao`.

### 2.3 classes/ – Lógica de negócio

- **ClGdf (gdf.py)**  
  Serviço de sessão e cadastros: `get_dados(user)` (preenche sessão: cod_cliente, t_solucoes, usuario_cliente_1000, etc.), `calcular_status_certificado`, `gerar_token` (JWT para dashboards), CRUD de cliente GDF, empresa, usuário, grupos, soluções/subsoluções, certificado e conexão SAP.

- **CargaXml (CargaXml.py)**  
  Leitura e persistência de XML: `set_upload_xml` (lista de arquivos), `set_nfe`, `set_cte`, `set_nfse`, `set_evento` (eventos NFe/CTe/NFSe). Extrai dados do XML (emitente, destinatário, produtos, impostos, totais, cobrança, pagamento, etc.) e grava nos models do `db_GDF` (NFe, CTe, NFSe). Trata empresa não cadastrada (`EmpresaNaoCadastradaError`). Pode gravar `CondicaoParam` (reprocessamento) ao processar NFe.

- **CargaSped (CargaSped.py)**  
  Processa arquivos .txt do SPED (EFD ICMS/IPI, EFD Contribuições); grava em `sped_fiscal` e `sped_contribuicao`.

- **Reprocessamento (Reprocessamento.py)**  
  Confronto SPED x NFe: gera lotes (`ReprocessamentoLote`), divergências (`Divergencia`), condições de pagamento (`CondicaoPagamentoLote`). Usa models do schema `reprocessamento`.

- **SapRfc (SapRfc.py)**  
  Integração SAP: `get_connection(cod_cliente)`, `config_from_connection`, `connect`, `call(rfc_name, **params)`, `with_connection`, `enviar_condicoes_pagamento_sap(id_lote, cod_empresa, condicoes_lista)`. Usa modelo `ConexaoSap` (public).

### 2.4 db_GDF/ – Modelos por schema

- **Public (db_GDF/Public/models.py)**  
  CertificadoDigital, ClienteGdf, GrupoEmpresa, Empresa, PermissaoGrupoCliente, UsuarioEmpresa, Solucao, Subsolucao, AcessoSolucaoCliente, AcessoSubsolucaoGrupo, ParametroCargaXml, JobCargaXml, ParametroCargaSped, JobCargaSped, ConexaoSap. Tabelas no schema `public` (sem prefixo de schema no db_table, exceto quando indicado).

- **NFe (db_GDF/NFe/models.py)**  
  Schema `nfe`: nfe_endereco, nfe_emitente, nfe_destinatario, nfe_identificacao, nfe_produto, nfe_icms, nfe_ipi, nfe_pis, nfe_cofins, nfe_total, nfe_transporte, nfe_cobranca, nfe_parcela, nfe_pagamento, nfe_informacoes_adicionais, nfe, nfe_evento, nfe_documento, nfe_documento_item.

- **CTe (db_GDF/CTe/models.py)**  
  Schema `cte`: cte_endereco, cte_emitente, cte_destinatario, cte_identificacao, cte_valor, cte_transporte, cte, cte_evento, cte_carga, cte_servico, cte_veiculo, cte_motorista, cte_percurso, cte_fiscal.

- **NFSe (db_GDF/NFSe/models.py)**  
  Schema `nfse`: nfse_endereco, nfse_prestador, nfse_tomador, nfse_identificacao, nfse_rps, nfse_retencao, nfse_pagamento, nfse_credenciamento, nfse_servico, nfse, nfse_evento.

- **sped_fiscal** / **sped_contribuicao**  
  Arquivos e registros SPED (EFD ICMS/IPI e EFD Contribuições).

- **reprocessamento (db_GDF/reprocessamento/models.py)**  
  Schema `reprocessamento`: reprocessamento_lote, divergencia, reprocessamento_job, condicao_pagamento_lote, condicao_param.

### 2.5 security/ – Segurança

- **decorators.py**
  - `validate_idor_empresa` – Garante que `cod_empresa` pertence ao `cod_cliente` da sessão.
  - `validate_idor_usuario` – Garante que `user_id` pertence ao cliente (via usuario_empresa → empresa → gdfcliente).
  - `validate_session_required` – Exige `cod_cliente` na sessão.
- **password_validator.py** – Regras de senha forte (tamanho, caracteres especiais, etc.).
- **validators.py** – Sanitização de entradas (evitar injeção/XSS em campos de texto).
- **middlewares/**
  - **security_headers.py** – SecurityHeadersMiddleware: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy, Strict-Transport-Security.
  - **rate_limit.py** – Limite de requisições por IP/usuário (evitar abuso).
  - **session_fixation.py** – Regenera session key após login.

- **templatetags/security.py** – Filtros de template para escape seguro (HTML/JS/URL), usando XSSProtectionUtility.

### 2.6 utils/view_helpers.py

- **COD_CLIENTE_PROJETO** = "1000" (cliente dona do projeto).
- **usuario_vinculado_cliente_1000(user)** – True se o usuário tem empresa no cliente 1000.
- **usuario_acesso_total_painel(request)** – True se superuser ou usuario_cliente_1000 na sessão.
- **get_subsolucoes_usuario(user)** – Set de cod_subsolucao dos grupos do usuário; None se superuser ou cliente 1000 (acesso total).
- **relatorio_empresas_queryset(request)** – Queryset de empresas do cliente da sessão (para relatórios e reprocessamento); considera acesso total ao painel.
- **descricao_tipo_pagamento(codigo)** – Descrição do tipo de pagamento (código XML) a partir do JSON Tipo_pagamento.json.

---

## 3. Multi-tenancy e controle de acesso

- **Cliente GDF:** entidade de negócio (`cod_cliente`). Todas as empresas e usuários (via vínculo empresa) pertencem a um cliente. A sessão guarda `cod_cliente` como cliente ativo.
- **Login:** após autenticação, `ClGdf().get_dados(user)` define na sessão: cod_cliente (primeiro cliente do usuário ou 1000), t_solucoes, is_superuser, usuario_cliente_1000 (se usuário tem empresa no cliente 1000).
- **Troca de cliente:** apenas se `usuario_acesso_total_painel(request)` (superuser ou cliente 1000). API `fn_api_sessao_cliente` atualiza `cod_cliente` na sessão.
- **Subsoluções:** o menu (Home) e as rotas são liberados conforme as subsoluções do grupo do usuário (AcessoSubsolucaoGrupo). Códigos típicos: Dm_Usuarios, Dm_Empresas, Dm_Clientes, Pro_CargaXml, Pro_CargaSped, Pro_Relatorio, Reproc_Painel, Mnf_Painel, Db_Vendas, Db_Compras.
- **IDOR:** APIs que recebem `cod_empresa` ou `user_id` usam os decorators `validate_idor_empresa` ou `validate_idor_usuario` para garantir que o recurso pertence ao cliente da sessão.

---

## 4. Banco de dados (PostgreSQL)

- **Um único banco PostgreSQL** (configuração `default` no Django). **Router:** `config.routers.GDFRouter` envia todos os apps em `db_GDF` para esse banco.
- **Schemas:** public (cadastros), nfe, cte, nfse, sped_fiscal, sped_contribuicao, reprocessamento. Cada model que não é do public usa `db_table = '"schema"."tabela"'`.
- **Migrações:** `app/migrations/`; ao rodar `migrate`, as tabelas são criadas/alteradas nos schemas corretos.

---

## 5. Tarefas assíncronas

- **Celery:** tarefas em `app.api.tasks`. `scan_cargaxml_params` é agendada no `CELERY_BEAT_SCHEDULE` (ex.: a cada minuto). `process_cargaxml_param` processa um parâmetro por vez (diretório, ZIPs, XMLs, CargaXml, movendo arquivos).
- **Jobs em thread:** carga manual de XML e SPED não usam Celery; a view cria o job e inicia uma thread que chama `processar_job_xml_background` ou `processar_job_sped_background`. O front consulta as APIs de jobs para exibir status.

---

## 6. Funcionalidades por subsolução (resumo)

| Subsolução | Descrição |
|------------|-----------|
| Dm_Usuarios | Listar, inserir e editar usuários; vincular a empresas e grupos. |
| Dm_Empresas | CRUD empresas, grupos de empresa, certificado digital (.pfx). |
| Dm_Clientes | CRUD clientes GDF, acessos (soluções), grupos, conexão SAP. |
| Pro_CargaXml | Upload XML/ZIP, parâmetros agendados, jobs, avisos, relatório de carga. |
| Pro_CargaSped | Upload SPED, parâmetros, jobs, avisos. |
| Pro_Relatorio | Filtros por empresa/grupo e período; listagem e detalhe NFe, CTe, NFSe, SPED. |
| Reproc_Painel | Lotes, confronto SPED x NFe, divergências, condições de pagamento, envio SAP. |
| Mnf_Painel | Painel de manifesto (NFe, CTe, NFSe). |
| Db_Vendas / Db_Compras | Dashboards Streamlit em iframe (JWT). |

---

## 7. Referências rápidas

- Nomenclatura: [WORKBOOK_NOMENCLATURA.md](WORKBOOK_NOMENCLATURA.md).
- Estrutura e fluxos: [ARQUITETURA.md](ARQUITETURA.md).
- Uso das telas: [MANUAL_USUARIO.md](MANUAL_USUARIO.md).
- Deploy: [DEPLOY.md](DEPLOY.md).
- Termos: [GLOSSARIO.md](GLOSSARIO.md).

---

*Última atualização: Março 2026*
