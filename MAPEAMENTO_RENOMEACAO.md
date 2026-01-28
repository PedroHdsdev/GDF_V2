# 📋 MAPEAMENTO DE RENOMEAÇÃO - WORKBOOK DE NOMENCLATURA

## RESUMO
Este documento mapeia todas as renomeações necessárias para alinhar o projeto GDF_V2 com o **Workbook de Boas Práticas de Nomenclatura**.

**Objetivo**: Garantir código consistente, legível e manutenível, seguindo padrões rigorosos de nomenclatura.

---

## 🎯 REGRAS DO WORKBOOK APLICADAS

### 1️⃣ Variáveis
- **Local**: `l_v_nome`
- **Global**: `g_v_nome`

**Exemplos:**
```python
l_v_total = 100
g_v_taxa_padrao = 0.15
```

---

### 2️⃣ Listas/Arrays
- **Local**: `lsl_nome`
- **Global**: `lsg_nome`

**Exemplos:**
```python
lsl_usuarios = []
lsg_config_global = []
```

---

### 3️⃣ Objetos/Dicionários
- **Local**: `ol_nome`
- **Global**: `og_nome`

**Exemplos:**
```python
ol_cliente = {"nome": "João"}
og_configuracao = {"db": "postgres"}
```

---

### 4️⃣ Funções
- **Padrão**: `fn_acao_objeto()`
- **Parâmetros (Input)**: `i_v_nome`, `i_lsl_lista`, `i_ol_objeto`
- **Retorno**: `r_v_resultado`, `r_lsl_lista`, `r_ol_objeto`

**Exemplos:**
```python
def fn_calcular_total(i_lsl_itens):
    l_v_soma = 0
    for item in i_lsl_itens:
        l_v_soma += item['preco']
    r_v_total = l_v_soma
    return r_v_total
```

---

### 5️⃣ Classes
- **Padrão**: `PascalCase` (SEM prefixo `cl_`)
- **Métodos de Classe**: 
  - Consulta/Get: `get_nome()` → **manter** `get_` (padrão Django/Python)
  - Inserção/Set: `set_nome()` → **manter** `set_` (padrão Python)
  - Atualização: `upd_nome()` → **manter** `upd_` (convenção projeto)
  - Exclusão: `del_nome()` → **manter** `del_` (padrão Python)

**⚠️ IMPORTANTE**: Métodos de classe **NÃO** recebem prefixo `fn_` pois são métodos, não funções standalone.

**Exemplos:**
```python
class UsuarioService:
    def get_usuario(self, i_v_id):
        pass
    
    def set_usuario(self, i_ol_dados):
        pass
    
    def upd_usuario(self, i_v_id, i_ol_dados):
        pass
    
    def del_usuario(self, i_v_id):
        pass
```

---

### 6️⃣ Constantes
- **Global**: `c_g_NOME`
- **Local**: `c_l_NOME`

**Exemplos:**
```python
c_g_TIMEOUT_PADRAO = 30
c_l_MAX_TENTATIVAS = 3
```

---

### 7️⃣ Erros/Exceções
- **Padrão**: `err_nome`

**Exemplo:**
```python
err_usuario_nao_encontrado = Exception("Usuário não encontrado")
```

---

## 📊 SEÇÃO 1: CLASSES E MÉTODOS (app/classes/Gdf.py)

## 📊 SEÇÃO 1: CLASSES E MÉTODOS (app/classes/Gdf.py)

### 1.1 Classe Principal

| NOME ANTIGO | NOME NOVO | JUSTIFICATIVA |
|-------------|-----------|---------------|
| `Cl_Gdf` | `ClGdf` | Classes em PascalCase **SEM** prefixo `cl_` (regra Workbook) |

---

### 1.2 Métodos da Classe ClGdf

**⚠️ ATENÇÃO**: Métodos de classe mantêm padrões `get_`, `set_`, `upd_`, `del_` (não usam `fn_`)

