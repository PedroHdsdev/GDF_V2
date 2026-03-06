# Preenchimento Completo de NFe - Documentação

## Visão Geral
O sistema agora processa XMLs de NFe de forma completa, preenchendo **TODAS** as tabelas relacionadas com todos os campos disponíveis no XML.

## Tabelas Preenchidas

### 1. NFe_Endereco
✅ **Emitente e Destinatário** recebem endereços completos:
- logradouro, numero, complemento
- bairro, codigo_municipio, nome_municipio
- uf, cep
- pais (default '1058'), nome_pais (default 'Brasil')
- telefone
- data_criacao

### 2. NFe_Emitente
✅ **Campos completos do emitente**:
- cnpj (chave única)
- razao_social, nome_fantasia
- ie, ie_st, im
- cnae_fiscal
- crt (Regime tributário)
- endereco (OneToOne com NFe_Endereco)
- data_criacao, data_atualizacao

### 3. NFe_Destinatario
✅ **Campos completos do destinatário**:
- documento (CNPJ ou CPF)
- tipo ('1'=CNPJ, '2'=CPF)
- razao_social, nome_fantasia
- ie, isuf, im
- email
- endereco (OneToOne com NFe_Endereco)
- indicador_ie
- data_criacao, data_atualizacao

### 4. NFe_Identificacao
✅ **Dados completos da nota**:
- numero, serie
- emissao, saida_entrada
- tipo_documento, tipo_operacao
- codigo_municipio, municipio, uf
- finalidade_emissao
- consumidor_final, presenca_comprador
- natureza_operacao
- modelo, ambiente, forma_emissao
- chave_acesso, dv_chave
- data_atualizacao

### 5. NFe
✅ **Documento principal**:
- identificacao (OneToOne)
- emitente, destinatario
- empresa (vínculo automático baseado em entrada/saída)
- status ('DRAFT' por padrão)
- xml_assinado
- usuario_criacao, usuario_atualizacao
- origem_dados ('LOCAL', 'SAP', 'SPED', 'OUTROS')
- data_criacao, data_atualizacao

### 6. NFe_Produto
✅ **Todos os itens da nota** (loop através de `<det>`):
- nfe_serie (ForeignKey para identificacao)
- numero_item
- codigo_interno, descricao
- ean, ean_tributavel
- ncm, cfop, cest
- quantidade, quantidade_tributavel
- valor_unitario, valor_unitario_tributavel
- valor_total, valor_desconto, valor_outras_despesas
- unidade
- indicador_total, origem
- data_criacao

### 7. NFe_ICMS
✅ **Impostos ICMS de cada produto**:
- produto (OneToOne)
- origem ('0'=Nacional, etc)
- cst (código de situação tributária)
- valor_base_calculo
- aliquota
- valor_icms
- aliquota_st, valor_base_st, valor_icms_st
- percentual_reducao
- uf
- data_criacao

### 8. NFe_IPI
✅ **Impostos IPI de cada produto**:
- produto (OneToOne)
- cst
- valor_base_calculo
- aliquota
- valor_ipi
- data_criacao

### 9. NFe_PIS
✅ **Impostos PIS de cada produto**:
- produto (OneToOne)
- cst
- valor_base_calculo
- aliquota
- valor_pis
- data_criacao

### 10. NFe_COFINS
✅ **Impostos COFINS de cada produto**:
- produto (OneToOne)
- cst
- valor_base_calculo
- aliquota
- valor_cofins
- data_criacao

### 11. NFe_Total
✅ **Totalizações da nota**:
- identificacao (OneToOne)
- valor_subtotal_produtos
- valor_frete, valor_seguro
- valor_desconto, valor_outras_despesas
- valor_total_ii, valor_total_ipi
- valor_pis, valor_cofins
- base_calculo_icms, valor_icms
- base_calculo_icms_st, valor_icms_st
- valor_total_nfe
- valor_aproximado_tributos
- data_criacao

## Estrutura de Código

### Métodos Auxiliares

#### `_get_text(element, path, default='')`
Extrai texto de nó XML com fallback para namespace alternativo.
- Tenta primeiro com namespace `nfe:`
- Fallback para sem namespace
- Retorna default se não encontrar

#### `_to_decimal(value, default=0)`
Converte string para Decimal de forma segura.
- Trata valores vazios
- Substitui vírgula por ponto
- Retorna default em caso de erro

#### `_to_datetime(value, format='%Y-%m-%d')`
Converte string para datetime de forma segura.
- Suporta múltiplos formatos
- Retorna None em caso de erro

#### `_processar_endereco(element, is_emitente=True)`
Processa nó de endereço do XML e cria registro NFe_Endereco.
- Detecta automaticamente tag (enderEmit ou enderDest)
- Extrai todos os campos disponíveis
- Retorna objeto NFe_Endereco criado

