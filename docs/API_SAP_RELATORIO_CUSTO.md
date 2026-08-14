# API SAP – Relatório de Custo (POST)

API para receber dados de Relatório de Custo enviados pelo SAP e persistir em `sap.relatorio_custo` (PostgreSQL).

---

## Endpoint

```
POST /gdf/api/sap/relatorio-custo/
```

(Substitua `/gdf` pelo `FORCE_SCRIPT_NAME` se configurado diferente.)

---

## Autenticação

A API exige chave de autenticação configurada no servidor.

**Configuração (.env):**
```
SAP_RELATORIO_CUSTO_API_KEY=sua_chave_secreta
```

**Headers aceitos:**
- `X-API-Key: sua_chave_secreta`
- `Authorization: Bearer sua_chave_secreta`

---

## Formato do body (JSON)

```json
{
  "cod_empresa": "1000",
  "cod_filial": "001",
  "registros": [
    {
      "DOCNUM": "4500012345",
      "MJAHR": "2025",
      "MBLNR": "",
      "PSTDAT": "2025-01-15",
      "MATNR": "MAT001",
      "NFENUM": "000123456",
      "SERIES": "1",
      "DOCSTA": " ",
      "KUNNR": "0000123456",
      "NAME1": "Cliente Exemplo",
      "CHAVE_ACESSO": "35250112345678000199550010001234561123456789",
      "VLR_TOT_DOC": "15000.00",
      "TOTAL_IMPOSTOS": "2500.00",
      "CMV_GERENCIAL": "8000.00",
      "MARGEM_CONTRIB_GER": "4500.00",
      "QTD_PROD": "100.000"
    }
  ]
}
```

### Campos obrigatórios no nível raiz

| Campo         | Tipo   | Obrigatório | Descrição                          |
|---------------|--------|-------------|------------------------------------|
| `cod_empresa` | string | Sim         | Código da empresa (GDF = bukrs SAP) |
| `cod_filial`  | string | Não         | Código da filial                   |
| `registros`   | array  | Sim         | Lista de registros                 |

### Campos por registro

Chaves aceitas em **maiúsculo** (ex.: DOCNUM) ou **minúsculo** (ex.: docnum).

| Campo SAP      | Campo modelo   | Tipo    |
|----------------|----------------|---------|
| DOCNUM         | docnum         | string  |
| MJAHR          | mjahr          | string  |
| MBLNR          | mblnr          | string  |
| PSTDAT         | pstdat         | date    |
| MATNR          | matnr          | string  |
| NFENUM         | nfenum         | string  |
| CHAVE_ACESSO   | chave_acesso   | string  |
| VLR_TOT_DOC    | vlr_tot_doc    | decimal |
| TOTAL_IMPOSTOS | total_impostos | decimal |
| CMV_GERENCIAL  | cmv_gerencial  | decimal |
| MARGEM_CONTRIB_GER | margem_contrib_ger | decimal |
| QTD_PROD       | qtd_prod       | decimal |
| ...            | ...            | ...     |

Chave única: `(empresa, docnum, mjahr, mblnr)`. Registros existentes são atualizados.

---

## Resposta

### Sucesso (200)

```json
{
  "sucesso": true,
  "mensagem": "5 registro(s) gravado(s) em sap.relatorio_custo.",
  "total_recebidos": 5,
  "total_gravados": 5,
  "erros": []
}
```

### Erro de validação (400)

```json
{
  "sucesso": false,
  "mensagem": "Empresa \"9999\" não encontrada no cadastro.",
  "total_recebidos": 5,
  "total_gravados": 0,
  "erros": []
}
```

### API key inválida (401)

```json
{
  "sucesso": false,
  "mensagem": "API key inválida ou não informada. Use header X-API-Key ou Authorization: Bearer."
}
```

### API não configurada (503)

```json
{
  "sucesso": false,
  "mensagem": "API não configurada. Defina SAP_RELATORIO_CUSTO_API_KEY no .env."
}
```

---

## Exemplo de chamada (curl)

```bash
curl -X POST "https://seu-dominio.com/gdf/api/sap/relatorio-custo/" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sua_chave_secreta" \
  -d '{
    "cod_empresa": "1000",
    "cod_filial": "001",
    "registros": [
      {
        "DOCNUM": "4500012345",
        "MJAHR": "2025",
        "MBLNR": "",
        "PSTDAT": "2025-01-15",
        "VLR_TOT_DOC": "15000.00",
        "TOTAL_IMPOSTOS": "2500.00"
      }
    ]
  }'
```
