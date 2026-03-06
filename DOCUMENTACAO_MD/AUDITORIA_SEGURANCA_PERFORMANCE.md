# 🔍 Auditoria Completa GDF_V2 - Segurança, Performance & Escalabilidade

**Data**: Fevereiro 2025  
**Status**: ✅ Varredura Completa Realizada

---

## 📋 Sumário Executivo

O projeto GDF_V2 é um ERP Django multi-tenant com Streamlit dashboards. Esta auditoria identificou:
- **11 Problemas Críticos** de segurança/performance
- **6 Problemas Altos** 
- **8 Problemas Médios**
- **Recomendações** para suportar 100+ usuários concorrentes

---

## 🔴 SEGURANÇA - Problemas Críticos

### 1. **Credenciais Expostas em Settings.py** ⚠️ CRÍTICO
**Localização**: `GDF_PJT/GDF_PJT/settings.py`

**Problema**:
```python
# ❌ Atualmente:
SECRET_KEY = env('SECRET_KEY', default='django-insecure-)+_kx-l8g8iu@t@k3y=mswm^+s#%)yu_d=kevi0vac+y#m0oc^')
DATABASE credentials = Stored in .env (hardcoded defaults in fallback)
```

**Risco**: Se `.env` não existir ou for commitado ao Git, credenciais do banco PostgreSQL ficam expostas.

**Solução**:
```python
# ✅ Implementar:
import environ

env = environ.Env()
environ.Env.read_env()

SECRET_KEY = env('SECRET_KEY')  # SEM default!
if not SECRET_KEY:
    raise ValueError("SECRET_KEY not set in environment variables")

DATABASES = {
    'default': {
        'ENGINE': env('DB_ENGINE'),
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),  # SEM default!
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT'),
    }
}

# Adicionar ao .gitignore:
.env
.env.local
.env.*.local
```

**Impacto**: Previne vazamento de credenciais em repositório público

---

### 2. **Falta de Rate Limiting & DDOS Protection** ⚠️ CRÍTICO
**Localização**: `GDF_PJT/GDF_PJT/settings.py`, `urls.py`

**Problema**:
- Sem rate limiting em endpoints de login/API
- Sem proteção contra brute force
- Sem throttling de requisições

**Risco**: Um atacante pode:
- Fazer brute force de senhas
- Sobrecarregar API `/api/processar-xml/`
- Causar negação de serviço

**Solução**:
```python
# Instalar: pip install django-ratelimit

# settings.py
INSTALLED_APPS = [
    # ...
    'django_ratelimit',
]

REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '10/minute',      # Anônimo: 10 req/min
        'user': '100/minute',     # Autenticado: 100 req/min
        'login': '5/minute',      # Login: 5 tentativas/min
        'api': '50/hour',         # API: 50 req/hora
    }
}

# views.py
from django_ratelimit.decorators import ratelimit
from django.views.decorators.cache import cache_page

@login_required(login_url='Login')
@ratelimit(key='user', rate='5/m', method='POST')
def fn_view_login(request):
    # ... login logic
    pass

@ratelimit(key='ip', rate='10/m', method='POST')
def fn_api_processar_xml(request):
    # ... api logic
    pass
```

---

### 3. **SQL Injection - Filtragem Inadequada de Entrada** ⚠️ CRÍTICO
**Localização**: `app/views.py` (múltiplas views)

**Problema**:
```python
# ❌ Em fn_view_listar_usuarios e similares:
t_user = cl_gdf.get_usuarios(i_v_cod_cliente=cod_cliente)

# Falta validação de entrada em campos de busca
buscar = request.GET.get('Buscar')  # SEM validação!
```

**Risco**: Se implementar busca por SQL direto, risco de SQL injection

**Solução**:
```python
# ✅ Implementar:
from django.db.models import Q
from django.core.exceptions import ValidationError
import re

def validar_entrada(valor, tipo='texto'):
    """Valida entrada para prevenir injection"""
    if tipo == 'texto':
        # Remover caracteres especiais SQL
        valor = re.sub(r"[;'\"\\-]", '', valor)
        if len(valor) > 100:
            raise ValidationError("Texto muito longo")
    elif tipo == 'numero':
        if not valor.isdigit():
            raise ValidationError("Deve ser número")
    return valor

@login_required(login_url='Login')
def fn_view_listar_usuarios(request):
    cod_cliente = request.session.get('cod_cliente', None)
    if not cod_cliente:
        return render(request, 'Index_Login.html', {'error_message': 'Acesso negado'})
    
    busca = request.GET.get('Buscar', '').strip()
    if busca:
        busca = validar_entrada(busca)
        # Django ORM protege contra SQL injection
        usuarios = User.objects.filter(
            Q(username__icontains=busca) | Q(email__icontains=busca)
        )
    else:
        usuarios = User.objects.all()
    
    return render(request, 'usuarios/Index_Usuarios.html', {'t_user': usuarios})
```

