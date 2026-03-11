# Condição de pagamento – Documentação completa

Este documento descreve o tratamento de **condições de pagamento** no GDF: origem dos dados (NFe/NFSe), modelos de dados, fluxo de reprocessamento, integração SAP e APIs.

---

## 1. Visão geral

No GDF, “condição de pagamento” aparece em dois contextos principais:

| Contexto | Descrição |
|----------|-----------|
| **Condição na NFe** | Texto ou código que descreve como a NF-e será paga (ex.: “À vista”, “3x em 30/60/90 dias”). É **derivada** das parcelas de cobrança da NFe (tag `cobr` / `dup`). |
| **Condição no SAP** | Código da condição de pagamento no ERP SAP (ex.: Z001). O sistema faz o **mapeamento** NFe → SAP por cliente (tabela de parâmetros) e envia ao SAP via RFC. |

O fluxo principal é:

1. **Carga XML:** ao importar NFe, a condição é extraída das parcelas e, se ainda não existir, é criado um registro em **CondicaoParam** (condição NFe + tipo pagamento, SAP em branco).
2. **Reprocessamento:** o usuário (ou processo) gera a **tabela de condições do lote** (`CondicaoPagamentoLote`), onde cada chave de NFe ganha condição NFe + condição SAP (preenchida pelo depara em CondicaoParam).
3. **Envio SAP:** as condições do lote são enviadas ao SAP via RFC; o sistema atualiza o status de cada registro conforme o retorno (P/E/S/U/I/R).

---

## 2. Origem dos dados

### 2.1 NF-e (condição derivada das parcelas)

A “condição de pagamento” da NFe **não** vem de um campo único no XML; é **montada** a partir do bloco de cobrança (`cobr` / `dup`):

- **Sem cobrança ou sem parcelas:** considera-se **“À vista”**.
- **Com parcelas:** a string é no formato  
  `"Nx em d1/d2/d3... dias"`, onde:
  - `N` = quantidade de parcelas;
  - `d1, d2, d3...` = dias entre a data de emissão e o vencimento de cada parcela (ordenadas por `numero_parcela`).

**Exemplo:** 3 parcelas com vencimentos 30, 60 e 90 dias após a emissão → `"3x em 30/60/90 dias"`.

**Implementação:** função `condicao_pagamento_da_nfe(identificacao)` em `app/classes/Reprocessamento.py`. Ela usa os models `NFe_Identificacao` → `NFe_Cobranca` → `NFe_Parcela` (schema `nfe`, tabelas `nfe_cobranca`, `nfe_parcela`).

**Regra especial na carga:** se alguma parcela tiver `valor_parcela` negativo, a condição **não** é gravada em CondicaoParam (evita cadastrar condições inválidas). Um aviso é registrado no log da carga.

### 2.2 NF-e (tipo de pagamento – tPag)

O **tipo de pagamento** é o código do meio de pagamento da NFe (tag `tPag`), por exemplo 01 (Dinheiro), 03 (Cartão de Crédito), 17 (PIX). No sistema:

- É obtido de `NFe_Identificacao` → `NFe_Pagamento` (`meio_pagamento`, 2 caracteres).
- Usado no **CondicaoParam** como parte da chave de mapeamento: (cliente, condição NFe, tipo_pagamento) → condição SAP.
- Usado na busca do depara: primeiro tenta com o tipo informado; se não achar, tenta sem tipo (tipo vazio/null).

Referência de códigos: `GDF_PJT/json/Tipo_pagamento.json` (ex.: 01=Dinheiro, 03=Cartão de Crédito, 17=PIX).

### 2.3 NFSe (condição de pagamento)

No modelo de **NFSe** (`app/db_GDF/NFSe/models.py`), existe um campo direto:

- `condicao_pagamento`: CharField com choices `VISTA`, `PRAZO`, `PARCELADO` (À Vista, À Prazo, Parcelado).

Esse campo é usado no contexto de NFSe (relatórios, dashboards). O fluxo de **reprocessamento e envio SAP** descrito neste documento refere-se às **NF-e** e às tabelas do schema `reprocessamento` (CondicaoPagamentoLote, CondicaoParam).

