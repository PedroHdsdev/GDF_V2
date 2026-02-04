"""
Decoradores de segurança para views
"""
from functools import wraps
from django.http import JsonResponse
from django.shortcuts import redirect


def validate_idor_empresa(view_func):
    """
    Decorador que valida se a empresa pertence ao cliente da sessão
    Uso: @validate_idor_empresa
    View precisa ter parâmetro cod_empresa
    """
    @wraps(view_func)
    def wrapper(request, cod_empresa=None, *args, **kwargs):
        from app.db_GDF.Public.models import Empresas
        
        cod_cliente = request.session.get('cod_cliente', None)
        if not cod_cliente:
            return JsonResponse({"erro": "Cliente não identificado"}, status=403)
        
        # Valida se a empresa pertence ao cliente
        if cod_empresa:
            empresa_pertence = Empresas.objects.filter(
                cod_empresa=cod_empresa,
                cliente__cod_cliente=cod_cliente
            ).exists()
            
            if not empresa_pertence:
                return JsonResponse({
                    "erro": "Acesso negado: empresa não pertence ao seu cliente"
                }, status=403)
        
        return view_func(request, cod_empresa, *args, **kwargs)
    
    return wrapper


def validate_idor_usuario(view_func):
    """
    Decorador que valida se o usuário pertence ao cliente da sessão
    Uso: @validate_idor_usuario
    View precisa ter parâmetro user_id
    """
    @wraps(view_func)
    def wrapper(request, user_id=None, *args, **kwargs):
        from django.contrib.auth.models import User
        from app.db_GDF.Public.models import Clientes
        
        cod_cliente = request.session.get('cod_cliente', None)
        if not cod_cliente:
            return JsonResponse({"erro": "Cliente não identificado"}, status=403)
        
        # Valida se o usuário pertence ao cliente
        if user_id:
            user_pertence = User.objects.filter(
                id=user_id,
                clientes__cod_cliente=cod_cliente
            ).exists()
            
            if not user_pertence:
                return JsonResponse({
                    "erro": "Acesso negado: usuário não pertence ao seu cliente"
                }, status=403)
        
        return view_func(request, user_id, *args, **kwargs)
    
    return wrapper


def validate_session_required(view_func):
    """
    Decorador que valida se cod_cliente existe na sessão
    Uso: @validate_session_required
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        cod_cliente = request.session.get('cod_cliente', None)
        if not cod_cliente:
            return JsonResponse({"erro": "Sessão inválida: cliente não identificado"}, status=403)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper
