# Relatório de Segurança – GDF

**Data:** 2026-03-12 10:02:07
**Resultado:** 18/18 verificações passaram

---

## 1. Metodologia

Verificações automáticas com Django test client: acesso não autenticado a rotas protegidas, APIs que exigem sessão (cod_cliente), tentativas IDOR, parâmetros de busca maliciosos (SQL-like), headers HTTP de segurança e logout. Não substitui auditoria manual nem testes de penetração.

---

## 2. Resumo por categoria

| Categoria | Passou | Total | Descrição / impacto |
|-----------|--------|-------|----------------------|
| Autenticação | 7 | 7 | Rotas protegidas devem redirecionar para login; login públic |
| Headers de segurança | 3 | 3 | X-Content-Type-Options, X-Frame-Options, X-XSS-Protection. |
| IDOR | 1 | 1 | Acesso a recurso de outro cliente (empresa) deve ser negado  |
| Sessão | 1 | 1 | Logout deve invalidar a sessão. |
| Sessão / Autorização | 3 | 3 | APIs que exigem cod_cliente devem retornar 403 sem sessão vá |
| Validação de entrada | 3 | 3 | Inputs maliciosos (SQL, XSS) não devem causar 500 nem vazar  |

---

## 3. Tabela de verificações

| Categoria | Verificação | Detalhe | Esperado | Resultado | OK | Observação |
|-----------|-------------|---------|----------|-----------|---|------------|
| Autenticação | Acesso não autenticado a Home | GET /Home/ | Redirect para Login (302) | 302 | Sim | /gdf/Login/?next=/Home/ |
| Autenticação | Acesso não autenticado a Usuários | GET /usuarios/ | Redirect para Login (302) | 302 | Sim | /gdf/Login/?next=/usuarios/ |
| Autenticação | Acesso não autenticado a Empresas | GET /empresas/ | Redirect para Login (302) | 302 | Sim | /gdf/Login/?next=/empresas/ |
| Autenticação | Acesso não autenticado a Relatório Fiscal | GET /Relatorio/ | Redirect para Login (302) | 302 | Sim | /gdf/Login/?next=/Relatorio/ |
| Autenticação | Acesso não autenticado a API Relatório NFe | GET /api/relatorio/nfe/ | Redirect para Login (302) | 302 | Sim | /gdf/Login/?next=/api/relatorio/nfe/ |
| Autenticação | Acesso não autenticado a Painel Reprocessamento | GET /Reprocessamento/Painel/ | Redirect para Login (302) | 302 | Sim | /gdf/Login/?next=/Reprocessamento/Painel |
| Autenticação | Página de login acessível (GET) | GET /Login/ | 200 | 200 | Sim | - |
| Sessão / Autorização | API CargaXml Jobs sem cliente na sessão | GET /api/cargaxml/jobs/ (autenticado, sem cod_clie | 403 | 403 | Sim | - |
| Sessão / Autorização | API CargaXml Parâmetros sem cliente na sessão | GET /api/cargaxml/parametros/ (autenticado, sem co | 403 | 403 | Sim | - |
| Sessão / Autorização | API Reprocessamento Lotes sem cliente na sessão | GET /api/reprocessamento/lotes/ (autenticado, sem  | 403 | 403 | Sim | - |
| IDOR | Acesso a empresa por cod_empresa arbitrário | GET /empresa/COD_NAO_PERTENCE/ (sem cliente ou out | 403 | 403 | Sim | - |
| Validação de entrada | Busca maliciosa rejeitada/sanitizada (SQL-like OR) | GET /api/relatorio/nfe/?busca=... | Não 500, sem vazamento de stack | 200 | Sim | 200 |
| Validação de entrada | Busca maliciosa rejeitada/sanitizada (SQL DROP) | GET /api/relatorio/nfe/?busca=... | Não 500, sem vazamento de stack | 400 | Sim | 400 |
| Validação de entrada | Busca maliciosa rejeitada/sanitizada (UNION SELECT) | GET /api/relatorio/nfe/?busca=... | Não 500, sem vazamento de stack | 400 | Sim | 400 |
| Headers de segurança | X-Content-Type-Options: nosniff | Resposta GET /Login/ | Presente | OK | Sim | nosniff |
| Headers de segurança | X-Frame-Options (SAMEORIGIN ou DENY) | Resposta GET /Login/ | Presente | OK | Sim | SAMEORIGIN |
| Headers de segurança | X-XSS-Protection | Resposta GET /Login/ | Presente | OK | Sim | 1; mode=block |
| Sessão | Logout invalida sessão | GET /Logout/ depois GET /Home/ | Redirect para login | 302 | Sim | /gdf/Login/?next=/Home/ |

---

## 4. Detalhes por categoria

### Autenticação

- **✅** Acesso não autenticado a Home: esperado Redirect para Login (302), obtido 302. /gdf/Login/?next=/Home/
- **✅** Acesso não autenticado a Usuários: esperado Redirect para Login (302), obtido 302. /gdf/Login/?next=/usuarios/
- **✅** Acesso não autenticado a Empresas: esperado Redirect para Login (302), obtido 302. /gdf/Login/?next=/empresas/
- **✅** Acesso não autenticado a Relatório Fiscal: esperado Redirect para Login (302), obtido 302. /gdf/Login/?next=/Relatorio/
- **✅** Acesso não autenticado a API Relatório NFe: esperado Redirect para Login (302), obtido 302. /gdf/Login/?next=/api/relatorio/nfe/
- **✅** Acesso não autenticado a Painel Reprocessamento: esperado Redirect para Login (302), obtido 302. /gdf/Login/?next=/Reprocessamento/Painel/
- **✅** Página de login acessível (GET): esperado 200, obtido 200. -

### Headers de segurança

- **✅** X-Content-Type-Options: nosniff: esperado Presente, obtido OK. nosniff
- **✅** X-Frame-Options (SAMEORIGIN ou DENY): esperado Presente, obtido OK. SAMEORIGIN
- **✅** X-XSS-Protection: esperado Presente, obtido OK. 1; mode=block

### IDOR

- **✅** Acesso a empresa por cod_empresa arbitrário: esperado 403, obtido 403. -

### Sessão

- **✅** Logout invalida sessão: esperado Redirect para login, obtido 302. /gdf/Login/?next=/Home/

### Sessão / Autorização

- **✅** API CargaXml Jobs sem cliente na sessão: esperado 403, obtido 403. -
- **✅** API CargaXml Parâmetros sem cliente na sessão: esperado 403, obtido 403. -
- **✅** API Reprocessamento Lotes sem cliente na sessão: esperado 403, obtido 403. -

### Validação de entrada

- **✅** Busca maliciosa rejeitada/sanitizada (SQL-like OR): esperado Não 500, sem vazamento de stack, obtido 200. 200
- **✅** Busca maliciosa rejeitada/sanitizada (SQL DROP): esperado Não 500, sem vazamento de stack, obtido 400. 400
- **✅** Busca maliciosa rejeitada/sanitizada (UNION SELECT): esperado Não 500, sem vazamento de stack, obtido 400. 400

---

## 5. Conclusão e recomendações

- **Total:** 18/18 verificações passaram.

- **Recomendações:** Manter CSRF habilitado em produção; não desativar validação de `busca` nas APIs; revisar periodicamente decoradores IDOR em novas views; manter headers de segurança (middleware).