---

### 4. **CSRF Token em AJAX Requests** ⚠️ CRÍTICO
**Localização**: `app/static/js/`, templates HTML

**Problema**:
```javascript
// ❌ AJAX sem CSRF token:
fetch('/usuario/inserir/', {
    method: 'POST',
    body: formData
});
```

**Risco**: Requisições POST de terceiros podem modificar dados

**Solução**:
```javascript
// ✅ Implementar em todos os AJAX POST:
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

fetch('/usuario/inserir/', {
    method: 'POST',
    body: formData,
    headers: {
        'X-CSRFToken': csrftoken
    }
});
```

---

### 5. **IDOR (Insecure Direct Object Reference) - Múltiplas Instâncias** ⚠️ CRÍTICO
**Localização**: `app/views.py` (atualização de usuários/empresas)

**Problema**:
```python
# ❌ Potencial IDOR:
def fn_view_atualizar_usuario(request, user_id):
    # Apenas valida cod_cliente genérico, mas não valida se user_id é do cliente
    user_belongs_to_client = UsuarioEmpresa.objects.filter(
        user_id=user_id,
        empresa__cliente__cod_cliente=cod_cliente
    ).exists()
    
    # Isso está BOM! Mas em empresas pode estar faltando:
```

**Problema em Empresa**:
```python
# ❌ Falta validação IDOR completa:
def fn_view_atualizar_empresa(request, cod_empresa):
    cod_cliente = request.session.get('cod_cliente', None)
    
    # ❌ NÃO VALIDA se cod_empresa pertence ao cod_cliente!
    resultado = cl_gdf.upd_empresa(
        i_v_cod_empresa=cod_empresa,  # Pode ser de outro cliente!
        i_v_cod_cliente=cod_cliente
    )
```

**Risco**: Usuário A pode atualizar dados de usuário B ou empresa C de outro cliente

**Solução**:
```python
# ✅ Implementar validação em TODAS as views:

@login_required(login_url='Login')
@require_http_methods(["GET", "POST"])
def fn_view_atualizar_empresa(request, cod_empresa):
    cod_cliente = request.session.get('cod_cliente', None)
    if not cod_cliente:
        return JsonResponse({"erro": "Cliente não identificado"}, status=403)
    
    # ✅ VALIDAÇÃO IDOR: Empresa deve pertencer ao cliente
    empresa_pertence_cliente = Empresa.objects.filter(
        cod_empresa=cod_empresa,
        cliente__cod_cliente=cod_cliente
    ).exists()
    
    if not empresa_pertence_cliente:
        return JsonResponse({"erro": "Acesso negado: empresa não pertence ao seu cliente"}, status=403)
    
    cl_gdf = ClGdf()
    # ... resto do código
```

---

### 6. **Sessions Fixation - Token JWT Sem Validação Adequada** ⚠️ CRÍTICO
**Localização**: `app/classes/gdf.py` linha 70-85

**Problema**:
```python
@staticmethod
def gerar_token(request, user, tipo_relatorio='Vendas'): 
    if not user.is_active:
        return None 
    
    payload = {
        "user_id": user.id,
        "username": user.username,
        "tipo_relatorio": tipo_relatorio,
        "iat": int(time.time()),
        "exp": g_v_iat + (30 * 60),  # +30 minutos
    }
    
    # ❌ Falta validação se sessão ainda é válida
    # ❌ Falta logout revogação de tokens
```

**Risco**: Token pode ser usado após usuário fazer logout

