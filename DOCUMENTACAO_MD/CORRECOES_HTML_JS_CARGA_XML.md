# Correções HTML e JS - Carga XML

## Problemas Identificados e Corrigidos ✅

### 1. **Falta de Seleção de Tipo de Documento**
❌ **Problema**: Modal não tinha campo para selecionar NFe/CTe/NFSe  
✅ **Solução**: Adicionado `<select id="select-tipo-documento">` com opções:
- NFe - Nota Fiscal Eletrônica
- CTe - Conhecimento de Transporte  
- NFSe - Nota Fiscal de Serviço

### 2. **Falta de Seleção de Origem dos Dados**
❌ **Problema**: Modal não tinha campo para origem_dados  
✅ **Solução**: Adicionado `<select id="select-origem-dados">` com opções:
- LOCAL - Máquina Local
- SAP - Importação SAP
- SPED - Importação SPED
- OUTROS - Outros

### 3. **Upload Individual vs Lote**
❌ **Problema**: JavaScript enviava 1 arquivo por vez em requisições separadas  
✅ **Solução**: Refatorado para enviar TODOS os arquivos em uma única requisição
```javascript
// ANTES: Loop fazendo N requisições
arquivos.forEach((file, index) => {
    uploadArquivo(file, index);
});

// DEPOIS: Uma requisição com todos os arquivos
uploadArquivosLote(arquivos, tipoDocumento, origemDados);
```

### 4. **Parâmetros Faltando**
❌ **Problema**: JavaScript não enviava `type_xml` nem `origem_dados`  
✅ **Solução**: Parâmetros adicionados ao FormData:
```javascript
formData.append('type_xml', tipoDocumento);
formData.append('origem_dados', origemDados);
```

### 5. **CSRF Token Ausente**
❌ **Problema**: Template não tinha `{% csrf_token %}`  
✅ **Solução**: Adicionado token Django no início do container

### 6. **Status de Processamento**
❌ **Problema**: Só tinha status "success" e "error"  
✅ **Solução**: Adicionado status "processing" com spinner visual

### 7. **Tratamento de Erros Individual**
❌ **Problema**: Response genérica não indicava qual arquivo teve erro  
✅ **Solução**: Backend retorna array de sucessos e erros:
```json
{
    "sucesso": true,
    "mensagem": "10 arquivo(s) processado(s), 2 erro(s)",
    "detalhes": {
        "success": ["nota1.xml", "nota2.xml", ...],
        "errors": [
            {"file": "nota3.xml", "error": "Empresa não encontrada", "type": "ValueError"}
        ]
    }
}
```

JavaScript agora mapeia cada arquivo ao resultado correto.

### 8. **Contador de Arquivos**
❌ **Problema**: Não mostrava quantos arquivos foram selecionados  
✅ **Solução**: Adicionado `<span id="contador-arquivos">` atualizado dinamicamente

## Alinhamento Backend ↔ Frontend

### Backend Espera (views.py):
```python
lsl_Xml = request.FILES.getlist('arquivo')          # Lista de arquivos
l_v_type_xml = request.POST.get('type_xml', 'NFe')  # Tipo: NFe/CTe/NFSe
l_v_origem_dados = request.POST.get('origem_dados', 'LOCAL')  # Origem
```

### Frontend Envia (Script_CargaXml.js):
```javascript
arquivos.forEach(file => {
    formData.append('arquivo', file);  // ✅ Nome correto
});
formData.append('type_xml', tipoDocumento);      // ✅ Nome correto
formData.append('origem_dados', origemDados);    // ✅ Nome correto
```

## Fluxo Completo de Upload

### 1. Usuário Seleciona Arquivos
- Click em drop zone OU drag & drop
- Arquivos validados (extensão .xml, tamanho < 50MB)
- Preview exibido na tabela

### 2. Usuário Configura Upload
- Seleciona tipo: NFe/CTe/NFSe
- Seleciona origem: LOCAL/SAP/SPED/OUTROS

### 3. Click em "Carregar"
- `iniciarUpload()` chamado
- Valida se tem arquivos selecionados
- Marca todos como "Processando..."
- Chama `uploadArquivosLote()`

### 4. Upload em Lote
- Cria FormData com TODOS os arquivos
- Adiciona type_xml e origem_dados
- POST para `/api/processar-xml/`
- Inclui CSRF token no header

### 5. Backend Processa
- Valida cliente autenticado
- Extrai arquivos, tipo e origem
- Chama `Carga_xml().set_upload_xml()`
- Retorna JSON com detalhes

### 6. Frontend Atualiza Status
- Percorre `detalhes.success` → marca verde
- Percorre `detalhes.errors` → marca vermelho com mensagem
- Exibe alerta com resumo
- Recarrega tabela após 3 segundos

## Estrutura do Modal Atualizada

