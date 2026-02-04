# 🛠️ Guia Prático - Implementações de Segurança & Performance para GDF_V2

## 1️⃣ PRIORITY 1 - Implementar IMEDIATAMENTE (1-2 dias)

### 1.1 Proteger Credenciais & SECRET_KEY

**Arquivo: `.env` (NOVO - criar na raiz do projeto)**
```bash
# Django settings
SECRET_KEY=gdf-secure-secret-key-min-50-chars-gfd-secure-secret-key-min-50-chars
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,gdf.seu-dominio.com

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=gdf_dev
DB_USER=postgres_user
DB_PASSWORD=senha_super_segura_aqui
DB_HOST=localhost
DB_PORT=5432

# Cache/Session
REDIS_URL=redis://localhost:6379/0

# Security
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
CSRF_COOKIE_SECURE=True

# File upload
DATA_UPLOAD_MAX_NUMBER_FILES=2000
SESSION_COOKIE_AGE=1800
```

**Arquivo: `.gitignore` (ATUALIZAR)**
```
.env
.env.local
.env.*.local
*.env
.vscode/settings.json
```

---

### 1.2 Implementar Rate Limiting - views.py

**Arquivo: `app/middlewares/rate_limit.py` (NOVO)**
```python
from django.core.cache import cache
from django.http import HttpResponse
from functools import wraps
from datetime import timedelta
import hashlib

def rate_limit(max_requests=10, time_window=60):
    """
    Decorator para rate limiting
    max_requests: número máximo de requisições
    time_window: janela de tempo em segundos
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Obter identificador (IP do usuário autenticado ou IP da requisição)
            if request.user.is_authenticated:
                identifier = f"user_{request.user.id}"
            else:
                identifier = f"ip_{request.META.get('REMOTE_ADDR', 'unknown')}"
            
            # Criar chave do cache
            cache_key = f"rate_limit_{identifier}_{request.path}"
            
            # Obter contador atual
            current_requests = cache.get(cache_key, 0)
            
            # Incrementar
            if current_requests >= max_requests:
                return HttpResponse("Rate limit exceeded", status=429)
            
            cache.set(cache_key, current_requests + 1, time_window)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
```

**Arquivo: `app/views.py` - ADICIONAR AO LOGIN (linha ~20)**
```python
from app.middlewares.rate_limit import rate_limit

@rate_limit(max_requests=5, time_window=60)  # 5 tentativas por minuto
def fn_view_login(request):
    if request.method == "POST":
        Username = request.POST.get('Username')
        password = request.POST.get('password')
        
        user = authenticate(username=Username, password=password)
        
        if user is not None:
            login(request, user)
            cl_gdf_instance = ClGdf()
            cl_gdf_instance.get_dados(request.user)
            
            if not cl_gdf_instance.Retorn:
                solucoes = cl_gdf_instance.get_solucoes()
                if solucoes:
                    request.session['t_solucoes'] = solucoes
                    request.session['cod_cliente'] = cl_gdf_instance.Cliente.cod_cliente
                    return render(request, 'Index_Home.html')
                else:
                    return render(request, 'Index_Login.html', 
                                {'error_message': 'Problema de Acesso.'})
            return redirect('Home')
        else:
            return render(request, 'Index_Login.html', 
                        {'error_message': 'Usuário ou senha inválidos.'})
    
    return render(request, 'Index_Login.html')
```

---

### 1.3 Corrigir IDOR em Views - VALIDAÇÃO COMPLETA

**Arquivo: `app/views.py` - ATUALIZAR fn_view_atualizar_empresa (linha ~380)**
```python
@login_required(login_url='Login')
@require_http_methods(["GET", "POST"])
def fn_view_atualizar_empresa(request, cod_empresa):
    """Atualizar empresa existente - COM VALIDAÇÃO IDOR"""
    cod_cliente = request.session.get('cod_cliente', None)
    if not cod_cliente:
        return JsonResponse({"erro": "Cliente não identificado"}, status=403)
    
    # ✅ VALIDAÇÃO IDOR: Empresa deve pertencer ao cliente
    empresa_pertence_cliente = Empresas.objects.filter(
        cod_empresa=cod_empresa,
        cliente__cod_cliente=cod_cliente
    ).exists()
    
    if not empresa_pertence_cliente:
        return JsonResponse({
            "erro": "Acesso negado: empresa não pertence ao seu cliente"
        }, status=403)
    
    cl_gdf = ClGdf()
    if request.method == "GET":
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            empresa_data = cl_gdf.get_empresa_upd(
                i_v_cod_empresa=cod_empresa,
                i_v_cod_cliente=cod_cliente
            )
            return JsonResponse(empresa_data)
        else:
            return JsonResponse({"erro": "Requisição inválida"}, status=400)
    
    elif request.method == "POST":
        # ... resto do código igual ...
        pass
```