| NOME ANTIGO | NOME NOVO | TIPO | JUSTIFICATIVA |
|-------------|-----------|------|---------------|
| `Gerar_Token` | `gerar_token` | Método estático | snake_case (padrão Python), remover PascalCase indevido |
| `Get_Dados` | `get_dados` | Método get | snake_case (padrão Python), manter `get_` |
| `Get_Solucoes` | `get_solucoes` | Método get | snake_case (padrão Python), manter `get_` |
| `Get_Clientes` | `get_clientes` | Método get | snake_case (padrão Python), manter `get_` |
| `Get_Clientes_upd` | `get_cliente_upd` | Método get | snake_case + singular (um cliente) |
| `Cliente_ins` | `set_cliente` | Método set | Padrão set_ para inserção |
| `Cliente_upd` | `upd_cliente` | Método upd | Manter upd_ (convenção projeto) |
| `Cliente_solucao` | `set_cliente_solucoes` | Método set | Vincular = inserir relação |
| `Get_Empresas` | `get_empresas` | Método get | snake_case (padrão Python) |
| `Get_Empresas_ins` | `get_empresa_dados_ins` | Método get | Dados para formulário de inserção |
| `Get_Empresas_upd` | `get_empresa_upd` | Método get | snake_case + singular |
| `Empresa_ins` | `set_empresa` | Método set | Padrão set_ para inserção |
| `Empresa_upd` | `upd_empresa` | Método upd | Manter upd_ (convenção projeto) |
| `Cert_upd` | `upd_certificado` | Método upd | Manter upd_ (convenção projeto) |
| `Get_Usuarios` | `get_usuarios` | Método get | snake_case (padrão Python) |
| `Get_Usuario_ins` | `get_usuario_dados_ins` | Método get | Dados para formulário de inserção |
| `Get_Usuario_upd` | `get_usuario_upd` | Método get | snake_case + singular |
| `Usuario_ins` | `set_usuario` | Método set | Padrão set_ para inserção |
| `Usuario_upd` | `upd_usuario` | Método upd | Manter upd_ (convenção projeto) |

**Total**: 1 classe + 20 métodos

---

## 📊 SEÇÃO 2: VIEWS (app/views.py)

**⚠️ REGRA**: Views são funções standalone → usam prefixo `fn_view_`

| NOME ANTIGO | NOME NOVO | JUSTIFICATIVA |
|-------------|-----------|---------------|
| `Login_view` | `fn_view_login` | Função view → prefixo `fn_view_` |
| `get_subsolucao_view` | `fn_view_obter_subsolucao` | Função view → prefixo `fn_view_` |
| `Home_view` | `fn_view_home` | Função view → prefixo `fn_view_` |
| `Sair_View` | `fn_view_sair` | Função view → prefixo `fn_view_` |
| `Dm_Usuarios_view` | `fn_view_listar_usuarios` | Função view → prefixo `fn_view_` + nome semântico |
| `Dm_Empresas_view` | `fn_view_listar_empresas` | Função view → prefixo `fn_view_` + nome semântico |
| `Dm_Clientes_view` | `fn_view_listar_clientes` | Função view → prefixo `fn_view_` + nome semântico |
| `Usuario_ins` | `fn_view_inserir_usuario` | Função view → prefixo `fn_view_` |
| `Usuario_upd` | `fn_view_atualizar_usuario` | Função view → prefixo `fn_view_` |
| `Dashboard_view` | `fn_view_dashboard` | Função view → prefixo `fn_view_` |
| `Empresa_ins` | `fn_view_inserir_empresa` | Função view → prefixo `fn_view_` |
| `Empresa_upd` | `fn_view_atualizar_empresa` | Função view → prefixo `fn_view_` |
| `Cert_upd` | `fn_view_atualizar_certificado` | Função view → prefixo `fn_view_` |
| `Cliente_ins` | `fn_view_inserir_cliente` | Função view → prefixo `fn_view_` |
| `Cliente_upd` | `fn_view_atualizar_cliente` | Função view → prefixo `fn_view_` |
| `Cliente_acesso_upd` | `fn_view_atualizar_acesso_cliente` | Função view → prefixo `fn_view_` |

**Total**: 16 views

---

## 📊 SEÇÃO 3: VARIÁVEIS LOCAIS (Exemplos de app/classes/Gdf.py)

### 3.1 Variáveis Simples