---

## 3. Modelos de dados (schema reprocessamento)

### 3.1 CondicaoParam (condição parâmetro)

**Tabela:** `reprocessamento.condicao_param`  
**Modelo:** `app.db_GDF.reprocessamento.models.CondicaoParam`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | PK | Identificador do registro. |
| gdfcliente_id (cod_cliente) | FK → ClienteGdf | Cliente GDF dono do mapeamento. |
| condicao_pagamento_nfe | VARCHAR(120) | Condição tal como extraída da NFe (ex.: "3x em 30/60/90 dias"). |
| condicao_pagamento_sap | VARCHAR(60) | Código da condição no SAP (ex.: Z001). Pode ficar vazio para o usuário preencher depois. |
| tipo_pagamento | VARCHAR(2) | Código tPag (ex.: 01, 03). Opcional. |

**Unicidade:** `(gdfcliente_id, condicao_pagamento_nfe, tipo_pagamento)`.

Uso: **depara** “condição NFe + tipo” → “condição SAP” por cliente. Ao gerar as condições do lote, o sistema consulta essa tabela para preencher `condicao_pagamento_sap` em cada linha.

### 3.2 CondicaoPagamentoLote (condição por lote)

**Tabela:** `reprocessamento.condicao_pagamento_lote`  
**Modelo:** `app.db_GDF.reprocessamento.models.CondicaoPagamentoLote`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id_reg | PK | Identificador. |
| lote_id | FK → ReprocessamentoLote | Lote de reprocessamento (empresa + competência). |
| cod_empresa | VARCHAR(10) | Código da empresa da NFe (para envio SAP por empresa, se necessário). |
| chave_nfe | VARCHAR(44) | Chave de acesso da NF-e (44 dígitos). |
| numero_nfe | VARCHAR(20) | Número da NFe. |
| serie_nfe | VARCHAR(5) | Série da NFe. |
| condicao_pagamento_nfe | VARCHAR(120) | Condição extraída da NFe. |
| condicao_pagamento_sap | VARCHAR(60) | Condição SAP (preenchida pelo depara ou manualmente). |
| tipo_pagamento | VARCHAR(2) | Código tPag. |
| status | CHAR(1) | Status do envio/processamento no SAP (ver abaixo). |
| data_criacao | TIMESTAMP | Criação do registro. |
| data_atualizacao | TIMESTAMP | Última atualização. |

**Unicidade:** `(lote_id, chave_nfe)` — uma linha por chave por lote.

**Status (CondicaoPagamentoLote.STATUS_CHOICES):**

| Código | Significado |
|--------|-------------|
| P | Pendente |
| E | Enviado ao SAP |
| S | Processado no SAP |
| U | Atualizado no SAP (U) |
| I | Processado no SAP (I) |
| R | Erro processamento (R) |

O SAP devolve o status por chave na RFC; o GDF persiste esse valor em `status`.

---

## 4. Fluxo de processamento

### 4.1 Carga XML (NFe)

- Ao processar cada NFe, a classe `CargaXml` chama `_salvar_condicao_param_se_nao_existir(identificacao, cod_cliente)`.
- Requer `cod_cliente` (a condição é por cliente).
- Calcula `condicao_pagamento_da_nfe(identificacao)` e `tipo_pagamento_da_nfe(identificacao)`.
- Se houver parcela com valor negativo, **não** grava em CondicaoParam e registra aviso.
- Faz `CondicaoParam.objects.get_or_create(..., defaults={'condicao_pagamento_sap': ''})`. Ou seja, **cria** apenas se ainda não existir a combinação (cliente, condição NFe, tipo); o campo SAP pode ficar vazio para preenchimento posterior.

### 4.2 Geração das condições do lote

