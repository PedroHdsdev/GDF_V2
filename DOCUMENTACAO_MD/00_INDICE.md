# Índice da documentação – GDF_V2

Sistema multi-tenant ERP para gestão fiscal (NFe, CTe, NFSe, SPED) e integração SAP.

---

## Visão geral da documentação

Esta documentação cobre **nomenclatura**, **arquitetura**, **funcionalidades**, **uso pelas telas** e **deploy** do projeto. Use o índice abaixo para ir direto ao que precisa.

---

## Documentos disponíveis

| Documento | Conteúdo resumido |
|-----------|-------------------|
| **[WORKBOOK_NOMENCLATURA.md](WORKBOOK_NOMENCLATURA.md)** | Padrões de nomenclatura do código: prefixos `fn_view_` / `fn_api_`, models (snake_case, db_table), classes de negócio (`ClGdf`, `CargaXml`, `CargaSped`, `SapRfc`), convenções de nomes. |
| **[DOCUMENTACAO_PROJETO_GDF.md](DOCUMENTACAO_PROJETO_GDF.md)** | Documentação técnica completa: visão geral, stack, módulos (views, api, classes, db_GDF, security, utils), multi-tenancy, schemas e modelos, segurança (decorators, middlewares, validação), tarefas assíncronas (Celery e jobs em thread), funcionalidades por subsolução, integração SAP. |
| **[ARQUITETURA.md](ARQUITETURA.md)** | Arquitetura do sistema: hierarquia completa de pastas e arquivos, estrutura do `app/`, schemas PostgreSQL e tabelas por schema, fluxos de dados (login, carga XML/SPED, relatório, reprocessamento), diagrama de dependências, lista completa de URLs e rotas. |
| **[MANUAL_USUARIO.md](MANUAL_USUARIO.md)** | Manual do usuário: acesso e login, menu e subsoluções, cadastros (usuários, empresas, clientes GDF, grupos, certificado, SAP), Carga XML (manual e agendada), Carga SPED, Relatório fiscal, Reprocessamento (confronto SPED x NFe, divergências, condições de pagamento, envio SAP), Manifesto e Dashboards, dicas e troubleshooting. |
| **[DEPLOY.md](DEPLOY.md)** | Deploy em produção: requisitos (Python, PostgreSQL, Redis, servidor), variáveis de ambiente detalhadas, instalação passo a passo, Gunicorn e Nginx, Celery (worker e beat), agendador alternativo sem Redis, HTTPS e certificados, checklist completo e monitoramento. |
| **[GLOSSARIO.md](GLOSSARIO.md)** | Glossário de termos: GDF, cliente GDF, cliente 1000, empresa, grupo de empresa, usuário, solução, subsolução, NFe/CTe/NFSe, SPED, carga XML/SPED, job, reprocessamento, divergência, condição de pagamento, SAP RFC, IDOR, schema, e outros. |

---

## Por onde começar

| Perfil | Ordem sugerida |
|--------|----------------|
| **Desenvolvedor (novo no projeto)** | 1. [WORKBOOK_NOMENCLATURA](WORKBOOK_NOMENCLATURA.md) → 2. [ARQUITETURA](ARQUITETURA.md) → 3. [DOCUMENTACAO_PROJETO_GDF](DOCUMENTACAO_PROJETO_GDF.md) |
| **Usuário final / suporte** | [MANUAL_USUARIO](MANUAL_USUARIO.md) e [GLOSSARIO](GLOSSARIO.md) |
| **DevOps / deploy** | [ARQUITETURA](ARQUITETURA.md) (seção de estrutura) → [DEPLOY](DEPLOY.md) |
| **Consultas rápidas** | [GLOSSARIO](GLOSSARIO.md) para termos; [ARQUITETURA](ARQUITETURA.md) para URLs e fluxos. |

---

## Convenções usadas nos documentos

- **Prefixo de funções:** `fn_view_*` = tela (HTML); `fn_api_*` = API (JSON).
- **Caminhos:** referências a arquivos são relativas à raiz do repositório (ex.: `GDF_PJT/app/views.py`).
- **Schemas do banco:** `public`, `nfe`, `cte`, `nfse`, `sped_fiscal`, `sped_contribuicao`, `reprocessamento`.

---

*Última atualização: Março 2026*
