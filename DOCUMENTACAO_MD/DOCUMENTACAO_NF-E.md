# Documentação da Estrutura NF-e (Nota Fiscal Eletrônica)

## Visão Geral

A estrutura NF-e (Nota Fiscal Eletrônica) foi implementada com 16 tabelas relacionadas no PostgreSQL, organizadas no schema `nfe`. O sistema segue o padrão da legislação brasileira para emissão de notas fiscais eletrônicas, com suporte completo para:

- Informações de emitentes e destinatários
- Produtos/serviços com cálculo de impostos
- Múltiplos impostos (ICMS, IPI, PIS, COFINS)
- Informações de transporte e cobrança
- Diversos meios de pagamento (PIX, Cartão, Dinheiro, etc.)
- Histórico de autorização e autoridades

---

## 📊 Diagrama de Relacionamentos

```
┌─────────────────────────────────────────────────────────────┐
│                      NFe (Principal)                        │
├─────────────────────────────────────────────────────────────┤
│ id_nfe (PK), status, protocolo_autorizacao, xml_assinado   │
└──────────────────────────┬──────────────────────────────────┘
        ├── OneToOne ──► NFe_Identificacao
        ├── ForeignKey ──► NFe_Emitente
        ├── ForeignKey ──► NFe_Destinatario
        └── ForeignKey ──► Empresa (public schema) ⭐

┌──────────────────────────────────────────────┐
│      NFe_Identificacao (Chave Documento)     │
├──────────────────────────────────────────────┤
│ id_identificacao (PK), numero, serie,        │
│ chave_acesso, emissao, tipo_operacao        │
└──────────┬──────────────────────────────────┘
        ├── OneToOne ──► NFe_Total
        ├── OneToOne ──► NFe_Transporte
        ├── OneToOne ──► NFe_Cobranca
        ├── OneToOne ──► NFe_Pagamento
        ├── OneToOne ──► NFe_Informacoes_Adicionais
        └── ForeignKey ──► NFe_Produto (1:N)

┌──────────────────────────┐
│    NFe_Produto (1:N)     │
├──────────────────────────┤
│ id_produto (PK)          │
│ descricao, ncm, quantidade│
└──────┬───────────────────┘
        ├── OneToOne ──► NFe_ICMS
        ├── OneToOne ──► NFe_IPI
        ├── OneToOne ──► NFe_PIS
        └── OneToOne ──► NFe_COFINS

┌─────────────────────────────────────┐
│  NFe_Emitente / NFe_Destinatario    │
├─────────────────────────────────────┤
│ Ambos relacionam com NFe_Endereco   │
│ (OneToOne, opcional)                │
└─────────────────────────────────────┘

┌──────────────────────────────────────┐
│       NFe_Cobranca (Pagamento)       │
├──────────────────────────────────────┤
│ id_cobranca (PK), banco, agencia    │
└──────────────┬───────────────────────┘
              └── ForeignKey ──► NFe_Parcela (1:N)
```

---

## 📋 Tabelas Detalhadas

### 1. **NFe_Endereco** (Tabela Base)
Armazena endereços reutilizáveis para emitentes, destinatários e terceiros.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id_endereco` | AutoField (PK) | Identificador único |
| `logradouro` | CharField(60) | Rua/Avenida |
| `numero` | CharField(60) | Número do imóvel |
| `complemento` | CharField(60) | Apartamento, sala, etc |
| `bairro` | CharField(60) | Bairro |
| `codigo_municipio` | CharField(7) | Código IBGE do município |
| `uf` | CharField(2) | UF (sigla) |
| `cep` | CharField(8) | CEP (sem hífen) |
| `pais` | CharField(4) | Código IBGE país (padrão: 1058 = Brasil) |
| `telefone` | CharField(14) | Contato |
| `email` | EmailField(60) | E-mail |
| `data_criacao` | DateTimeField | Data de criação (automático) |

**Índices:**
- `(codigo_municipio, uf)` - Busca por localização

---

### 2. **NFe_Emitente** (Dados do Emitente)
Dados da empresa que emite a NF-e.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id_emitente` | AutoField (PK) | Identificador único |
| `cnpj` | CharField(14) | CNPJ único |
| `razao_social` | CharField(120) | Razão social |
| `nome_fantasia` | CharField(60) | Nome fantasia (opcional) |
| `ie` | CharField(14) | Inscrição Estadual |
| `ie_st` | CharField(14) | IE Substituto Tributário |
| `im` | CharField(60) | Inscrição Municipal |
| `cnae_fiscal` | CharField(7) | CNAE Fiscal (atividade econômica) |
| `crt` | CharField(1) | Código de regime tributário |
| `endereco` | OneToOneField → NFe_Endereco | Endereço (opcional) |
| `data_criacao` | DateTimeField | Data de criação (automático) |

