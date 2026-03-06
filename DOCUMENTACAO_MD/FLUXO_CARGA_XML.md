# Fluxo Completo de Carga XML

## 📋 Resumo do Processo

```
FRONTEND (Browser)
    ↓
[Selecionar pasta/arquivos com XMLs]
    ↓
[JavaScript valida tipos e tamanhos]
    ↓
POST /api/processar-xml/ (AJAX)
    ↓
BACKEND (Django)
    ↓
fn_api_processar_xml() → Validações
    ↓
CargaXml.set_upload_xml()
    ↓
Loop em cada arquivo XML:
    ├─ set_nfe()   → Parse XML → Insere na tabela nfe
    ├─ set_cte()   → Parse XML → Será implementado
    └─ set_nfse()  → Parse XML → Será implementado
    ↓
Retorna JSON com resultados
    ↓
FRONTEND recebe resposta
    ↓
Atualiza tabela de cargas
    ↓
Exibe alertas de sucesso/erro
```

---

## 🔄 Fluxo Detalhado

### 1️⃣ **FRONTEND - Template (index_CargaXml.html)**
```javascript
// Usuário clica "Carregar XMLs"
// → Modal abre com 2 abas: **Carga Manual** (contém seleção por diretório ou arquivo) e **Carga Automática** (parâmetros e agendamento)

// Seleciona arquivos via drag & drop ou clique
// ↓
exibirPreviewArquivos(files)  // Valida e mostra preview

// Clica "Carregar"
// ↓
iniciarUpload()  // Chama função em Script_CargaXml.js
```

### 2️⃣ **FRONTEND - Script (Script_CargaXml.js)**
```javascript
function iniciarUpload() {
    estadoCargaXml.arquivos.forEach((file, index) => {
        uploadArquivo(file, index);  // Faz POST para cada arquivo
    });
}

function uploadArquivo(file, index) {
    const formData = new FormData();
    formData.append('arquivo', file);  // Nome: 'arquivo'
    formData.append('type_xml', 'NFe');  // Tipo do XML
    formData.append('origem_dados', 'LOCAL');  // Origem: LOCAL, SAP, SPED, OUTROS
    
    fetch('/api/processar-xml/', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // Atualiza status na tabela
        atualizarStatusUpload(index, data.sucesso ? 'success' : 'error', data.mensagem);
    });
}
```

### 3️⃣ **BACKEND - API Endpoint (fn_api_processar_xml)**
```python
@login_required(login_url='Login')
@require_http_methods(["POST"])
def fn_api_processar_xml(request):
    cod_cliente = request.session.get('cod_cliente', None)
    
    # 1. Validar cliente e arquivos
    if not cod_cliente:
        return JsonResponse({'sucesso': False, 'mensagem': 'Cliente não identificado'})
    for f in lsl_Xml:  # servidor repete validação de tipo/tamanho
        if not f.name.lower().endswith('.xml'):
            return JsonResponse({'sucesso': False, 'mensagem': f'Arquivo inválido: {f.name}'} , status=400)
        if f.size > 50*1024*1024:
            return JsonResponse({'sucesso': False, 'mensagem': f'Arquivo muito grande: {f.name}'}, status=400)
    
    # 2. Extrair dados do request
    lsl_Xml = request.FILES.getlist('arquivo')  # Lista de arquivos
    l_v_type_xml = request.POST.get('type_xml', 'NFe')
    l_v_origem_dados = request.POST.get('origem_dados', 'LOCAL')
    
    # 3. Chamar classe de processamento
    cl_xml = CargaXml()
    upload_result = cl_xml.set_upload_xml(
        lsl_Xml,
        l_v_type_xml,
        l_v_origem_dados,
        cod_cliente,
        request.user.username
    )
    
    # 4. Retornar JSON com resultado
    return JsonResponse({
        'sucesso': len(upload_result['errors']) == 0,
        'mensagem': f"{len(upload_result['success'])} arquivo(s) com sucesso, {len(upload_result['errors'])} erro(s)",
        'detalhes': upload_result
    })
```

### 4️⃣ **BACKEND - Classe CargaXml (CargaXml.py)**
```python
def set_upload_xml(self, I_LsXml, i_type, I_origem_dados, i_cod_cliente, i_usuario):
    """
    Loop em cada arquivo da lista
    """
    result = {
        'success': [],
        'errors': []
    }
    
    for xml_file in I_LsXml:  # ← LOOP PRINCIPAL
        try:
            xml_data = xml_file.read()  # Ler bytes do arquivo
            
            if i_type == 'NFe':
                self.set_nfe(xml_data, I_origem_dados, i_cod_cliente, i_usuario)
            
            elif i_type == 'CTe':
                self.set_cte(xml_data, I_origem_dados, i_cod_cliente, i_usuario)
            
            elif i_type == 'NFSe':
                self.set_nfse(xml_data, I_origem_dados, i_cod_cliente, i_usuario)
            
            result['success'].append(xml_file.name)  # Adiciona sucesso
        
        except Exception as e:
            result['errors'].append({
                'file': xml_file.name,
                'error': str(e)
            })  # Adiciona erro
    
    return result  # Retorna resultado final
```

