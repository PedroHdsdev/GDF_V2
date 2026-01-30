# 🔍 ANÁLISE E CORREÇÃO DE QUERIES - Streamlit Dashboard

## ❌ PROBLEMAS IDENTIFICADOS

### **Problema 1: Relacionamentos Incorretos**

**Antes:**
```python
# ❌ ERRADO - Campo 'identificacao_id' não existe
nfe_queryset = NFe.objects.filter(filter_Empresas).values(*ls.ls_g_nfe)
heard_queryset = NFe_Identificacao.objects.filter(
    identificacao_id__in=nfe_queryset.values_list('identificacao_id', flat=True)
)

# ❌ ERRADO - Campo 'nfe_id' não existe em NFe_Produto
item_queryset = NFe_Produto.objects.filter(
    nfe_id__in=nfe_queryset.values_list('id_nfe', flat=True)
)
```

**Estrutura Real dos Models:**
```python
# NFe (tabela principal)
class NFe(models.Model):
    id_nfe = models.AutoField(primary_key=True)  # ✓ Campo correto
    identificacao = models.OneToOneField(NFe_Identificacao, ...)  # Relacionamento

# NFe_Identificacao
class NFe_Identificacao(models.Model):
    id_identificacao = models.AutoField(primary_key=True)
    # ... campos ...

# NFe_Produto
class NFe_Produto(models.Model):
    id_produto = models.AutoField(primary_key=True)
    nfe_serie = models.ForeignKey(NFe_Identificacao, ...)  # ✓ Relacionamento correto
    # NFe_Produto não tem relação direta com NFe, mas com NFe_Identificacao
```

---

### **Problema 2: Filtro de CFOP em Local Errado**

**Antes:**
```python
# ❌ ERRADO - Aplicado a NFe_Total que não tem campo 'cfop'
q_filtros &= Q(cfop__in=ls.ls_g_cfop_Saida)
total_queryset = NFe_Total.objects.filter(q_filtros).values(...)
```

**Estrutura Real:**
```python
class NFe_Total(models.Model):
    # ❌ NÃO HÁ CAMPO 'cfop'
    valor_total_nfe = models.DecimalField(...)
    valor_icms = models.DecimalField(...)
    # ...

class NFe_Produto(models.Model):
    # ✓ CFOP está aqui
    cfop = models.CharField(max_length=4, blank=True, null=True)
```

---

### **Problema 3: Filtro de Data Não Aplicado**

**Antes:**
```python
# ❌ Período não é aplicado às queries
q_filtros &= Q(cfop__in=ls.ls_g_cfop_Saida)
# ... mas data_inicio e data_fim não são usadas em nenhuma query
```

**Correto:**
```python
# ✓ Filtro de data aplicado corretamente
heard_queryset = NFe_Identificacao.objects.filter(
    # ... filtros anteriores ...
).filter(Q(emissao__date__range=(data_inicio, data_fim)) if usar_periodo else Q())
```

---

### **Problema 4: Campo `tipo_operacao` vs `tipo_documento`**

**Antes:**
```python
# Sem distinção clara entre entrada e saída
# Dependia de Q(cfop__in=...) que não funciona
```

**Correto:**
```python
# ✓ Usar tipo_operacao para filtrar entrada/saída
nfe_queryset = NFe.objects.filter(
    filter_Empresas,
    identificacao__tipo_operacao='1'  # '0'=Entrada, '1'=Saída
)
```

---

## ✅ SOLUÇÃO IMPLEMENTADA

### **Novo Fluxo de Queries (Correto)**

```python
# ============================================================
# VENDAS (Notas de Saída)
# ============================================================
if tipo_relatorio == "Vendas":
    # 1️⃣ Filtrar NFe por empresa e tipo operação (SAÍDA)
    nfe_queryset = NFe.objects.filter(
        filter_Empresas,  # Por empresa do usuário
        identificacao__tipo_operacao='1'  # Saída
    ).select_related('identificacao')
    
    # 2️⃣ Buscar identificações (header) com filtro de data
    heard_queryset = NFe_Identificacao.objects.filter(
        nfe__in=nfe_queryset,
        tipo_operacao='1'  # Saída
    ).filter(
        Q(emissao__date__range=(data_inicio, data_fim)) if usar_periodo else Q()
    )
    
    # 3️⃣ Totais (valores agregados por nota)
    total_queryset = NFe_Total.objects.filter(
        nfe_identificacao__in=heard_queryset.values_list('id_identificacao', flat=True)
    )
    
    # 4️⃣ Itens/Produtos (com filtro CFOP aqui!)
    item_queryset = NFe_Produto.objects.filter(
        nfe_serie__in=heard_queryset.values_list('id_identificacao', flat=True),
        cfop__in=ls.ls_g_cfop_Saida  # ✓ CFOP está em NFe_Produto
    )

# ============================================================
# COMPRAS (Notas de Entrada)
# ============================================================
elif tipo_relatorio == "Compras":
    # Mesmo padrão, mas com tipo_operacao='0' (Entrada)
    nfe_queryset = NFe.objects.filter(
        filter_Empresas,
        identificacao__tipo_operacao='0'  # Entrada
    ).select_related('identificacao')
    
    # ... resto das queries similar com tipo_operacao='0'
```

