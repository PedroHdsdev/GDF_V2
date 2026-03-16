# Deploy – GDF_V2

Requisitos, variáveis de ambiente, instalação, execução do servidor, Celery, HTTPS e checklist para colocar o GDF_V2 em produção.

---

## 1. Requisitos

### 1.1 Software

- **Python:** 3.10 ou superior (conforme `requirements.txt`).
- **PostgreSQL:** versão compatível com Django 6 e psycopg2; o projeto usa um único banco com múltiplos schemas (public, nfe, cte, nfse, sped_fiscal, sped_contribuicao, reprocessamento). O usuário do banco deve ter permissão para criar e alterar schemas e tabelas.
- **Redis:** recomendado como broker do Celery quando houver carga XML agendada. Sem Redis, é possível usar o script `run_carga_scheduler.py` como agendador alternativo (ver seção 5).
- **Servidor:** Linux recomendado para produção. A aplicação Django é servida via **Gunicorn** (ou outro WSGI); na frente, use **Nginx** (ou Apache) como proxy reverso e para servir arquivos estáticos e SSL.
- **SAP (opcional):** integração SAP via PyRFC exige **SAP NetWeaver RFC SDK** instalado no servidor e configurado (bibliotecas nativas). Consulte documentação do PyRFC e do SAP.

### 1.2 Dependências Python

As principais estão em `requirements.txt` na raiz do repositório, por exemplo: Django 6.x, psycopg2, celery, redis, PyJWT, PyRFC (opcional), streamlit (para os dashboards externos), etc. Instale com:

```bash
pip install -r requirements.txt
```

---

## 2. Variáveis de ambiente

Configure as variáveis abaixo em **.env** (ou no ambiente do sistema / do processo), **sem commitar** o arquivo `.env` no repositório.

### 2.1 Django e banco (obrigatórias em produção)

| Variável | Obrigatória | Descrição | Exemplo |
|----------|-------------|-----------|---------|
| **SECRET_KEY** | Sim (produção) | Chave secreta do Django; em produção **sempre** definir no .env | string longa e aleatória |
| **DEBUG** | Sim | Em produção use **False** | False |
| **ALLOWED_HOSTS** | Sim | Hosts permitidos (vírgula) | homo.processit.com.br,localhost |
| **DB_ENGINE** | Sim | Engine do banco | django.db.backends.postgresql |
| **DB_NAME** | Sim | Nome do banco | gdf_db |
| **DB_USER** | Sim | Usuário | gdf_user |
| **DB_PASSWORD** | Sim | Senha | *** |
| **DB_HOST** | Sim | Host | localhost |
| **DB_PORT** | Sim | Porta | 5432 |

O `settings.py` usa `environ.Env.read_env(BASE_DIR / '.env')`. **Não commitar** o arquivo `.env`.

### 2.2 Segurança e URL

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| **CSRF_TRUSTED_ORIGINS** | Origens HTTPS permitidas para CSRF (vírgula) | https://homo.processit.com.br |
| **FORCE_SCRIPT_NAME** | Subpath da aplicação (vazio = raiz) | /gdf |

### 2.3 Celery e cache (produção)

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| **CELERY_BROKER_URL** | URL do broker (Redis) | redis://localhost:6379/0 |
| **CELERY_RESULT_BACKEND** | Backend de resultados | redis://localhost:6379/1 |
| **CACHE_URL** ou **REDIS_URL** | Cache compartilhado entre workers (Redis) | redis://localhost:6379/2 |

Se `CACHE_URL` ou `REDIS_URL` estiver definido com URL redis, o Django usa Redis para cache; caso contrário usa cache em memória (apenas um worker).

O `settings.py` define `CELERY_BROKER_URL` e `CELERY_RESULT_BACKEND`. O agendamento (beat) usa `CELERY_BEAT_SCHEDULE` (ex.: `scan_cargaxml_params` a cada minuto).

### 2.5 SAP (opcional)

Se houver integração SAP, as credenciais costumam ficar no banco (modelo `ConexaoSap` por cliente). Variáveis de ambiente podem ser usadas para override ou para um usuário genérico; isso depende da implementação. Não armazene senhas SAP em arquivos versionados.

### 2.6 Dashboard (Streamlit) e outras

Configure no **.env**:

- **STREAMLIT_IFRAME_URL:** URL do Streamlit para o iframe do Dashboard. Produção: `https://homo.processit.com.br/streamlit`. Dev: `http://127.0.0.1:8600`.
- **CSP_FRAME_SRC_EXTRA:** Origens extras para o CSP `frame-src` (iframe), separadas por vírgula. Ex.: `https://homo.processit.com.br`, `https://localhost:8600`.
- **STREAMLIT_FRAME_ORIGINS:** se usado no middleware de security headers, lista de origens para iframe.
- Demais variáveis referenciadas no `settings.py` (e-mail, cache, etc.) conforme o ambiente.

---

## 3. Instalação passo a passo

Assumindo raiz do repositório em `/app/gdf_v2` (ou caminho equivalente):

```bash
cd /app/gdf_v2
python -m venv venv
source venv/bin/activate   # Linux/macOS; no Windows: venv\Scripts\activate
pip install -r requirements.txt
cd GDF_PJT
```

Configurar `.env` (ou variáveis) com SECRET_KEY, DEBUG=False, ALLOWED_HOSTS, DATABASE e, se for usar Celery, CELERY_BROKER_URL.

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

Criar superusuário se necessário:

```bash
python manage.py createsuperuser
```

---

## 4. Execução do servidor de aplicação

### 4.1 Gunicorn

Na pasta `GDF_PJT` (ou na raiz, conforme o `gunicorn_config.py`):

```bash
gunicorn -c gunicorn_config.py GDF_PJT.wsgi:application
```

Ou, de forma direta:

```bash
gunicorn --bind 0.0.0.0:8000 --workers 4 GDF_PJT.wsgi:application
```

O `run_gunicorn.sh` pode encapsular o comando; use-o se já existir no projeto.

### 4.2 Nginx (proxy reverso e estáticos)

- **Proxy:** encaminhar requisições para o Gunicorn. No projeto o Gunicorn usa a **porta 8500** (`bin/start_gdf.sh` e `etc/gunicorn_config.py`).
- **Streamlit:** usado para dashboards de análise de **qualquer solução** (não só a solução Dashboard). Uma única URL base (ex.: `/gdf/streamlit/`) atende todos; o dashboard exibido vem do parâmetro `?dashboard=`. É **obrigatório** ter um `location` para esse path fazendo proxy para o processo Streamlit (porta 8600). Sem isso, o iframe retorna **404**. Ver também `documentacao_md/README_streamlit.md` para adicionar novos dashboards por solução.
- **Estáticos:** `alias` (ou `root`) apontando para o diretório de `collectstatic` (ex.: `staticfiles/`).
- **SSL:** configurar certificado e listen 443; redirecionar HTTP para HTTPS se desejado.

Exemplo mínimo com app na **raiz** (ajuste paths e domínio):

```nginx
server {
    listen 443 ssl;
    server_name seu-dominio.com;
    ssl_certificate     /caminho/cert.crt;
    ssl_certificate_key /caminho/cert.key;
    location /static/ {
        alias /app/gdf_v2/GDF_PJT/staticfiles/;
    }
    location /streamlit/ {
        proxy_pass http://127.0.0.1:8600/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
    location / {
        proxy_pass http://127.0.0.1:8500;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Exemplo com aplicação sob o prefixo **`/gdf`** (ex.: `FORCE_SCRIPT_NAME=/gdf`):

- `.env`: use a URL completa do iframe, ex. `STREAMLIT_BASE_URL=https://homo.processit.com.br/gdf/streamlit`.
- Nginx: o proxy do Streamlit **deve vir antes** do `location /gdf/`, para que `/gdf/streamlit/` não seja enviado ao Django.

```nginx
server {
    listen 443 ssl;
    server_name homo.processit.com.br;
    ssl_certificate     /caminho/cert.crt;
    ssl_certificate_key /caminho/cert.key;

    location /gdf/static/ {
        alias /app/gdf_v2/GDF_PJT/staticfiles/;
    }
    # Streamlit: obrigatório para o iframe do Dashboard (antes do location /gdf/)
    location /gdf/streamlit/ {
        proxy_pass http://127.0.0.1:8600/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
    location /gdf/ {
        proxy_pass http://127.0.0.1:8500/gdf/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Se o iframe continuar com 404:** inspecione o `src` do iframe no navegador (botão direito no quadro → Inspecionar). A URL deve ser exatamente a que está no Nginx (ex.: `https://homo.processit.com.br/gdf/streamlit/`). Confirme que existe um `location` para esse path fazendo proxy para `http://127.0.0.1:8600/` e que o processo Streamlit está em execução na porta 8600.

### 4.3 404 no iframe do Dashboard (JSON "The requested URL was not found...")

Quando o iframe do Dashboard (Compras/Vendas) retorna **404** com corpo em JSON (`"detail": "The requested URL was not found on the server."`), a requisição está indo para o **Django** em vez do **Streamlit**. O proxy reverso não está encaminhando o path do Streamlit para a porta 8600.

**Checklist no servidor:**

1. **Confirmar a URL do iframe**  
   No navegador: botão direito no quadro do dashboard → **Inspecionar** → no `<iframe>` veja o atributo `src`.  
   Será algo como:
   - `https://seu-dominio.com/gdf/streamlit/?token=...` (app em `/gdf`), ou  
   - `https://seu-dominio.com/streamlit/?token=...` (app na raiz).

