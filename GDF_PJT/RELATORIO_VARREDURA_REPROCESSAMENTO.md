# Varredura Completa - Reprocessamento Painel

## Resumo
A varredura foi realizada em: views, models, classes Reprocessamento, frontend (JS, HTML, CSS), APIs e lógica do confronto.

---

## 1. CONFRONTO SPED x NFe - LÓGICA

### Fluxo correto
- **SPED**: Extrai chaves (44 dígitos) de `Sped_Reg_C100.chv_nfe` e de `Sped_Registro` (D100) via regex
- **NFe**: Lista NF-e por `empresa_id` e competência (mês/ano)
- **Comparação**:
  - NFe nos XMLs mas não no SPED → `NFE_AUSENTE_SPED`
  - Chaves no SPED mas não nos XMLs → `SPED_AUSENTE_NFE`

### Verificações
- Chaves: 44 dígitos em ambos (chv_nfe e chave_acesso)
- Empresa: NFe.empresa_id = cod_empresa (Empresas usa cod_empresa como PK)
- Competência: primeiro dia do mês em ambos
- Sped_Arquivo: filtro por empresa, tipo='F', competencia

---

## 2. PONTOS VERIFICADOS

### APIs
- GET /api/reprocessamento/lotes/ - OK
- GET /api/reprocessamento/lotes/<id>/divergencias/ - OK
- POST /api/reprocessamento/confronto/ - OK
- POST /api/reprocessamento/condicoes-pagamento/gerar/ - OK
- GET/POST condicao-param - OK

### Frontend
- Filtros, modais, botões - OK
- Filtro condicao_param (Todos/Vazia/Específica) - OK

### Segurança
- Todas as APIs verificam cod_cliente da sessão
- Lotes e divergências filtrados por empresas do cliente

---

## 3. CORREÇÕES APLICADAS

### 3.1 Normalização de chaves no confronto
- Função `_normalizar_chave(chave)` para garantir chaves 44 dígitos (strip, remove espaços)
- Uso em `_extrair_chaves_sped` (C100 e D100) e em `confrontar_sped_nfe` ao montar `chaves_nfe` e `nfe_por_chave`
- Chaves inválidas são ignoradas (não entram no confronto)

### 3.2 Correção de indentação
- Bloco de criação de divergência `NFE_AUSENTE_SPED` estava incorretamente indentado após `continue`, tornando-o inalcançável
- Corrigido: descricao e Divergencia.objects.create agora executam quando `ch not in chaves_sped`