---

### 1.4 CSRF em AJAX - Template Base

**Arquivo: `app/templates/Index_Base.html` - ADICIONAR NO `<HEAD>`**
```html
<head>
    <!-- ... estilos existentes ... -->
    
    <!-- ✅ CSRF Token para AJAX -->
    {% csrf_token %}
    
    <script>
        // Função para obter CSRF token
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
        
        // Adicionar CSRF token automaticamente em todos os AJAX requests
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

### 1.5 Security Headers - settings.py

**Arquivo: `GDF_PJT/GDF_PJT/settings.py` - ADICIONAR (fim do arquivo)**
```python
# ✅ Segurança HTTP Headers
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_SECURITY_POLICY = {
    "default-src": ("'self'",),
    "script-src": ("'self'", "'unsafe-inline'", "code.jquery.com", "cdn.jsdelivr.net"),
    "style-src": ("'self'", "'unsafe-inline'", "cdn.jsdelivr.net"),
    "img-src": ("'self'", "data:", "https:"),
    "font-src": ("'self'", "data:", "fonts.googleapis.com"),
}

# SSL/TLS em produção
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=False)
SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=False)
CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=False)
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

---

## 2️⃣ PRIORITY 2 - N+1 Queries & Performance (3-5 dias)

### 2.1 Corrigir N+1 em get_solucoes - gdf.py

**Arquivo: `app/classes/gdf.py` - REPLACE linhas 140-200**
```python
def get_solucoes(self):
    """Retorna soluções com subsoluções - OTIMIZADO COM PREFETCH"""
    self.Retorn = []
    try:
        if not self.subsolucoes_acesso or not self.solucoes_acesso:
            return []

        # ✅ Pré-processar IDs de subsoluções
        lsl_ids_subsolucoes = {
            acesso.subsolucao.cod_subsolucao
            for acesso in self.subsolucoes_acesso
            if getattr(acesso, "subsolucao", None) is not None
        }

        if not lsl_ids_subsolucoes:
            return []

        # ✅ OTIMIZAÇÃO: Prefetch para evitar N+1
        from django.db.models import Prefetch
        
        l_v_queryset_solucoes = Solucoes.objects.filter(
            solucoesacesso__in=self.solucoes_acesso
        ).prefetch_related(
            Prefetch(
                'subsolucoes_set',
                queryset=Subsolucoes.objects.filter(
                    cod_subsolucao__in=lsl_ids_subsolucoes
                ).only('id', 'cod_subsolucao', 'descricao')
            )
        ).distinct()

        lsl_dados_solucoes = []
        for l_v_solucao in l_v_queryset_solucoes:
            subsolucoes_list = [
                {
                    'cod_subsolucao': sub.cod_subsolucao,
                    'descricao': sub.descricao
                }
                for sub in l_v_solucao.subsolucoes_set.all()
            ]

            if subsolucoes_list:  # Apenas adicionar se tem subsoluções
                lsl_dados_solucoes.append({
                    "codigo": l_v_solucao.cod_solucao,
                    "descricao": l_v_solucao.descricao,
                    "sub_solucoes": subsolucoes_list
                })

        # Ordenação
        def sort_key(sol):
            desc = sol["descricao"].lower()
            if desc == "administração":
                return -1
            elif desc == "dashboard":
                return 9999
            return 0

        lsl_dados_solucoes.sort(key=sort_key)
        return lsl_dados_solucoes

    except Exception as e:
        print(f"[ERROR] get_solucoes: {str(e)}")
        return []
```

---

### 2.2 Implementar Paginação Backend - views.py

**Arquivo: `app/views.py` - REPLACE fn_view_listar_usuarios**
```python
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

@login_required(login_url='Login')
def fn_view_listar_usuarios(request):
    """Listar usuários com paginação"""
    cod_cliente = request.session.get('cod_cliente', None)
    
    if not cod_cliente:
        return render(request, 'Index_Login.html', 
                    {'error_message': 'Acesso negado: cliente não identificado'})
    
    page = request.GET.get('page', 1)
    per_page = 25  # Items por página
    
    cl_gdf = ClGdf()
    t_user = cl_gdf.get_usuarios(i_v_cod_cliente=cod_cliente)
    
    # ✅ Paginar
    paginator = Paginator(t_user, per_page)
    
    try:
        usuarios = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        usuarios = paginator.page(1)
    
    return render(
        request,
        'usuarios/Index_Usuarios.html',
        {
            't_user': usuarios.object_list,
            'paginator': paginator,
            'page_obj': usuarios,
        }
    )
```

