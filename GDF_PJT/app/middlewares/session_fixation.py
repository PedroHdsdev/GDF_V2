"""
Session Fixation Protection
Valida JWT tokens com expiração e emissão (iat/exp)
Previne reutilização de tokens antigos
"""

from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from datetime import datetime, timezone
import time

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
    """Validar JWT tokens com proteção contra session fixation"""
    
    # Tokens revogados (em produção, usar Redis)
    REVOKED_TOKENS = set()
    
    @staticmethod
    def validate_token(token_string):
        """
        Valida JWT token
        
        Args:
            token_string: String do JWT
            
        Returns:
            dict: Payload do token se válido
            None: Se inválido/expirado
        """
        if jwt_decode is None:
            return None
        
        try:
            # Decodificar token
            payload = jwt_decode(
                token_string,
                settings.SECRET_KEY,
                algorithms=['HS256']
            )
            
            # Verificar se token foi revogado
            if token_string in JWTTokenValidator.REVOKED_TOKENS:
                return None
            
            # Verificar timestamp de emissão (iat)
            if 'iat' not in payload:
                return None
            
            iat = payload['iat']
            now = int(time.time())
            
            # Token não pode ser do futuro (proteção contra clock skew)
            if iat > now + 60:  # Tolerância de 60 segundos
                return None
            
            # Token não pode ser muito antigo (mesmo se não expirou)
            max_token_age = 24 * 60 * 60  # 24 horas em segundos
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
        """Revoga um token (e.g., ao fazer logout)"""
        JWTTokenValidator.REVOKED_TOKENS.add(token_string)
    
    @staticmethod
    def clear_revoked_tokens():
        """Limpar tokens revogados (chamar periodicamente)"""
        JWTTokenValidator.REVOKED_TOKENS.clear()


class SessionFixationMiddleware(MiddlewareMixin):
    """
    Middleware para prevenir session fixation
    Valida integridade da sessão em cada request
    """
    
    def process_request(self, request):
        """Verificar integridade da sessão"""
        
        if not request.user.is_authenticated:
            return None
        
        # Pegar agent info
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        remote_addr = request.META.get('REMOTE_ADDR', '')
        
        # Pegar dados salvos na sessão
        session_user_agent = request.session.get('_user_agent', None)
        session_remote_addr = request.session.get('_remote_addr', None)
        
        # Se primeira vez, salvar
        if not session_user_agent:
            request.session['_user_agent'] = user_agent
            request.session['_remote_addr'] = remote_addr
            return None
        
        # Validar se mudou de forma suspeita
        # User-Agent pode mudar (updates do navegador), então flexível
        # IP pode mudar (proxy/VPN), então verificar apenas se MUITO diferente
        
        # Se IP mudou completamente, pode ser session fixation
        # Em ambiente de produção, pode usar whitelist de IPs conhecidos
        # Por agora, apenas log
        
        if session_remote_addr != remote_addr:
            # IP mudou - registrar mas não bloquear (usuário pode estar em VPN)
            import logging
            logger = logging.getLogger('security')
            logger.warning(
                f"IP mismatch for user {request.user.id}: "
                f"expected {session_remote_addr}, got {remote_addr}"
            )
        
        return None


def validate_jwt_required(view_func):
    """
    Decorador para validar JWT em requests
    Usa para endpoints que usam JWT ao invés de session
    """
    def wrapper(request, *args, **kwargs):
        # Extrair token do header Authorization
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith('Bearer '):
            return JsonResponse(
                {'error': 'Missing or invalid authorization header'},
                status=401
            )
        
        token = auth_header[7:]  # Remove 'Bearer '
        
        payload = JWTTokenValidator.validate_token(token)
        if not payload:
            return JsonResponse(
                {'error': 'Invalid or expired token'},
                status=401
            )
        
        # Adicionar payload ao request
        request.jwt_payload = payload
        
        return view_func(request, *args, **kwargs)
    
    return wrapper