### **Estrutura de Dados do DataFrame**

```python
# DataFrame final com todas as informações necessárias para gráficos
df = {
    'id_identificacao': [1, 2, ...],
    'numero': ['001', '002', ...],
    'serie': ['001', '001', ...],
    'emissao': [2025-01-15, 2025-01-16, ...],
    'tipo_operacao': ['1', '1', ...],
    'valor_total_nfe': [1000.00, 2000.00, ...],  # De NFe_Total
    'valor_base_icms': [1000.00, 2000.00, ...],  # De NFe_Total
    'valor_icms': [170.00, 340.00, ...],  # De NFe_Total
    'valor_ipi': [0.00, 100.00, ...],  # De NFe_Total
    'quantidade': [10.5, 25.0, ...],  # Agregado de NFe_Produto
    'valor_produtos': [1000.00, 2000.00, ...],  # Agregado de NFe_Produto
    'total_itens': [3, 5, ...]  # Quantidade de linhas por nota
}
```

---

## 📊 IMPACTO NAS QUERIES

| Aspecto | Antes | Depois |
|---------|-------|--------|
| **Relacionamento NFe ↔ NFe_Identificacao** | ❌ Errado | ✓ OneToOneField |
| **Relacionamento NFe_Produto ↔ NFe** | ❌ Errado | ✓ via NFe_Identificacao |
| **Filtro CFOP** | ❌ Em NFe_Total | ✓ Em NFe_Produto |
| **Filtro Data** | ❌ Não aplicado | ✓ Em NFe_Identificacao |
| **Filtro Entrada/Saída** | ❌ Apenas por CFOP | ✓ Por tipo_operacao |
| **Performance** | ⚠️ N+1 queries | ✓ select_related otimizado |

---

## 🔧 CAMPO DE RELACIONAMENTO CORRETO

```
NFe (id_nfe)
  ↓ (OneToOneField: identificacao)
NFe_Identificacao (id_identificacao)
  ↓ (ForeignKey Reverso: produtos)
NFe_Produto (id_produto)
  ├─ cfop ← FILTRO AQUI
  ├─ quantidade
  └─ valor_total

NFe (id_nfe)
  ↓ (OneToOneField: identificacao)
NFe_Identificacao (id_identificacao)
  ↓ (OneToOneField Reverso: totalizacao)
NFe_Total (id_total)
  ├─ valor_total_nfe
  ├─ valor_icms
  └─ valor_ipi ← DADOS PARA GRÁFICOS
```

---

## 📝 REFERÊNCIA DE CAMPOS DISPONÍVEIS

### NFe_Identificacao
- `emissao` ✓ (usar para filtro de data)
- `tipo_operacao` ✓ ('0'=Entrada, '1'=Saída)
- `numero`, `serie`, `chave_acesso`

### NFe_Total
- `valor_total_nfe` ✓ (Faturamento)
- `valor_base_icms` ✓ (Base ICMS)
- `valor_icms` ✓ (ICMS)
- `valor_ipi` ✓ (IPI)
- `valor_pis` ✓ (PIS)
- `valor_cofins` ✓ (COFINS)

### NFe_Produto
- `cfop` ✓ (Código Fiscal de Operações)
- `quantidade` ✓
- `valor_total` ✓ (Valor por item)
- `ncm`, `descricao`, `unidade`

---

## ✨ PRÓXIMAS OTIMIZAÇÕES

1. **Prefetch para 1-N:** Usar `prefetch_related` para NFe_Produto
2. **Agregação em DB:** Usar `annotate()` para somas ao invés de Python
3. **Índices:** Criar índices em `emissao` e `tipo_operacao`
4. **Cache:** Implementar `@st.cache_data` para queries frequentes