**CRT (Código Regime Tributário):**
- `'1'` - Simples Nacional
- `'2'` - Simples Nacional com Excesso
- `'3'` - Regime Normal

**Índices:**
- `(cnpj, razao_social)` - Busca por emitente

---

### 3. **NFe_Destinatario** (Dados do Destinatário)
Dados da empresa/pessoa que recebe a NF-e.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id_destinatario` | AutoField (PK) | Identificador único |
| `tipo` | CharField(1) | Tipo de documento (CNPJ ou CPF) |
| `documento` | CharField(14) | CNPJ ou CPF |
| `razao_social` | CharField(120) | Razão social (opcional para CPF) |
| `nome_fantasia` | CharField(60) | Nome fantasia |
| `ie` | CharField(14) | Inscrição Estadual (opcional para CPF) |
| `im` | CharField(60) | Inscrição Municipal |
| `email` | EmailField(60) | E-mail |
| `endereco` | OneToOneField → NFe_Endereco | Endereço (opcional) |
| `indicador_ie` | CharField(1) | Indicador de contribuinte ICMS |
| `data_criacao` | DateTimeField | Data de criação (automático) |

**Tipo:**
- `'1'` - CNPJ
- `'2'` - CPF

**Indicador IE:**
- `'1'` - Contribuinte ICMS
- `'2'` - Não contribuinte
- `'9'` - Exterior

**Índices:**
- `(documento, tipo)` - Busca por identificação

---

### 4. **NFe_Identificacao** (Chave do Documento)
Identificação geral e características da NF-e.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id_identificacao` | AutoField (PK) | Identificador único |
| `numero` | CharField(9) | Número sequencial |
| `serie` | CharField(3) | Série de emissão |
| `emissao` | DateTimeField | Data/hora de emissão |
| `saida_entrada` | DateTimeField | Data de saída/entrada (opcional) |
| `tipo_documento` | CharField(1) | 0=Entrada, 1=Saída |
| `tipo_operacao` | CharField(1) | 0=Entrada, 1=Saída |
| `municipio` | CharField(7) | Código IBGE do município |
| `tipo_impressao` | CharField(1) | Formato DANFE (1=Normal, 2=Simplificado, etc) |
| `tipo_emissao` | CharField(1) | Tipo de emissão (1=Normal, 2=Contingência, etc) |
| `ambiente` | CharField(1) | 1=Produção, 2=Homologação |
| `finalidade` | CharField(1) | 1=Normal, 2=Complementar, 3=Ajuste, 4=Devolução |
| `consumidor_final` | BooleanField | Indica se é consumidor final |
| `presencial` | CharField(1) | Indicador de presencialidade |
| `chave_acesso` | CharField(44) | Chave de acesso única **[ÚNICO]** |
| `dv_chave` | CharField(1) | Dígito verificador |
| `digito_rastreamento` | CharField(1) | Para contingência |
| `referencia_nfe` | CharField(44) | Para NF-e de referência |

**Índices:**
- `(chave_acesso, numero, serie)` - Busca por chave ou documento
- `(emissao)` - Busca temporal

---

