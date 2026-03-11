"""
Session Fixation Protection
Valida JWT tokens com expiração e emissão (iat/exp).
Previne reutilização de tokens antigos.
Considera X-Forwarded-For / X-Real-IP quando atrás de proxy (NGINX).
"""

import time

from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

from app.security_logger import SecurityLogger

try:
    from jwt import decode as jwt_decode, DecodeError, ExpiredSignatureError
except ImportError:
    try:
        import jwt as jwt_module
        jwt_decode = jwt_module.decode
        DecodeError = jwt_module.DecodeError
        ExpiredSignatureError = jwt_module.ExpiredSignatureError
    except (ImportError, AttributeError):
        jwt_decode = None
        DecodeError = None
        ExpiredSignatureError = None


class JWTTokenValidator:
    """
    Revogação em memória: em multi-worker (Gunicorn) cada worker tem seu próprio set.
    Para revogação global use cache (ex.: Redis) ou persistência.
    """
    REVOKED_TOKENS = set()

    @staticmethod
    def validate_token(token_string):
        if jwt_decode is None:
            return None
        try:
            payload = jwt_decode(
                token_string,
                settings.SECRET_KEY,
                algorithms=["HS256"],
            )
            if token_string in JWTTokenValidator.REVOKED_TOKENS:
                return None
            if "iat" not in payload:
                return None
            iat = payload["iat"]
            now = int(time.time())
            if iat > now + 60:
                return None
            max_token_age = 24 * 60 * 60
            if (now - iat) > max_token_age:
                return None
            return payload
        except ExpiredSignatureError:
            return None
        except DecodeError:
            return None
        except Exception:
            return None

    @staticmethod
    def revoke_token(token_string):
        JWTTokenValidator.REVOKED_TOKENS.add(token_string)

    @staticmethod
    def clear_revoked_tokens():
        JWTTokenValidator.REVOKED_TOKENS.clear()


class SessionFixationMiddleware(MiddlewareMixin):
    """Middleware para prevenir session fixation"""

    def process_request(self, request):
        if not request.user.is_authenticated:
            return None
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        remote_addr = SecurityLogger.get_client_ip(request) or ""
        session_user_agent = request.session.get("_user_agent", None)
        session_remote_addr = request.session.get("_remote_addr", None)
        if not session_user_agent:
            request.session["_user_agent"] = user_agent
            request.session["_remote_addr"] = remote_addr
            return None
        if session_remote_addr != remote_addr:
            import logging
            logger = logging.getLogger("security")
            logger.warning(
                f"IP mismatch for user {request.user.id}: "
                f"expected {session_remote_addr}, got {remote_addr}"
            )
        return None


def validate_jwt_required(view_func):
    """Decorador para validar JWT em requests."""

    def wrapper(request, *args, **kwargs):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer "):
            return JsonResponse(
                {"error": "Missing or invalid authorization header"},
                status=401,
            )
        token = auth_header[7:]
        payload = JWTTokenValidator.validate_token(token)
        if not payload:
            return JsonResponse(
                {"error": "Invalid or expired token"},
                status=401,
            )
        request.jwt_payload = payload
        return view_func(request, *args, **kwargs)

    return wrapper
