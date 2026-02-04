"""
Security & Audit Logging
Registra eventos de segurança, tentativas de acesso, etc
"""

import logging
from django.utils.timezone import now
from functools import wraps

# Loggers
security_logger = logging.getLogger('security')
audit_logger = logging.getLogger('audit')


class SecurityLogger:
    """Centralizar logging de segurança"""
    
    @staticmethod
    def get_request_info(request):
        """Extrair informações úteis do request"""
        return {
            'username': request.user.username if request.user.is_authenticated else 'anonymous',
            'ip': SecurityLogger.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200],
            'path': request.path,
            'method': request.method,
        }
    
    @staticmethod
    def get_client_ip(request):
        """Obter IP real do cliente (considerando proxies)"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @staticmethod
    def log_login_attempt(request, success, reason=None):
        """Log de tentativa de login"""
        info = SecurityLogger.get_request_info(request)
        if success:
            audit_logger.info(
                f"Login bem-sucedido | User: {info['username']} | IP: {info['ip']}"
            )
        else:
            security_logger.warning(
                f"Login falhou | User: {info['username']} | IP: {info['ip']} | "
                f"Reason: {reason or 'Unknown'}"
            )
    
    @staticmethod
    def log_unauthorized_access(request, resource, reason):
        """Log de tentativa de acesso não autorizado"""
        info = SecurityLogger.get_request_info(request)
        security_logger.warning(
            f"Acesso não autorizado | User: {info['username']} | IP: {info['ip']} | "
            f"Resource: {resource} | Reason: {reason}"
        )
    
    @staticmethod
    def log_idor_attempt(request, resource_type, resource_id, owner_id):
        """Log de tentativa de IDOR"""
        info = SecurityLogger.get_request_info(request)
        security_logger.warning(
            f"IDOR attempt | User: {info['username']} (ID: {request.user.id}) | "
            f"IP: {info['ip']} | Trying to access {resource_type} {resource_id} "
            f"(owned by user {owner_id})"
        )
    
    @staticmethod
    def log_data_modification(request, model_name, action, object_id, changes=None):
        """Log de modificação de dados"""
        info = SecurityLogger.get_request_info(request)
        audit_logger.info(
            f"Data {action} | User: {info['username']} | IP: {info['ip']} | "
            f"Model: {model_name} | ID: {object_id} | Changes: {changes or 'N/A'}"
        )
    
    @staticmethod
    def log_suspicious_activity(request, activity_type, details):
        """Log de atividade suspeita"""
        info = SecurityLogger.get_request_info(request)
        security_logger.warning(
            f"Suspicious activity | User: {info['username']} | IP: {info['ip']} | "
            f"Type: {activity_type} | Details: {details}"
        )
    
    @staticmethod
    def log_rate_limit_exceeded(request, limit_type):
        """Log de rate limit excedido"""
        info = SecurityLogger.get_request_info(request)
        security_logger.warning(
            f"Rate limit exceeded | User: {info['username']} | IP: {info['ip']} | "
            f"Type: {limit_type}"
        )


def log_security_event(event_type):
    """
    Decorador para registrar eventos de segurança
    
    Usage:
        @log_security_event('DELETE_USER')
        def delete_user(request, user_id):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            info = SecurityLogger.get_request_info(request)
            audit_logger.info(
                f"Event: {event_type} | User: {info['username']} | "
                f"IP: {info['ip']} | Path: {info['path']}"
            )
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