### 5. **NFe_Produto** (Itens/Produtos)
Produtos e serviços da NF-e. **Relacionamento 1:N** com NFe_Identificacao.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id_produto` | AutoField (PK) | Identificador único |
| `descricao` | CharField(120) | Descrição do produto/serviço |
| `ncm` | CharField(8) | NCM (Nomenclatura Comum do Mercosul) |
| `nfe_serie` | ForeignKey → NFe_Identificacao | Documento ao qual pertence |
| `numero_item` | IntegerField | Número sequencial do item (1, 2, 3...) |
| `codigo_interno` | CharField(60) | Código interno da empresa |
| `ean` | CharField(14) | Código EAN do produto |
| `ean_tributavel` | CharField(14) | EAN para tributação |
| `quantidade` | DecimalField | Quantidade vendida |
| `quantidade_tributavel` | DecimalField | Quantidade para cálculo de impostos |
| `valor_unitario` | DecimalField | Preço unitário |
| `valor_unitario_tributavel` | DecimalField | Valor para tributação |
| `valor_total` | DecimalField | Subtotal do item |
| `valor_desconto` | DecimalField | Desconto no item |
| `valor_outras_despesas` | DecimalField | Outras despesas |
| `unidade` | CharField(6) | Unidade (UN, KG, L, etc) |
| `indicador_total` | BooleanField | Inclui no total da NF |
| `origem` | CharField(1) | 0=Nacional, 1=Importado direto, 2=Importado (mercado interno) |
| `data_criacao` | DateTimeField | Data de criação (automático) |

**Índices:**
- `(nfe_serie, numero_item)` - Busca por documento e item
- `(ncm)` - Busca por classificação fiscal

---

### 6. **NFe_ICMS** (Imposto sobre Circulação de Mercadorias)
Cálculo do ICMS por produto. **Relacionamento 1:1** com NFe_Produto.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id_icms` | AutoField (PK) | Identificador único |
| `produto` | OneToOneField → NFe_Produto | Produto associado |
| `origem` | CharField(1) | Origem do produto |
| `cst` | CharField(2) | Código de Situação Tributária |
| `aliquota` | DecimalField | Alíquota ICMS (%) |
| `aliquota_st` | DecimalField | Alíquota ST |
| `valor_base_calculo` | DecimalField | Base de cálculo |
| `valor_icms` | DecimalField | Valor do ICMS |
| `percentual_reducao` | DecimalField | Percentual de redução BC |
| `valor_base_st` | DecimalField | Base ICMS ST |
| `valor_icms_st` | DecimalField | Valor ICMS ST |
| `uf` | CharField(2) | UF (para ST interestadual) |

**CST (Código Situação Tributária):**
- `'00'` - Tributada integralmente
- `'10'` - Tributada e com cobrança ICMS por ST
- `'20'` - Com redução de BC
- `'30'` - Isenta ou não tributada com ST
- `'40'` - Isenta
- `'41'` - Não tributada
- `'50'` - Suspensão
- `'51'` - Diferimento
- `'60'` - ICMS cobrado anteriormente por ST
- `'70'` - Redução de BC e ST
- `'90'` - Outras operações

---

### 7. **NFe_IPI** (Imposto sobre Produtos Industrializados)
Cálculo do IPI por produto. **Relacionamento 1:1** com NFe_Produto.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id_ipi` | AutoField (PK) | Identificador único |
| `produto` | OneToOneField → NFe_Produto | Produto associado |
| `cst` | CharField(2) | Código de Situação Tributária |
| `enquadramento_legal` | CharField(3) | Código de enquadramento legal |
| `aliquota` | DecimalField | Alíquota IPI (%) |
| `valor_base_calculo` | DecimalField | Base de cálculo |
| `valor_ipi` | DecimalField | Valor do IPI |
| `selagem` | CharField(1) | 'S' = Sim, 'N' = Não |

---

### 8. **NFe_PIS** (Programa de Integração Social)
Cálculo do PIS por produto. **Relacionamento 1:1** com NFe_Produto.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id_pis` | AutoField (PK) | Identificador único |
| `produto` | OneToOneField → NFe_Produto | Produto associado |
| `cst` | CharField(2) | Código de Situação Tributária (01-99) |
| `aliquota` | DecimalField | Alíquota PIS (%) |
| `valor_base_calculo` | DecimalField | Base de cálculo |
| `valor_pis` | DecimalField | Valor do PIS |
| `quantidade_vendida` | DecimalField | Qtd. para cálculo por quantidade |
| `aliquota_quantidade` | DecimalField | Valor por unidade |

---

