# Lógica Melhorada de Busca de Empresa na Carga XML

## 📋 Resumo da Alteração

A lógica agora detecta automaticamente se a NFe é de **ENTRADA** ou **SAÍDA** e busca a empresa no registro correto:

```
NFe SAÍDA (tpNF=1)
    ↓
    CNPJ do EMITENTE
    ↓
    Busca empresa cadastrada com esse CNPJ
    ↓
    Se não encontrar → ❌ Erro: "Empresa não encontrada"

NFe ENTRADA (tpNF=0)
    ↓
    CNPJ do DESTINATÁRIO
    ↓
    Busca empresa cadastrada com esse CNPJ
    ↓
    Se não encontrar → ❌ Erro: "Empresa não encontrada"
```

---

## 🔍 Implementação Técnica

### Antes (Incorreto):
```python
# Sempre buscava pelo emitente, mesmo em notas de entrada
empresa = Empresa.objects.get(cnpj=emitente_cnpj)  # ❌ Errado para entrada!
```

### Depois (Correto):
```python
# Determina o tipo de operação a partir do XML
tipo_operacao = ide.findtext('.//nfe:tpNF')  # 0=Entrada, 1=Saída

if tipo_operacao == '1':  # SAÍDA
    cnpj_para_busca = emitente_cnpj  # Usa CNPJ do emitente
else:  # ENTRADA (0)
    cnpj_para_busca = destinatario_cnpj  # Usa CNPJ do destinatário

# Buscar empresa com validação
try:
    empresa = Empresa.objects.get(cnpj=cnpj_para_busca)
except Empresa.DoesNotExist:
    raise ValueError(
        f"Empresa não encontrada no registro. "
        f"NFe {tipo_nfe}: CNPJ {cnpj_para_busca} não existe na base de dados."
    )
```

---

## 📊 Exemplos Práticos

### Exemplo 1: NFe de SAÍDA
```
Emitente: ABC Ltda (CNPJ: 12.345.678/0001-00)
Destinatário: XYZ Ltda (CNPJ: 98.765.432/0001-11)

tpNF = 1 (Saída)
    ↓
Busca: Empresa.objects.get(cnpj='12345678000100')
    ↓
Se encontrar ✅ → Cria NFe com essa empresa
Se não ❌ → Erro: "Empresa 12345678000100 não encontrada"
```

### Exemplo 2: NFe de ENTRADA
```
Emitente: Fornecedor Brasil (CNPJ: 11.111.111/0001-22)
Destinatário: ABC Ltda (CNPJ: 12.345.678/0001-00)

tpNF = 0 (Entrada)
    ↓
Busca: Empresa.objects.get(cnpj='12345678000100')
    ↓
Se encontrar ✅ → Cria NFe com essa empresa
Se não ❌ → Erro: "Empresa 12345678000100 não encontrada"
```

---

## 🛠️ Campos Extraídos do XML

| Campo | XML Path | Tipo | Descrição |
|-------|----------|------|-----------|
| `tipo_operacao` | `ide/tpNF` | char(1) | 0=Entrada, 1=Saída |
| `emitente_cnpj` | `emit/CNPJ` | varchar(14) | CNPJ de quem emite |
| `emitente_razao` | `emit/xNome` | varchar(255) | Razão social do emitente |
| `destinatario_cnpj` | `dest/CNPJ` | varchar(14) | CNPJ de quem recebe |
| `destinatario_razao` | `dest/xNome` | varchar(255) | Razão social do destinatário |

---

## ✅ Melhorias Implementadas

1. ✅ **Detecção automática de tipo** - Lê `tpNF` do XML
2. ✅ **CNPJ correto** - Usa emitente para saída, destinatário para entrada
3. ✅ **Mensagem de erro clara** - Informa qual CNPJ não foi encontrado
4. ✅ **Tipo de NFe na mensagem** - Mostra se é ENTRADA ou SAÍDA
5. ✅ **Validação robusta** - Trata exception do Django ORM corretamente
6. ✅ **Destinatário salvo** - Agora cria registro de destinatário também