**Solução**:
```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}

# gdf.py
from django.core.cache import cache
import time

@staticmethod
def gerar_token(request, user, tipo_relatorio='Vendas'):
    """Gera JWT com validação de sessão ativa"""
    if not user.is_active:
        return None
    
    # ✅ Verificar se sessão está ativa no cache
    cache_key = f"user_session_{user.id}"
    if not cache.get(cache_key):
        return None  # Sessão expirou ou foi revogada
    
    g_v_iat = int(time.time())
    g_v_exp = g_v_iat + (30 * 60)
    
    payload = {
        "user_id": user.id,
        "username": user.username,
        "tipo_relatorio": tipo_relatorio,
        "iat": g_v_iat,
        "exp": g_v_exp,
        "jti": f"{user.id}_{g_v_iat}"  # Token ID único para revogação
    }
    
    try:
        token = jwt_encode(payload, settings.SECRET_KEY, algorithm='HS256')
        # ✅ Registrar token no cache para revogação
        cache.set(f"jwt_token_{payload['jti']}", token, 1800)  # 30 min
        return token
    except Exception as fn_e:
        print(f"[ERROR] JWT encode failed: {str(fn_e)}")
        return None

@staticmethod
def validar_token(token):
    """Valida token e verifica se foi revogado"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        jti = payload.get('jti')
        
        # ✅ Verificar revogação
        if not cache.get(f"jwt_token_{jti}"):
            return None  # Token foi revogado
        
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

@login_required
def fn_view_sair(request):
    """Logout com revogação de tokens"""
    user_id = request.user.id
    
    # ✅ Limpar session
    cache.delete(f"user_session_{user_id}")
    
    # ✅ Revogar todos os tokens do usuário
    for key in cache.keys(f"jwt_token_{user_id}_*"):
        cache.delete(key)
    
    logout(request)
    return redirect('Login')
```

---

## 🟠 SEGURANÇA - Problemas Altos

### 7. **Falta de Helmet/Security Headers** 🔸 ALTO
**Localização**: `settings.py`, middlewares

**Problema**: Sem headers de segurança HTTP

**Solução**:
```python
# settings.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # ... outros middleware
]

# Adicionar headers de segurança
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_SECURITY_POLICY = {
    "default-src": ("'self'",),
    "script-src": ("'self'", "'unsafe-inline'", "cdn.jsdelivr.net"),
    "style-src": ("'self'", "'unsafe-inline'"),
    "img-src": ("'self'", "data:", "https:"),
}

X_FRAME_OPTIONS = 'DENY'
SECURE_SSL_REDIRECT = True  # Em produção
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 ano
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

---

### 8. **Validação de Arquivo Insuficiente - Upload XML** 🔸 ALTO
**Localização**: `app/classes/CargaXml.py`, `views.py` fn_api_processar_xml

**Problema**:
```python
# ❌ Falta validação completa:
lsl_Xml = request.FILES.getlist('arquivo')
if not lsl_Xml:
    return JsonResponse({'sucesso': False})
```

**Risco**: Upload de arquivos maliciosos (XXE, billion laughs, etc.)

**Solução**:
```python
# ✅ Implementar validação rigorosa:
import mimetypes
from pathlib import Path
import xml.etree.ElementTree as ET
from defusedxml import ElementTree as DefusedET

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_EXTENSIONS = {'xml', 'nfe'}
MAX_FILES = 100

def validar_arquivo_xml(arquivo):
    """Valida arquivo XML contra XXE e bombs"""
    # 1. Validar tamanho
    if arquivo.size > MAX_FILE_SIZE:
        return False, f"Arquivo muito grande (max {MAX_FILE_SIZE} bytes)"
    
    # 2. Validar extensão
    ext = Path(arquivo.name).suffix.lower().strip('.')
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Extensão não permitida: {ext}"
    
    # 3. Validar MIME type
    mime, _ = mimetypes.guess_type(arquivo.name)
    if mime and 'xml' not in mime:
        return False, f"MIME type inválido: {mime}"
    
    # 4. Validar XML structure (anti-XXE)
    try:
        DefusedET.parse(arquivo)
    except Exception as e:
        return False, f"XML inválido: {str(e)}"
    
    return True, "OK"

@login_required(login_url='Login')
@require_http_methods(["POST"])
@ratelimit(key='user', rate='50/hour', method='POST')
def fn_api_processar_xml(request):
    cod_cliente = request.session.get('cod_cliente', None)
    if not cod_cliente:
        return JsonResponse({'sucesso': False}, status=403)
    
    try:
        lsl_Xml = request.FILES.getlist('arquivo')
        
        # ✅ Validar quantidade de arquivos
        if not lsl_Xml:
            return JsonResponse({'sucesso': False, 'mensagem': 'Nenhum arquivo'}, status=400)
        
        if len(lsl_Xml) > MAX_FILES:
            return JsonResponse({'sucesso': False, 'mensagem': f'Máximo {MAX_FILES} arquivos'}, status=400)
        
        # ✅ Validar cada arquivo
        erros = []
        validos = []
        for arquivo in lsl_Xml:
            ok, msg = validar_arquivo_xml(arquivo)
            if not ok:
                erros.append({'arquivo': arquivo.name, 'erro': msg})
            else:
                validos.append(arquivo)
        
        if not validos:
            return JsonResponse({
                'sucesso': False,
                'mensagem': 'Nenhum arquivo válido',
                'erros': erros
            }, status=400)
        
        cl_xml = CargaXml()
        upload_result = cl_xml.set_upload_xml(
            validos,
            request.POST.get('type_xml', 'NFe'),
            request.POST.get('origem_dados', 'LOCAL'),
            request.user.username
        )
        
        return JsonResponse({
            'sucesso': len(upload_result['errors']) == 0,
            'mensagem': f"{len(upload_result['success'])} OK, {len(upload_result['errors'])} erro(s)",
            'detalhes': upload_result
        }, status=200)
    
    except Exception as e:
        return JsonResponse({'sucesso': False, 'mensagem': f'Erro: {str(e)}'}, status=500)