- **Função:** `gerar_condicoes_pagamento_lote(id_lote)` em `app/classes/Reprocessamento.py`.
- Lista todas as NF-e do mês da empresa/competência do lote (`_nfe_do_mes`).
- Para cada NFe: obtém condição NFe e tipo; busca condição SAP em CondicaoParam (`_condicao_sap_da_param`) usando o cliente do lote (empresa → gdfcliente_id).
- Cria ou atualiza registro em **CondicaoPagamentoLote** (um por chave), com `status='P'`.
- Retorno: `(criados, atualizados)`.

### 4.3 Depara NFe → SAP (CondicaoParam)

- **Função:** `_condicao_sap_da_param(condicao_nfe, tipo_pagamento=None, cod_cliente=None)` em `Reprocessamento.py`.
- Filtra por `condicao_pagamento_nfe` e opcionalmente por `tipo_pagamento` e `cod_cliente`.
- Prioridade: primeiro tenta com o tipo informado; se não houver registro com condição SAP preenchida, tenta com tipo vazio/null.
- Retorna o primeiro `condicao_pagamento_sap` não vazio encontrado; senão, string vazia.

### 4.4 Envio ao SAP (RFC)

- **Função:** `enviar_condicoes_pagamento_sap(id_lote, cod_cliente, condicoes_lista)` em `app/classes/SapRfc.py`.
- **RFC:** `ZGDF_CONDICOES_PAGAMENTO`.
- **Entrada:** tabela `T_COND_PAGAMENTO` com colunas:
  - `CHAVE` (44) — chave da NFe;
  - `COND_PAG_NFE` (50) — condição NFe;
  - `COND_PAG_SAP` (4) — condição SAP.
- **Saída:** tabela `R_T_COND` (ou `T_COND_PAGAMENTO`) com `CHAVE`, `COND_PAG_SAP`, `STATUS` (P/E/S/U/I/R).
- O GDF atualiza em **CondicaoPagamentoLote** o `status` (e opcionalmente a condição retornada) por chave.

Se PyRFC não estiver disponível ou `cod_cliente` não informado, a função retorna erro sem chamar o SAP; em caso de falha na RFC, retorna `sucesso: False` e mensagem de erro.

---

## 5. APIs (HTTP)

Todas as APIs abaixo exigem usuário autenticado e sessão com `cod_cliente` (exceto onde indicado). O lote deve pertencer a uma empresa do cliente da sessão.

### 5.1 Gerar condições do lote

- **URL:** `POST /api/reprocessamento/lotes/<id_lote>/condicoes-pagamento/gerar/`
- **Nome:** `API_ReprocessamentoCondicoesGerar`
- **Descrição:** Gera/atualiza registros em CondicaoPagamentoLote para todas as NF-e do lote.
- **Resposta (200):**  
  `{ "sucesso": true, "criados": N, "atualizados": M, "mensagem": "..." }`

### 5.2 Listar condições do lote

- **URL:** `GET /api/reprocessamento/lotes/<id_lote>/condicoes-pagamento/`
- **Nome:** `API_ReprocessamentoCondicoesListar`
- **Resposta (200):**  
  `{ "sucesso": true, "condicoes": [ { "id_reg", "cod_empresa", "chave_nfe", "numero_nfe", "serie_nfe", "condicao_pagamento_nfe", "condicao_pagamento_sap", "tipo_pagamento", "status", "data_criacao", "data_atualizacao" }, ... ], "total": N }`

### 5.3 Atualizar retorno (condições do lote)

- **URL:** `POST /api/reprocessamento/lotes/<id_lote>/condicoes-pagamento/atualizar-retorno/`
- **Nome:** `API_ReprocessamentoCondicoesAtualizarRetorno`
- **Body (JSON):**  
  `{ "itens": [ { "chave_nfe": "44...", "condicao_sap_retorno": "Z001", "status": "S" }, ... ] }`  
  (também aceita chave `retornos` em vez de `itens`; para status pode usar `condicao_sap` como alternativa a `condicao_sap_retorno`.)
- **Resposta (200):**  
  `{ "sucesso": true, "atualizados": N, "mensagem": "..." }`

### 5.4 Enviar condições ao SAP

