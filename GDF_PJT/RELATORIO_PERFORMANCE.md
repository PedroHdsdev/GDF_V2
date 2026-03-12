# Relatório de Performance – GDF

**Data e hora:** 2026-03-12 10:01:59
**Execuções por endpoint:** 5
**DEBUG (contagem de queries):** True

---

## 1. Metodologia

- Cada endpoint foi chamado **5 vezes** em sequência.
- Métricas: tempo de resposta (ms), quantidade de queries SQL (com DEBUG=True).
- Ambiente: Django test client (sem rede real). Em produção, latência pode ser maior.

---

## 2. Resumo executivo

| Endpoint | Status | Tempo médio (ms) | Min | Max | Queries (média) | Queries (máx) |
|----------|--------|------------------|-----|-----|-----------------|--------------|
| Tela de login (GET) | 200 | 10.8 | 5.96 | 27.93 | 5.0 | 5 |
| Home (autenticado) | 200 | 9.79 | 6.42 | 16.56 | 6.0 | 6 |
| API Sessão Cliente | 405 | 5.17 | 4.75 | 5.64 | 5.0 | 5 |
| API Relatório NFe | 200 | 6.02 | 5.67 | 6.52 | 5.0 | 5 |
| API Relatório CTe | 200 | 4.77 | 4.58 | 5.15 | 5.0 | 5 |
| API Relatório NFSe | 200 | 5.95 | 5.43 | 6.36 | 5.0 | 5 |
| API Relatório SPED | 200 | 5.02 | 4.63 | 6.13 | 5.0 | 5 |
| API CargaXml Jobs | 403 | 6.22 | 5.92 | 6.81 | 5.0 | 5 |
| API CargaXml Parâmetros | 403 | 6.28 | 5.87 | 6.95 | 5.0 | 5 |
| API Reprocessamento Lotes | 403 | 6.43 | 6.29 | 6.53 | 5.0 | 5 |
| View Listar Usuários | 200 | 7.07 | 6.33 | 9.34 | 5.0 | 5 |
| View Listar Empresas | 302 | 5.57 | 5.38 | 5.8 | 5.0 | 5 |
| View Relatório Fiscal | 200 | 6.74 | 5.87 | 8.57 | 5.0 | 5 |
| View Painel Reprocessamento | 200 | 8.18 | 6.48 | 12.17 | 5.0 | 5 |

---

## 3. Detalhes por endpoint

### Tela de login (GET)

- **URL:** `GET /Login/`
- **Status HTTP:** 200
- **Tempo médio:** 10.8 ms
- **Tempo min/max:** 5.96 / 27.93 ms
- **Queries SQL (média/máx):** 5.0 / 5

### Home (autenticado)

- **URL:** `GET /Home/`
- **Status HTTP:** 200
- **Tempo médio:** 9.79 ms
- **Tempo min/max:** 6.42 / 16.56 ms
- **Queries SQL (média/máx):** 6.0 / 6

### API Sessão Cliente

- **URL:** `GET /api/sessao/cliente/`
- **Status HTTP:** 405
- **Tempo médio:** 5.17 ms
- **Tempo min/max:** 4.75 / 5.64 ms
- **Queries SQL (média/máx):** 5.0 / 5

### API Relatório NFe

- **URL:** `GET /api/relatorio/nfe/`
- **Status HTTP:** 200
- **Tempo médio:** 6.02 ms
- **Tempo min/max:** 5.67 / 6.52 ms
- **Queries SQL (média/máx):** 5.0 / 5

### API Relatório CTe

- **URL:** `GET /api/relatorio/cte/`
- **Status HTTP:** 200
- **Tempo médio:** 4.77 ms
- **Tempo min/max:** 4.58 / 5.15 ms
- **Queries SQL (média/máx):** 5.0 / 5

### API Relatório NFSe

- **URL:** `GET /api/relatorio/nfse/`
- **Status HTTP:** 200
- **Tempo médio:** 5.95 ms
- **Tempo min/max:** 5.43 / 6.36 ms
- **Queries SQL (média/máx):** 5.0 / 5

### API Relatório SPED

- **URL:** `GET /api/relatorio/sped/`
- **Status HTTP:** 200
- **Tempo médio:** 5.02 ms
- **Tempo min/max:** 4.63 / 6.13 ms
- **Queries SQL (média/máx):** 5.0 / 5

### API CargaXml Jobs

- **URL:** `GET /api/cargaxml/jobs/`
- **Status HTTP:** 403
- **Tempo médio:** 6.22 ms
- **Tempo min/max:** 5.92 / 6.81 ms
- **Queries SQL (média/máx):** 5.0 / 5

### API CargaXml Parâmetros

- **URL:** `GET /api/cargaxml/parametros/`
- **Status HTTP:** 403
- **Tempo médio:** 6.28 ms
- **Tempo min/max:** 5.87 / 6.95 ms
- **Queries SQL (média/máx):** 5.0 / 5

### API Reprocessamento Lotes

- **URL:** `GET /api/reprocessamento/lotes/`
- **Status HTTP:** 403
- **Tempo médio:** 6.43 ms
- **Tempo min/max:** 6.29 / 6.53 ms
- **Queries SQL (média/máx):** 5.0 / 5

### View Listar Usuários

- **URL:** `GET /usuarios/`
- **Status HTTP:** 200
- **Tempo médio:** 7.07 ms
- **Tempo min/max:** 6.33 / 9.34 ms
- **Queries SQL (média/máx):** 5.0 / 5

### View Listar Empresas

- **URL:** `GET /empresas/`
- **Status HTTP:** 302
- **Tempo médio:** 5.57 ms
- **Tempo min/max:** 5.38 / 5.8 ms
- **Queries SQL (média/máx):** 5.0 / 5

### View Relatório Fiscal

- **URL:** `GET /Relatorio/`
- **Status HTTP:** 200
- **Tempo médio:** 6.74 ms
- **Tempo min/max:** 5.87 / 8.57 ms
- **Queries SQL (média/máx):** 5.0 / 5

### View Painel Reprocessamento

- **URL:** `GET /Reprocessamento/Painel/`
- **Status HTTP:** 200
- **Tempo médio:** 8.18 ms
- **Tempo min/max:** 6.48 / 12.17 ms
- **Queries SQL (média/máx):** 5.0 / 5

---

## 4. Métricas agregadas

- **Endpoints medidos:** 14
- **Tempo médio geral:** 6.71 ms
- **Endpoint mais lento:** Tela de login (GET) (10.8 ms)
- **Endpoint mais rápido:** API Relatório CTe (4.77 ms)

---

## 5. Classificação por faixa de tempo

| Faixa | Quantidade | Endpoints (exemplos) |
|-------|------------|----------------------|
| **Rápido** (< 50 ms) | 14 | Tela de login (GET), Home (autenticado), API Sessão Cliente, API Relatório NFe, API Relatório CTe... |
| **Médio** (50–150 ms) | 0 | - |
| **Lento** (≥ 150 ms) | 0 | - |

---

## 6. Recomendações

- Endpoints com **muitas queries** (máx > 20): considerar `select_related()`/`prefetch_related()` ou cache.
- Endpoints **lentos** (≥ 150 ms): revisar consultas ao banco e tamanho de payload.
- Em produção, medir novamente com carga real e com DEBUG=False.