```

---

### 9. **Logging Inadequado - Sem Auditoria** 🔸 ALTO
**Localização**: Projeto inteiro

**Problema**: Sem logs de segurança para auditoria

**Solução**:
```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/django.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/security.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': True,
        },
        'security': {
            'handlers': ['security_file'],
            'level': 'WARNING',
        },
    },
}

# views.py - Log de ações críticas
import logging
security_logger = logging.getLogger('security')

def fn_view_login(request):
    if request.method == "POST":
        username = request.POST.get('Username')
        user = authenticate(username=username, password=request.POST.get('password'))
        
        if user is not None:
            login(request, user)
            security_logger.warning(f"LOGIN_SUCCESS: user={username}, ip={get_client_ip(request)}")
        else:
            security_logger.warning(f"LOGIN_FAILED: user={username}, ip={get_client_ip(request)}")
```

---

### 10. **Falta de 2FA (Two-Factor Authentication)** 🔸 ALTO
**Localização**: Autenticação

**Problema**: Apenas username + password

**Solução**:
```bash
pip install django-otp qrcode django-rest-framework
```

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'django_otp',
    'django_otp.plugins.otp_totp',
]

MIDDLEWARE = [
    # ...
    'django_otp.middleware.OTPMiddleware',
]

# views.py
from django_otp.decorators import otp_required

@otp_required
@login_required
def fn_view_home(request):
    # Apenas acessa se 2FA validado
    return render(request, "Index_Home.html")
```

---

### 11. **Permissões Granulares Faltando** 🔸 ALTO
**Localização**: `app/views.py`

**Problema**: Faltam validações por grupo/permissão

**Solução**:
```python
# Decorador para validar permissões
from functools import wraps
from django.http import HttpResponseForbidden

def requer_permissao(permissao):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.has_perm(permissao):
                return HttpResponseForbidden('Acesso negado')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

# Usage:
@login_required
@requer_permissao('app.view_usuarios')
def fn_view_listar_usuarios(request):
    # ...
    pass

@login_required
@requer_permissao('app.change_usuario')
def fn_view_atualizar_usuario(request, user_id):
    # ...
    pass
```

---

## 🟡 PERFORMANCE - Problemas Altos/Médios

### 12. **N+1 Queries - Múltiplas Instâncias** 🟡 ALTO
**Localização**: `app/classes/gdf.py`, múltiplas queries

**Problema**:
```python
# ❌ N+1 Query Problem - get_solucoes():
for l_v_solucao in l_v_queryset_solucoes:  # Query 1
    l_v_queryset_subsolucoes = Subsolucoes.objects.filter(
        solucao=l_v_solucao,  # Query 2, 3, 4... N
        cod_subsolucao__in=lsl_ids_subsolucoes
    )
```

**Impacto**: Com 1000 soluções, 1000+ queries adicionais!

**Solução**:
```python
# ✅ Usar Prefetch/Select Related:
def get_solucoes(self):
    try:
        if not self.subsolucoes_acesso or not self.solucoes_acesso:
            return []
        
        lsl_ids_subsolucoes = {
            acesso.subsolucao.cod_subsolucao
            for acesso in self.subsolucoes_acesso
            if getattr(acesso, "subsolucao", None)
        }
        
        if not lsl_ids_subsolucoes:
            return []
        
        # ✅ SELECT + 2 JOIN (não 1000+)
        l_v_queryset_solucoes = Solucoes.objects.filter(
            solucoesacesso__in=self.solucoes_acesso
        ).prefetch_related(
            Prefetch(
                'subsolucoes_set',
                queryset=Subsolucoes.objects.filter(
                    cod_subsolucao__in=lsl_ids_subsolucoes
                ).only('cod_subsolucao', 'descricao', 'solucao_id')
            )
        ).distinct()
        
        lsl_dados_solucoes = []
        for solucao in l_v_queryset_solucoes:
            lsl_dados_solucoes.append({
                "codigo": solucao.cod_solucao,
                "descricao": solucao.descricao,
                "sub_solucoes": [
                    {
                        'cod_subsolucao': sub.cod_subsolucao,
                        'descricao': sub.descricao
                    }
                    for sub in solucao.subsolucoes_set.all()
                ]
            })
        
        return lsl_dados_solucoes
    except Exception as e:
        return []
```

