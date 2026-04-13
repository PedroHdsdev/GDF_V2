"""
Querysets e listas completas para o Relatório Fiscal (mesmos filtros das APIs JSON).
Usado pela exportação Excel e pelas views de listagem para evitar divergência de regras.
"""
from django.db.models import Count, Q
from django.http import HttpRequest
from django.utils import timezone

from app.db_GDF.CTe.models import CTe
from app.db_GDF.NFe.models import NFe
from app.db_GDF.NFSe.models import NFSe
from app.db_GDF.reprocessamento.models import CondicaoParam
from app.db_GDF.sped_contribuicao.models import SpedContribuicaoArquivo
from app.db_GDF.sped_fiscal.models import SpedFiscalArquivo

from app.utils.relatorio_params import (
    RelatorioParams,
    nfe_condicao_pagamento_nfe_rawsql,
    parse_date_safe,
    parse_filial_id,
    parse_relatorio_order,
    q_condicao_param_tipo_pagamento_match,
)


def queryset_relatorio_nfe(request: HttpRequest, params: RelatorioParams):
    """NFe filtradas como em fn_api_relatorio_nfe, antes de order_by/paginação."""
    if not params.cod_empresas and not params.cod_cliente:
        return NFe.objects.none()

    parcelas = request.GET.get('parcelas', '').strip()
    tipo_operacao = request.GET.get('tipo_operacao', '').strip()
    tipo_pagamento = request.GET.get('tipo_pagamento', '').strip()

    if params.empresa_id:
        qs = NFe.objects.filter(empresa__cod_empresa__in=params.cod_empresas).select_related(
            'identificacao', 'empresa', 'filial'
        )
    else:
        qs = NFe.objects.filter(
            Q(empresa__cod_empresa__in=params.cod_empresas)
            | Q(empresa__isnull=True, gdfcliente__cod_cliente=params.cod_cliente)
        ).select_related('identificacao', 'empresa', 'filial')
    filial_id = parse_filial_id(request, params.cod_empresas)
    if filial_id:
        qs = qs.filter(filial_id=filial_id)
    if tipo_operacao in ('0', '1'):
        qs = qs.filter(identificacao__tipo_operacao=tipo_operacao)
    if tipo_pagamento:
        qs = qs.filter(identificacao__pagamento__meio_pagamento=tipo_pagamento)
    if parcelas != '':
        try:
            qtd = int(parcelas)
            if qtd >= 0:
                qs = qs.annotate(
                    num_parcelas=Count('identificacao__cobranca__parcelas', distinct=True)
                ).filter(num_parcelas=qtd)
        except ValueError:
            pass
    if params.busca:
        qs = qs.filter(
            Q(identificacao__chave_acesso__icontains=params.busca)
            | Q(identificacao__numero__icontains=params.busca)
            | Q(identificacao__serie__icontains=params.busca)
            | Q(status__icontains=params.busca)
            | Q(identificacao__natureza_operacao__icontains=params.busca)
        )
    dt_ini = parse_date_safe(params.data_inicio)
    if dt_ini:
        qs = qs.filter(identificacao__emissao__date__gte=dt_ini)
    dt_fim = parse_date_safe(params.data_fim)
    if dt_fim:
        qs = qs.filter(identificacao__emissao__date__lte=dt_fim)
    if params.tem_sap == 'sim':
        qs = qs.filter(tem_sap=True)
    elif params.tem_sap == 'nao':
        qs = qs.filter(tem_sap=False)

    filtro_cond_sap = (request.GET.get('condicao_pagamento_sap') or '').strip()[:60]
    cod_cli_filtro = (params.cod_cliente or '').strip() or None
    if filtro_cond_sap and cod_cli_filtro:
        pairs = list(
            CondicaoParam.objects.filter(
                gdfcliente_id=cod_cli_filtro,
                condicao_pagamento_sap=filtro_cond_sap,
            ).values('condicao_pagamento_nfe', 'tipo_pagamento')
        )
        combined = None
        for row in pairs:
            cn = (row.get('condicao_pagamento_nfe') or '').strip()
            if not cn:
                continue
            part = Q(_rel_cond_nfe_txt=cn) & q_condicao_param_tipo_pagamento_match(row.get('tipo_pagamento'))
            combined = part if combined is None else combined | part
        if combined is not None:
            qs = qs.annotate(_rel_cond_nfe_txt=nfe_condicao_pagamento_nfe_rawsql()).filter(combined)

    order_nfe = {
        'numero': 'identificacao__numero',
        'serie': 'identificacao__serie',
        'chave': 'identificacao__chave_acesso',
        'emissao': 'identificacao__emissao',
        'tipo_operacao': 'identificacao__tipo_operacao',
        'status': 'status',
        'empresa': 'empresa__cod_empresa',
        'natureza': 'identificacao__natureza_operacao',
        'filial': 'filial__cod_filial',
    }
    return qs.order_by(parse_relatorio_order(request, order_nfe, '-identificacao__emissao'))


