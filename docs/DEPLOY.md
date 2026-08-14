# Deploy em QAS

O ambiente QAS usa Docker Compose, PostgreSQL externo, Redis interno, Gunicorn, Celery e Streamlit. A publicação externa é feita pelo Nginx do host em `https://homo.processit.com.br/gdf/`.

## Requisitos

- Docker Engine e Docker Compose Plugin.
- PostgreSQL acessível pelo host Docker, com os schemas usados pelo projeto.
- SAP NetWeaver RFC SDK em `nwrfcsdk/` quando a integração SAP estiver habilitada.
- Certificado HTTPS configurado no Nginx do host.

O Compose não cria PostgreSQL. O banco é configurado pelas variáveis `DB_*` do arquivo `gdf/.env`.

## Configuração

Copie `gdf/.env.qas.example` para `gdf/.env` no servidor e substitua todos os placeholders. Nunca versione o arquivo real:

```dotenv
APP_ENV=qas
DEBUG=False
SECRET_KEY=<chave-django-aleatoria>
ALLOWED_HOSTS=homo.processit.com.br,localhost,127.0.0.1
DB_ENGINE=django.db.backends.postgresql
DB_NAME=GDF_QAS
DB_USER=<usuario>
DB_PASSWORD=<senha>
DB_HOST=<host-postgresql>
DB_PORT=5432
CERT_PASSWORD_FERNET_KEY=<chave-fernet>
CERT_PASSWORD_FERNET_KEY=<chave-fernet>
FORCE_SCRIPT_NAME=/gdf
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
CSRF_TRUSTED_ORIGINS=https://homo.processit.com.br
STREAMLIT_BASE_URL=https://homo.processit.com.br/gdf/streamlit
```

O Compose injeta automaticamente as URLs internas do Redis para cache e Celery. Não use `localhost` para Redis dentro dos containers.

## Subida da aplicação

Na raiz do projeto:

```bash
docker compose config
docker compose build
docker compose run --rm django python manage.py check --deploy
docker compose run --rm django python manage.py migrate
docker compose up -d
docker compose ps
```

Os serviços publicados são:

- Django/Gunicorn: `8500`
- Streamlit: `8600`
- Redis: somente na rede interna do Compose

O `Dockerfile` executa `collectstatic` durante o build usando a configuração PostgreSQL e valores descartáveis de build. Nenhuma conexão com o banco real é feita nessa etapa.

## Verificações

```bash
sudo docker compose ps
sudo docker compose logs --tail=100 django
curl -I http://127.0.0.1:8500/
curl -I http://127.0.0.1:8600/
```

Os healthchecks devem ficar `healthy`. Os arquivos estáticos devem retornar o MIME correspondente, por exemplo `text/css` para CSS e `image/png` para imagens.

## Nginx reverso e HTTPS

O proxy deve encaminhar:

- `/gdf/` para `http://127.0.0.1:8500/gdf/`;
- `/gdf/streamlit/` para `http://127.0.0.1:8600/`;
- `/gdf/static/` para os estáticos da aplicação ou para o Django, conforme a estratégia escolhida.

O bloco `/gdf/streamlit/` deve ser avaliado antes do bloco genérico `/gdf/`. Para acesso público, use HTTPS; o acesso HTTP por IP é apenas para diagnóstico local.

Exemplo mínimo de roteamento:

```nginx
location /gdf/streamlit/ {
	proxy_pass http://127.0.0.1:8600/;
	proxy_http_version 1.1;
	proxy_set_header Host $host;
	proxy_set_header X-Forwarded-Proto $scheme;
	proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
	proxy_set_header Upgrade $http_upgrade;
	proxy_set_header Connection "upgrade";
	proxy_read_timeout 300s;
}

location /gdf/ {
	proxy_pass http://127.0.0.1:8500;
	proxy_set_header Host $host;
	proxy_set_header X-Forwarded-Proto $scheme;
	proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
	proxy_read_timeout 300s;
}
```

## Operação

```bash
sudo docker compose logs -f django
sudo docker compose logs -f celery_worker
sudo docker compose restart django streamlit celery_worker celery_beat
sudo docker compose down
```

Não execute `docker compose down -v` em produção sem confirmar o impacto: isso remove os volumes persistentes do Redis e do schedule do Celery Beat.

## Segurança QAS

- Rotacione imediatamente qualquer credencial que tenha sido exposta.
- Restrinja `ALLOWED_HOSTS` aos domínios reais.
- Use `DEBUG=False`.
- Não publique a porta do Redis fora da rede Docker.
- Mantenha backups do PostgreSQL e dos volumes persistentes.
- Gere uma nova `SECRET_KEY` e uma nova `CERT_PASSWORD_FERNET_KEY` específicas do QAS.
- Não inclua o SDK SAP, certificados ou chaves em commits; disponibilize-os por meio do mecanismo aprovado pela infraestrutura.
- Confirme que `docker compose ps` mostra Redis, Django, Streamlit, Worker e Beat saudáveis antes do teste funcional.
