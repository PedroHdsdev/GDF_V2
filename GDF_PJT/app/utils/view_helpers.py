"""
Helpers compartilhados pelas views e APIs: sessão, acesso, tipo de pagamento.
Centraliza lógica de multi-tenancy e segurança.
"""
import json
import os

from django.conf import settings
from app.db_GDF.Public.models import Empresa, AcessoSubsolucaoGrupo


# Cliente dono do projeto (ex.: IT Process). Acesso total ao painel.
COD_CLIENTE_PROJETO = "PRCIT"

# Dicionário tipo de pagamento (código XML → descrição) para relatório fiscal
_path_tipo_pagamento = getattr(settings, "BASE_DIR", None)
if _path_tipo_pagamento is not None:
    _path_tipo_pagamento = os.path.join(str(_path_tipo_pagamento), "json", "Tipo_pagamento.json")
    try:
        with open(_path_tipo_pagamento, "r", encoding="utf-8") as _f:
            TIPO_PAGAMENTO_DESC = json.load(_f)
    except Exception:
        TIPO_PAGAMENTO_DESC = {}
else:
    TIPO_PAGAMENTO_DESC = {}


def descricao_tipo_pagamento(codigo):
    """Retorna a descrição do tipo de pagamento pelo código (XML). Usado no relatório fiscal."""
    if codigo is None or codigo == "":
        return "Não informado"
    return TIPO_PAGAMENTO_DESC.get(str(codigo).strip(), None)


def usuario_vinculado_cliente_1000(user):
    """True se o usuário tem empresas vinculadas ao cliente dono do projeto (COD_CLIENTE_PROJETO)."""
    if not user or not user.is_authenticated:
        return False
    return Empresa.objects.filter(
        userempresas__user=user,
        gdfcliente__cod_cliente=COD_CLIENTE_PROJETO,
    ).exists()


def usuario_acesso_total_painel(request):
    """True se o usuário pode gerenciar todos os clientes (superuser ou cliente dono do projeto)."""
    if not request.user.is_authenticated:
        return False
    if getattr(request.user, "is_superuser", False):
        return True
    return request.session.get("usuario_cliente_1000", False)


def superuser_acesso_total_painel(request):
    """Compatibilidade: True se superuser OU usuário do cliente dono do projeto tem acesso total."""
    return usuario_acesso_total_painel(request)


def get_subsolucoes_usuario(user):
    """Set de cod_subsolucao que o usuário tem acesso via grupos. None = acesso total."""
    if getattr(user, "is_superuser", False):
        return None
    if usuario_vinculado_cliente_1000(user):
        return None
    group_ids = list(user.groups.values_list("id", flat=True))
    if not group_ids:
        return set()
    codigos = AcessoSubsolucaoGrupo.objects.filter(
        group_id__in=group_ids,
        subsolucao__isnull=False,
    ).values_list("subsolucao__cod_subsolucao", flat=True).distinct()
    return set(c for c in codigos if c)


def relatorio_empresas_queryset(request):
    """Queryset de empresas do cliente que o usuário pode acessar (relatórios/reprocessamento)."""
    cod_cliente = request.session.get("cod_cliente", None)
    if not cod_cliente:
        return Empresa.objects.none()
    if usuario_acesso_total_painel(request):
        return Empresa.objects.filter(gdfcliente__cod_cliente=cod_cliente).distinct()
    return Empresa.objects.filter(
        gdfcliente__cod_cliente=cod_cliente,
        userempresas__user=request.user,
    ).distinct()


def reprocessamento_empresas_cliente(cod_cliente):
    """Lista de cod_empresa permitidos para o cliente (uso em relatórios/outros)."""
    if not cod_cliente:
        return []
    return list(
        Empresa.objects.filter(gdfcliente_id=cod_cliente).values_list("cod_empresa", flat=True)
    )


