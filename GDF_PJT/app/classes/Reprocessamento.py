"""
Confronto SPED Fiscal (EFD ICMS/IPI) x XMLs NF-e.
Identifica inconsistências: NF-e sem SPED, SPED sem NF-e, e persiste divergências.
Funciona mesmo sem SPED (só XML): todas as NF-e do mês aparecem como divergência "NF-e ausente no SPED".
Condições de pagamento: extração a partir das parcelas da NFe e geração da tabela por lote para uso no SAP.
"""
import re
from django.db import models
from django.utils import timezone


def _normalizar_chave(chave):
    """Retorna chave de 44 dígitos normalizada (strip) ou None se inválida."""
    if not chave or not isinstance(chave, str):
        return None
    s = chave.strip().replace(' ', '')
    return s if len(s) == 44 and s.isdigit() else None


def _extrair_chaves_sped(competencia, cod_empresa):
    """
    Busca arquivos SPED da empresa/competência e extrai chaves NF-e dos registros C100/D100.
    Considera sped_fiscal e sped_contribuicao — ambos têm C100 com chv_nfe.
    Usa SpedFiscalReg_C100/SpedContribuicaoReg_C100 e SpedFiscalRegistro/SpedContribuicaoRegistro (D100).
    Retorna set de chaves (44 dígitos).
    """
    from app.db_GDF.sped_fiscal.models import (
        SpedFiscalArquivo, SpedFiscalReg_C100, SpedFiscalRegistro, SpedFiscalReg_0000,
    )
    from app.db_GDF.sped_contribuicao.models import (
        SpedContribuicaoArquivo, SpedContribuicaoReg_C100, SpedContribuicaoRegistro, SpedContribuicaoReg_0000,
    )
    from app.db_GDF.Public.models import Empresa

    chaves = set()
    try:
        empresa = Empresa.objects.get(cod_empresa=cod_empresa)
        cnpj_empresa = (empresa.cnpj or '').replace('.', '').replace('/', '').replace('-', '').strip()[:14]
    except Empresa.DoesNotExist:
        return chaves

    arqs_f = SpedFiscalArquivo.objects.filter(
        empresa=empresa,
        competencia__year=competencia.year,
        competencia__month=competencia.month,
    )
    arqs_c = SpedContribuicaoArquivo.objects.filter(
        empresa=empresa,
        competencia__year=competencia.year,
        competencia__month=competencia.month,
    )
    cod_cliente = getattr(empresa.gdfcliente, 'cod_cliente', None) if empresa.gdfcliente else None
    arquivos = list(arqs_f) + list(arqs_c)
    if not arquivos:
        if cod_cliente and cnpj_empresa:
            qs_cf = SpedFiscalArquivo.objects.filter(gdfcliente_id=cod_cliente, competencia__year=competencia.year, competencia__month=competencia.month)
            qs_cc = SpedContribuicaoArquivo.objects.filter(gdfcliente_id=cod_cliente, competencia__year=competencia.year, competencia__month=competencia.month)
            for arq in list(qs_cf) + list(qs_cc):
                Reg0000 = SpedFiscalReg_0000 if isinstance(arq, SpedFiscalArquivo) else SpedContribuicaoReg_0000
                reg0000 = Reg0000.objects.filter(arquivo=arq).first()
                if reg0000 and reg0000.cnpj:
                    cnpj_arq = (reg0000.cnpj or '').replace('.', '').replace('/', '').replace('-', '').strip()[:14]
                    if cnpj_arq == cnpj_empresa:
                        arquivos.append(arq)
        if not arquivos and cnpj_empresa:
            qs_sem_f = SpedFiscalArquivo.objects.filter(empresa__isnull=True, competencia__year=competencia.year, competencia__month=competencia.month)
            qs_sem_c = SpedContribuicaoArquivo.objects.filter(empresa__isnull=True, competencia__year=competencia.year, competencia__month=competencia.month)
            if cod_cliente:
                qs_sem_f = qs_sem_f.filter(gdfcliente_id=cod_cliente)
                qs_sem_c = qs_sem_c.filter(gdfcliente_id=cod_cliente)
            for arq in list(qs_sem_f) + list(qs_sem_c):
                Reg0000 = SpedFiscalReg_0000 if isinstance(arq, SpedFiscalArquivo) else SpedContribuicaoReg_0000
                reg0000 = Reg0000.objects.filter(arquivo=arq).first()
                if reg0000 and reg0000.cnpj:
                    cnpj_arq = (reg0000.cnpj or '').replace('.', '').replace('/', '').replace('-', '').strip()[:14]
                    if cnpj_arq == cnpj_empresa:
                        arquivos.append(arq)
    if not arquivos:
        return chaves
    padrao_chave = re.compile(r'\d{44}')
    for arq in arquivos:
        Reg_C100 = SpedFiscalReg_C100 if isinstance(arq, SpedFiscalArquivo) else SpedContribuicaoReg_C100
        Reg_Registro = SpedFiscalRegistro if isinstance(arq, SpedFiscalArquivo) else SpedContribuicaoRegistro
        for c100 in Reg_C100.objects.filter(arquivo=arq):
            ch = _normalizar_chave(c100.chv_nfe)
            if ch:
                chaves.add(ch)
        for reg in Reg_Registro.objects.filter(arquivo=arq, registro='D100'):
            texto = reg.conteudo or str(reg.campos or '')
            for match in padrao_chave.findall(texto):
                ch = _normalizar_chave(match)
                if ch:
                    chaves.add(ch)
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


