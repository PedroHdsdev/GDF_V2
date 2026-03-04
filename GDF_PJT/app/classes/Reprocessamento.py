"""
Confronto SPED Fiscal (EFD ICMS/IPI) x XMLs NF-e.
Identifica inconsistências: NF-e sem SPED, SPED sem NF-e, e persiste divergências.
Funciona mesmo sem SPED (só XML): todas as NF-e do mês aparecem como divergência "NF-e ausente no SPED".
Condições de pagamento: extração a partir das parcelas da NFe e geração da tabela por lote para uso no SAP.
"""
import re
from django.utils import timezone


def _extrair_chaves_sped(competencia, cod_empresa):
    """
    Busca arquivos SPED Fiscal da empresa/competência e extrai chaves NF-e dos registros C100/D100.
    Usa Sped_Reg_C100 (chv_nfe) e Sped_Registro (D100). Retorna set de chaves (44 dígitos).
    """
    from app.db_GDF.Sped.models import Sped_Arquivo, Sped_Reg_C100, Sped_Registro
    from app.db_GDF.Public.models import Empresas

    chaves = set()
    try:
        empresa = Empresas.objects.get(cod_empresa=cod_empresa)
    except Empresas.DoesNotExist:
        return chaves
    arquivos = Sped_Arquivo.objects.filter(empresa=empresa, tipo='F', competencia=competencia)
    if not arquivos.exists():
        return chaves
    padrao_chave = re.compile(r'\d{44}')
    for arq in arquivos:
        for c100 in Sped_Reg_C100.objects.filter(arquivo=arq):
            if c100.chv_nfe and len(c100.chv_nfe) == 44 and c100.chv_nfe.isdigit():
                chaves.add(c100.chv_nfe)
        for reg in Sped_Registro.objects.filter(arquivo=arq, registro='D100'):
            texto = reg.conteudo or str(reg.campos or '')
            for match in padrao_chave.findall(texto):
                if len(match) == 44:
                    chaves.add(match)
    return chaves


def _nfe_do_mes(cod_empresa, competencia):
    """
    Retorna lista de dict com id_nfe, chave_acesso, numero, serie, emissao
    para NF-e da empresa no mês da competência.
    """
    from app.db_GDF.NFe.models import NFe, NFe_Identificacao

    qs = NFe.objects.filter(
        empresa_id=cod_empresa,
        identificacao__emissao__year=competencia.year,
        identificacao__emissao__month=competencia.month,
    ).select_related('identificacao')
    lista = []
    for nfe in qs:
        idn = nfe.identificacao
        lista.append({
            'id_nfe': nfe.id_nfe,
            'chave_acesso': idn.chave_acesso,
            'numero': idn.numero,
            'serie': idn.serie,
            'emissao': idn.emissao,
        })
    return lista


def condicao_pagamento_da_nfe(identificacao):
    """
    Monta a string de condição de pagamento a partir das parcelas da NF-e.
    identificacao: instância de NFe_Identificacao (com emissao).
    Retorna ex.: "3x em 28/35/42 dias", "1x em 28 dias", "À vista" (sem cobrança/parcelas).
    """
    from app.db_GDF.NFe.models import NFe_Cobranca

    try:
        cobranca = identificacao.cobranca
    except NFe_Cobranca.DoesNotExist:
        return 'À vista'
    parcelas = list(cobranca.parcelas.order_by('numero_parcela'))
    if not parcelas:
        return 'À vista'
    emissao_date = identificacao.emissao.date()
    dias = [(p.data_vencimento - emissao_date).days for p in parcelas]
    return f"{len(parcelas)}x em {'/'.join(str(d) for d in dias)} dias"


def gerar_condicoes_pagamento_lote(id_lote):
    """
    Gera/atualiza registros em CondicaoPagamentoLote para todas as NF-e do lote
    (empresa + competência do lote). Condição NFe é extraída das parcelas; SAP e retorno ficam em branco.
    Retorna (criados, atualizados).
    """
    from app.db_Reprocessamento.models import ReprocessamentoLote, CondicaoPagamentoLote
    from app.db_GDF.NFe.models import NFe

    lote = ReprocessamentoLote.objects.get(id_lote=id_lote)
    nfe_list = _nfe_do_mes(lote.cod_empresa, lote.competencia)
    if not nfe_list:
        return 0, 0
    ids = [item['id_nfe'] for item in nfe_list]
    nfe_por_id = {
        nfe.id_nfe: nfe
        for nfe in NFe.objects.filter(id_nfe__in=ids).select_related(
            'identificacao'
        ).prefetch_related('identificacao__cobranca__parcelas')
    }
    criados = 0
    atualizados = 0
    for item in nfe_list:
        nfe = nfe_por_id.get(item['id_nfe'])
        if not nfe:
            continue
        condicao_nfe = condicao_pagamento_da_nfe(nfe.identificacao)
        obj, created = CondicaoPagamentoLote.objects.update_or_create(
            lote=lote,
            chave_nfe=item['chave_acesso'],
            defaults={
                'numero_nfe': item.get('numero'),
                'serie_nfe': item.get('serie'),
                'condicao_pagamento_nfe': condicao_nfe,
                'status': 'PENDENTE',
            },
        )
        if created:
            criados += 1
        else:
            atualizados += 1
    return criados, atualizados


