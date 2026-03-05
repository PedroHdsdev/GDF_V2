# Configuração SAP RFC

Guia para configurar e utilizar a integração SAP RFC no GDF.

---

## 1. Pré-requisitos

### 1.1 SAP NetWeaver RFC SDK

O **PyRFC** depende do **SAP NetWeaver RFC SDK** (sapnwrfc). É obrigatório instalá-lo antes do PyRFC.

- **Download**: [SAP Support Portal](https://support.sap.com/swdc) → Software Downloads → SAP NetWeaver → SAP NW RFC SDK
- **Versão recomendada**: 7.50 Patch Level 12 ou superior

### 1.2 Instalação do SDK (Linux) – Projeto GDF

O SDK já está extraído em `gdf_v2/nwrfcsdk/` (a partir do zip `nwrfc750P_18-70002752`).

**Estrutura esperada:**
```
gdf_v2/
├── nwrfcsdk/
│   ├── lib/          # libsapnwrfc.so, libicu*.so
│   ├── include/
│   └── bin/
```

**Configuração automática:** O `settings.py` já define `SAPNWRFC_HOME` e `LD_LIBRARY_PATH` se a pasta `nwrfcsdk` existir no projeto.

**Alternativa (instalação em diretório do sistema):**
```bash
sudo mkdir -p /usr/local/sap/nwrfcsdk
# Extrair o SDK para esse diretório
export SAPNWRFC_HOME=/usr/local/sap/nwrfcsdk
echo "/usr/local/sap/nwrfcsdk/lib" | sudo tee /etc/ld.so.conf.d/nwrfcsdk.conf
sudo ldconfig
```

### 1.3 Instalação do SDK (Windows)

1. Extrair o SDK em `C:\nwrfcsdk` (ou outro caminho)
2. Definir variável de ambiente: `SAPNWRFC_HOME=C:\nwrfcsdk`
3. Adicionar `%SAPNWRFC_HOME%\lib` ao PATH
4. Instalar **Visual C++ Redistributable** (2013 ou superior)

---

## 2. Instalação do PyRFC

```bash
cd GDF_PJT
pip install pyrfc
```

Ou via requirements:

```bash
pip install -r requirements.txt
```

**Verificar instalação**:

```bash
python -c "from pyrfc import Connection; print('PyRFC OK')"
```

Se aparecer erro de importação, o SDK não está configurado corretamente.

---

## 3. Configuração da Conexão SAP por Cliente

Cada cliente pode ter **uma conexão SAP** configurada na tela de Clientes.

1. Acesse **Clientes** → editar cliente
2. Aba **Conexão SAP**
3. Clique em **Criar conexão SAP** (se ainda não existir)
4. Preencha os campos:

| Campo | Descrição |
|-------|-----------|
| **Host (ashost)** | Endereço IP ou hostname do servidor SAP |
| **Nº do sistema (sysnr)** | Número do sistema (ex: 00, 01) |
| **Cliente (client)** | Mandante SAP (ex: 100, 800) |
| **Usuário** | Usuário SAP com permissão RFC |
| **Senha** | Senha do usuário |
| **Idioma (lang)** | Código do idioma (ex: PT, EN) |
| **Conexão ativa** | Marcar para habilitar |

5. Clique em **Salvar conexão SAP**

---

## 4. Funcionalidades RFC Disponíveis

### 4.1 Condições de Pagamento (Reprocessamento)

- **RFC**: `Z_ATUALIZAR_COND_PAGAMENTO_PO` (ajustar conforme o FM real no seu SAP)
- **Uso**: Painel de Reprocessamento → Lote → Gerar condições → Enviar ao SAP
- **Parâmetros**: `IT_CONDICOES`, `IV_EMPRESA`
- **Retorno esperado**: `ET_RETORNOS` com `chave_nfe` e `condicao_sap`

### 4.2 Importar Custo Cliente (exemplo)

- **RFC**: `/BRGMN/CUSTR_IMP_CUSTO`
- **Parâmetros**: `I_V_BUKRS`, `I_V_BRANCH`, `I_V_PSDAT_INI`, `I_V_PSDAT_FIM`

---

## 5. Ajustar Nome do RFC (Condições de Pagamento)

Se o nome do Function Module no seu SAP for diferente de `Z_ATUALIZAR_COND_PAGAMENTO_PO`, edite o arquivo:

**`GDF_PJT/app/classes/SapRfc.py`** – função `enviar_condicoes_pagamento_sap`:

```python
success, result = SapRfc.call(
    cod_cliente,
    'SEU_FM_AQUI',  # ← Alterar para o nome real do FM
    IT_CONDICOES=condicoes_lista,
    IV_EMPRESA=cod_empresa,
)
```

Ajuste também os nomes dos parâmetros (`IT_CONDICOES`, `IV_EMPRESA`) e da tabela de retorno (`ET_RETORNOS`) conforme a interface do seu FM.

---

## 6. Testar Conexão SAP

### Via API (requer login)

```bash
# POST com cod_cliente na sessão ou como admin
curl -X POST "http://localhost:8000/api/sap/testar-conexao/" \
  -H "Cookie: sessionid=..." \
  -H "Content-Type: application/json" \
  -d '{"cod_cliente": "COD_CLIENTE"}'
```

### Via Management Command

```bash
cd GDF_PJT
python manage.py sap_testar_conexao --cliente COD_CLIENTE
```

---

## 7. Conexão via SAP Router (opcional)

Se o acesso ao SAP for via SAP Router, use o parâmetro `saprouter` na configuração. O modelo `SapConnection` atual suporta `ashost`, `sysnr`, `client`, `user`, `passwd`, `lang`. Para SAP Router, pode ser necessário estender o modelo e o `config_from_connection` em `SapRfc.py`.

---

## 8. Troubleshooting

| Erro | Solução |
|------|---------|
| `ModuleNotFoundError: No module named 'pyrfc'` | Instalar PyRFC: `pip install pyrfc` |
| `DLL load failed` / `libsapnwrfc.so not found` | Configurar `SAPNWRFC_HOME` e `ldconfig` |
| `Nenhuma conexão SAP ativa para o cliente` | Criar/ativar conexão na aba SAP do cliente |
| `Falha ao abrir conexão SAP` | Verificar host, sysnr, client, usuário e senha; testar ping e firewall |
| RFC retorna erro | Verificar permissões do usuário SAP e nome/parâmetros do FM |

---

## 9. Estrutura de Arquivos

```
GDF_PJT/
├── app/
│   ├── classes/
│   │   └── SapRfc.py          # Classe principal RFC
│   ├── db_GDF/Public/models.py # SapConnection
│   └── views.py               # fn_view_cliente_sap, fn_api_*_enviar_sap
├── management/commands/
│   └── sap_testar_conexao.py  # Comando de teste
└── DOCUMENTACAO_MD/
    └── SAP_RFC_SETUP.md       # Este arquivo
```