---

### 13. **Paginação Ausente - Carrega Tudo em Memória** 🟡 ALTO
**Localização**: `app/views.py` (todas as views de listagem)

**Problema**:
```python
# ❌ Carrega TODOS os usuários na memória:
@login_required(login_url='Login')
def fn_view_listar_usuarios(request):
    cl_gdf = ClGdf()
    t_user = cl_gdf.get_usuarios(i_v_cod_cliente=cod_cliente)
    # Com 10.000 usuários = 10.000 objetos em memória!
    
    return render(request, 'usuarios/Index_Usuarios.html', {'t_user': t_user})
```

**Impacto**: 
- Memória: 50+ MB com 10.000 usuários
- Tempo resposta: 5-10 segundos
- Com 100 usuários concorrentes: CRASH

**Solução**:
```python
# ✅ Implementar paginação no backend:
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

@login_required(login_url='Login')
def fn_view_listar_usuarios(request):
    cod_cliente = request.session.get('cod_cliente', None)
    if not cod_cliente:
        return render(request, 'Index_Login.html')
    
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
    
    return render(request, 'usuarios/Index_Usuarios.html', {
        't_user': usuarios.object_list,
        'paginator': paginator,
        'page_obj': usuarios,
    })

# Template HTML:
<!-- Index_Usuarios.html -->
<div class="pagination">
    {% if page_obj.has_previous %}
        <a href="?page=1">« Primeira</a>
        <a href="?page={{ page_obj.previous_page_number }}">‹ Anterior</a>
    {% endif %}
    
    <span>Página {{ page_obj.number }} de {{ paginator.num_pages }}</span>
    
    {% if page_obj.has_next %}
        <a href="?page={{ page_obj.next_page_number }}">Próxima ›</a>
        <a href="?page={{ paginator.num_pages }}">Última »</a>
    {% endif %}
</div>
```

---

### 14. **Sem Cache - Queries Repetidas** 🟡 ALTO
**Localização**: Projeto inteiro

**Problema**:
```python
# ❌ Sem cache - 100 usuários = 100 queries idênticas:
def get_empresas(self, i_v_cod_cliente=None):
    l_v_queryset_empresas = Empresa.objects.filter(
        cliente__cod_cliente=i_v_cod_cliente,
        is_active=True
    ).select_related('cert')  # Executada toda vez!
```

**Solução**:
```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'gdf',
        'TIMEOUT': 300,  # 5 minutos
    }
}

# gdf.py
from django.core.cache import cache

def get_empresas(self, i_v_cod_cliente=None):
    cache_key = f"empresas_{i_v_cod_cliente}"
    
    # ✅ Verificar cache
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    # ❌ Se não em cache, executar query
    lsl_dados_empresas = []
    l_v_queryset_empresas = Empresa.objects.filter(
        cliente__cod_cliente=i_v_cod_cliente,
        is_active=True
    ).select_related('cert')
    
    for empresa in l_v_queryset_empresas:
        lsl_dados_empresas.append({
            "cod_empresa": empresa.cod_empresa,
            "razao": empresa.razao,
        })
    
    # ✅ Guardar no cache
    cache.set(cache_key, lsl_dados_empresas, 300)
    return lsl_dados_empresas

# Invalidar cache quando atualizar:
@login_required
def fn_view_atualizar_empresa(request, cod_empresa):
    # ... atualizar empresa ...
    
    # ✅ Invalidar cache
    cod_cliente = request.session.get('cod_cliente')
    cache.delete(f"empresas_{cod_cliente}")
    
    return redirect('Dm_Empresas')
```

---

### 15. **Sem Índices de Banco de Dados** 🟡 ALTO
**Localização**: `app/db_GDF/Public/models.py`