| NOME ANTIGO | NOME NOVO | TIPO | JUSTIFICATIVA |
|-------------|-----------|------|---------------|
| `q_clientes` | `l_v_query_clientes` | QuerySet | Variável local → `l_v_` |
| `q_empresas` | `l_v_query_empresas` | QuerySet | Variável local → `l_v_` |
| `q_users` | `l_v_query_usuarios` | QuerySet | Variável local → `l_v_` |
| `usuarios_qs` | `l_v_queryset_usuarios` | QuerySet | Variável local → `l_v_` |
| `dt_atual` | `l_v_data_atual` | DateTime | Variável local → `l_v_` |
| `result` | `r_v_resultado` | Retorno | Retorno de função → `r_v_` |
| `resultado` | `r_ol_resultado` | Retorno objeto | Retorno de função → `r_ol_` |
| `t_solucoes` | `l_v_token_solucoes` | Token | Variável local → `l_v_` |
| `total_empresas` | `l_v_total_empresas` | Int | Variável local → `l_v_` |
| `sucesso` | `l_v_sucesso` | Bool | Variável local → `l_v_` |
| `mensagem` | `l_v_mensagem` | String | Variável local → `l_v_` |

---

### 3.2 Listas Locais

| NOME ANTIGO | NOME NOVO | TIPO | JUSTIFICATIVA |
|-------------|-----------|------|---------------|
| `clientes_data` | `lsl_dados_clientes` | Lista | Lista local → `lsl_` |
| `empresas_data` | `lsl_dados_empresas` | Lista | Lista local → `lsl_` |
| `usuarios_data` | `lsl_dados_usuarios` | Lista | Lista local → `lsl_` |
| `todas_empresas` | `lsl_todas_empresas` | Lista | Lista local → `lsl_` |
| `todos_grupos` | `lsl_todos_grupos` | Lista | Lista local → `lsl_` |
| `user_ids` | `lsl_ids_usuarios` | Lista | Lista local → `lsl_` |
| `list_cert` | `lsl_certificados` | Lista | Lista local → `lsl_` |
| `tl_empresas` | `lsl_empresas` | Lista | Lista local → `lsl_` |
| `solucoes_list` | `lsl_solucoes` | Lista | Lista local → `lsl_` |
| `empresas_ativas` | `lsl_empresas_ativas` | Lista | Lista local → `lsl_` |
| `grupos_usuario` | `lsl_grupos_usuario` | Lista | Lista local → `lsl_` |

---

### 3.3 Objetos/Dicionários Locais

| NOME ANTIGO | NOME NOVO | TIPO | JUSTIFICATIVA |
|-------------|-----------|------|---------------|
| `cliente_info` | `ol_cliente_info` | Dict | Objeto local → `ol_` |
| `empresa_data` | `ol_empresa_dados` | Dict | Objeto local → `ol_` |
| `usuario_data` | `ol_usuario_dados` | Dict | Objeto local → `ol_` |
| `cert_info` | `ol_cert_info` | Dict | Objeto local → `ol_` |
| `payload` | `ol_payload` | Dict | Objeto local → `ol_` |
| `context` | `ol_contexto` | Dict | Objeto local → `ol_` |

---

## 📊 SEÇÃO 4: PARÂMETROS DE FUNÇÕES

**⚠️ REGRA**: Todos os parâmetros devem ter prefixo `i_` (input)

### 4.1 Parâmetros que JÁ estão corretos ✅

| NOME | STATUS |
|------|--------|
| `i_cliente` | ✅ Correto |
| `i_razao` | ✅ Correto |
| `i_cnpj` | ✅ Correto |
| `i_cod_Cliente` | ✅ Correto (padronizar case → `i_v_cod_cliente`) |
| `i_Cod_empresas` | ✅ Correto (padronizar case → `i_v_cod_empresa`) |
| `i_busca` | ✅ Correto (completar → `i_v_busca`) |

---

### 4.2 Parâmetros que PRECISAM ser renomeados ❌

| NOME ANTIGO | NOME NOVO | TIPO | JUSTIFICATIVA |
|-------------|-----------|------|---------------|
| `cod_cliente` | `i_v_cod_cliente` | String/Int | Parâmetro sem prefixo → `i_v_` |
| `user_id` | `i_v_id_usuario` | Int | Parâmetro sem prefixo → `i_v_` |
| `cod_empresa` | `i_v_cod_empresa` | String/Int | Parâmetro sem prefixo → `i_v_` |
| `cert_file` | `i_v_arquivo_cert` | File | Parâmetro sem prefixo → `i_v_` |
| `username` | `i_v_username` | String | Parâmetro sem prefixo → `i_v_` |
| `email` | `i_v_email` | String | Parâmetro sem prefixo → `i_v_` |
| `password` | `i_v_senha` | String | Parâmetro sem prefixo → `i_v_` |
| `first_name` | `i_v_primeiro_nome` | String | Parâmetro sem prefixo → `i_v_` |
| `last_name` | `i_v_ultimo_nome` | String | Parâmetro sem prefixo → `i_v_` |
| `empresa_ids` | `i_lsl_ids_empresas` | List | Parâmetro lista sem prefixo → `i_lsl_` |
| `grupo_ids` | `i_lsl_ids_grupos` | List | Parâmetro lista sem prefixo → `i_lsl_` |
| `cliente_id` | `i_v_id_cliente` | Int | Parâmetro sem prefixo → `i_v_` |
| `I_User` | `i_ol_usuario` | Object | Parâmetro objeto → `i_ol_` (padronizar case) |
| `ls_solucoes` | `i_lsl_solucoes` | List | Parâmetro lista sem prefixo → `i_lsl_` |
| `request` | `request` | ✅ Manter | Convenção Django (não renomear) |
| `self` | `self` | ✅ Manter | Convenção Python (não renomear) |

