# Relatório de Escalabilidade – GDF

**Data:** 2026-03-12 10:07:18
**Usuários concorrentes (máx testado):** 50
**Volume (requisições sequenciais):** 100

### Limite de usuários simultâneos (resumo)

- **Recomendado para operação hoje:** **35 usuários simultâneos** (margem de segurança ~70% sobre o limite com 100% sucesso).
- **Maior nível testado com 100% sucesso:** 50 usuários.

---

## 1. Carga concorrente

Requisições simultâneas ao mesmo endpoint (threads).

| Endpoint | Concorrentes | Tempo parede (s) | Req/s | Tempo médio (ms) | Min | Max | P95 (ms) | P99 (ms) | Sucesso |
|----------|--------------|------------------|-------|------------------|-----|-----|----------|----------|--------|
| Login (público) | 1 | 0.02 | 42.07 | 23.1 | 23.1 | 23.1 | 23.1 | 23.1 | 1/1 |
| Home (autenticado) | 1 | 0.06 | 16.9 | 15.29 | 15.29 | 15.29 | 15.29 | 15.29 | 1/1 |
| API Relatório NFe | 1 | 0.05 | 21.4 | 6.83 | 6.83 | 6.83 | 6.83 | 6.83 | 1/1 |
| View Usuários | 1 | 0.04 | 24.15 | 7.55 | 7.55 | 7.55 | 7.55 | 7.55 | 1/1 |
| Login (público) | 2 | 0.0 | 470.43 | 1.89 | 1.77 | 2.01 | 2.0 | 2.01 | 2/2 |
| Home (autenticado) | 2 | 0.06 | 32.71 | 10.81 | 9.87 | 11.76 | 11.67 | 11.74 | 2/2 |
| API Relatório NFe | 2 | 0.07 | 30.11 | 8.68 | 8.61 | 8.75 | 8.74 | 8.75 | 2/2 |
| View Usuários | 2 | 0.07 | 29.32 | 10.01 | 9.89 | 10.13 | 10.12 | 10.13 | 2/2 |
| Login (público) | 5 | 0.01 | 395.77 | 7.26 | 5.05 | 10.74 | 10.1 | 10.61 | 5/5 |
| Home (autenticado) | 5 | 0.13 | 39.02 | 28.95 | 24.8 | 31.77 | 31.48 | 31.71 | 5/5 |
| API Relatório NFe | 5 | 0.12 | 41.55 | 11.67 | 10.08 | 13.39 | 13.16 | 13.34 | 5/5 |
| View Usuários | 5 | 0.11 | 44.27 | 12.96 | 10.29 | 15.95 | 15.45 | 15.85 | 5/5 |
| Login (público) | 10 | 0.02 | 441.35 | 7.66 | 1.45 | 13.7 | 13.36 | 13.63 | 10/10 |
| Home (autenticado) | 10 | 0.23 | 42.87 | 37.37 | 12.63 | 73.13 | 70.73 | 72.65 | 10/10 |
| API Relatório NFe | 10 | 0.26 | 37.96 | 27.25 | 9.03 | 79.4 | 79.28 | 79.38 | 10/10 |
| View Usuários | 10 | 0.21 | 48.01 | 20.83 | 10.86 | 34.32 | 34.23 | 34.3 | 10/10 |
| Login (público) | 50 | 0.11 | 460.52 | 26.22 | 4.71 | 55.66 | 47.18 | 55.58 | 50/50 |
| Home (autenticado) | 50 | 1.11 | 45.08 | 75.71 | 12.58 | 138.1 | 122.38 | 136.12 | 50/50 |
| API Relatório NFe | 50 | 0.94 | 53.24 | 46.01 | 6.17 | 125.12 | 84.8 | 107.99 | 50/50 |
| View Usuários | 50 | 0.94 | 53.23 | 42.59 | 13.53 | 76.24 | 68.96 | 75.74 | 50/50 |

---

## 2. Volume (requisições sequenciais)

**Endpoint:** `GET /api/relatorio/nfe/`
**Requisições:** 100

| Tempo total (s) | Throughput (req/s) | Tempo médio (ms) | P95 (ms) | P99 (ms) | Sucesso |
|-----------------|--------------------|------------------|----------|----------|--------|
| 0.35 | 284.38 | 3.51 | 6.48 | 7.34 | 32/100 |

*Observação:* 68 requisições falharam (ex.: rate limit 429). Throughput e P95 referem-se às requisições bem-sucedidas.

---

## 3. Throughput (Login público)

Requisições sequenciais GET /Login/ (sem autenticação).

| Requisições | Tempo (s) | Req/s |
|-------------|-----------|-------|
| 40 | 0.1 | 413.24 |

---

## 4. Limite de usuários simultâneos (hoje)

Com base nos testes de carga concorrente realizados:

| Métrica | Valor | Observação |
|---------|-------|------------|
| **Máximo testado** | 50 usuários | Maior N de threads simuladas neste relatório |
| **Limite com 100% sucesso** | 50 usuários | Maior N em que todos os endpoints responderam 200/302 em todas as requisições |
| **Recomendado (operação)** | **35 usuários** | Margem de segurança (~70% do limite) para picos e variação de rede/servidor |

**Interpretação:** Em ambiente similar ao do teste (mesmo servidor, banco e rede), é seguro planejar até **35 usuários simultâneos** usando a aplicação. Acima disso, considere escalar (mais workers, cache, BD) ou rodar novo teste com `--concorrentes 20` (ou maior) para reavaliar.

**Latência P95 no limite (ms) por endpoint:**

- Home (autenticado): 122.38 ms
- API Relatório NFe: 84.8 ms
- View Usuários: 68.96 ms
- Login (público): 47.18 ms

---

## 5. Resumo geral

- **Cenários de concorrência:** 20 (com sucesso: 20/20)
- **Throughput (volume sequencial):** 284.38 req/s (GET API NFe, 100 requisições)
- **Throughput (Login público):** 413.24 req/s

---

## 6. Metodologia e recomendações

- **Concorrência:** cada nível (1, 2, 5, 10, …) executa N requisições em paralelo (threads) ao mesmo endpoint.
- **Volume:** requisições sequenciais ao mesmo endpoint para medir throughput estável.
- Para aumentar o limite testado, execute: `python manage.py run_escalabilidade_report --concorrentes 20 --volume 100`.
- Em produção, o limite real depende de CPU, memória, conexões ao banco e rede.
