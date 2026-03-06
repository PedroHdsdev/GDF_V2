# ⚡ Quick Start - Começar em 30 Minutos

## 🎯 Objetivo
Implementar o **mínimo crítico** para ter o projeto seguro e pronto para staging.

## ⏱️ Timeline
- **5 min**: Ler este arquivo
- **10 min**: Preparar ambiente
- **15 min**: Implementar Fase 1

---

## 📋 Fase 1 - AGORA (15 minutos)

### 1. Criar `.env` na raiz do projeto

**Arquivo: `GDF_V2/.env` (NOVO)**
```bash
# Django
SECRET_KEY=seu-secret-key-super-seguro-min-50-chars-gfd-seu-secret-key-super-seguro
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=gdf_dev
DB_USER=postgres
DB_PASSWORD=sua_senha_postgres
DB_HOST=localhost
DB_PORT=5432

# Cache
REDIS_URL=redis://localhost:6379/1

# Security
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
SESSION_COOKIE_AGE=1800
```

### 2. Adicionar ao `.gitignore`

**Arquivo: `GDF_V2/.gitignore` - ADICIONAR**
```
.env
.env.local
*.env
```

### 3. Instalar dependências

```bash
cd GDF_V2
pip install python-dotenv django-redis redis
```

### 4. Atualizar settings.py

**Arquivo: `GDF_PJT/GDF_PJT/settings.py` - ADICIONAR NO TOPO (depois dos imports)**

```python
import environ
import os

# Load .env
env = environ.Env()
environ.Env.read_env(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

# USAR VARIÁVEIS
SECRET_KEY = env('SECRET_KEY')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# Database - ATUALIZAR
DATABASES = {
    'default': {
        'ENGINE': env('DB_ENGINE'),
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT'),
        'CONN_MAX_AGE': 600,  # Connection pooling
        'OPTIONS': {
            'options': '-c search_path=public,"nfe"'
        }
    }
}

# Cache - ADICIONAR
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Session - ADICIONAR
SESSION_ENGINE = 'django_redis.cache.session.SessionCache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=False)
CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=False)
```

### 5. Testar

```bash
cd GDF_PJT

# Verificar se carregou .env corretamente
python manage.py shell
>>> from django.conf import settings
>>> print(settings.DEBUG)  # Deve ser False
>>> print(settings.ALLOWED_HOSTS)  # Seus hosts
>>> exit()

# Testar migrações
python manage.py migrate
```

---

## 🔒 Fase 2 - Rate Limiting (10 minutos)

### 1. Criar middleware

**Arquivo: `app/middlewares/rate_limit.py` (NOVO)**
```python
from django.core.cache import cache
from django.http import HttpResponse
from functools import wraps
import time

def rate_limit(max_requests=10, time_window=60):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated:
                identifier = f"user_{request.user.id}"
            else:
                identifier = f"ip_{request.META.get('REMOTE_ADDR', 'unknown')}"
            
            cache_key = f"rate_limit_{identifier}_{request.path}"
            current = cache.get(cache_key, 0)
            
            if current >= max_requests:
                return HttpResponse("Too many requests", status=429)
            
            cache.set(cache_key, current + 1, time_window)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
```

### 2. Aplicar no login

**Arquivo: `app/views.py` - ATUALIZAR fn_view_login**
```python
from app.middlewares.rate_limit import rate_limit

@rate_limit(max_requests=5, time_window=60)
def fn_view_login(request):
    # ... código existente ...
    pass
```

### 3. Testar

```bash
python manage.py runserver

# Tentar logar mais de 5x em 1 min - deve dar 429
```

---

## 🛡️ Fase 3 - CSRF em AJAX (5 minutos)

### 1. Adicionar CSRF token

**Arquivo: `app/templates/Index_Base.html` - ADICIONAR NO <HEAD>**
```html
<head>
    {% csrf_token %}
    
    <script>
        function getCookie(name) {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }
        
        const csrftoken = getCookie('csrftoken');
        
        // Para jQuery AJAX
        $(document).ajaxSetup({
            beforeSend: function(xhr, settings) {
                if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            }
        });
    </script>
</head>
```

---

## 🔐 Fase 4 - IDOR Validation (5 minutos)

### Em `app/views.py` - ADICIONAR VALIDAÇÃO

```python
# Em fn_view_atualizar_empresa (linha ~380)
@login_required(login_url='Login')
@require_http_methods(["GET", "POST"])
def fn_view_atualizar_empresa(request, cod_empresa):
    cod_cliente = request.session.get('cod_cliente', None)
    if not cod_cliente:
        return JsonResponse({"erro": "Cliente não identificado"}, status=403)
    
    # ✅ VALIDAÇÃO IDOR
    empresa_pertence_cliente = Empresa.objects.filter(
        cod_empresa=cod_empresa,
        cliente__cod_cliente=cod_cliente
    ).exists()
    
    if not empresa_pertence_cliente:
        return JsonResponse({
            "erro": "Acesso negado: empresa não pertence ao seu cliente"
        }, status=403)
    
    # ... resto do código igual ...
```

---

## ✅ Validar Implementação

```bash
python test_security_config.py
```

Esperado:
```
✅ DEBUG OFF
✅ SECRET_KEY long enough
✅ XSS Filter
✅ X-Frame-Options: DENY
✅ SESSION SECURE
✅ CSRF SECURE
```

---

## 🚀 Próximo Passo

Depois de implementar estas 4 fases rápidas:

1. **Ler**: [GUIA_IMPLEMENTACAO_PRATICA.md](GUIA_IMPLEMENTACAO_PRATICA.md#2️⃣-priority-2---n1-queries--performance-3-5-dias)
2. **Implementar**: N+1 queries + Paginação + Cache (3-5 dias)
3. **Testar**: `python manage.py runserver` e verificar performance

---

## 📊 Checklist Rápido

- [ ] `.env` criado e no `.gitignore`
- [ ] `django-redis` instalado
- [ ] `settings.py` atualizado
- [ ] Rate limiting implementado
- [ ] CSRF em AJAX adicionado
- [ ] IDOR validação em views
- [ ] Testes passam
- [ ] Código commitado

---

## 💡 Dicas

**Se deu erro ao conectar PostgreSQL:**
```bash
# Verificar se PostgreSQL está rodando
sudo systemctl status postgresql

# Testar conexão
psql -h localhost -U postgres -d gdf_dev
```

**Se Redis não conecta:**
```bash
# Instalar Redis
sudo apt-get install redis-server

# Iniciar
sudo service redis-server start

# Testar
redis-cli ping  # Deve retornar PONG
```

**Se deu erro ao testar:**
```bash
# Entrar no shell Django
python manage.py shell

# Testar cache
from django.core.cache import cache
cache.set('test', 'valor', 60)
cache.get('test')  # Deve retornar 'valor'
```

---

## ❓ Dúvidas?

Consulte:
- **Como implementar**: [GUIA_IMPLEMENTACAO_PRATICA.md](GUIA_IMPLEMENTACAO_PRATICA.md)
- **Análise completa**: [AUDITORIA_SEGURANCA_PERFORMANCE.md](AUDITORIA_SEGURANCA_PERFORMANCE.md)
- **Deploy**: [CHECKLIST_DEPLOY_ESCALABILIDADE.md](CHECKLIST_DEPLOY_ESCALABILIDADE.md)

---

**⏱️ Tempo Total**: ~30 minutos para Fase 1-4 básica  
**🎯 Próximo Milestone**: Fases 5-8 em 3-4 dias  
**📈 Resultado**: Projeto seguro, escalável, pronto para 100+ usuários

