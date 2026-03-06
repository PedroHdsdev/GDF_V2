"""
Rate Limiting Middleware
Protege contra abuso e DDoS básico
"""
from django.core.cache import cache
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin


class RateLimitMiddleware(MiddlewareMixin):
    """
    Rate limiting por IP ou usuário autenticado
    Padrão: 100 requests por minuto
    """

    def process_request(self, request):
        if request.user.is_authenticated:
            identifier = f"user_{request.user.id}"
        else:
            identifier = f"ip_{request.META.get('REMOTE_ADDR', 'unknown')}"
        path = request.path
        cache_key = f"rate_limit_{identifier}_{path}"
        current = cache.get(cache_key, 0)
        if path.startswith("/Login"):
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