---

## 📝 Fluxo Completo Atualizado

```python
def set_nfe(xml_data, origem_dados, usuario):
    
    # 1. Parse do XML
    root = ET.fromstring(xml_data)
    infNFe = root.find('.//infNFe')
    ide = infNFe.find('.//ide')
    
    # 2. Extrair dados básicos
    numero = ide.findtext('.//nNF')
    serie = ide.findtext('.//serie')
    chave_acesso = infNFe.get('Id').replace('NFe', '')
    
    # 3. Extrair tipo de operação ← NOVO!
    tipo_operacao = ide.findtext('.//tpNF')  # 0 ou 1
    
    # 4. Extrair emitente
    emit = infNFe.find('.//emit')
    emitente_cnpj = emit.findtext('.//CNPJ')
    emitente_razao = emit.findtext('.//xNome')
    
    # 5. Extrair destinatário ← NOVO!
    dest = infNFe.find('.//dest')
    destinatario_cnpj = dest.findtext('.//CNPJ') if dest else None
    destinatario_razao = dest.findtext('.//xNome') if dest else None
    
    # 6. Criar/Obter Emitente
    emitente = NFe_Emitente.objects.get_or_create(
        cnpj=emitente_cnpj,
        defaults={'razao_social': emitente_razao}
    )
    
    # 7. Criar/Obter Destinatário ← NOVO!
    if destinatario_cnpj:
        destinatario = NFe_Destinatario.objects.get_or_create(
            documento=destinatario_cnpj,
            defaults={'razao_social': destinatario_razao}
        )
    
    # 8. Criar/Obter Identificação
    identificacao = NFe_Identificacao.objects.get_or_create(
        chave_acesso=chave_acesso,
        defaults={
            'numero': numero,
            'serie': serie,
            'tipo_documento': tipo_operacao,
            ...
        }
    )
    
    # 9. ⭐ BUSCAR EMPRESA CORRETAMENTE ← PONTO-CHAVE!
    if tipo_operacao == '1':  # Saída
        cnpj_para_busca = emitente_cnpj
    else:  # Entrada (0)
        cnpj_para_busca = destinatario_cnpj
    
    try:
        empresa = Empresa.objects.get(cnpj=cnpj_para_busca)
    except Empresa.DoesNotExist:
        raise ValueError(f"CNPJ {cnpj_para_busca} não encontrado!")
    
    # 10. Criar NFe
    nfe = NFe.objects.create(
        identificacao=identificacao,
        emitente=emitente,
        destinatario=destinatario,
        empresa=empresa,
        origem_dados=origem_dados,
        usuario_criacao=usuario,
        status='DRAFT',
        xml_assinado=xml_data.decode('utf-8')
    )
    
    return nfe
```

---

## 🔗 Relacionamentos de Banco

```
NFe
  ├─ identificacao → NFe_Identificacao (1:1)
  ├─ emitente → NFe_Emitente (FK)
  ├─ destinatario → NFe_Destinatario (FK, nullable)
  └─ empresa → Empresa (FK)
       └─ Busca pela empresa correta baseado no tipo de NFe
```

---

## 📌 Mensagens de Erro Agora Exibem

### Saída - CNPJ do emitente não encontrado:
```
"Empresa não encontrada no registro. NFe SAÍDA: CNPJ 12345678000100 não existe na base de dados."
```

### Entrada - CNPJ do destinatário não encontrado:
```
"Empresa não encontrada no registro. NFe ENTRADA: CNPJ 98765432000111 não existe na base de dados."
```

---

## 🚀 Como Funciona Agora

1. **Upload XML** → API recebe arquivo
2. **Parse XML** → Lê tipo de operação (ENTRADA/SAÍDA)
3. **Extrai CNPJs** → Emitente e Destinatário
4. **Define busca** → Se SAÍDA usa emitente, se ENTRADA usa destinatário
5. **Valida empresa** → Tenta encontrar no registro, se não encontrar mostra erro claro
6. **Insere no banco** → Cria NFe com empresa correta

