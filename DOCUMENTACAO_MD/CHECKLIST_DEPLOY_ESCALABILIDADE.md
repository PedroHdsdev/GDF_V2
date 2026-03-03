# 📋 Checklist de Deploy & Escalabilidade para 100+ Usuários

## PRÉ-REQUISITOS

- [ ] PostgreSQL 12+
- [ ] Redis 6+
- [ ] Python 3.9+
- [ ] Host web server / load balancer (Nginx/Apache/Cloud LB)
- [ ] Docker & Docker Compose

---

## FASE 1: Preparação Local (1-2 dias)

### Segurança
- [ ] Criar `.env` com credenciais seguras
- [ ] Gerar novo `SECRET_KEY` (min 50 caracteres)
- [ ] Adicionar `.env` ao `.gitignore`
- [ ] Implementar rate limiting em login
- [ ] Adicionar CSRF tokens em AJAX
- [ ] Validar IDOR em todas as views de atualização
- [ ] Implementar Security Headers (CSP, X-Frame-Options, etc.)

### Performance Local
- [ ] Instalar Redis localmente: `sudo apt-get install redis-server`
- [ ] Configurar cache em `settings.py`
- [ ] Corrigir N+1 queries (prefetch_related)
- [ ] Implementar paginação backend
- [ ] Adicionar índices de banco
- [ ] Testar queries com `django-debug-toolbar`

**Validar com script de teste**:
```bash
python test_security_config.py
```

---

## FASE 2: Setup em Staging (3-5 dias)

### 2.1 PostgreSQL com Replicação

**Instalar PostgreSQL Server**:
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# Verificar
psql --version
```

**Criar banco de dados**:
```bash
sudo -u postgres createdb gdf_dev
sudo -u postgres createuser gdf_user
sudo -u postgres psql -c "ALTER USER gdf_user WITH PASSWORD 'senha_segura';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE gdf_dev TO gdf_user;"
```

**Atualizar .env**:
```bash
DB_HOST=localhost
DB_NAME=gdf_dev
DB_USER=gdf_user
DB_PASSWORD=senha_segura
```

### 2.2 Redis Setup

```bash
# Instalar
sudo apt-get install redis-server

# Iniciar
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Testar
redis-cli ping  # Deve retornar PONG
```

### 2.3 Django Migrations

```bash
cd GDF_PJT
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
```

### 2.4 Gunicorn Setup

```bash
pip install gunicorn

# Testar localmente
gunicorn -c gunicorn_config.py GDF_PJT.wsgi:application

# Verificar em outro terminal
curl http://localhost:8000
```

### 2.5 Host load balancer / reverse proxy (optional)

The host should provide TLS termination and act as a reverse proxy to local
Gunicorn workers. The repository no longer contains a default Nginx config —
configure the host web server (Nginx, Apache or cloud LB) with an upstream to
`127.0.0.1:8500` (or 8000/8001/8002 for multiple instances), enable gzip and
static file caching on the host, and ensure `X-Forwarded-*` headers are set.

If you need a sample configuration for a particular host web server, request
it and it will be provided separately; keeping host config out of the repo
avoids accidental overwrites of production settings.
        location /login/ {
            proxy_pass http://django_app;
            proxy_set_header Host $host;
            
            # Rate limiting para login
            limit_req zone=login_limit burst=3 nodelay;
        }

        location /api/ {
            proxy_pass http://django_app;
            proxy_set_header Host $host;
            
            # Rate limiting para API
            limit_req zone=api_limit burst=20 nodelay;
        }

        # Static files
        location /static/ {
            alias /var/www/gdf/staticfiles/;
            expires 30d;
            add_header Cache-Control "public, immutable";
        }

        # Media files
        location /media/ {
            alias /var/www/gdf/media/;
            expires 7d;
        }

        # Health check
        location /health/ {
            access_log off;
            proxy_pass http://django_app;
            proxy_set_header Host $host;
        }
    }
}
```

**Habilitar Nginx**:
```bash
sudo systemctl start nginx
sudo systemctl enable nginx
sudo systemctl reload nginx

# Verificar
sudo systemctl status nginx
```

### 2.6 Systemd Services para Gunicorn

**Arquivo: `/etc/systemd/system/gdf-gunicorn.service`**
```ini
[Unit]
Description=GDF Gunicorn Application
After=network.target postgresql.service redis-server.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/gdf/GDF_PJT
ExecStart=/var/www/gdf/venv/bin/gunicorn -c gunicorn_config.py GDF_PJT.wsgi:application
Restart=on-failure
RestartSec=5s
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Ativar serviço**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable gdf-gunicorn
sudo systemctl start gdf-gunicorn
sudo systemctl status gdf-gunicorn
```

### 2.7 Celery Setup (Async Tasks)

```bash
pip install celery redis
```

**Arquivo: `/etc/systemd/system/gdf-celery.service`**
```ini
[Unit]
Description=GDF Celery Worker
After=network.target redis-server.service postgresql.service

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/var/www/gdf
ExecStart=/var/www/gdf/venv/bin/celery -A GDF_PJT worker --loglevel=info --concurrency=4 --detach

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable gdf-celery
sudo systemctl start gdf-celery
```

