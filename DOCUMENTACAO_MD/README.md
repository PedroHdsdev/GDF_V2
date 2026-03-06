# 📚 Documentação GDF_V2

Pasta central da documentação do projeto GDF_V2 (sistema multi-tenant ERP). Use este README para localizar documentos por tema.

---

## 🗂️ Estrutura por tema

### 🚀 Começar
| Documento | Descrição |
|-----------|-----------|
| [00_COMECE_AQUI.md](00_COMECE_AQUI.md) | Ponto de partida: entrega da auditoria e caminhos por perfil |
| [QUICK_START.md](QUICK_START.md) | Implementação rápida (Fase 1 em ~30 min) |
| [INDICE.md](INDICE.md) | Índice completo com acesso por papel (Gerente, Dev, DevOps, Security) |

### 📐 Nomenclatura e padrões do projeto
| Documento | Descrição |
|-----------|-----------|
| [WORKBOOK_NOMENCLATURA.md](WORKBOOK_NOMENCLATURA.md) | **Padrão oficial**: prefixos, models Public (ClienteGdf, Empresa, etc.), módulo `app.classes` (ClGdf, CargaXml, CargaSped, SapRfc) |

### 🏗️ Arquitetura e domínio
| Documento | Descrição |
|-----------|-----------|
| [ARQUITETURA_USUARIOS.md](ARQUITETURA_USUARIOS.md) | Usuários, clientes, empresas, grupos, sessão e multi-tenancy |
| [ARQUITETURA_ANTES_DEPOIS.md](ARQUITETURA_ANTES_DEPOIS.md) | Diagramas atual vs recomendado e escalabilidade |
| [SUBSOLUCOES_E_PAGINA_PRODUTOS.md](SUBSOLUCOES_E_PAGINA_PRODUTOS.md) | Subsoluções, menus e páginas de produtos |

### 📄 Funcionalidades (NFe, Carga XML, SAP)
| Documento | Descrição |
|-----------|-----------|
| [DOCUMENTACAO_NF-E.md](DOCUMENTACAO_NF-E.md) | Modelos e fluxos de NF-e |
| [FLUXO_CARGA_XML.md](FLUXO_CARGA_XML.md) | Fluxo completo da carga de XML (NFe, CTe, NFSe) |
| [CORRECOES_HTML_JS_CARGA_XML.md](CORRECOES_HTML_JS_CARGA_XML.md) | Ajustes de frontend na tela de Carga XML |
| [LOGICA_BUSCA_EMPRESA_NFE.md](LOGICA_BUSCA_EMPRESA_NFE.md) | Lógica de busca de empresa para NF-e |
| [PREENCHIMENTO_NFE_COMPLETO.md](PREENCHIMENTO_NFE_COMPLETO.md) | Preenchimento completo dos dados da NFe |
| [SAP_RFC_SETUP.md](SAP_RFC_SETUP.md) | Configuração de conexão SAP RFC |

### 🔐 Segurança e auditoria
| Documento | Descrição |
|-----------|-----------|
| [RESUMO_EXECUTIVO.md](RESUMO_EXECUTIVO.md) | Visão executiva dos achados de auditoria |
| [AUDITORIA_SEGURANCA_PERFORMANCE.md](AUDITORIA_SEGURANCA_PERFORMANCE.md) | Análise técnica (segurança, performance, escalabilidade) |
| [GUIA_IMPLEMENTACAO_PRATICA.md](GUIA_IMPLEMENTACAO_PRATICA.md) | Código pronto para implementar correções |
| [SEGURANCA_IMPLEMENTACAO_COMPLETA.md](SEGURANCA_IMPLEMENTACAO_COMPLETA.md) | Implementação de segurança por fases |

### ⚡ Performance e deploy
| Documento | Descrição |
|-----------|-----------|
| [PERFORMANCE_ESCALABILIDADE_COMPLETO.md](PERFORMANCE_ESCALABILIDADE_COMPLETO.md) | Performance e escalabilidade (100/1000 usuários) |
| [CHECKLIST_DEPLOY_ESCALABILIDADE.md](CHECKLIST_DEPLOY_ESCALABILIDADE.md) | Checklist de deploy (staging/produção) |
| [DEPLOYMENT_HTTPS.md](DEPLOYMENT_HTTPS.md) | Deploy com HTTPS |
| [BASELINE_GUIA_COMPLETO.md](BASELINE_GUIA_COMPLETO.md) | Guia de baseline e testes |

### 📋 Análise e referência
| Documento | Descrição |
|-----------|-----------|
| [ANALISE_DOCUMENTACAO_LIMPEZA.md](ANALISE_DOCUMENTACAO_LIMPEZA.md) | Análise de limpeza e consolidação da documentação |

---

## 📌 Nomenclatura atual do projeto (referência rápida)

- **Models Public:** `ClienteGdf`, `Empresa`, `UsuarioEmpresa`, `AcessoSolucaoCliente`, `AcessoSubsolucaoGrupo`, `PermissaoGrupoCliente`, `GrupoEmpresa`, `CertificadoDigital`, `ConexaoSap`.
- **Classes de negócio (`app.classes`):** `ClGdf`, `CargaXml`, `CargaSped`, `SapRfc`.
- **Filtros multi-tenant:** `gdfcliente__cod_cliente`; reverse de Empresa em ClienteGdf: `empresa_set`.

Detalhes: [WORKBOOK_NOMENCLATURA.md](WORKBOOK_NOMENCLATURA.md).

---

**Última atualização da estrutura:** Março 2026