#### `_processar_produtos(infNFe, identificacao)`
Loop através de todos os produtos (`<det>`) da nota.
- Extrai dados de cada item
- Cria NFe_Produto
- Chama `_processar_impostos()` para cada item

#### `_processar_impostos(imposto_node, produto)`
Processa todos os impostos de um produto.
- ICMS: Detecta tipo (ICMS00, ICMS10, etc)
- IPI: Processa nó IPITrib
- PIS: Processa nó PISAliq
- COFINS: Processa nó COFINSAliq

#### `_processar_total(infNFe, identificacao)`
Extrai nó `<total><ICMSTot>` e cria NFe_Total.
- Todos os valores de totalização
- Bases de cálculo e valores de tributos
- Valor final da nota

### Método Principal: `set_nfe()`

**Fluxo de Execução:**

1. **Parse do XML**
   - ElementTree.fromstring()
   - Localiza nó infNFe

2. **Identificação**
   - Extrai dados do nó `<ide>`
   - Determina tipo de operação (0=Entrada, 1=Saída)

3. **Emitente**
   - Extrai dados do nó `<emit>`
   - Processa endereço com `_processar_endereco()`
   - update_or_create() para não duplicar

4. **Destinatário**
   - Extrai dados do nó `<dest>`
   - Detecta CNPJ ou CPF
   - Processa endereço
   - update_or_create()

5. **Buscar Empresa**
   - Se Saída (1): busca pelo CNPJ do emitente
   - Se Entrada (0): busca pelo CNPJ do destinatário
   - Levanta erro se empresa não encontrada

6. **Criar Identificação**
   - Todos os campos de ide preenchidos
   - update_or_create() usando chave_acesso

7. **Criar NFe**
   - Liga todas as entidades
   - Armazena XML completo
   - Rastreamento de usuário

8. **Processar Produtos**
   - `_processar_produtos()` → cria todos os itens
   - `_processar_impostos()` → cria ICMS, IPI, PIS, COFINS

9. **Processar Totais**
   - `_processar_total()` → cria NFe_Total

## Validações Implementadas

### ✅ Validação de Estrutura XML
- infNFe obrigatório
- Seção ide obrigatória
- CNPJ do emitente obrigatório
- Número e série obrigatórios

### ✅ Validação de Empresa
- Detecta tipo de NFe (entrada/saída)
- Busca empresa pelo CNPJ correto
- Erro claro indicando qual CNPJ está faltando

### ✅ Tratamento de Campos Opcionais
- Todos os métodos usam defaults seguros
- Campos não obrigatórios marcados como `blank=True, null=True`
- Conversões de tipo com fallback

## Migrations Aplicadas

### 0006_add_origem_dados_nfe
- Adiciona campo origem_dados à NFe

### 0007_rename_nfe_empresa_idx...
- usuario_atualizacao → NFe
- data_atualizacao → NFe_Emitente
- nome_municipio, nome_pais → NFe_Endereco
- codigo_municipio, natureza_operacao, uf, modelo, forma_emissao, finalidade_emissao, presenca_comprador → NFe_Identificacao
- data_atualizacao → NFe_Identificacao

### 0008_nfe_produto_cest_nfe_produto_cfop
- Adiciona CFOP e CEST ao NFe_Produto

### 0009_nfe_destinatario_data_atualizacao
- data_atualizacao → NFe_Destinatario
- isuf → NFe_Destinatario

## Como Usar

```python
from app.classes.CargaXml import CargaXml

# Instanciar classe
carga = CargaXml()

# Processar XMLs
result = carga.set_upload_xml(
    I_LsXml=arquivos_upload,  # Lista de arquivos Django
    i_type='NFe',  # Tipo: NFe, CTe, NFSe
    I_origem_dados='LOCAL',  # LOCAL, SAP, SPED, OUTROS
    i_usuario='usuario@email.com'
)

# Resultado
# {
#     'success': ['nota1.xml', 'nota2.xml'],
#     'errors': [
#         {'file': 'nota3.xml', 'error': 'Mensagem', 'type': 'ValueError'}
#     ]
# }
```

## Campos XML Mapeados

### Nó `<ide>`
- nNF → numero
- serie → serie
- dhEmi ou dEmi → emissao
- dhSaiEnt ou dSaiEnt → saida_entrada
- tpNF → tipo_operacao
- tpEmis → tipo_documento
- cMunFG → codigo_municipio
- xMunFG → municipio
- UF → uf
- natOp → natureza_operacao
- mod → modelo
- tpAmb → ambiente
- finNFe → finalidade_emissao
- indFinal → consumidor_final
- indPres → presenca_comprador