def tipo_pagamento_da_nfe(identificacao):
    """
    Retorna o código do tipo de pagamento (tPag) da NF-e, ex.: '01', '02', '20'.
    Usa o primeiro detPag (meio_pagamento) do NFe_Pagamento. Retorna '' se não houver.
    """
    try:
        pag = identificacao.pagamento
        t = (pag.meio_pagamento or '').strip()
        return t[:2] if t else ''
    except Exception:
        return ''


def _condicao_sap_da_param(condicao_nfe, tipo_pagamento=None, cod_cliente=None):
    """
    Busca condicao_pagamento_sap em CondicaoParam pelo condicao_pagamento_nfe e tipo_pagamento (depara).
    Filtra por cod_cliente quando informado.
    Primeiro tenta com tipo_pagamento específico; se não achar, tenta com tipo vazio (fallback).
    Retorna string ou '' se não houver correspondência.
    """
    from app.db_GDF.reprocessamento.models import CondicaoParam

    if not (condicao_nfe or '').strip():
        return ''
    cond_nfe = (condicao_nfe or '').strip()[:120]
    tipo = (tipo_pagamento or '').strip()[:2] if tipo_pagamento else None

    def _buscar(tipo_val):
        qs = CondicaoParam.objects.filter(condicao_pagamento_nfe=cond_nfe)
        if tipo_val is not None and tipo_val != '':
            qs = qs.filter(tipo_pagamento=tipo_val)
        else:
            qs = qs.filter(models.Q(tipo_pagamento='') | models.Q(tipo_pagamento__isnull=True))
        if cod_cliente:
            qs = qs.filter(gdfcliente_id=cod_cliente)
        obj = qs.exclude(condicao_pagamento_sap='').exclude(condicao_pagamento_sap__isnull=True).order_by('condicao_pagamento_sap').first()
        if obj:
            return (obj.condicao_pagamento_sap or '').strip()
        obj = qs.first()
        return (obj.condicao_pagamento_sap or '').strip() if obj else ''

    # Primeiro tenta com tipo específico
    if tipo:
        result = _buscar(tipo)
        if result:
            return result
    # Fallback: tipo vazio (compatibilidade com registros antigos)
    return _buscar(None)


