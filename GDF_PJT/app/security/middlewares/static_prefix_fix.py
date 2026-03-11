"""
Estáticos quando o app está em subpath e o proxy (NGINX) envia /static/... sem o prefixo.
Reescreve PATH_INFO para /gdf/static/... e serve o arquivo de STATIC_ROOT (fallback garantido).
"""
import os
from django.conf import settings
from django.http import Http404
from django.utils.deprecation import MiddlewareMixin
from django.views.static import serve


def _serve_static_from_root(request, path_info):
    """Serve um arquivo de STATIC_ROOT; retorna None se não existir."""
    static_root = getattr(settings, "STATIC_ROOT", None)
    if not static_root or not os.path.isdir(static_root):
        return None
    # path_info = /static/css/foo.css -> rel = css/foo.css
    rel = path_info.lstrip("/")
    if not rel.startswith("static/"):
        return None
    rel = rel[7:]
    rel = os.path.normpath(rel)
    if rel.startswith("..") or os.path.isabs(rel):
        raise Http404("Invalid path")
    file_path = os.path.join(static_root, rel)
    if not os.path.isfile(file_path):
        return None
    return serve(request, rel, document_root=static_root)


class StaticPrefixFixMiddleware(MiddlewareMixin):
    """
    Quando a requisição chega como /static/... (proxy removeu /gdf/):
    - Reescreve PATH_INFO para /gdf/static/... (WhiteNoise pode servir)
    - Se ainda assim falhar, serve o arquivo direto de STATIC_ROOT (fallback)
    Deve ficar ANTES do WhiteNoiseMiddleware na lista MIDDLEWARE.
    """

    def process_request(self, request):
        path_info = (request.META.get("PATH_INFO") or "").strip()
        if not path_info.startswith("/static/"):
            return None

        prefix = getattr(settings, "FORCE_SCRIPT_NAME", None)
        if prefix:
            prefix = prefix.rstrip("/")
            # Reescrever para o WhiteNoise reconhecer
            request.META["PATH_INFO"] = f"{prefix}/{path_info.lstrip('/')}"

        # Fallback: servir direto de STATIC_ROOT (garante 200 para Style_Login.css, logo_Process.png, etc.)
        response = _serve_static_from_root(request, path_info)
        if response is not None:
            return response
        return None