---

## FASE 3: Monitoramento & Observabilidade (1 semana)

### 3.1 Logs Centralizados

**Instalar ELK Stack** (ou usar Papertrail):
```bash
docker run -d -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:7.14.0
docker run -d -p 5601:5601 docker.elastic.co/kibana/kibana:7.14.0
```

**settings.py**:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter'
        },
    },
    'handlers': {
        'elasticsearch': {
            'level': 'INFO',
            'class': 'logstash_formatter.LogstashFormatterHandler',
            'host': 'localhost',
            'port': 5000,
            'version': 1,
            'message_type': 'django',
            'tags': ['django'],
        },
    },
    'root': {
        'handlers': ['elasticsearch'],
        'level': 'INFO',
    },
}
```

### 3.2 Monitoramento de Performance

**Instalar Prometheus + Grafana**:
```bash
pip install django-prometheus

# settings.py
INSTALLED_APPS = [
    'django_prometheus',
    # ...
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    # ...
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

# urls.py
urlpatterns = [
    path('metrics/', include('django_prometheus.urls')),
]
```

### 3.3 Alertas

**Usar Sentry para erro tracking**:
```bash
pip install sentry-sdk

# settings.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=env('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,
    send_default_pii=False
)
```

---

## FASE 4: Teste de Carga (2-3 dias)

### 4.1 Teste com Locust

**Arquivo: `locustfile.py`**
```python
from locust import HttpUser, task, between
import random

class GDFUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login antes de começar"""
        self.client.post("/Login/", {
            "Username": f"user_{random.randint(1, 100)}",
            "password": "senha123"
        })
    
    @task(2)
    def listar_usuarios(self):
        page = random.randint(1, 5)
        self.client.get(f"/usuarios/?page={page}")
    
    @task(2)
    def listar_empresas(self):
        page = random.randint(1, 5)
        self.client.get(f"/empresas/?page={page}")
    
    @task(1)
    def listar_clientes(self):
        self.client.get("/clientes/")
    
    @task(1)
    def dashboard_vendas(self):
        self.client.get("/dashboard/vendas/")
```

**Executar teste**:
```bash
pip install locust

# 100 usuários, ramp-up 10 por segundo, 5 minutos
locust -f locustfile.py \
    --host=https://gdf.seu-dominio.com \
    -u 100 \
    -r 10 \
    --run-time 5m \
    --headless \
    --csv=results
```

**Métricas esperadas**:
- Latência P95: < 1s
- Latência P99: < 2s
- Taxa de erro: < 0.5%
- Throughput: > 50 req/s

---

## FASE 5: Produção (Final)

### 5.1 Checklist Final

- [ ] SSL/TLS configurado (Let's Encrypt)
- [ ] Backup automático PostgreSQL (diário)
- [ ] Backup automático Redis
- [ ] Logs centralizados funcionando
- [ ] Alertas configurados
- [ ] Monitoramento ativo
- [ ] Plano de disaster recovery documentado
- [ ] Runbook de troubleshooting criado
- [ ] Equipe treinada em deploy
- [ ] Teste de failover executado

### 5.2 Database Replication Setup

**Master-Slave Replication**:

**Master (`/etc/postgresql/13/main/postgresql.conf`)**:
```conf
wal_level = replica
max_wal_senders = 5
max_replication_slots = 5
hot_standby = on
```

**Slave**:
```bash
sudo -u postgres pg_basebackup -h master_ip -U replication_user -v -P -W -D /var/lib/postgresql/13/main -R

# Iniciar replica
sudo systemctl start postgresql
```

### 5.3 Auto-Scaling (Opcional)

**Docker Swarm or Kubernetes**:
```bash
# Docker Swarm
docker swarm init
docker stack deploy -c docker-compose.yml gdf

# Kubernetes
kubectl apply -f k8s-deployment.yaml
kubectl autoscale deployment gdf-django --min=2 --max=10 --cpu-percent=70
```

---

## 🆘 Troubleshooting

### Django não conecta PostgreSQL
```bash
# Testar conexão
psql -h localhost -U gdf_user -d gdf_dev

# Verificar em Django
python manage.py dbshell
```

### Redis não conecta
```bash
redis-cli ping
redis-cli info server
```

### Gunicorn crashes
```bash
# Ver logs
journalctl -u gdf-gunicorn -n 50

# Testar gunicorn
gunicorn --check-config -c gunicorn_config.py GDF_PJT.wsgi
```

### Nginx 502 Bad Gateway
```bash
# Verificar upstream
curl http://127.0.0.1:8000

# Ver logs nginx
tail -f /var/log/nginx/error.log

# Reiniciar gunicorn
sudo systemctl restart gdf-gunicorn
```

---

## 📊 Capacidade Esperada Após Otimizações

| Métrica | Antes | Depois |
|---------|-------|--------|
| Usuários simultâneos | 10 | 100+ |
| Tempo resposta P95 | 5s | <1s |
| Requisições/segundo | 10 | 100+ |
| Uso de memória | 50% | 30% |
| CPU | 80% | 40% |
| Queries por página | 50+ | 3-5 |

---

