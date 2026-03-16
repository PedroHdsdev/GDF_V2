# Documentação GDF_V2

Esta pasta concentra **toda a documentação** do projeto **GDF_V2**: sistema multi-tenant ERP para gestão fiscal (NFe, CTe, NFSe, SPED) e integração SAP.

---

## Estrutura dos arquivos

| Arquivo | Propósito |
|---------|-----------|
| **00_INDICE.md** | Índice geral com descrição de cada documento e sugestão “por onde começar” (desenvolvedor, usuário, DevOps). |
| **README.md** | Este arquivo: visão da pasta e link para o índice. |
| **WORKBOOK_NOMENCLATURA.md** | Padrões de nomenclatura do código (views, APIs, models, classes de negócio). |
| **DOCUMENTACAO_PROJETO_GDF.md** | Documentação técnica detalhada: visão geral, módulos, banco de dados, segurança, tarefas assíncronas, funcionalidades por subsolução. |
| **ARQUITETURA.md** | Estrutura de pastas, schemas e tabelas, fluxos de dados, dependências entre módulos, lista completa de URLs. |
| **MANUAL_USUARIO.md** | Manual do usuário: como usar cada tela (login, cadastros, carga XML/SPED, relatório, reprocessamento, manifesto, dashboards). |
| **DEPLOY.md** | Guia de deploy em produção: requisitos, variáveis de ambiente, instalação, servidor, Celery, HTTPS, checklist. |
| **GLOSSARIO.md** | Glossário de termos do domínio (GDF, cliente, empresa, subsolução, NFe, SPED, job, etc.). |
| **CONDICAO_PAGAMENTO.md** | Condições de pagamento (mapeamento NFe → SAP). |
| **RELATORIO_ESCALABILIDADE.md** | Relatório de escalabilidade (testes de carga). |
| **RELATORIO_PERFORMANCE.md** | Relatório de performance. |
| **RELATORIO_SEGURANCA.md** | Relatório de segurança. |
| **README_views.md** | Views: estrutura e migração por domínio. |
| **README_streamlit.md** | Streamlit: dashboards por solução. |
| **README_security.md** | Security: decorators, middlewares. |
| **README_api.md** | API: jobs, tasks Celery, endpoints. |

---

## Como usar

1. **Comece pelo [00_INDICE.md](00_INDICE.md)** para escolher o documento certo.
2. Para **desenvolvimento**, siga: Workbook → Arquitetura → Documentação do projeto.
3. Para **uso do sistema**, use o **Manual do usuário** e o **Glossário**.
4. Para **colocar em produção**, use **Arquitetura** (contexto) e **DEPLOY.md** (passo a passo).

---

*Última atualização: Março 2026*