def confrontar_sped_nfe(id_lote, cod_empresa, competencia):
    """
    Executa o confronto entre SPED Fiscal e NF-e (XML) para a empresa e o mês.
    - Se não houver SPED: lista todas as NF-e do mês e registra cada uma como "NF-e ausente no SPED".
    - Se não houver NF-e: lista todas as chaves do SPED e registra cada uma como "Registro SPED sem NF-e".
    - Se houver ambos: cruza por chave e gera divergência para os que não batem.
    """
    from app.db_Reprocessamento.models import ReprocessamentoLote, Divergencia, ReprocessamentoJob

    lote = ReprocessamentoLote.objects.get(id_lote=id_lote)
    job = ReprocessamentoJob.objects.filter(id_lote=id_lote, tipo='CONFRONTO').order_by('-data_criacao').first()
    try:
        chaves_sped = _extrair_chaves_sped(competencia, cod_empresa)
        nfe_list = _nfe_do_mes(cod_empresa, competencia)
        chaves_nfe = {n['chave_acesso'] for n in nfe_list}
        nfe_por_chave = {n['chave_acesso']: n for n in nfe_list}

        total_nfe_esperado = len(chaves_sped)  # documentos esperados pelo SPED
        total_nfe_encontrado = len(nfe_list)   # documentos encontrados nos XMLs
        div_criadas = 0

        # 1) NF-e que existem nos XMLs mas não no SPED (ou não há SPED)
        for n in nfe_list:
            if n['chave_acesso'] not in chaves_sped:
                descricao = 'NF-e presente nos XMLs e não encontrada no SPED Fiscal.'
                if not chaves_sped:
                    descricao = 'NF-e presente nos XMLs. Não há arquivo SPED Fiscal para esta competência.'
                Divergencia.objects.create(
                    lote=lote,
                    tipo='NFE_AUSENTE_SPED',
                    status='ABERTA',
                    chave_nfe=n['chave_acesso'],
                    numero_nfe=n['numero'],
                    serie_nfe=n['serie'],
                    descricao=descricao,
                    id_nfe=n['id_nfe'],
                    detalhe_json={
                        'emissao': n['emissao'].isoformat() if n.get('emissao') else None,
                    },
                )
                div_criadas += 1

        # 2) Chaves que existem no SPED mas não nos XMLs
        for chave in chaves_sped:
            if chave not in chaves_nfe:
                Divergencia.objects.create(
                    lote=lote,
                    tipo='SPED_AUSENTE_NFE',
                    status='ABERTA',
                    chave_nfe=chave,
                    descricao='Documento informado no SPED Fiscal não possui NF-e (XML) correspondente.',
                    registro_sped='C100/D100',
                )
                div_criadas += 1

        lote.total_nfe_esperado = total_nfe_esperado
        lote.total_nfe_encontrado = total_nfe_encontrado
        lote.total_divergencias = div_criadas
        lote.status = 'CONCLUIDO'
        lote.data_fim = timezone.now()
        lote.save(update_fields=[
            'total_nfe_esperado', 'total_nfe_encontrado', 'total_divergencias', 'status', 'data_fim'
        ])
        if job:
            job.status = 'CONCLUIDO'
            job.data_fim = timezone.now()
            job.total_processados = total_nfe_encontrado + len(chaves_sped)
            job.save(update_fields=['status', 'data_fim', 'total_processados'])
    except Exception as e:
        lote.status = 'ERRO'
        lote.mensagem_erro = str(e)[:2000]
        lote.data_fim = timezone.now()
        lote.save(update_fields=['status', 'mensagem_erro', 'data_fim'])
        if job:
            job.status = 'ERRO'
            job.mensagem = str(e)[:2000]
            job.data_fim = timezone.now()
            job.save(update_fields=['status', 'mensagem', 'data_fim'])
        raise