2. **Configurar o Nginx para esse path exato**
   - Se o `src` for `.../gdf/streamlit/`, o Nginx **precisa** de um bloco **`location /gdf/streamlit/`** com `proxy_pass http://127.0.0.1:8600/;` (e os headers de WebSocket do exemplo acima). Esse `location` deve vir **antes** do `location /gdf/`.
   - Se o `src` for `.../streamlit/`, use **`location /streamlit/`** com o mesmo `proxy_pass`.

3. **Garantir que o Streamlit está em execução** na porta 8600 (ex.: `sudo systemctl status gdf` deve mostrar o processo `streamlit run ... --server.port 8600`).

4. **Alinhar o `.env` com o path do Nginx**  
   A URL do iframe vem de **`STREAMLIT_BASE_URL`** no `.env`. Se a aplicação está em `/gdf/`, use:
   ```env
   STREAMLIT_BASE_URL=https://seu-dominio.com/gdf/streamlit
   ```
   (sem barra no final; uma única URL, sem vírgulas.)

5. **Recarregar o Nginx** após alterar a config:
   ```bash
   sudo nginx -t && sudo systemctl reload nginx
   ```

---

## 5. Celery (worker e beat)

Se usar carga XML agendada com Celery:

1. **Redis** em execução e `CELERY_BROKER_URL` configurado.
2. **Worker:** em um terminal (ou processo gerenciado por systemd/supervisor):

   ```bash
   cd /app/gdf_v2/GDF_PJT
   celery -A GDF_PJT worker -l info
   ```

3. **Beat:** em outro processo, para agendar `scan_cargaxml_params`:

   ```bash
   celery -A GDF_PJT beat -l info
   ```

Ou use um único comando que inicia worker + beat, se disponível na documentação do Celery para a sua versão.

### 5.1 Agendador alternativo (sem Redis/Celery)

O projeto inclui `run_carga_scheduler.py`, que consulta a tabela `ParametroCargaXml` e executa a tarefa de processamento no horário configurado (sem fila). Para usar:

```bash
cd /app/gdf_v2/GDF_PJT
python run_carga_scheduler.py
```

Mantenha esse script rodando (ex.: via systemd ou supervisor). Ele verifica a cada 30 segundos se há parâmetros para executar; após executar um parâmetro no dia, não repete no mesmo dia (conforme lógica do script). Observe que no script pode existir referência a `param.cliente`; se o model usar `gdfcliente`, será necessário ajustar o script (ex.: `param.gdfcliente`).

---

## 6. HTTPS e certificados

- Em produção, **sirva sempre por HTTPS**. Use Nginx (ou Apache) para terminar SSL.
- Certificados: **Let's Encrypt** (certbot) ou certificado corporativo. Os arquivos `cert.crt` e `cert.key` na raiz do projeto são exemplos; em produção use paths configurados no Nginx.
- No **Django**, com `DEBUG=False`, configure no `settings.py`:
  - **SECURE_SSL_REDIRECT = True** (redirecionar HTTP → HTTPS).
  - **SESSION_COOKIE_SECURE = True**
  - **CSRF_COOKIE_SECURE = True**
  - **SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')** quando o proxy envia o header correto.

---

## 7. Checklist de deploy

- [ ] **Python 3.10+** e dependências instaladas (`pip install -r requirements.txt`).
- [ ] **PostgreSQL** criado; usuário com permissão para schemas e tabelas; **migrate** executado.
- [ ] **DEBUG=False**, **ALLOWED_HOSTS** com o(s) domínio(s) de produção, **SECRET_KEY** forte e único.
- [ ] **collectstatic** executado; Nginx (ou outro) servindo `/static/` a partir do diretório de static files.
- [ ] **Gunicorn** em execução (ou outro WSGI); Nginx faz proxy para a aplicação e envia headers (Host, X-Forwarded-For, X-Forwarded-Proto).
- [ ] **HTTPS** ativo no proxy; certificados válidos; Django com SECURE_*, SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE.
- [ ] **Streamlit** em execução (porta 8600) e **Nginx** com `location /streamlit/` (ou path equivalente) em proxy para o processo; `STREAMLIT_BASE_URL` no `.env` com a URL completa do iframe.
- [ ] **Celery worker e beat** rodando (se usar carga agendada) ou **run_carga_scheduler.py** em execução.
- [ ] **Redis** acessível quando Celery estiver em uso.
- [ ] **Logs** configurados (Django LOGGING e logs do Gunicorn/Nginx); **monitoramento** (opcional: saúde da aplicação, fila Celery, disco para diretórios de carga).
- [ ] **Backup** do banco e política de retenção definidos.
- [ ] **SAP:** se usar PyRFC, RFC SDK instalado e testado; credenciais por cliente no banco (ConexaoSap) ou via variáveis seguras.

---

## 8. Referências

- Estrutura do projeto: [ARQUITETURA.md](ARQUITETURA.md).
- Documentação geral: [DOCUMENTACAO_PROJETO_GDF.md](DOCUMENTACAO_PROJETO_GDF.md).

---

*Última atualização: Março 2026*