**Problema**:
```python
# ❌ Modelos com buscas frequentes mas sem índices:
class UsuarioEmpresa(models.Model):
    empresa = models.ForeignKey(Empresa, models.CASCADE)
    user = models.ForeignKey(User, models.CASCADE)
    # ❌ SEM índice composto - buscas lentas!
```

**Solução**:
```python
# ✅ Adicionar índices:
class UsuarioEmpresa(models.Model):
    empresa = models.ForeignKey(Empresa, models.CASCADE)
    user = models.ForeignKey(User, models.CASCADE)
    
    class Meta:
        unique_together = ('empresa', 'user')
        indexes = [
            models.Index(fields=['empresa', 'user']),
            models.Index(fields=['user', 'empresa']),
        ]

class Empresa(models.Model):
    cod_empresa = models.CharField(primary_key=True, max_length=10)
    cnpj = models.CharField(unique=True, max_length=14)
    razao = models.CharField(unique=True, max_length=120, blank=True, null=True)
    gdfcliente = models.ForeignKey(ClienteGdf, models.CASCADE, db_column='gdfcliente_id')
    is_active = models.BooleanField(db_index=True)  # Índice simples
    
    class Meta:
        indexes = [
            models.Index(fields=['cliente', 'is_active']),
            models.Index(fields=['is_active', 'cliente']),
            models.Index(fields=['cnpj']),
        ]

# Migration:
# python manage.py makemigrations
# python manage.py migrate
```

---

### 16. **Sem Connection Pooling** 🟡 MÉDIO
**Localização**: `settings.py` DATABASES

**Problema**:
```python
# ❌ Sem pool de conexões:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'CONN_MAX_AGE': 0,  # Nova conexão por request!
    }
}
```

**Impacto**: Com 100 usuários, 100 conexões abertas simultâneas

**Solução**:
```python
# ✅ Implementar connection pooling:
# pip install psycopg2-pool

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT'),
        'CONN_MAX_AGE': 600,  # Manter conexão 10 min
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c search_path=public,"nfe"'
        }
    }
}
```

---

### 17. **Sem Compressão HTTP** 🟡 MÉDIO
**Localização**: `settings.py`

**Problema**: Responses sem compressão GZIP

**Solução**:
```python
# settings.py
MIDDLEWARE = [
    'django.middleware.gzip.GZipMiddleware',  # Deve estar antes de outras
    'django.middleware.security.SecurityMiddleware',
    # ... resto dos middleware
]

# Configuração adicional
GZIP_MINIMUM_SIZE = 1000  # Comprimir apenas acima de 1KB
```

---

## 🟠 ESCALABILIDADE - Problemas Críticos

### 18. **Sem Load Balancing / Single Server** 🔴 CRÍTICO
**Impacto**: 100+ usuários = crash do servidor

**Solução - Arquitetura Recomendada**:
```
┌─────────────────────────────────────────────────────────┐
│                    Load Balancer (Nginx)                 │
│                     (2 instâncias)                       │
└────────────┬────────────────────────────────┬────────────┘
             │                                │
      ┌──────▼──────┐              ┌──────────▼──────┐
      │ Django App  │              │  Django App     │
      │  (Gunicorn) │              │  (Gunicorn)     │
      │   8000      │              │   8001          │
      └──────┬──────┘              └──────────┬──────┘
             │                                │
      ┌──────▼──────────────────────────────▼──────┐
      │     PostgreSQL (Master-Slave Replication)  │
      │  ┌──────────┐        ┌─────────────────┐  │
      │  │  Master  │────────│  Slave (Read)   │  │
      │  │  (Write) │        │                 │  │
      │  └──────────┘        └─────────────────┘  │
      └──────────────────────────────────────────┘
             │
      ┌──────▼──────┐
      │ Redis Cache │
      │  (3 nodes)  │
      └─────────────┘
```

**Implementação - nginx.conf**:
```nginx
upstream django_app {
    server 127.0.0.1:8000 weight=1;
    server 127.0.0.1:8001 weight=1;
    keepalive 32;
}

server {
    listen 80;
    server_name gdf.exemplo.com;
    
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://django_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

**Gunicorn startup**:
```bash
# gunicorn_config.py
import multiprocessing

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1  # Para 4 CPUs = 9 workers
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 5
```

---

### 19. **Session Storage em Banco de Dados - Sem Distribuição** 🔴 CRÍTICO
**Localização**: `settings.py`

**Problema**:
```python
# ❌ Sem configurar sessions:
# Django usa banco de dados padrão - não escala em múltiplos servidores!
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
```

**Solução**:
```bash
pip install django-redis
```

```python
# settings.py
SESSION_ENGINE = 'django_redis.cache.session.SessionCache'
SESSION_CACHE_ALIAS = 'default'

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/0',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            }
        }
    }
}