def queryset_relatorio_cte(request: HttpRequest, params: RelatorioParams):
    if not params.cod_empresas and not params.cod_cliente:
        return CTe.objects.none()
    if params.empresa_id:
        qs = CTe.objects.filter(empresa__cod_empresa__in=params.cod_empresas).select_related(
            'identificacao', 'empresa', 'filial'
        )
    else:
        qs = CTe.objects.filter(
            Q(empresa__cod_empresa__in=params.cod_empresas)
            | Q(empresa__isnull=True, gdfcliente__cod_cliente=params.cod_cliente)
        ).select_related('identificacao', 'empresa', 'filial')
    filial_id = parse_filial_id(request, params.cod_empresas)
    if filial_id:
        qs = qs.filter(filial_id=filial_id)
    if params.busca:
        qs = qs.filter(
            Q(identificacao__chave_acesso__icontains=params.busca)
            | Q(identificacao__numero__icontains=params.busca)
            | Q(identificacao__serie__icontains=params.busca)
        )
    dt_ini = parse_date_safe(params.data_inicio)
    if dt_ini:
        qs = qs.filter(identificacao__emissao__date__gte=dt_ini)
    dt_fim = parse_date_safe(params.data_fim)
    if dt_fim:
        qs = qs.filter(identificacao__emissao__date__lte=dt_fim)
    if params.tem_sap == 'sim':
        qs = qs.filter(tem_sap=True)
    elif params.tem_sap == 'nao':
        qs = qs.filter(tem_sap=False)
    order_cte = {
        'numero': 'identificacao__numero',
        'serie': 'identificacao__serie',
        'chave': 'identificacao__chave_acesso',
        'emissao': 'identificacao__emissao',
        'empresa': 'empresa__cod_empresa',
        'filial': 'filial__cod_filial',
    }
    return qs.order_by(parse_relatorio_order(request, order_cte, '-identificacao__emissao'))


def queryset_relatorio_nfse(request: HttpRequest, params: RelatorioParams):
    if not params.cod_empresas and not params.cod_cliente:
        return NFSe.objects.none()
    if params.empresa_id:
        qs = NFSe.objects.filter(empresa__cod_empresa__in=params.cod_empresas).select_related(
            'identificacao', 'empresa', 'filial'
        )
    else:
        qs = NFSe.objects.filter(
            Q(empresa__cod_empresa__in=params.cod_empresas)
            | Q(empresa__isnull=True, gdfcliente__cod_cliente=params.cod_cliente)
        ).select_related('identificacao', 'empresa', 'filial')
    filial_id = parse_filial_id(request, params.cod_empresas)
    if filial_id:
        qs = qs.filter(filial_id=filial_id)
    if params.busca:
        qs = qs.filter(
            Q(identificacao__chave__icontains=params.busca)
            | Q(identificacao__numero__icontains=params.busca)
        )
    dt_ini = parse_date_safe(params.data_inicio)
    if dt_ini:
        qs = qs.filter(identificacao__emissao__date__gte=dt_ini)
    dt_fim = parse_date_safe(params.data_fim)
    if dt_fim:
        qs = qs.filter(identificacao__emissao__date__lte=dt_fim)
    if params.tem_sap == 'sim':
        qs = qs.filter(tem_sap=True)
    elif params.tem_sap == 'nao':
        qs = qs.filter(tem_sap=False)
    order_nfse = {
        'numero': 'identificacao__numero',
        'chave': 'identificacao__chave',
        'emissao': 'identificacao__emissao',
        'empresa': 'empresa__cod_empresa',
        'filial': 'filial__cod_filial',
    }
    return qs.order_by(parse_relatorio_order(request, order_nfse, '-identificacao__emissao'))