### Nó `<emit>`
- CNPJ → cnpj
- xNome → razao_social
- xFant → nome_fantasia
- IE → ie
- IEST → ie_st
- IM → im
- CNAE → cnae_fiscal
- CRT → crt
- enderEmit → NFe_Endereco

### Nó `<dest>`
- CNPJ/CPF → documento
- xNome → razao_social
- IE → ie
- ISUF → isuf
- IM → im
- email → email
- enderDest → NFe_Endereco

### Nó `<enderEmit>` / `<enderDest>`
- xLgr → logradouro
- nro → numero
- xCpl → complemento
- xBairro → bairro
- cMun → codigo_municipio
- xMun → nome_municipio
- UF → uf
- CEP → cep
- cPais → pais
- xPais → nome_pais
- fone → telefone

### Nó `<det>` (produtos)
- nItem → numero_item
- cProd → codigo_interno
- cEAN → ean
- xProd → descricao
- NCM → ncm
- CFOP → cfop
- uCom → unidade
- qCom → quantidade
- vUnCom → valor_unitario
- vProd → valor_total
- cEANTrib → ean_tributavel
- qTrib → quantidade_tributavel
- vUnTrib → valor_unitario_tributavel
- vDesc → valor_desconto
- vOutro → valor_outras_despesas

### Nó `<imposto>` (impostos)
#### ICMS
- orig → origem
- CST/CSOSN → cst
- vBC → valor_base_calculo
- pICMS → aliquota
- vICMS → valor_icms

#### IPI
- CST → cst
- vBC → valor_base_calculo
- pIPI → aliquota
- vIPI → valor_ipi

#### PIS
- CST → cst
- vBC → valor_base_calculo
- pPIS → aliquota
- vPIS → valor_pis

#### COFINS
- CST → cst
- vBC → valor_base_calculo
- pCOFINS → aliquota
- vCOFINS → valor_cofins

### Nó `<total><ICMSTot>`
- vProd → valor_subtotal_produtos
- vFrete → valor_frete
- vSeg → valor_seguro
- vDesc → valor_desconto
- vOutro → valor_outras_despesas
- vII → valor_total_ii
- vIPI → valor_total_ipi
- vPIS → valor_pis
- vCOFINS → valor_cofins
- vBC → base_calculo_icms
- vICMS → valor_icms
- vBCST → base_calculo_icms_st
- vST → valor_icms_st
- vNF → valor_total_nfe
- vTotTrib → valor_aproximado_tributos

## Status do Projeto

### ✅ Implementado
- NFe_Endereco (emitente e destinatário)
- NFe_Emitente (todos os campos)
- NFe_Destinatario (todos os campos)
- NFe_Identificacao (completo)
- NFe (documento principal)
- NFe_Produto (todos os itens)
- NFe_ICMS (por produto)
- NFe_IPI (por produto)
- NFe_PIS (por produto)
- NFe_COFINS (por produto)
- NFe_Total (totalizações)

### ⏳ Pendente (Fases Futuras)
- NFe_Transporte (dados de transporte)
- NFe_Cobranca (dados de cobrança)
- NFe_Parcela (parcelas de cobrança)
- NFe_Pagamento (formas de pagamento)
- NFe_Informacoes_Adicionais (informações complementares)

## Observações Técnicas

### Namespace XML
O sistema trata XMLs com e sem namespace:
- Com namespace: `nfe:tag`
- Sem namespace: `tag`

### Update vs Create
Usamos `update_or_create()` para:
- NFe_Emitente (por CNPJ)
- NFe_Destinatario (por documento)
- NFe_Identificacao (por chave_acesso)
- NFe (por identificacao)

Isso evita duplicação em reprocessamentos.

### Defaults Seguros
Todos os campos opcionais têm defaults:
- Strings: `''` ou valor padrão específico
- Decimals: `0`
- Datas: `None` ou `datetime.now()`

### Performance
- Criação em lote não implementada (possível melhoria futura)
- Um XML = múltiplas inserções (1 NFe + N produtos + N*4 impostos + 1 total + 2 endereços)
- Transação implícita do Django garante atomicidade

## Testagem

Para testar o sistema completo:

1. Preparar XML de NFe válido
2. Ter empresa cadastrada com CNPJ correspondente
3. Fazer upload via interface ou chamar API
4. Verificar:
   - Registro em NFe criado
   - Endereços criados para emitente e destinatário
   - Produtos criados com impostos
   - Totais calculados e armazenados

## Logs de Erro

Erros retornam:
```json
{
    "file": "nome_arquivo.xml",
    "error": "Mensagem detalhada",
    "type": "TipoException"
}
```

Mensagens claras indicam:
- Estrutura XML inválida
- Empresa não encontrada (com CNPJ faltante)
- Campos obrigatórios ausentes
- Erros de conversão de tipo