### 9. **NFe_COFINS** (Contribuição para Financiamento da Seguridade Social)
Cálculo do COFINS por produto. **Relacionamento 1:1** com NFe_Produto.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id_cofins` | AutoField (PK) | Identificador único |
| `produto` | OneToOneField → NFe_Produto | Produto associado |
| `cst` | CharField(2) | Código de Situação Tributária (01-99) |
| `aliquota` | DecimalField | Alíquota COFINS (%) |
| `valor_base_calculo` | DecimalField | Base de cálculo |
| `valor_cofins` | DecimalField | Valor do COFINS |
| `quantidade_vendida` | DecimalField | Qtd. para cálculo por quantidade |
| `aliquota_quantidade` | DecimalField | Valor por unidade |

---

### 10. **NFe_Total** (Totalizações)
Somatórios e totais da NF-e. **Relacionamento 1:1** com NFe_Identificacao.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id_total` | AutoField (PK) | Identificador único |
| `nfe_identificacao` | OneToOneField → NFe_Identificacao | Documento associado |
| `valor_subtotal_produtos` | DecimalField | Soma produtos |
| `valor_frete` | DecimalField | Valor frete |
| `valor_seguro` | DecimalField | Valor seguro |
| `valor_desconto` | DecimalField | Desconto geral |
| `valor_outras_despesas` | DecimalField | Outras despesas |
| `valor_total_tributos` | DecimalField | Total de tributos |
| `valor_base_icms` | DecimalField | Base cálculo ICMS |
| `valor_icms` | DecimalField | Valor ICMS |
| `valor_icms_st` | DecimalField | Valor ICMS ST |
| `valor_ipi` | DecimalField | Valor IPI |
| `valor_pis` | DecimalField | Valor PIS |
| `valor_cofins` | DecimalField | Valor COFINS |
| `valor_total_nfe` | DecimalField | **TOTAL FINAL** |
| `valor_servicos` | DecimalField | Valor serviços |
| `valor_base_pis` | DecimalField | Base PIS |
| `valor_base_cofins` | DecimalField | Base COFINS |
| `data_criacao` | DateTimeField | Data de criação (automático) |

---

### 11. **NFe_Transporte** (Informações de Transporte)
Dados de transporte e frete. **Relacionamento 1:1** com NFe_Identificacao.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id_transporte` | AutoField (PK) | Identificador único |
| `nfe_identificacao` | OneToOneField → NFe_Identificacao | Documento associado |
| `modalidade` | CharField(1) | Tipo de frete (0-4, 9) |
| `valor_frete` | DecimalField | Valor total do frete |
| **Dados do Transportador:** | | |
| `transportador_tipo` | CharField(1) | 1=CNPJ, 2=CPF |
| `transportador_documento` | CharField(14) | CNPJ ou CPF |
| `transportador_razao` | CharField(120) | Razão social |
| `transportador_inscricao` | CharField(14) | IE |
| `transportador_endereco` | CharField(60) | Endereço |
| `transportador_uf` | CharField(2) | UF |
| `transportador_telefone` | CharField(14) | Contato |
| **Dados do Veículo:** | | |
| `veiculo_placa` | CharField(8) | Placa do veículo |
| `veiculo_uf` | CharField(2) | UF da placa |
| `veiculo_rntc` | CharField(20) | RNTC (registro transportista) |
| `veiculo_tara` | IntegerField | Peso tara |
| `veiculo_capac_max` | IntegerField | Capacidade máxima |
| **Dados do Reboque:** | | |
| `reboque_placa` | CharField(8) | Placa reboque |
| `reboque_uf` | CharField(2) | UF reboque |
| `reboque_rntc` | CharField(20) | RNTC reboque |
| `reboque_tara` | IntegerField | Peso tara reboque |
| `reboque_capac_max` | IntegerField | Capacidade máx. reboque |
| **Lacres:** | | |
| `lacre_numero` | CharField(60) | Número do lacre |
| `lacre_uf` | CharField(2) | UF que aplicou lacre |
| `data_criacao` | DateTimeField | Data de criação (automático) |

**Modalidade de Frete:**
- `'0'` - Contratação por conta do Remetente
- `'1'` - Contratação por conta do Destinatário
- `'2'` - Contratação por conta de Terceiros
- `'3'` - Transporte Próprio (Remetente)
- `'4'` - Transporte Próprio (Destinatário)
- `'9'` - Sem ocorrência

---

### 12. **NFe_Cobranca** (Dados Bancários/Cobrança)
Informações bancárias para cobrança. **Relacionamento 1:1** com NFe_Identificacao.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id_cobranca` | AutoField (PK) | Identificador único |
| `nfe_identificacao` | OneToOneField → NFe_Identificacao | Documento associado |
| `banco` | CharField(5) | Código banco |
| `agencia` | CharField(6) | Agência |
| `agencia_dv` | CharField(1) | DV agência |
| `conta` | CharField(12) | Número da conta |
| `conta_dv` | CharField(1) | DV conta |
| `cnpj_banco` | CharField(14) | CNPJ do banco |
| `data_criacao` | DateTimeField | Data de criação (automático) |

