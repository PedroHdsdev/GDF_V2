# Streamlit GDF – Dashboards por solução

O Streamlit no GDF é usado como **motor de dashboards de análise** para **qualquer solução**, não só para a solução "Dashboard". Cada solução pode ter um ou mais dashboards (ex.: Vendas, Compras, Reprocessamento, etc.).

## Arquitetura

- **Um único processo Streamlit** (uma porta, ex.: 8600), uma **única URL base** no proxy (ex.: `/gdf/streamlit/`).
- **Vários “apps”** no mesmo processo: qual dashboard rodar vem do **token JWT** (`tipo_relatorio`). O Django já informa no token qual dashboard apresentar; o iframe usa só `?token=...`.
- Opcionalmente, o parâmetro **`?dashboard=Chave`** na URL pode sobrescrever o que está no token (ex.: para testes).

## Como adicionar um novo dashboard (de qualquer solução)

1. **Streamlit**
   - Crie uma classe em `dashboards/` herdando de `BaseDashboard` (ex.: `dashboards/reprocessamento.py`).
   - Registre em **`core/factory.py`** no `DASHBOARD_REGISTRY` com uma chave (ex.: `"Reprocessamento"`).

2. **Django**
   - Crie uma view que gera o token com **`tipo_relatorio='Chave'`** (a chave do dashboard), chama `_streamlit_iframe_url(request)` e renderiza um template com iframe.
   - Passe no context: `streamlit_iframe_url`, `token`. O dashboard é definido pelo token.
   - Adicione a rota em `urls.py` e o item no menu da solução/subsolução.

3. **Template**
   - Iframe com `src="{{ streamlit_iframe_url }}/?token={{ token }}"`. O Streamlit lê qual dashboard exibir do `tipo_relatorio` do token.

4. **Nginx**
   - Nenhuma alteração: o mesmo `location /gdf/streamlit/` atende todos os dashboards.

## Parâmetros da URL do iframe

| Parâmetro   | Obrigatório | Descrição |
|------------|-------------|-----------|
| `token`    | Sim         | JWT gerado pelo Django. Contém `tipo_relatorio`, que define qual dashboard exibir (chave no `DASHBOARD_REGISTRY`). |
| `dashboard`| Não         | Opcional: sobrescreve o dashboard (ex.: para testes). Se omitido, usa `tipo_relatorio` do token. |

Exemplo de URL (com app em `/gdf`):  
`https://seu-dominio.com/gdf/streamlit/?token=...`  
O dashboard (Vendas, Compras, etc.) é definido pelo `tipo_relatorio` já informado no token ao gerar com `ClGdf.gerar_token(..., tipo_relatorio='Chave')`.
