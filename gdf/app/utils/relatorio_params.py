"""
Helper de parâmetros para APIs de relatório fiscal (NFe, CTe, NFSe, SPED).
Centraliza leitura, validação e paginação (DRY).
"""
from dataclasses import dataclass
from typing import List, Optional

from django.db.models import CharField, F, Q
from django.db.models.expressions import RawSQL
from django.http import HttpRequest

from app.db_GDF.Public.models import Filial
from app.security.validators import InputValidator
from django.core.exceptions import ValidationError


@dataclass
class RelatorioParams:
    """Parâmetros validados para listagem de relatório."""
    cod_empresas: List[str]
    cod_cliente: Optional[str]
    empresa_id: str
    data_inicio: Optional[str]
    data_fim: Optional[str]
    busca: str
    page: int
    page_size: int
    # Integração SAP (NFe, CTe, NFSe): '' = todos, 'sim' = tem_sap True, 'nao' = tem_sap False
    tem_sap: str


def parse_relatorio_params(
    request: HttpRequest,
    relatorio_empresas_queryset,
    max_busca_length: int = 100,
) -> RelatorioParams:
    """
    Extrai e valida parâmetros GET comuns às APIs de relatório (NFe, CTe, NFSe, SPED).
    Levanta ValidationError se busca for inválida.
    """
    empresas = relatorio_empresas_queryset(request)
    cod_empresas = list(empresas.values_list('cod_empresa', flat=True))
    cod_cliente = request.session.get('cod_cliente') or None

    empresa_id = (request.GET.get('empresa_id') or '').strip()
    if empresa_id and empresa_id in cod_empresas:
        cod_empresas = [empresa_id]
    elif empresa_id:
        cod_empresas = []

    data_inicio = (request.GET.get('data_inicio') or '').strip()
    data_fim = (request.GET.get('data_fim') or '').strip()

    try:
        busca = InputValidator.validate_search_query(
            request.GET.get('busca', '') or '', max_length=max_busca_length
        )
    except ValidationError:
        raise

    try:
        page_size = min(max(int(request.GET.get('page_size', 50)), 1), 200)
    except (TypeError, ValueError):
        page_size = 50
    try:
        page = max(1, int(request.GET.get('page', 1)))
    except (TypeError, ValueError):
        page = 1

    raw_tem_sap = (request.GET.get('tem_sap') or '').strip().lower()
    tem_sap = ''
    if raw_tem_sap in ('sim', 'tem', 's', '1', 'true', 'yes'):
        tem_sap = 'sim'
    elif raw_tem_sap in ('nao', 'não', 'nao_tem', 'sem', '0', 'false', 'no'):
        tem_sap = 'nao'

    return RelatorioParams(
        cod_empresas=cod_empresas,
        cod_cliente=cod_cliente,
        empresa_id=empresa_id,
        data_inicio=data_inicio or None,
        data_fim=data_fim or None,
        busca=busca,
        page=page,
        page_size=page_size,
        tem_sap=tem_sap,
    )


def parse_date_safe(value: Optional[str]):
    """Retorna date ou None. Usado para data_inicio/data_fim."""
    if not value:
        return None
    from django.utils.dateparse import parse_date
    return parse_date(value)


def paginate_queryset(qs, page: int, page_size: int):
    """Retorna (total, total_pages, qs_slice)."""
    total = qs.count()
    total_pages = max(1, (total + page_size - 1) // page_size) if total else 1
    page = min(page, total_pages)
    start = (page - 1) * page_size
    return total, total_pages, page, qs[start : start + page_size]


def parse_filial_id(request: HttpRequest, cod_empresas: List[str]):
    """
    Valida filial_id do GET contra filiais das empresas permitidas.
    Retorna int pk ou None.
    """
    if not cod_empresas:
        return None
    raw = (request.GET.get('filial_id') or '').strip()
    if not raw:
        return None
    try:
        fid = int(raw)
    except (TypeError, ValueError):
        return None
    if not Filial.objects.filter(pk=fid, empresa__cod_empresa__in=cod_empresas).exists():
        return None
    return fid


def nfe_condicao_pagamento_nfe_rawsql():
    """
    Expressão SQL (anotação) alinhada a condicao_pagamento_da_nfe (Reprocessamento):
    sem cobrança / sem parcelas → 'À vista'; caso contrário 'Nx em d1/d2/... dias'.
    Usada para filtrar NF-e no relatório pela condição SAP mapeada em CondicaoParam.
    """
    sql = """(
        SELECT CASE
            WHEN c.id_cobranca IS NULL THEN 'À vista'
            WHEN NOT EXISTS (
                SELECT 1 FROM nfe.nfe_parcela p0
                WHERE p0.nfe_cobranca_id = c.id_cobranca
            ) THEN 'À vista'
            ELSE (
                SELECT lp.cnt || 'x em ' || lp.parts || ' dias'
                FROM (
                    SELECT COUNT(*)::int AS cnt,
                        string_agg(
                            ((p.data_vencimento - DATE(i.emissao))::integer)::text,
                            '/' ORDER BY p.numero_parcela
                        ) AS parts
                    FROM nfe.nfe_parcela p
                    INNER JOIN nfe.nfe_cobranca c2 ON p.nfe_cobranca_id = c2.id_cobranca
                    WHERE c2.nfe_identificacao_id = i.id_identificacao
                ) lp
            )
        END
        FROM nfe.nfe_identificacao i
        LEFT JOIN nfe.nfe_cobranca c ON c.nfe_identificacao_id = i.id_identificacao
        WHERE i.id_identificacao = %s
        LIMIT 1
    )"""
    return RawSQL(sql, [F('identificacao_id')], output_field=CharField())


def q_condicao_param_tipo_pagamento_match(tipo_pagamento) -> Q:
    """Combina com tipo_pagamento armazenado em CondicaoParam (e tipo_pagamento_da_nfe)."""
    if tipo_pagamento is None or str(tipo_pagamento).strip() == '':
        return (
            Q(identificacao__pagamento__isnull=True)
            | Q(identificacao__pagamento__meio_pagamento='')
            | Q(identificacao__pagamento__meio_pagamento__isnull=True)
        )
    t = str(tipo_pagamento).strip()[:2]
    return Q(identificacao__pagamento__meio_pagamento=t)


def parse_relatorio_order(request: HttpRequest, field_to_orm: dict, default_order_expr: str) -> str:
    """
    Monta um único argumento para order_by() a partir de order + dir no GET.
    field_to_orm: chave da API (ex.: 'emissao') -> caminho ORM (ex.: 'identificacao__emissao').
    default_order_expr: ex.: '-identificacao__emissao' quando order inválido ou omitido.
    """
    order_key = (request.GET.get('order') or '').strip()
    direction = (request.GET.get('dir') or '').strip().lower()
    if direction not in ('asc', 'desc'):
        direction = 'desc'
    orm_field = field_to_orm.get(order_key)
    if not orm_field:
        return default_order_expr
    want_desc = direction == 'desc'
    default_desc = default_order_expr.lstrip().startswith('-')
    prefix = '-' if want_desc else ''
    return prefix + orm_field