---

### 13. **NFe_Parcela** (Parcelas de Pagamento)
Informações de parcelamento. **Relacionamento N:1** com NFe_Cobranca.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id_parcela` | AutoField (PK) | Identificador único |
| `nfe_cobranca` | ForeignKey → NFe_Cobranca | Cobrança associada |
| `numero_parcela` | IntegerField | Número da parcela (1, 2, 3...) |
| `data_vencimento` | DateField | Data de vencimento |
| `valor_parcela` | DecimalField | Valor da parcela |
| `dias_desconto` | IntegerField | Dias para desconto |
| `percentual_desconto` | DecimalField | Desconto (%) |
| `valor_desconto` | DecimalField | Valor desconto |
| `data_desconto` | DateField | Data limite desconto |

**Índices:**
- `(nfe_cobranca, numero_parcela)` - Busca por parcela

---

### 14. **NFe_Pagamento** (Informações de Pagamento)
Dados de pagamento da NF-e. **Relacionamento 1:1** com NFe_Identificacao.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id_pagamento` | AutoField (PK) | Identificador único |
| `nfe_identificacao` | OneToOneField → NFe_Identificacao | Documento associado |
| `meio_pagamento` | CharField(2) | Tipo de pagamento (01-99) |
| `valor_pago` | DecimalField | Valor do pagamento |
| **Dados de Cartão:** | | |
| `cartao_bandeira` | CharField(2) | Bandeira (01-09, 99) |
| `cartao_cnpj` | CharField(14) | CNPJ da adquirente |
| `cartao_numero_autoriza` | CharField(20) | Número de autorização |
| **Dados de PIX:** | | |
| `pix_tipo_chave` | CharField(1) | Tipo chave PIX (1-5) |
| `pix_chave` | CharField(140) | Chave PIX |
| `data_criacao` | DateTimeField | Data de criação (automático) |

**Meio de Pagamento:**
- `'01'` - Dinheiro
- `'02'` - Cheque
- `'03'` - Cartão de Crédito
- `'04'` - Cartão de Débito
- `'05'` - Crédito Loja
- `'18'` - Boleto Bancário
- `'19'` - Depósito Bancário
- `'20'` - PIX
- `'99'` - Outros

**Bandeira Cartão:**
- `'01'` - Visa
- `'02'` - Mastercard
- `'03'` - American Express
- `'06'` - Elo
- `'07'` - Hipercard
- `'09'` - Discover

**Tipo Chave PIX:**
- `'1'` - CPF
- `'2'` - CNPJ
- `'3'` - Telefone
- `'4'` - Email
- `'5'` - Aleatória

---

