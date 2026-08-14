"""
Garante que request.META['SCRIPT_NAME'] seja definido quando FORCE_SCRIPT_NAME está configurado.
Assim o Django gera URLs com o prefixo correto (ex.: /gdf/Login/, /gdf/Home/) em redirects,
{% url %}, build_absolute_uri(), etc. Evita 404 ao acessar por https://homo.processit.com.br/gdf/
quando o proxy não envia SCRIPT_NAME.
"""
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


class ScriptNameFixMiddleware(MiddlewareMixin):
    """
    Se FORCE_SCRIPT_NAME estiver definido e SCRIPT_NAME ainda não estiver em META,
    define SCRIPT_NAME para que todas as URLs geradas pelo Django incluam o prefixo.
    Deve rodar cedo na pilha (após SecurityMiddleware).
    """

    def process_request(self, request):
        prefix = getattr(settings, "FORCE_SCRIPT_NAME", None)
        if not prefix or not isinstance(prefix, str):
            return None
        prefix = prefix.strip().rstrip("/")
        if not prefix:
            return None
        if not prefix.startswith("/"):
            prefix = "/" + prefix
        existing = (request.META.get("SCRIPT_NAME") or "").strip()
        if not existing:
            request.META["SCRIPT_NAME"] = prefix
        return None