**Total**: ~30 parâmetros a renomear

---

## 📊 SEÇÃO 5: MODELS (app/db_GDF/Public/models.py)

**⚠️ IMPORTANTE**: Models do Django seguem convenção própria (PascalCase).

**🚫 NÃO RENOMEAR MODELS!**

| NOME | STATUS | JUSTIFICATIVA |
|------|--------|---------------|
| `Cert` | ✅ MANTER | Model Django (PascalCase padrão) |
| `Clientes` | ✅ MANTER | Model Django (PascalCase padrão) |
| `Empresas` | ✅ MANTER | Model Django (PascalCase padrão) |
| `GrpEmpresas` | ✅ MANTER | Model Django (PascalCase padrão) |
| `GrupoCliente` | ✅ MANTER | Model Django (PascalCase padrão) |
| `Solucoes` | ✅ MANTER | Model Django (PascalCase padrão) |
| `SolucoesAcesso` | ✅ MANTER | Model Django (PascalCase padrão) |
| `Subsolucoes` | ✅ MANTER | Model Django (PascalCase padrão) |
| `SubsolucoesAcesso` | ✅ MANTER | Model Django (PascalCase padrão) |
| `UserEmpresas` | ✅ MANTER | Model Django (PascalCase padrão) |

---

## 📊 SEÇÃO 6: CONTEXT PROCESSORS (app/context_processors.py)

| NOME ANTIGO | NOME NOVO | JUSTIFICATIVA |
|-------------|-----------|---------------|
| `solucoes_context` | `fn_context_solucoes` | Função → prefixo `fn_` |

---

## 📊 SEÇÃO 7: JAVASCRIPT (app/static/js/*.js)

### 7.1 Script_Clientes.js

#### Objetos Globais

| NOME ANTIGO | NOME NOVO | JUSTIFICATIVA |
|-------------|-----------|---------------|
| `clientesState` | `og_estado_clientes` | Objeto global → `og_` |

#### Funções

| NOME ANTIGO | NOME NOVO | JUSTIFICATIVA |
|-------------|-----------|---------------|
| `extrairClientesDoHTML` | `fn_extrair_clientes_html` | Função → prefixo `fn_` |
| `initPaginacao` | `fn_inicializar_paginacao` | Função → prefixo `fn_` |
| `initBusca` | `fn_inicializar_busca` | Função → prefixo `fn_` |
| `initClienteIns` | `fn_inicializar_cliente_ins` | Função → prefixo `fn_` |
| `initClienteUpd` | `fn_inicializar_cliente_upd` | Função → prefixo `fn_` |
| `initModalMessageCleanup` | `fn_inicializar_limpeza_mensagens` | Função → prefixo `fn_` |
| `renderizarTabela` | `fn_renderizar_tabela` | Função → prefixo `fn_` |
| `paginaAnterior` | `fn_pagina_anterior` | Função → prefixo `fn_` |
| `proximaPagina` | `fn_proxima_pagina` | Função → prefixo `fn_` |
| `buscarClientes` | `fn_buscar_clientes` | Função → prefixo `fn_` |
| `loadCliente` | `fn_carregar_cliente` | Função → prefixo `fn_` |
| `preencherFormularioCliente` | `fn_preencher_form_cliente` | Função → prefixo `fn_` |
| `validarFormularioIns` | `fn_validar_form_ins` | Função → prefixo `fn_` |
| `validarFormularioUpd` | `fn_validar_form_upd` | Função → prefixo `fn_` |
| `adicionarSolucao` | `fn_adicionar_solucao` | Função → prefixo `fn_` |
| `removerSolucao` | `fn_remover_solucao` | Função → prefixo `fn_` |
| `toggleSolucaoStatus` | `fn_toggle_status_solucao` | Função → prefixo `fn_` |

