"""
Rate Limiting Middleware
Protege contra abuso e DDoS básico.
Considera X-Forwarded-For / X-Real-IP quando atrás de proxy (NGINX).
Configurável por env para não bloquear acesso externo (VPN/NAT com muitos usuários).
"""
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin

from app.security_logger import SecurityLogger


def _is_login_path(request):
    """True se o path for a tela de login (com ou sem subpath /gdf/)."""
    path = (request.path or "").rstrip("/")
    prefix = (getattr(settings, "FORCE_SCRIPT_NAME", None) or "").rstrip("/")
    if prefix and path.startswith(prefix):
        path = path[len(prefix) :].lstrip("/") or "/"
    else:
        path = path or "/"
    return path == "Login" or path.startswith("Login/")


def _get_int_setting(name, default):
    """Lê configuração inteira do settings (pode vir de env)."""
    try:
        val = getattr(settings, name, default)
        return int(val) if val is not None else default
    except (TypeError, ValueError):
        return default


class RateLimitMiddleware(MiddlewareMixin):
    """
    Rate limiting por IP ou usuário autenticado.
    Padrão: 100 req/min (geral), 15 req/min (login). Desativável por env para acesso externo.
    """

    def process_request(self, request):
        # Desativa rate limit se RATE_LIMIT_DISABLED=True (ex.: acesso externo/VPN)
        if getattr(settings, "RATE_LIMIT_DISABLED", False):
            return None
        if request.user.is_authenticated:
            identifier = f"user_{request.user.id}"
        else:
            client_ip = SecurityLogger.get_client_ip(request)
            identifier = f"ip_{client_ip or 'unknown'}"
        path = request.path
        cache_key = f"rate_limit_{identifier}_{path}"
        current = cache.get(cache_key, 0)
        if _is_login_path(request):
            max_requests = _get_int_setting("RATE_LIMIT_LOGIN_MAX", 15)
        else:
            max_requests = _get_int_setting("RATE_LIMIT_GENERAL_MAX", 100)
        if max_requests <= 0:
            return None
        if current >= max_requests:
            return HttpResponse(
                "Too many requests. Please try again in 1 minute.",
                status=429,
                content_type="text/plain",
            )
        cache.set(cache_key, current + 1, 60)
        return None