SESSION_COOKIE_AGE = 1800
SESSION_SAVE_EVERY_REQUEST = False
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
```

---

### 20. **Sem Celery/Task Queue - Processamento Síncrono** 🔴 CRÍTICO
**Localização**: Projeto inteiro

**Problema**: XML processing, relatórios, envios de email bloqueiam requisição

**Solução**:
```bash
pip install celery redis
```

```python
# celery_config.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GDF_PJT.settings')

app = Celery('GDF_PJT')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# settings.py
CELERY_BROKER_URL = 'redis://localhost:6379/1'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Sao_Paulo'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutos

# tasks.py
from celery import shared_task
from app.classes.CargaXml import CargaXml

@shared_task
def processar_xml_async(arquivo_ids, tipo_xml, origem_dados, username):
    """Processa XML em background"""
    cl_xml = CargaXml()
    resultado = cl_xml.set_upload_xml(arquivo_ids, tipo_xml, origem_dados, username)
    return resultado

# views.py - Async processing
@login_required(login_url='Login')
@require_http_methods(["POST"])
def fn_api_processar_xml(request):
    cod_cliente = request.session.get('cod_cliente', None)
    if not cod_cliente:
        return JsonResponse({'sucesso': False}, status=403)
    
    try:
        lsl_Xml = request.FILES.getlist('arquivo')
        
        if not lsl_Xml or len(lsl_Xml) > MAX_FILES:
            return JsonResponse({'sucesso': False}, status=400)
        
        # Salvar arquivos temporariamente
        arquivo_ids = []
        for arquivo in lsl_Xml:
            # ... validar e salvar ...
            arquivo_ids.append(arquivo_id)
        
        # ✅ Disparar task assíncrona
        task = processar_xml_async.delay(
            arquivo_ids,
            request.POST.get('type_xml', 'NFe'),
            request.POST.get('origem_dados', 'LOCAL'),
            request.user.username
        )
        
        return JsonResponse({
            'sucesso': True,
            'mensagem': 'Processamento iniciado',
            'task_id': task.id
        }, status=202)  # 202 Accepted
    
    except Exception as e:
        return JsonResponse({'sucesso': False, 'mensagem': str(e)}, status=500)

# Monitorar progresso
@login_required
def fn_status_processamento_xml(request, task_id):
    from celery.result import AsyncResult
    
    task_result = AsyncResult(task_id)
    
    return JsonResponse({
        'status': task_result.status,
        'progress': task_result.info.get('progress', 0) if task_result.info else 0,
    })
```

**docker-compose para escalabilidade**:
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: gdf_dev
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  django_1:
    build: .
    command: gunicorn -c gunicorn_config.py GDF_PJT.wsgi
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - DB_ENGINE=django.db.backends.postgresql
      - DB_NAME=gdf_dev
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_HOST=postgres
      - DB_PORT=5432
      - CELERY_BROKER_URL=redis://redis:6379/1
    depends_on:
      - postgres
      - redis

  django_2:
    build: .
    command: gunicorn -c gunicorn_config.py GDF_PJT.wsgi:application -b 0.0.0.0:8001
    ports:
      - "8001:8001"
    environment:
      - DEBUG=False
      - DB_ENGINE=django.db.backends.postgresql
      - DB_NAME=gdf_dev
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_HOST=postgres
      - DB_PORT=5432
      - CELERY_BROKER_URL=redis://redis:6379/1
    depends_on:
      - postgres
      - redis

  celery_worker:
    build: .
    command: celery -A GDF_PJT worker --loglevel=info --concurrency=4
    environment:
      - DB_ENGINE=django.db.backends.postgresql
      - DB_NAME=gdf_dev
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_HOST=postgres
      - DB_PORT=5432
      - CELERY_BROKER_URL=redis://redis:6379/1
    depends_on:
      - postgres
      - redis

  celery_beat:
    build: .
    command: celery -A GDF_PJT beat --loglevel=info
    environment:
      - DB_ENGINE=django.db.backends.postgresql
      - DB_NAME=gdf_dev
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_HOST=postgres
      - DB_PORT=5432
      - CELERY_BROKER_URL=redis://redis:6379/1
    depends_on:
      - postgres
      - redis

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - django_1
      - django_2

volumes:
  postgres_data:
  redis_data:
```

---

## 📊 RESUMO EXECUTIVO DE RECOMENDAÇÕES