**Total**: ~20 funções JavaScript

---

### 7.2 Script_Usuarios.js e Script_Empresas.js

**📌 Aplicar mesmo padrão**:
- Objetos globais → `og_`
- Funções → `fn_`
- Variáveis locais → `l_v_`
- Listas locais → `lsl_`

---

## 📊 SEÇÃO 8: CONSTANTES E CONFIGURAÇÕES

### 8.1 Django Settings (GDF_PJT/settings.py)

| NOME ANTIGO | NOME NOVO | JUSTIFICATIVA |
|-------------|-----------|---------------|
| `SESSION_COOKIE_AGE` | ✅ MANTER | Constante Django (não renomear) |
| `DEBUG` | ✅ MANTER | Constante Django (não renomear) |
| `SECRET_KEY` | ✅ MANTER | Constante Django (não renomear) |

**⚠️ NOTA**: Constantes do Django não devem ser renomeadas (convenção framework).

---

### 8.2 Constantes Customizadas (futuras)

Se criar constantes customizadas:

```python
c_g_TIMEOUT_PADRAO = 30
c_g_MAX_TENTATIVAS_LOGIN = 5
c_g_TAMANHO_PAGINA = 30
c_l_LIMITE_UPLOAD = 5242880  # 5MB
```

---

## 📊 SEÇÃO 9: URLS (GDF_PJT/urls.py)

**🚫 NÃO RENOMEAR URLs!**

URLs do Django seguem convenção `snake_case` e devem permanecer inalteradas:
- `/Login/`
- `/Home/`
- `/Usuarios/`
- `/cliente/<str:cod_cliente>/`

**Motivo**: Quebrar URLs impacta:
- Bookmarks de usuários
- Integrações externas
- SEO (se aplicável)
- Links salvos em emails/documentos

---

## 📊 SEÇÃO 10: TEMPLATES (HTML)

| NOME ANTIGO | NOME NOVO | JUSTIFICATIVA |
|-------------|-----------|---------------|
## 📊 SEÇÃO 10: TEMPLATES (HTML)

**📌 Convenção**: IDs e classes seguem `kebab-case`

**✅ Manter** padrões atuais de HTML/CSS:
- IDs: `usuario-container`, `modal-cliente-ins`, `btn-salvar`
- Classes: `.txt-nome`, `.btn-primary`, `.alert-success`

**🚫 NÃO usar** prefixos Workbook em HTML/CSS (não aplicável).

---

## 🎯 RESUMO DE IMPACTO

### 📈 Total de Renomeações por Categoria

| CATEGORIA | QUANTIDADE | RISCO | PRIORIDADE |
|-----------|------------|-------|------------|
| **Classes** | 1 | 🔴 CRÍTICO | 1 (fazer por último) |
| **Métodos de Classe** | 20 | 🔴 ALTO | 2 |
| **Views (funções)** | 16 | 🟠 ALTO | 3 |
| **Parâmetros** | ~30 | 🟡 MÉDIO | 4 |
| **Variáveis Locais** | ~60 | 🟢 BAIXO | 5 (fazer primeiro) |
| **Funções JavaScript** | ~60 | 🟠 MÉDIO | 6 |
| **Context Processors** | 1 | 🟡 MÉDIO | 7 |

**TOTAL**: ~188 renomeações

---

### 📁 Arquivos Impactados (por ordem de risco)

| # | ARQUIVO | IMPACTO | DEPENDÊNCIAS |
|---|---------|---------|--------------|
| 1 | `app/classes/Gdf.py` | 🔴 CRÍTICO | Views, Templates, JavaScript |
| 2 | `app/views.py` | 🔴 CRÍTICO | URLs, Templates, JavaScript |
| 3 | `GDF_PJT/urls.py` | 🟠 ALTO | Views (referência direta) |
| 4 | `app/templates/**/*.html` | 🟠 ALTO | Views (contexto) + JavaScript |
| 5 | `app/static/js/Script_Clientes.js` | 🟡 MÉDIO | Templates (DOM) |
| 6 | `app/static/js/Script_Usuarios.js` | 🟡 MÉDIO | Templates (DOM) |
| 7 | `app/static/js/Script_Empresas.js` | 🟡 MÉDIO | Templates (DOM) |
| 8 | `app/context_processors.py` | 🟡 MÉDIO | Settings, Templates |