def gerar_condicoes_pagamento_lote(id_lote):
    """
    Gera/atualiza registros em CondicaoPagamentoLote para todas as NF-e do lote
    (empresa + competência do lote). Condição NFe é extraída das parcelas.
    Faz depara com CondicaoParam (filtrado por cliente da empresa) para preencher condicao_pagamento_sap;
    se não houver correspondência, fica vazio.
    Retorna (criados, atualizados).
    """
    from app.db_GDF.reprocessamento.models import ReprocessamentoLote, CondicaoPagamentoLote
    from app.db_GDF.NFe.models import NFe
    from app.db_GDF.Public.models import Empresa

    lote = ReprocessamentoLote.objects.get(id_lote=id_lote)
    cod_cliente = None
    try:
        emp = Empresa.objects.get(cod_empresa=lote.cod_empresa)
        cod_cliente = emp.gdfcliente_id if emp.gdfcliente_id else None
    except Empresa.DoesNotExist:
        pass
    nfe_list = _nfe_do_mes(lote.cod_empresa, lote.competencia)
    if not nfe_list:
        return 0, 0
    ids = [item['id_nfe'] for item in nfe_list]
    nfe_por_id = {
        nfe.id_nfe: nfe
        for nfe in NFe.objects.filter(id_nfe__in=ids).select_related(
            'identificacao', 'identificacao__pagamento'
        ).prefetch_related('identificacao__cobranca__parcelas')
    }
    criados = 0
    atualizados = 0
    for item in nfe_list:
        nfe = nfe_por_id.get(item['id_nfe'])
        if not nfe:
            continue
        condicao_nfe = condicao_pagamento_da_nfe(nfe.identificacao)
        tipo_pag = tipo_pagamento_da_nfe(nfe.identificacao)
        condicao_sap = _condicao_sap_da_param(condicao_nfe, tipo_pagamento=tipo_pag, cod_cliente=cod_cliente)
        obj, created = CondicaoPagamentoLote.objects.update_or_create(
            lote=lote,
            chave_nfe=item['chave_acesso'],
            defaults={
                'numero_nfe': item.get('numero'),
                'serie_nfe': item.get('serie'),
                'condicao_pagamento_nfe': condicao_nfe,
                'condicao_pagamento_sap': condicao_sap,
                'tipo_pagamento': tipo_pag or None,
                'status': 'P',
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
    from app.db_GDF.reprocessamento.models import ReprocessamentoLote, Divergencia, ReprocessamentoJob

    lote = ReprocessamentoLote.objects.get(id_lote=id_lote)
    job = ReprocessamentoJob.objects.filter(id_lote=id_lote, tipo='CONFRONTO').order_by('-data_criacao').first()
    try:
        chaves_sped = _extrair_chaves_sped(competencia, cod_empresa)
        nfe_list = _nfe_do_mes(cod_empresa, competencia)
        chaves_nfe = set()
        nfe_por_chave = {}
        for n in nfe_list:
            ch = _normalizar_chave(n.get('chave_acesso'))
            if ch:
                chaves_nfe.add(ch)
                nfe_por_chave[ch] = n

        total_nfe_esperado = len(chaves_sped)  # documentos esperados pelo SPED
        total_nfe_encontrado = len(nfe_list)   # documentos encontrados nos XMLs
        div_criadas = 0

        # 1) NF-e que existem nos XMLs mas não no SPED (ou não há SPED)
        for n in nfe_list:
            ch = _normalizar_chave(n.get('chave_acesso'))
            if not ch or ch in chaves_sped:
                continue
            descricao = 'NF-e presente nos XMLs e não encontrada no SPED Fiscal.'
            if not chaves_sped:
                descricao = 'NF-e presente nos XMLs. Não há arquivo SPED Fiscal para esta competência.'
            Divergencia.objects.create(
                lote=lote,
                tipo='NFE_AUSENTE_SPED',
                status='ABERTA',
                chave_nfe=ch,
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