### 15. **NFe_Informacoes_Adicionais** (Informações Complementares)
Dados adicionais e respostas da autorização. **Relacionamento 1:1** com NFe_Identificacao.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id_info_adic` | AutoField (PK) | Identificador único |
| `nfe_identificacao` | OneToOneField → NFe_Identificacao | Documento associado |
| `informacoes_complementares` | TextField | Observações gerais |
| `informacoes_interesse_fisco` | TextField | Informações para fisco |
| `resposta_json` | TextField | Resposta JSON da SEFAZ |
| `data_criacao` | DateTimeField | Data de criação (automático) |

---

### 16. **NFe** (Tabela Principal - Documento)
Aggregação de toda a NF-e. **Centro do relacionamento**.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id_nfe` | AutoField (PK) | Identificador único |
| `identificacao` | OneToOneField → NFe_Identificacao | Chave do documento |
| `empresa` | ForeignKey → Empresa (public) | Empresa emissora (vínculo multi-schema) ⭐ |
| `emitente` | ForeignKey → NFe_Emitente | Quem emitiu |
| `destinatario` | ForeignKey → NFe_Destinatario | Para quem |
| `status` | CharField(20) | Estado da NF-e |
| `protocolo_autorizacao` | CharField(15) | Protocolo da SEFAZ |
| `data_autorizacao` | DateTimeField | Data aprovação |
| `xml_assinado` | TextField | XML assinado digitalmente |
| `xml_resposta` | TextField | Resposta da SEFAZ |
| `data_criacao` | DateTimeField | Data criação |
| `data_atualizacao` | DateTimeField | Data última atualização |
| `usuario_criacao` | CharField(120) | Usuário que criou |

**Status:**
- `'DRAFT'` - Rascunho
- `'ASSINADA'` - Assinada
- `'ENVIADA'` - Enviada para autorização
- `'AUTORIZADA'` - Autorizada pela SEFAZ
- `'CANCELADA'` - Cancelada
- `'DENEGADA'` - Denegada
- `'REJEITADA'` - Rejeitada
- `'CONTINGENCIA'` - Em regime de contingência

**Índices:**
- `(status, data_criacao)` - Busca por status
- `(identificacao)` - Busca por identificação
- `(emitente, destinatario)` - Busca por parceiros
- `(empresa)` - Busca por empresa emissora ⭐

---

## 🔗 Fluxo de Relacionamentos

```
Criar NF-e
    ↓
1. Criar NFe_Endereco (Emitente e Destinatário)
    ↓
2. Criar NFe_Emitente (com referência Endereco)
    ↓
3. Criar NFe_Destinatario (com referência Endereco)
    ↓
4. Criar NFe_Identificacao (Chave do documento)
    ↓
5. Criar NFe_Produto (1 ou mais itens)
    ├─ Criar NFe_ICMS (por produto)
    ├─ Criar NFe_IPI (por produto)
    ├─ Criar NFe_PIS (por produto)
    └─ Criar NFe_COFINS (por produto)
    ↓
6. Criar NFe_Total (Somatórios)
    ↓
7. Criar NFe_Transporte (Dados frete)
    ↓
8. Criar NFe_Cobranca (Dados bancários)
    └─ Criar NFe_Parcela (1 ou mais parcelas)
    ↓
9. Criar NFe_Pagamento (Meio de pagamento)
    ↓
10. Criar NFe_Informacoes_Adicionais (Dados complementares)
    ↓
11. Criar NFe (Documento principal, agregando tudo)
    ↓
Assinatura Digital
    ↓
Envio para SEFAZ
    ↓
Atualizar status e protocolo na NFe
```

---

## 📊 Queries Úteis

### Listar todas as NF-e por emitente
```sql
SELECT nfe.id_nfe, nfe_ident.numero, nfe_ident.serie, nfe.status, nfe.data_criacao
FROM nfe.nfe
JOIN nfe.nfe_identificacao nfe_ident ON nfe.identificacao_id = nfe_ident.id_identificacao
WHERE nfe.emitente_id = ?
ORDER BY nfe.data_criacao DESC;
```

### Total de impostos por NF-e
```sql
SELECT 
    nfe.id_nfe,
    nfe_total.valor_icms,
    nfe_total.valor_ipi,
    nfe_total.valor_pis,
    nfe_total.valor_cofins,
    nfe_total.valor_total_tributos
FROM nfe.nfe
JOIN nfe.nfe_total ON nfe.identificacao_id = nfe_total.nfe_identificacao_id;
```

### Produtos com NCM específico
```sql
SELECT np.descricao, np.quantidade, np.valor_total, nfi.numero, nfi.serie
FROM nfe.nfe_produto np
JOIN nfe.nfe_identificacao nfi ON np.nfe_serie_id = nfi.id_identificacao
WHERE np.ncm = '12345678'
ORDER BY np.data_criacao DESC;
```