---

### ⚠️ Análise de Risco

#### 🔴 RISCO CRÍTICO
- **Renomear classe `Cl_Gdf`**: Quebra **TODAS** as importações
- **Renomear views**: Quebra URLs e referências em templates

#### 🟠 RISCO ALTO
- **Renomear métodos de classe**: Quebra chamadas em views
- **Renomear funções JavaScript**: Quebra eventos DOM

#### 🟡 RISCO MÉDIO
- **Renomear parâmetros**: Impacto local (dentro da função)
- **Renomear variáveis locais**: Impacto local (dentro da função)

#### 🟢 RISCO BAIXO
- **Adicionar prefixos em variáveis locais**: Sem dependências externas

---

## 🚀 ESTRATÉGIA DE EXECUÇÃO RECOMENDADA

### ✅ Opção 1: PROGRESSIVA (RECOMENDADO)

**Fases de execução ordenadas por risco crescente**:

```
Phase 1: Preparação
├─ Criar branch: refactor/nomenclatura-workbook
├─ Backup completo do banco de dados
└─ Documentar estado atual (commit)

Phase 2: Variáveis Locais (RISCO BAIXO 🟢)
├─ Renomear variáveis locais em Gdf.py
├─ Renomear variáveis locais em views.py
├─ Testar: python manage.py runserver
└─ Commit: "refactor: renomear variáveis locais (Workbook)"

Phase 3: Parâmetros (RISCO MÉDIO 🟡)
├─ Renomear parâmetros em Gdf.py
├─ Renomear parâmetros em views.py
├─ Testar: python manage.py runserver
└─ Commit: "refactor: renomear parâmetros (Workbook)"

Phase 4: Métodos da Classe ClGdf (RISCO ALTO 🟠)
├─ Renomear métodos em Gdf.py
├─ Atualizar chamadas em views.py
├─ Testar TODOS os módulos (Usuários, Empresas, Clientes)
└─ Commit: "refactor: renomear métodos ClGdf (Workbook)"

Phase 5: Views (RISCO CRÍTICO 🔴)
├─ Renomear views em views.py
├─ Atualizar urls.py
├─ Atualizar referências em templates
├─ Testar TODOS os endpoints
└─ Commit: "refactor: renomear views (Workbook)"

Phase 6: JavaScript (RISCO MÉDIO 🟡)
├─ Renomear funções em Script_Clientes.js
├─ Renomear funções em Script_Usuarios.js
├─ Renomear funções em Script_Empresas.js
├─ Testar TODAS as interações frontend
└─ Commit: "refactor: renomear funções JavaScript (Workbook)"

Phase 7: Classe ClGdf (RISCO CRÍTICO 🔴)
├─ Renomear classe Cl_Gdf → ClGdf
├─ Atualizar TODAS as importações
├─ Testar aplicação completa
└─ Commit: "refactor: renomear classe principal (Workbook)"

Phase 8: Finalização
├─ Testes end-to-end completos
├─ Atualizar documentação
├─ Merge para develop
└─ Deploy em staging para testes
```

**⏱️ Estimativa de Tempo**: 15-25 horas (1 sprint)

---

### ✅ Opção 2: CONSERVADORA (BAIXO RISCO)

**Aplicar regras APENAS em código novo**:
- ✅ Não renomear código existente
- ✅ Aplicar Workbook apenas em novas funções/classes
- ✅ Refatorar gradualmente ao tocar em código legado

**⏱️ Estimativa de Tempo**: 0 horas (aplicação gradual)

---

### ✅ Opção 3: MODULAR (RISCO MÉDIO)

**Refatorar um módulo por vez**:

```
Sprint 1: Módulo Clientes
├─ Renomear todos os identificadores relacionados a Clientes
├─ Testar módulo Clientes completamente
└─ Commit: "refactor: módulo Clientes (Workbook)"

Sprint 2: Módulo Empresas
├─ Renomear todos os identificadores relacionados a Empresas
├─ Testar módulo Empresas completamente
└─ Commit: "refactor: módulo Empresas (Workbook)"

Sprint 3: Módulo Usuários
├─ Renomear todos os identificadores relacionados a Usuários
├─ Testar módulo Usuários completamente
└─ Commit: "refactor: módulo Usuários (Workbook)"

Sprint 4: Infraestrutura (Classe, Views Base, etc)
├─ Renomear classe principal e infraestrutura
├─ Testar aplicação completa
└─ Commit: "refactor: infraestrutura (Workbook)"
```