- **URL:** `POST /api/reprocessamento/lotes/<id_lote>/condicoes-pagamento/enviar-sap/`
- **Nome:** `API_ReprocessamentoCondicoesEnviarSap`
- **Descrição:** Monta a lista de condições do lote, chama a RFC e atualiza status (e condição, se aplicável) por chave.
- **Resposta (200):**  
  `{ "sucesso": true, "mensagem": "...", "enviados": N, "atualizados": M }`  
- **Erro (400):** “Gere a tabela de condições antes de enviar ao SAP.” se não houver registros no lote.

### 5.5 Listar CondicaoParam (depara do cliente)

- **URL:** `GET /api/reprocessamento/condicao-param/`
- **Nome:** `API_ReprocessamentoCondicaoParamListar`
- **Resposta (200):**  
  `{ "sucesso": true, "condicoes": [ { "id", "condicao_pagamento_nfe", "condicao_pagamento_sap", "tipo_pagamento" }, ... ] }`

### 5.6 Atualizar CondicaoParam (condição SAP)

- **URL:** `POST /api/reprocessamento/condicao-param/atualizar/`
- **Nome:** `API_ReprocessamentoCondicaoParamAtualizar`
- **Body (JSON):**  
  `{ "itens": [ { "id": 1, "condicao_pagamento_sap": "Z001" }, ... ] }`
- **Resposta (200):**  
  `{ "sucesso": true, "atualizados": N, "mensagem": "..." }`

---

## 6. Interface (Painel de reprocessamento)

No painel de reprocessamento (`Reprocessamento/index_Painel.html` e `Script_ReprocessamentoPainel.js`):

- Há seção específica para **condições de pagamento do lote**: listagem por chave com colunas condição NFe, condição SAP (editável), status com cores (P/E/S/U/I/R).
- O usuário pode **gerar** a tabela de condições, **editar** a coluna “Condição SAP” manualmente e **enviar ao SAP**.
- A documentação na tela orienta: cadastre o mapeamento em Condição parâmetro (condição NFe → condição SAP e tipo); ao gerar o lote, o sistema fará o depara. Se não houver correspondência, o campo SAP ficará vazio e pode ser preenchido manualmente.

Detalhes de uso: [MANUAL_USUARIO.md](MANUAL_USUARIO.md) (seção 7.3).

---

## 7. Resumo de arquivos e funções

| O quê | Onde |
|-------|------|
| Modelos CondicaoPagamentoLote, CondicaoParam | `GDF_PJT/app/db_GDF/reprocessamento/models.py` |
| condicao_pagamento_da_nfe, tipo_pagamento_da_nfe, _condicao_sap_da_param, gerar_condicoes_pagamento_lote | `GDF_PJT/app/classes/Reprocessamento.py` |
| _salvar_condicao_param_se_nao_existir (carga NFe) | `GDF_PJT/app/classes/CargaXml.py` |
| enviar_condicoes_pagamento_sap (RFC) | `GDF_PJT/app/classes/SapRfc.py` |
| APIs (gerar, listar, atualizar retorno, enviar SAP, condicao-param listar/atualizar) | `GDF_PJT/app/views.py` |
| URLs das APIs | `GDF_PJT/GDF_PJT/urls.py` |
| Tipos de pagamento (tPag) | `GDF_PJT/json/Tipo_pagamento.json` |
| Painel (HTML/JS) | `GDF_PJT/app/templates/Reprocessamento/index_Painel.html`, `GDF_PJT/app/static/js/Script_ReprocessamentoPainel.js` |

---

## 8. Referências

- [GLOSSARIO.md](GLOSSARIO.md) — termos “Condição de pagamento (lote)” e “Condição parâmetro”.
- [MANUAL_USUARIO.md](MANUAL_USUARIO.md) — uso do reprocessamento e condições (seção 7).
- [ARQUITETURA.md](ARQUITETURA.md) — schemas, tabelas e fluxos.
- [DOCUMENTACAO_PROJETO_GDF.md](DOCUMENTACAO_PROJETO_GDF.md) — visão geral do projeto e integração SAP.

---

*Última atualização: Março 2026*
