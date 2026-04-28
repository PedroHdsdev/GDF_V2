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
        from app.db_GDF.Public.models import Empresa

        cod_cliente = request.session.get("cod_cliente", None)
        if not cod_cliente:
            return JsonResponse({"erro": "Cliente não identificado"}, status=403)

        if cod_empresa:
            empresa_pertence = Empresa.objects.filter(
                cod_empresa=cod_empresa,
                gdfcliente__cod_cliente=cod_cliente,
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

        cod_cliente = request.session.get("cod_cliente", None)
        if not cod_cliente:
            return JsonResponse({"erro": "Cliente não identificado"}, status=403)

        if user_id:
            user_pertence = User.objects.filter(
                id=user_id,
                usuarioempresa__empresa__gdfcliente__cod_cliente=cod_cliente,
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
        cod_cliente = request.session.get("cod_cliente", None)
        if not cod_cliente:
            return JsonResponse({
                "erro": "Sessão inválida: cliente não identificado"
            }, status=403)
        return view_func(request, *args, **kwargs)

    return wrapper


def requer_acesso_subsolucao(cod_subsolucao, redirect_on_deny=True):
    """
    Decorador que valida se o usuário tem acesso à subsolução (via grupos).
    Uso: @requer_acesso_subsolucao('Dm_Empresas')  para views de página (redireciona para Home se negado)
         @requer_acesso_subsolucao('Pro_CargaXml', redirect_on_deny=False)  para APIs (retorna 403 JSON)
    """
    from app.utils.view_helpers import get_subsolucoes_usuario

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                if redirect_on_deny:
                    return redirect("Login")
                return JsonResponse({"erro": "Não autenticado"}, status=403)
            subsolucoes = get_subsolucoes_usuario(request.user)
            # None = acesso total (superuser ou cliente 1000)
            if subsolucoes is None:
                return view_func(request, *args, **kwargs)
            if cod_subsolucao not in subsolucoes:
                if redirect_on_deny:
                    return redirect("Home")
                return JsonResponse({
                    "erro": "Acesso negado: você não tem permissão para esta subsolução"
                }, status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def requer_acesso_um_de(*cod_subsolucoes, redirect_on_deny=True):
    """
    Acesso se o usuário tiver qualquer uma das subsoluções listadas
    (ex.: duas soluções que abrem a mesma API compartilhada).
    Uso: @requer_acesso_um_de('Reproc_Painel', 'OutroCod', redirect_on_deny=False)
    """
    from app.utils.view_helpers import get_subsolucoes_usuario

    cods = tuple(cod_subsolucoes)
    if not cods:
        raise ValueError("requer_acesso_um_de: informe ao menos um código de subsolução")

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                if redirect_on_deny:
                    return redirect("Login")
                return JsonResponse({"erro": "Não autenticado"}, status=403)
            subsolucoes = get_subsolucoes_usuario(request.user)
            if subsolucoes is None:
                return view_func(request, *args, **kwargs)
            if any(c in subsolucoes for c in cods):
                return view_func(request, *args, **kwargs)
            if redirect_on_deny:
                return redirect("Home")
            return JsonResponse(
                {"erro": "Acesso negado: você não tem permissão para esta subsolução"},
                status=403,
            )

        return wrapper

    return decorator


def requer_acesso_total_painel(redirect_on_deny=True):
    """
    Decorador que exige usuário com acesso total ao painel (superuser ou cliente dono do projeto).
    Uso em APIs: @requer_acesso_total_painel(redirect_on_deny=False)
    """
    from app.utils.view_helpers import usuario_acesso_total_painel

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                if redirect_on_deny:
                    return redirect("Login")
                return JsonResponse({"erro": "Não autenticado"}, status=403)
            if not usuario_acesso_total_painel(request):
                if redirect_on_deny:
                    return redirect("Home")
                return JsonResponse({
                    "erro": "Acesso negado: apenas usuários com acesso total ao painel podem usar este recurso"
                }, status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def requer_superuser(redirect_on_deny=True):
    """
    Decorador que exige superuser. Uso em APIs de debug: @requer_superuser(redirect_on_deny=False)
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                if redirect_on_deny:
                    return redirect("Login")
                return JsonResponse({"erro": "Não autenticado"}, status=403)
            if not getattr(request.user, "is_superuser", False):
                if redirect_on_deny:
                    return redirect("Home")
                return JsonResponse({
                    "erro": "Acesso negado: recurso restrito a superusuário"
                }, status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