**Template: `app/templates/usuarios/Index_Usuarios.html` - ADICIONAR**
```html
<!-- No final do HTML -->
<div class="pagination">
    {% if page_obj.has_previous %}
        <a href="?page=1" class="btn btn-sm">« Primeira</a>
        <a href="?page={{ page_obj.previous_page_number }}" class="btn btn-sm">‹ Anterior</a>
    {% endif %}
    
    <span>Página {{ page_obj.number }} de {{ paginator.num_pages }}</span>
    
    {% if page_obj.has_next %}
        <a href="?page={{ page_obj.next_page_number }}" class="btn btn-sm">Próxima ›</a>
        <a href="?page={{ paginator.num_pages }}" class="btn btn-sm">Última »</a>
    {% endif %}
</div>
```

---

### 2.3 Implementar Redis Cache - settings.py

**Arquivo: `requirements.txt` - ADICIONAR**
```
django-redis==5.4.0
redis==5.0.1
```

**Instalar**:
```bash
pip install -r requirements.txt
```

**Arquivo: `GDF_PJT/GDF_PJT/settings.py` - ADICIONAR**
```python
# ✅ CACHE com Redis
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
        },
        'KEY_PREFIX': 'gdf',
        'TIMEOUT': 300,  # 5 minutos padrão
    }
}

# ✅ SESSIONS em Redis
SESSION_ENGINE = 'django_redis.cache.session.SessionCache'
SESSION_CACHE_ALIAS = 'default'
```

---

### 2.4 Adicionar Cache em get_empresas - gdf.py

**Arquivo: `app/classes/gdf.py` - ADICIONAR ao método get_empresas**
```python
from django.core.cache import cache

def get_empresas(self, i_v_cod_cliente=None, i_busca=None):
    """Buscar empresas com CACHE"""
    
    # ✅ Chave do cache
    cache_key = f"empresas_{i_v_cod_cliente}"
    
    # ✅ Verificar cache
    cached_result = cache.get(cache_key)
    if cached_result and not i_busca:  # Cache válido apenas sem busca
        return cached_result
    
    self.Retorn = []
    try:
        lsl_dados_empresas = []

        # SELECT_RELATED para evitar N+1
        l_v_queryset_empresas = Empresas.objects.filter(
            cliente__cod_cliente=i_v_cod_cliente,
            is_active=True
        ).select_related('cert', 'cliente').only(
            'cod_empresa', 'cnpj', 'razao', 'fantasia', 'cert__fim_validade'
        )

        for empresa in l_v_queryset_empresas:
            lsl_dados_empresas.append({
                "cod_empresa": empresa.cod_empresa,
                "razao": empresa.razao,
                "cnpj": empresa.cnpj,
                "fantasia": empresa.fantasia,
                "is_active": empresa.is_active,
            })

        # ✅ Guardar no cache por 5 minutos
        if not i_busca:
            cache.set(cache_key, lsl_dados_empresas, 300)

        return lsl_dados_empresas

    except Exception as e:
        print(f"[ERROR] get_empresas: {str(e)}")
        return []
```

**Invalidar cache ao atualizar**:
```python
def upd_empresa(self, i_v_cod_empresa, i_v_cod_cliente, **kwargs):
    """Atualizar empresa e INVALIDAR CACHE"""
    try:
        # ... lógica de atualização ...
        
        # ✅ Invalidar cache
        cache.delete(f"empresas_{i_v_cod_cliente}")
        
        return {"success": True, "message": "Empresa atualizada"}
    except Exception as e:
        return {"success": False, "message": str(e)}
```

---

### 2.5 Adicionar Índices de Banco - models.py

**Arquivo: `app/db_GDF/Public/models.py` - ATUALIZAR**
```python
class UserEmpresas(models.Model):
    empresa = models.ForeignKey(Empresas, models.CASCADE)
    user = models.ForeignKey(User, models.CASCADE)

    class Meta:
        managed = True
        db_table = 'user_empresas'
        unique_together = ('empresa', 'user')
        # ✅ ADICIONAR ÍNDICES
        indexes = [
            models.Index(fields=['empresa', 'user']),
            models.Index(fields=['user', 'empresa']),
        ]

class Empresas(models.Model):
    cod_empresa = models.CharField(primary_key=True, max_length=10)
    cnpj = models.CharField(unique=True, max_length=14)
    razao = models.CharField(unique=True, max_length=120, blank=True, null=True)
    fantasia = models.CharField(max_length=60, blank=True, null=True)
    cliente = models.ForeignKey(Clientes, models.CASCADE)
    is_active = models.BooleanField(db_index=True)  # ✅ Índice simples

    class Meta:
        managed = True
        db_table = 'empresas'
        # ✅ ADICIONAR/ATUALIZAR ÍNDICES
        indexes = [
            models.Index(fields=['cliente', 'is_active']),
            models.Index(fields=['is_active']),
            models.Index(fields=['cnpj']),
            models.Index(fields=['razao']),
        ]

class SolucoesAcesso(models.Model):
    cliente = models.ForeignKey(Clientes, models.CASCADE)
    solucao = models.ForeignKey(Solucoes, models.CASCADE)
    is_active = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'solucoes_acesso'
        unique_together = ('cliente', 'solucao')
        # ✅ ADICIONAR ÍNDICES
        indexes = [
            models.Index(fields=['cliente', 'is_active']),
            models.Index(fields=['is_active']),
        ]
```