### NF-e em status específico
```sql
SELECT nfe.id_nfe, nfi.chave_acesso, nfe.status, nfe.protocolo_autorizacao
FROM nfe.nfe
JOIN nfe.nfe_identificacao nfi ON nfe.identificacao_id = nfi.id_identificacao
WHERE nfe.status = 'AUTORIZADA'
AND nfe.data_autorizacao >= NOW() - INTERVAL '30 days';
```

---

## 🔐 Integridade Referencial

| Relacionamento | Tipo | Ação Delete |
|---|---|---|
| NFe.identificacao → NFe_Identificacao | OneToOne | CASCADE |
| NFe.empresa → Empresa (public) | ForeignKey | PROTECT |
| NFe.emitente → NFe_Emitente | ForeignKey | PROTECT |
| NFe.destinatario → NFe_Destinatario | ForeignKey | SET_NULL |
| NFe_Produto.nfe_serie → NFe_Identificacao | ForeignKey | CASCADE |
| NFe_ICMS.produto → NFe_Produto | OneToOne | CASCADE |
| NFe_IPI.produto → NFe_Produto | OneToOne | CASCADE |
| NFe_PIS.produto → NFe_Produto | OneToOne | CASCADE |
| NFe_COFINS.produto → NFe_Produto | OneToOne | CASCADE |
| NFe_Total.nfe_identificacao → NFe_Identificacao | OneToOne | CASCADE |
| NFe_Transporte.nfe_identificacao → NFe_Identificacao | OneToOne | CASCADE |
| NFe_Cobranca.nfe_identificacao → NFe_Identificacao | OneToOne | CASCADE |
| NFe_Parcela.nfe_cobranca → NFe_Cobranca | ForeignKey | CASCADE |
| NFe_Pagamento.nfe_identificacao → NFe_Identificacao | OneToOne | CASCADE |
| NFe_Informacoes_Adicionais.nfe_identificacao → NFe_Identificacao | OneToOne | CASCADE |

---

## 📝 Schema PostgreSQL

**Database:** `GDF_DEV`  
**Schema:** `nfe`  
**Encoding:** UTF-8  
**Tabelas:** 16  
**Índices:** 13+

---

## 🔗 Relacionamento Multi-Schema

### Vínculo NFe ↔ Empresa (public)

A tabela `NFe` (schema `nfe`) está vinculada à tabela `Empresa` (schema `public`, tabela `empresa`) através de uma Foreign Key:

```sql
ALTER TABLE nfe.nfe
ADD COLUMN empresa_id character varying(10)
ADD CONSTRAINT nfe_empresa_fk 
FOREIGN KEY (empresa_id) REFERENCES public.empresa(cod_empresa);

CREATE INDEX nfe_empresa_idx ON nfe.nfe(empresa_id);
```

**Propósito:**
- Identificar qual empresa do sistema emitiu cada NF-e
- Permitir filtrar NF-e por empresa
- Manter integridade referencial entre schemas
- Facilitar relatórios consolidados por empresa

**Restrição:** `on_delete=PROTECT` - não permite deletar uma empresa que tenha NF-e

**Exemplo de Consulta:**
```sql
SELECT 
    nfe.id_nfe,
    emp.cod_empresa,
    emp.razao,
    emp.cnpj,
    nfi.numero,
    nfi.serie,
    nfe.status,
    nfe.data_criacao
FROM nfe.nfe
JOIN public.empresas emp ON nfe.empresa_id = emp.cod_empresa
JOIN nfe.nfe_identificacao nfi ON nfe.identificacao_id = nfi.id_identificacao
ORDER BY nfe.data_criacao DESC;
```

---

## ✅ Validações e Constraints

- **CNPJ Emitente:** Único (não pode repetir)
- **Chave de Acesso:** Única (identificador único nacional)
- **Documento Destinatário:** Pode se repetir (mesmo cliente, múltiplas NF-e)
- **Status NFe:** Controlado por enum (validação em nível de aplicação)
- **Valores Decimais:** 15 dígitos, 2 casas decimais (compatível com padrão fiscal)

---

**Última Atualização:** Janeiro de 2026  
**Versão:** 1.0  
**Schema:** nfe
