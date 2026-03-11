"""
Rate Limiting Middleware
Protege contra abuso e DDoS básico.
Considera X-Forwarded-For / X-Real-IP quando atrás de proxy (NGINX).
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


class RateLimitMiddleware(MiddlewareMixin):
    """
    Rate limiting por IP ou usuário autenticado.
    Padrão: 100 requests por minuto (5 para tela de login).
    """

    def process_request(self, request):
        if request.user.is_authenticated:
            identifier = f"user_{request.user.id}"
        else:
            client_ip = SecurityLogger.get_client_ip(request)
            identifier = f"ip_{client_ip or 'unknown'}"
        path = request.path
        cache_key = f"rate_limit_{identifier}_{path}"
        current = cache.get(cache_key, 0)
        if _is_login_path(request):
            max_requests = 5
        else:
            max_requests = 100
        if current >= max_requests:
            return HttpResponse(
                "Too many requests. Please try again in 1 minute.",
                status=429,
                content_type="text/plain",
            )
        cache.set(cache_key, current + 1, 60)
        return None