def list_relatorio_sped_items(request: HttpRequest, params: RelatorioParams):
    """
    Lista completa de itens SPED (dicts) como a API JSON antes da paginação,
    respeitando tipo_sped, busca, datas e ordenação.
    """
    cod_empresas = params.cod_empresas
    cod_cliente = params.cod_cliente
    if not cod_empresas and not cod_cliente:
        return []
    q_sped_base = Q(empresa__cod_empresa__in=cod_empresas)
    if cod_cliente:
        q_sped_base |= Q(empresa__isnull=True, gdfcliente__cod_cliente=cod_cliente)
    tipo_sped = request.GET.get('tipo_sped', '').strip().upper()
    busca = params.busca
    data_inicio = params.data_inicio
    data_fim = params.data_fim

    items = []
    if tipo_sped in ('F', 'C'):
        ModelSped = SpedFiscalArquivo if tipo_sped == 'F' else SpedContribuicaoArquivo
        qs = ModelSped.objects.filter(q_sped_base).select_related('empresa')
        if busca:
            qs = qs.filter(Q(nome_arquivo__icontains=busca))
        if data_inicio:
            try:
                dt = parse_date_safe(data_inicio)
                if dt:
                    qs = qs.filter(competencia__gte=dt)
            except Exception:
                pass
        if data_fim:
            try:
                dt = parse_date_safe(data_fim)
                if dt:
                    qs = qs.filter(competencia__lte=dt)
            except Exception:
                pass
        order_sped = {
            'competencia': 'competencia',
            'nome_arquivo': 'nome_arquivo',
            'data_carga': 'data_carga',
            'empresa': 'empresa__cod_empresa',
            'tipo': 'id_arquivo',
        }
        qs = qs.order_by(parse_relatorio_order(request, order_sped, '-data_carga'))
        for arq in qs:
            items.append(
                {
                    'id_arquivo': arq.id_arquivo,
                    'tipo': tipo_sped,
                    'tipo_display': 'Fiscal' if tipo_sped == 'F' else 'Contribuição',
                    'competencia': arq.competencia.isoformat() if arq.competencia else None,
                    'nome_arquivo': arq.nome_arquivo,
                    'data_carga': arq.data_carga.isoformat() if arq.data_carga else None,
                    'empresa': arq.empresa.cod_empresa if arq.empresa else None,
                }
            )
        return items

    qs_f = SpedFiscalArquivo.objects.filter(q_sped_base).select_related('empresa')
    qs_c = SpedContribuicaoArquivo.objects.filter(q_sped_base).select_related('empresa')
    if data_inicio:
        try:
            dt = parse_date_safe(data_inicio)
            if dt:
                qs_f = qs_f.filter(competencia__gte=dt)
                qs_c = qs_c.filter(competencia__gte=dt)
        except Exception:
            pass
    if data_fim:
        try:
            dt = parse_date_safe(data_fim)
            if dt:
                qs_f = qs_f.filter(competencia__lte=dt)
                qs_c = qs_c.filter(competencia__lte=dt)
        except Exception:
            pass
    merged = list(qs_f) + list(qs_c)
    merged.sort(key=lambda a: (a.data_carga or timezone.now()), reverse=True)
    for arq in merged:
        t = 'F' if isinstance(arq, SpedFiscalArquivo) else 'C'
        items.append(
            {
                'id_arquivo': arq.id_arquivo,
                'tipo': t,
                'tipo_display': 'Fiscal' if t == 'F' else 'Contribuição',
                'competencia': arq.competencia.isoformat() if arq.competencia else None,
                'nome_arquivo': arq.nome_arquivo,
                'data_carga': arq.data_carga.isoformat() if arq.data_carga else None,
                'empresa': arq.empresa.cod_empresa if arq.empresa else None,
            }
        )

    if busca:
        b = busca.lower()
        items = [
            it
            for it in items
            if b in (it.get('nome_arquivo') or '').lower() or b in (it.get('tipo_display') or '').lower()
        ]

    order_key_sped = (request.GET.get('order') or '').strip()
    dir_sped = (request.GET.get('dir') or 'desc').strip().lower()
    if dir_sped not in ('asc', 'desc'):
        dir_sped = 'desc'
    _sped_sort_keys = {
        'tipo': lambda it: (it.get('tipo_display') or '').lower(),
        'competencia': lambda it: it.get('competencia') or '',
        'nome_arquivo': lambda it: (it.get('nome_arquivo') or '').lower(),
        'data_carga': lambda it: it.get('data_carga') or '',
        'empresa': lambda it: str(it.get('empresa') or ''),
    }
    if order_key_sped in _sped_sort_keys:
        items.sort(key=_sped_sort_keys[order_key_sped], reverse=(dir_sped == 'desc'))
    return items