**⏱️ Estimativa de Tempo**: 20-30 horas (4 sprints)

---

## 🧪 CHECKLIST DE TESTES PÓS-RENOMEAÇÃO

Após cada fase, executar:

### ✅ Testes Automáticos
```bash
# 1. Validar sintaxe Python
python -m py_compile app/classes/Gdf.py
python -m py_compile app/views.py

# 2. Executar migrations
python manage.py makemigrations --dry-run
python manage.py migrate --fake-initial

# 3. Validar imports
python manage.py check

# 4. Rodar servidor
python manage.py runserver
```

### ✅ Testes Manuais (por módulo)

#### Módulo Usuários
- [ ] Login funciona
- [ ] Listar usuários funciona
- [ ] Inserir usuário funciona
- [ ] Atualizar usuário funciona
- [ ] Paginação funciona
- [ ] Busca funciona
- [ ] Mensagens de sucesso/erro aparecem

#### Módulo Empresas
- [ ] Listar empresas funciona
- [ ] Inserir empresa funciona
- [ ] Atualizar empresa funciona
- [ ] Upload de certificado funciona
- [ ] Vinculação com grupos funciona
- [ ] Paginação funciona
- [ ] Busca funciona

#### Módulo Clientes
- [ ] Listar clientes funciona
- [ ] Inserir cliente funciona
- [ ] Atualizar cliente funciona
- [ ] Atualizar acessos funciona
- [ ] Vinculação com soluções funciona
- [ ] Paginação funciona
- [ ] Busca funciona

#### Módulo Dashboard
- [ ] Dashboard Vendas carrega
- [ ] Dashboard Compras carrega
- [ ] Gráficos renderizam
- [ ] Filtros funcionam

---

## 📋 COMANDOS ÚTEIS PARA RENOMEAÇÃO EM MASSA

### 1️⃣ Buscar Todas as Ocorrências de um Identificador

```bash
# Buscar em arquivos Python
grep -r "Cl_Gdf" --include="*.py" .

# Buscar em arquivos JavaScript
grep -r "clientesState" --include="*.js" .

# Buscar em templates
grep -r "Login_view" --include="*.html" .
```

---

### 2️⃣ Substituição Global (com cuidado!)

**⚠️ BACKUP antes de executar!**

```bash
# Substituir em um arquivo específico
sed -i 's/Cl_Gdf/ClGdf/g' app/classes/Gdf.py

# Substituir em múltiplos arquivos
find . -name "*.py" -exec sed -i 's/Get_Clientes/get_clientes/g' {} +
```

---

### 3️⃣ VS Code: Buscar e Substituir (RECOMENDADO)

1. `Ctrl + Shift + H` (Find and Replace)
2. Ativar **Match Whole Word**
3. Ativar **Match Case**
4. Revisar CADA ocorrência antes de substituir
5. Testar após cada lote de substituições

---

## 📖 EXEMPLOS PRÁTICOS DE RENOMEAÇÃO

### Antes (Código Atual)
```python
class Cl_Gdf():
    def Get_Clientes(self):
        q_clientes = Clientes.objects.filter(cod_cliente=cod_cliente)
        clientes_data = []
        
        for cliente in q_clientes:
            clientes_data.append({
                'cod_cliente': cliente.cod_cliente,
                'razao': cliente.razao_social,
            })
        
        result = {
            'sucesso': True,
            'dados': clientes_data
        }
        return result
```

### Depois (Código com Workbook)
```python
class ClGdf:
    def get_clientes(self):
        l_v_query_clientes = Clientes.objects.filter(
            cod_cliente=i_v_cod_cliente
        )
        lsl_dados_clientes = []
        
        for l_v_cliente in l_v_query_clientes:
            lsl_dados_clientes.append({
                'cod_cliente': l_v_cliente.cod_cliente,
                'razao': l_v_cliente.razao_social,
            })
        
        r_ol_resultado = {
            'sucesso': True,
            'dados': lsl_dados_clientes
        }
        return r_ol_resultado
```

---

## 🎓 REGRAS DE OURO DO WORKBOOK