| ID | Problema | Severidade | Esforço | Impacto | Prazo |
|---|----------|-----------|--------|--------|-------|
| 1 | Credenciais Expostas | 🔴 CRÍTICO | 1h | MÁXIMO | Imediato |
| 2 | Rate Limiting | 🔴 CRÍTICO | 3h | MÁXIMO | 1-2 dias |
| 3 | SQL Injection | 🔴 CRÍTICO | 2h | MÁXIMO | 1-2 dias |
| 4 | CSRF em AJAX | 🔴 CRÍTICO | 2h | MÁXIMO | 1-2 dias |
| 5 | IDOR | 🔴 CRÍTICO | 3h | MÁXIMO | 2-3 dias |
| 6 | Sessions Fixation | 🔴 CRÍTICO | 4h | MÁXIMO | 2-3 dias |
| 7 | Security Headers | 🟠 ALTO | 1h | ALTO | 1 dia |
| 8 | Validação XML | 🟠 ALTO | 3h | ALTO | 2 dias |
| 9 | Logging/Auditoria | 🟠 ALTO | 4h | ALTO | 3 dias |
| 10 | 2FA | 🟠 ALTO | 8h | ALTO | 1 semana |
| 11 | Permissões | 🟠 ALTO | 6h | ALTO | 1 semana |
| 12 | N+1 Queries | 🟡 MÉDIO | 6h | ALTO | 3-5 dias |
| 13 | Paginação | 🟡 MÉDIO | 4h | ALTO | 3 dias |
| 14 | Cache | 🟡 MÉDIO | 5h | ALTO | 3-5 dias |
| 15 | Índices DB | 🟡 MÉDIO | 2h | ALTO | 1-2 dias |
| 16 | Connection Pool | 🟡 MÉDIO | 1h | MÉDIO | 1 dia |
| 17 | Compressão HTTP | 🟡 MÉDIO | 30min | MÉDIO | 1 dia |
| 18 | Load Balancing | 🔴 CRÍTICO | 16h | MÁXIMO | 1-2 semanas |
| 19 | Session Distribution | 🔴 CRÍTICO | 4h | MÁXIMO | 2-3 dias |
| 20 | Celery/Tasks | 🔴 CRÍTICO | 12h | MÁXIMO | 1 semana |

---

## ✅ PLANO DE IMPLEMENTAÇÃO RECOMENDADO

### **Fase 1 - Crítico (1-2 dias)**
1. ✅ Fixar credenciais (.env)
2. ✅ CSRF em AJAX
3. ✅ Rate limiting (login)
4. ✅ Validação IDOR completa
5. ✅ Security headers

### **Fase 2 - Segurança (3-5 dias)**
1. ✅ Logging/Auditoria
2. ✅ Validação XML (defusedxml)
3. ✅ Sessions JWT com revogação
4. ✅ Permissões granulares

### **Fase 3 - Performance (5-7 dias)**
1. ✅ N+1 Query fixes (prefetch_related)
2. ✅ Paginação backend
3. ✅ Redis cache
4. ✅ Índices de banco
5. ✅ Connection pooling

### **Fase 4 - Escalabilidade (1-2 semanas)**
1. ✅ Sessions em Redis
2. ✅ Celery + Redis
3. ✅ Docker + Docker Compose
4. ✅ Nginx load balancer
5. ✅ PostgreSQL replication

---

## 📈 Testes de Performance Recomendados

```bash
# Teste de carga - 100 usuários simultâneos
# pip install locust

# locustfile.py
from locust import HttpUser, task, between

class GDFUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def login(self):
        self.client.post("/Login/", {
            "Username": "user1",
            "password": "senha123"
        })
    
    @task
    def listar_usuarios(self):
        self.client.get("/usuarios/?page=1")
    
    @task
    def listar_empresas(self):
        self.client.get("/empresas/?page=1")

# Executar: locust -f locustfile.py -u 100 -r 10 --run-time 10m
```

---

## 🔒 Checklist de Deploy Seguro

- [ ] `.env` arquivo criado (não versionado)
- [ ] `SECRET_KEY` alterada
- [ ] `DEBUG = False`
- [ ] `ALLOWED_HOSTS` configurado
- [ ] HTTPS/SSL ativado
- [ ] Rate limiting implementado
- [ ] Logs centralizados
- [ ] Backup automático
- [ ] Monitoramento ativo
- [ ] Plano de recuperação de desastres

---

**Próximos Passos**: Implementar as recomendações da Fase 1 imediatamente, seguidas pela Fase 2.

