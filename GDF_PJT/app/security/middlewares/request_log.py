"""
Middleware que registra requisições e erros no gdf.log
para monitoramento e diagnóstico (inclui 4xx, 5xx e exceções).
"""
import logging
import traceback

from django.utils.deprecation import MiddlewareMixin


def _path_info(request):
    """Path da requisição (sem prefixo SCRIPT_NAME para legibilidade)."""
    path = (getattr(request, "path", "") or "").strip() or "/"
    return path


def _user_info(request):
    """Usuário da sessão (se autenticado) e cod_cliente quando existir."""
    user = getattr(request, "user", None)
    if user and getattr(user, "is_authenticated", False):
        username = getattr(user, "username", None) or str(user)
        cod_cliente = (getattr(request, "session", None) or {}).get("cod_cliente", "")
        if cod_cliente:
            return f"{username} (cliente={cod_cliente})"
        return username
    return "-"


class RequestLogMiddleware(MiddlewareMixin):
    """
    Grava no gdf.log cada requisição (método, path, user, status).
    Para 4xx/5xx grava como WARNING/ERROR; para exceções não tratadas grava traceback.
    """

    def process_response(self, request, response):
        try:
            method = (getattr(request, "method", "") or "GET").upper()
            path = _path_info(request)
            get_qs = request.GET.urlencode() if hasattr(request, "GET") and request.GET else ""
            user = _user_info(request)
            status = getattr(response, "status_code", 0)

            msg = f"{method} {path}"
            if get_qs:
                msg += f" ?{get_qs}"
            msg += f" | user={user} | status={status}"

            logger = logging.getLogger("gdf")
            if status >= 500:
                logger.error(msg + " (ERRO servidor)")
            elif status >= 400:
                logger.warning(msg + " (ERRO cliente)")
            else:
                logger.info(msg)
        except Exception:
            pass
        return response

    def process_exception(self, request, exception):
        """Registra exceções não tratadas no gdf.log com traceback."""
        try:
            logger = logging.getLogger("gdf")
            path = _path_info(request)
            user = _user_info(request)
            tb = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
            logger.error(
                "EXCEÇÃO | %s %s | user=%s | %s: %s\n%s",
                getattr(request, "method", ""),
                path,
                user,
                type(exception).__name__,
                exception,
                tb,
            )
        except Exception:
            pass
        return None