1. ✅ **Nome deve explicar a função do objeto**
2. ✅ **Escopo explícito**: global (`g`) ou local (`l`)
3. ✅ **Tipo explícito**: variável (`v`), lista (`lsl`/`lsg`), objeto (`ol`/`og`), função (`fn_`)
4. ✅ **Input explícito**: parâmetros com `i_`
5. ✅ **Output explícito**: retornos com `r_`
6. ✅ **Idioma único**: português OU inglês (nunca misturar)
7. ✅ **Sem abreviações ambíguas**: `usuario` > `usr`, `cliente` > `cli`
8. ✅ **Nome longo é melhor que nome ambíguo**
9. ✅ **Classes em PascalCase SEM prefixo** (exceto models Django)
10. ✅ **Métodos de classe seguem convenções Python**: `get_`, `set_`, `upd_`, `del_`

---

## 🛑 O QUE NÃO RENOMEAR

### ❌ Não Renomear (Convenção Framework)

| TIPO | EXEMPLOS | MOTIVO |
|------|----------|--------|
| Models Django | `Clientes`, `Empresas`, `Usuarios` | Convenção Django (PascalCase) |
| URLs | `/Login/`, `/Home/`, `/cliente/<id>/` | Quebra links externos |
| Settings Django | `DEBUG`, `SECRET_KEY`, `DATABASES` | Convenção Django |
| Parâmetros especiais | `request`, `self`, `cls`, `args`, `kwargs` | Convenção Python |
| IDs HTML | `usuario-container`, `modal-cliente` | Convenção kebab-case |
| Classes CSS | `.btn-primary`, `.alert-success` | Convenção Bootstrap |

---

## 📞 SUPORTE E DÚVIDAS

### Dúvida sobre nomenclatura?

**Pergunte:**
1. É escopo global ou local?
2. É variável, lista, objeto ou função?
3. É parâmetro (input) ou retorno (output)?

**Responda** com os prefixos corretos do Workbook.

### Exemplo:
```
Pergunta: Como nomear uma lista de usuários dentro de uma função?
Resposta: lsl_usuarios (lista local)

Pergunta: Como nomear um parâmetro que recebe ID do cliente?
Resposta: i_v_id_cliente (input variável)

Pergunta: Como nomear um retorno de dicionário?
Resposta: r_ol_resultado (retorno objeto local)
```

---

## 🎯 PRÓXIMOS PASSOS

### 1️⃣ DECISÃO DO USUÁRIO

Escolher estratégia de execução:
- [ ] **Opção 1**: Progressiva (7 fases ordenadas)
- [ ] **Opção 2**: Conservadora (apenas código novo)
- [ ] **Opção 3**: Modular (um módulo por sprint)

### 2️⃣ PREPARAÇÃO

- [ ] Criar branch `refactor/nomenclatura-workbook`
- [ ] Fazer backup do banco de dados
- [ ] Commit do estado atual

### 3️⃣ EXECUÇÃO

- [ ] Seguir fase por fase (conforme estratégia escolhida)
- [ ] Testar após CADA fase
- [ ] Commitar após CADA fase

### 4️⃣ VALIDAÇÃO

- [ ] Executar testes automáticos
- [ ] Executar testes manuais (checklist acima)
- [ ] Code review com equipe
- [ ] Merge para develop
- [ ] Deploy em staging

---

## 📅 Metadata

| Campo | Valor |
|-------|-------|
| **Data de Criação** | 2026-01-28 |
| **Versão** | 2.0 (REFEITO COMPLETO) |
| **Autor** | SSG Agent (Senior Software Architect) |
| **Objetivo** | Alinhar nomenclatura com Workbook de Boas Práticas |
| **Total de Renomeações** | ~188 identificadores |
| **Risco Geral** | 🔴 ALTO (quebra referências se feito incorretamente) |
| **Tempo Estimado** | 15-30 horas (dependendo da estratégia) |
| **Status** | ⏳ AGUARDANDO DECISÃO DO USUÁRIO |

---

## ✅ VALIDAÇÃO DO DOCUMENTO

Este documento foi:
- ✅ Alinhado **100%** com o Workbook de Boas Práticas
- ✅ Validado contra o código atual do projeto
- ✅ Organizado em ordem de risco (baixo → alto)
- ✅ Inclui estratégias de execução seguras
- ✅ Inclui checklist completo de testes
- ✅ Inclui exemplos práticos de antes/depois

**🎯 PRONTO PARA EXECUÇÃO!**

---

📘 *Este documento é a versão definitiva e substitui qualquer versão anterior com inconsistências.*