### 5️⃣ **BACKEND - Listagem de Jobs & Detalhes**

**Novas APIs adicionadas:**

- `GET /api/cargaxml/jobs/` → retorna todos os `JobCargaXml` do cliente atual.
- `GET /api/cargaxml/jobs/<job_id>/` → detalhes de um job específico (status, totais, log, parâmetros).

Cada job é exibido na interface principal como uma linha clicável. Ao clicar abre modal com duas abas:

1. **Log** – mostra linhas de mensagem extraídas do campo `mensagem` do job. O texto agora contém entradas `OK: nome.xml` para cargas bem‑sucedidas e `ERRO: nome.xml – motivo` para falhas, tanto em execuções automáticas quanto manuais.
2. **Dados do Job** – campos como horário programado, origem, diretório e filtros gravados no parâmetro.

O frontend usa `Script_CargaXml.js` para consumir essas rotas, montar a tabela inicial de jobs e preencher o modal.

A tabela de filtros passou a tratar tipos de job (`Automático` vs `Manual`) em vez de tipos de documento.


### 6️⃣ **BACKEND - Processar NFe (set_nfe)**
```python
def set_nfe(self, xml_data, origem_dados, cod_cliente, usuario):
    """
    1. Faz parse do XML (ElementTree)
    2. Extrai dados: número, série, chave_acesso, emitente, etc
    3. Cria/Obtém registros relacionados:
       - NFe_Emitente (by CNPJ)
       - NFe_Identificacao (by chave_acesso)
    4. Cria NFe principal com:
       - status='DRAFT'
       - origem_dados=origem_dados  ← Campo novo!
       - usuario_criacao=usuario
       - xml_assinado=xml_data
    5. Retorna objeto NFe criado
    """
    root = ET.fromstring(xml_data)
    
    # Extrair dados
    numero = root.find('.//nNF').text
    serie = root.find('.//serie').text
    chave_acesso = root.find('.//infNFe').get('Id').replace('NFe', '')
    emitente_cnpj = root.find('.//CNPJ').text
    
    # Obter/Criar Emitente
    emitente, _ = NFe_Emitente.objects.get_or_create(
        cnpj=emitente_cnpj,
        defaults={'razao_social': '...'}
    )
    
    # Criar Identificação
    identificacao = NFe_Identificacao.objects.create(
        chave_acesso=chave_acesso,
        numero=numero,
        serie=serie,
        emissao=data_emissao,
        ...
    )
    
    # Criar NFe
    nfe = NFe.objects.create(
        identificacao=identificacao,
        emitente=emitente,
        empresa=empresa,
        status='DRAFT',
        origem_dados=origem_dados,  ← Campo novo!
        usuario_criacao=usuario,
        xml_assinado=xml_data.decode('utf-8'),
    )
    
    return nfe
```

---

## 📊 Banco de Dados - Tabela NFe

### Campo novo adicionado:
```python
origem_dados = models.CharField(
    max_length=8,
    choices=[
        ('LOCAL', 'Máquina Local'),
        ('SAP', 'Importação SAP'),
        ('SPED', 'Importação SPED'),
        ('OUTROS', 'Outros'),
    ],
    default='LOCAL'
)
```

### Valores possíveis:
- **LOCAL** → Arquivo carregado via interface web
- **SAP** → Importado de integração SAP
- **SPED** → Importado de arquivo SPED
- **OUTROS** → Outras origens

---

## 🔗 URLs Necessárias

### Adicionar em `urls.py`:
```python
path('api/processar-xml/', views.fn_api_processar_xml, name='API_ProcessarXml'),
```

---

## ✅ Checklist de Implementação

- [x] Criar view `fn_view_CargaXml()` (GET - exibe página)
- [x] Criar API `fn_api_processar_xml()` (POST - processa upload)
- [x] Criar rota `/api/processar-xml/`
- [x] Adicionar campo `origem_dados` à tabela NFe
- [x] Implementar `CargaXml.set_upload_xml()` com loop
- [x] Implementar `set_nfe()` com parse de XML
- [x] Frontend: Script_CargaXml.js com upload
- [ ] Implementar `set_cte()` (TODO)
- [ ] Implementar `set_nfse()` (TODO)
- [ ] Adicionar validações mais robustas
- [ ] Adicionar retry logic para falhas

---

## 🚀 Como Usar

1. Acessar `/CargaXml/`
2. Clicar "Carregar XMLs"
3. Selecionar pasta ou arquivos
4. Clicar "Carregar"
5. Aguardar resposta da API
6. Tabela de cargas será atualizada
7. Verificar coluna "Status" para resultados

---

## 🐛 Troubleshooting

### Erro: "Nenhum arquivo selecionado"
- Certifique-se de que selecionou arquivos antes de clicar "Carregar"

### Erro: "Cliente não identificado"
- Verifique se fez login corretamente
- Sessão pode ter expirado

### Erro ao fazer parse do XML
- XML pode estar corrompido
- Verificar encoding (UTF-8)
- Verificar estrutura do XML (valores vazios, atributos faltando)

### NFe não aparece na tabela
- Verificar se foi criada no banco (query na tabela `nfe`)
- Verificar coluna `origem_dados` para validar inserção