```html
<div class="modal">
  <div class="modal-body">
    <!-- Abas: Manual | Automática -->
    <!-- - Manual contém seleção por diretório e por arquivo, além de configurações de origem e preview -->
    <!-- - Automática exibe formulário e lista de parâmetros agendados -->

    <!-- Configurações (dentro da aba manual) -->
    <div class="row">
      <select id="select-tipo-documento">      <!-- ✅ NOVO -->
      <select id="select-origem-dados">        <!-- ✅ NOVO -->
    </div>
    
    <!-- Preview (aba manual) -->
    <table id="tabela-uploads">
      <span id="contador-arquivos">            <!-- ✅ NOVO -->
      <!-- Status com spinner animado -->
    </table>
  </div>
  
  <div class="modal-footer">
    <button id="btn-enviar-xml">Carregar</button>
  </div>
</div>
```

## Funções JavaScript Refatoradas

### Antes:
```javascript
function iniciarUpload() {
    arquivos.forEach((file, index) => {
        uploadArquivo(file, index);  // N requisições
    });
}
```

### Depois:
```javascript
function iniciarUpload() {
    const tipo = document.getElementById('select-tipo-documento').value;
    const origem = document.getElementById('select-origem-dados').value;
    uploadArquivosLote(arquivos, tipo, origem);  // 1 requisição
}

function uploadArquivosLote(arquivos, tipo, origem) {
    const formData = new FormData();
    arquivos.forEach(f => formData.append('arquivo', f));
    formData.append('type_xml', tipo);
    formData.append('origem_dados', origem);
    
    fetch('/api/processar-xml/', { ... })
        .then(data => {
            // Mapear resultados individuais
            data.detalhes.success.forEach(fileName => { ... });
            data.detalhes.errors.forEach(erro => { ... });
        });
}
```

## Status Badges

### Estados Visuais:

| Status | Cor | Ícone | Quando |
|--------|-----|-------|--------|
| Aguardando | Azul (badge-info) | Spinner | Arquivo selecionado |
| Processando | Amarelo (badge-warning) | Spinner | Upload em andamento |
| Sucesso | Verde (badge-success) | ✓ | Processado OK |
| Erro | Vermelho (badge-danger) | ✗ | Falha com mensagem |

## Validações Implementadas

### Client-Side (JavaScript):
- ✅ Extensão .xml obrigatória
- ✅ Tamanho máximo 50MB por arquivo
- ✅ Impede upload sem arquivos
- ✅ Validação de tipo de documento

### Server-Side (Python):
- ✅ Cliente autenticado (`cod_cliente` na sessão)
- ✅ Pelo menos 1 arquivo enviado
- ✅ Estrutura XML válida
- ✅ Empresa existe no cadastro
- ✅ Campos obrigatórios no XML

## Mensagens de Erro Claras

### Antes:
```
"Erro ao processar XML"
```

### Depois:
```
"Empresa não encontrada. NFe ENTRADA: CNPJ 12345678000190 não cadastrado."
"Estrutura de NFe inválida: infNFe não encontrado"
"CNPJ do emitente é obrigatório"
```

Cada erro indica:
- O que deu errado
- Tipo de NFe (ENTRADA/SAÍDA)
- CNPJ que está faltando
- Campo específico ausente

## Testagem Recomendada

### Cenários de Sucesso:
1. Upload 1 arquivo NFe válido
2. Upload múltiplos arquivos (10+)
3. Upload diretório completo
4. Alternar tipo: NFe → CTe → NFSe
5. Alternar origem: LOCAL → SAP

### Cenários de Erro:
1. Arquivo não-XML (deve rejeitar)
2. Arquivo > 50MB (deve rejeitar)
3. XML sem empresa cadastrada (deve mostrar CNPJ)
4. XML mal-formado (deve mostrar estrutura inválida)
5. Sem autenticação (deve retornar 403)

## Checklist de Funcionamento

- [x] Modal abre corretamente
- [x] Drag & drop funciona (diretório e arquivo)
- [x] Click na drop zone abre seletor
- [x] Preview mostra arquivos selecionados
- [x] Contador atualiza dinamicamente
- [x] Seleção de tipo funciona
- [x] Seleção de origem funciona
- [x] Botão "Carregar" envia corretamente
- [x] CSRF token incluído
- [x] Status atualiza em tempo real
- [x] Erros mostram mensagem detalhada
- [x] Modal pode ser fechado
- [x] Arquivos podem ser removidos individualmente

## Próximos Passos (Opcionais)

### Melhorias de UX:
- [ ] Barra de progresso geral
- [ ] Preview do conteúdo do XML antes do upload
- [ ] Filtro por data na tabela de cargas
- [ ] Exportar log de processamento
- [ ] Reprocessar arquivo com erro

### Performance:
- [ ] Upload com streaming (arquivos muito grandes)
- [ ] Processamento assíncrono com Celery
- [ ] WebSocket para status em tempo real

### Funcionalidades:
- [ ] Validação schema XSD antes do upload
- [ ] Assinatura digital automática
- [ ] Download de XMLs processados
- [ ] Comparação XML original vs processado