**Criar e aplicar migrations**:
```bash
cd GDF_PJT
python manage.py makemigrations
python manage.py migrate
```

---

## 3️⃣ PRIORITY 3 - Escalabilidade (1-2 semanas)

### 3.1 Sessions em Redis - settings.py

```python
# Já feito acima - adicionar ao .env:
REDIS_URL=redis://localhost:6379/1
```

### 3.2 Connection Pooling PostgreSQL

**Arquivo: `GDF_PJT/GDF_PJT/settings.py`**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT'),
        'CONN_MAX_AGE': 600,  # ✅ Manter conexão por 10 min
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c search_path=public,"nfe"',
            'isolation_level': psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED,
        }
    }
}
```

### 3.3 Gunicorn Config

**Arquivo: `gunicorn_config.py` (NOVO)**
```python
import multiprocessing
import os

# Bind
bind = os.environ.get('GUNICORN_BIND', '0.0.0.0:8000')

# Workers
cpu_count = multiprocessing.cpu_count()
workers = cpu_count * 2 + 1

# Settings
worker_class = 'sync'
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 5

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Performance
preload_app = False
```

**Iniciar com Gunicorn**:
```bash
pip install gunicorn
gunicorn -c gunicorn_config.py GDF_PJT.wsgi
```

---

## ✅ TESTE RÁPIDO DE SEGURANÇA

Execute este script para verificar configurações:

**Arquivo: `test_security_config.py`**
```python
#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GDF_PJT.settings')
django.setup()

from django.conf import settings

print("=" * 50)
print("🔒 SECURITY CHECK")
print("=" * 50)

checks = {
    'DEBUG': (not settings.DEBUG, "DEBUG OFF ✅" if not settings.DEBUG else "DEBUG ON ❌"),
    'SECRET_KEY': (len(settings.SECRET_KEY) > 50, "SECRET_KEY long enough ✅" if len(settings.SECRET_KEY) > 50 else "SECRET_KEY too short ❌"),
    'SECURE_BROWSER_XSS_FILTER': (settings.SECURE_BROWSER_XSS_FILTER, "XSS Filter ✅" if settings.SECURE_BROWSER_XSS_FILTER else "XSS Filter ❌"),
    'X_FRAME_OPTIONS': (settings.X_FRAME_OPTIONS == 'DENY', f"X-Frame-Options: {settings.X_FRAME_OPTIONS} ✅" if settings.X_FRAME_OPTIONS == 'DENY' else f"X-Frame-Options: {settings.X_FRAME_OPTIONS} ❌"),
    'SESSION_COOKIE_SECURE': (settings.SESSION_COOKIE_SECURE, "SESSION SECURE ✅" if settings.SESSION_COOKIE_SECURE else "SESSION SECURE ❌"),
    'CSRF_COOKIE_SECURE': (settings.CSRF_COOKIE_SECURE, "CSRF SECURE ✅" if settings.CSRF_COOKIE_SECURE else "CSRF SECURE ❌"),
}

for check_name, (passed, message) in checks.items():
    status = "✅" if passed else "❌"
    print(f"{status} {message}")

print("\n" + "=" * 50)
print("🗄️  DATABASE CHECK")
print("=" * 50)
print(f"Engine: {settings.DATABASES['default']['ENGINE']}")
print(f"Pool Timeout: {settings.DATABASES['default'].get('CONN_MAX_AGE', 0)} segundos")

print("\n" + "=" * 50)
print("💾 CACHE CHECK")
print("=" * 50)
print(f"Backend: {settings.CACHES['default']['BACKEND']}")
print(f"Location: {settings.CACHES['default']['LOCATION']}")

print("\n" + "=" * 50)
```

**Executar**:
```bash
python test_security_config.py
```

---

## 🚀 PRÓXIMOS PASSOS

1. **TODAY**: Implementar Fase 1 (credenciais, rate limiting, CSRF, IDOR)
2. **TOMORROW**: Implementar Fase 2 (N+1 queries, paginação, cache)
3. **THIS WEEK**: Implementar Fase 3 (índices, logging, validação XML)
4. **NEXT WEEK**: Começar Fase 4 (Celery, Redis sessions, Docker)

---

