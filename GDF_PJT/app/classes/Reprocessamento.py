"""
Confronto SPED Fiscal (EFD ICMS/IPI) x XMLs NF-e.
Identifica inconsistências: NF-e sem SPED, SPED sem NF-e, e persiste divergências.
Funciona mesmo sem SPED (só XML): todas as NF-e do mês aparecem como divergência "NF-e ausente no SPED".
Condições de pagamento: extração a partir das parcelas da NFe e geração da tabela por lote para uso no SAP.
"""
import re
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
    Considera tanto EFD ICMS/IPI (tipo F) quanto EFD Contribuições (tipo C) — ambos têm C100 com chv_nfe.
    Usa Sped_Reg_C100 (chv_nfe) e Sped_Registro (D100). Retorna set de chaves (44 dígitos).
    Filtra por mês/ano da competência. Considera empresa, cliente ou empresa=None com CNPJ no 0000.
    """
    from app.db_GDF.Sped.models import Sped_Arquivo, Sped_Reg_C100, Sped_Registro, Sped_Reg_0000
    from app.db_GDF.Public.models import Empresas

    chaves = set()
    try:
        empresa = Empresas.objects.get(cod_empresa=cod_empresa)
        cnpj_empresa = (empresa.cnpj or '').replace('.', '').replace('/', '').replace('-', '').strip()[:14]
    except Empresas.DoesNotExist:
        return chaves
    # Filtro por mês/ano. Tipo F (Fiscal) e C (Contribuições) — ambos têm C100 com chaves NF-e
    arquivos = Sped_Arquivo.objects.filter(
        empresa=empresa,
        tipo__in=['F', 'C'],
        competencia__year=competencia.year,
        competencia__month=competencia.month,
    )
    # Se não achou com empresa vinculada, tenta arquivos com cliente (SPED vinculado ao cliente)
    # ou empresa=None cujo 0000 tem mesmo CNPJ
    cod_cliente = getattr(empresa.cliente, 'cod_cliente', None) if empresa.cliente else None
    if not arquivos.exists():
        # Por cliente: SPED vinculado ao cliente da empresa (filtra por CNPJ pois 1 cliente = várias empresas)
        if cod_cliente and cnpj_empresa:
            qs_cliente = Sped_Arquivo.objects.filter(
                cliente_id=cod_cliente,
                tipo__in=['F', 'C'],
                competencia__year=competencia.year,
                competencia__month=competencia.month,
            )
            ids_por_cliente = []
            for arq in qs_cliente:
                reg0000 = Sped_Reg_0000.objects.filter(arquivo=arq).first()
                if not reg0000 or not reg0000.cnpj:
                    continue
                cnpj_arq = (reg0000.cnpj or '').replace('.', '').replace('/', '').replace('-', '').strip()[:14]
                if cnpj_arq == cnpj_empresa:
                    ids_por_cliente.append(arq.id_arquivo)
            if ids_por_cliente:
                arquivos = Sped_Arquivo.objects.filter(id_arquivo__in=ids_por_cliente)
        # Fallback: empresa=None, mesmo CNPJ no 0000
        if not arquivos.exists() and cnpj_empresa:
            ids_sem_empresa = []
            qs_sem_empresa = Sped_Arquivo.objects.filter(empresa__isnull=True, tipo__in=['F', 'C'])
            if cod_cliente:
                qs_sem_empresa = qs_sem_empresa.filter(cliente_id=cod_cliente)
            qs_sem_empresa = qs_sem_empresa.filter(
                competencia__year=competencia.year,
                competencia__month=competencia.month,
            )
            for arq in qs_sem_empresa:
                reg0000 = Sped_Reg_0000.objects.filter(arquivo=arq).first()
                if not reg0000 or not reg0000.cnpj:
                    continue
                cnpj_arq = (reg0000.cnpj or '').replace('.', '').replace('/', '').replace('-', '').strip()[:14]
                if cnpj_arq != cnpj_empresa:
                    continue
                # Verifica mês: por competencia ou por dt_ini do 0000
                if arq.competencia and arq.competencia.year == competencia.year and arq.competencia.month == competencia.month:
                    ids_sem_empresa.append(arq.id_arquivo)
                elif reg0000.dt_ini and reg0000.dt_ini.year == competencia.year and reg0000.dt_ini.month == competencia.month:
                    ids_sem_empresa.append(arq.id_arquivo)
            if ids_sem_empresa:
                arquivos = Sped_Arquivo.objects.filter(id_arquivo__in=ids_sem_empresa)
    if not arquivos.exists():
        return chaves
    padrao_chave = re.compile(r'\d{44}')
    for arq in arquivos:
        for c100 in Sped_Reg_C100.objects.filter(arquivo=arq):
            ch = _normalizar_chave(c100.chv_nfe)
            if ch:
                chaves.add(ch)
        for reg in Sped_Registro.objects.filter(arquivo=arq, registro='D100'):
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


def _condicao_sap_da_param(condicao_nfe, cod_cliente=None):
    """
    Busca condicao_pagamento_sap em CondicaoParam pelo condicao_pagamento_nfe (depara).
    Filtra por cod_cliente quando informado. Retorna string ou '' se não houver correspondência.
    """
    from app.db_Reprocessamento.models import CondicaoParam

    if not (condicao_nfe or '').strip():
        return ''
    cond_nfe = (condicao_nfe or '').strip()[:120]
    base_qs = CondicaoParam.objects.filter(condicao_pagamento_nfe=cond_nfe)
    if cod_cliente:
        base_qs = base_qs.filter(cliente_id=cod_cliente)
    # Preferir registro com condicao_pagamento_sap preenchida
    obj = base_qs.exclude(condicao_pagamento_sap='').order_by('condicao_pagamento_sap').first()
    if obj:
        return (obj.condicao_pagamento_sap or '').strip()
    obj = base_qs.first()
    return (obj.condicao_pagamento_sap or '').strip() if obj else ''


def gerar_condicoes_pagamento_lote(id_lote):
    """
    Gera/atualiza registros em CondicaoPagamentoLote para todas as NF-e do lote
    (empresa + competência do lote). Condição NFe é extraída das parcelas.
    Faz depara com CondicaoParam (filtrado por cliente da empresa) para preencher condicao_pagamento_sap;
    se não houver correspondência, fica vazio.
    Retorna (criados, atualizados).
    """
    from app.db_Reprocessamento.models import ReprocessamentoLote, CondicaoPagamentoLote
    from app.db_GDF.NFe.models import NFe
    from app.db_GDF.Public.models import Empresas

    lote = ReprocessamentoLote.objects.get(id_lote=id_lote)
    cod_cliente = None
    try:
        emp = Empresas.objects.get(cod_empresa=lote.cod_empresa)
        cod_cliente = emp.cliente_id if emp.cliente_id else None
    except Empresas.DoesNotExist:
        pass
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
        condicao_sap = _condicao_sap_da_param(condicao_nfe, cod_cliente=cod_cliente)
        obj, created = CondicaoPagamentoLote.objects.update_or_create(
            lote=lote,
            chave_nfe=item['chave_acesso'],
            defaults={
                'numero_nfe': item.get('numero'),
                'serie_nfe': item.get('serie'),
                'condicao_pagamento_nfe': condicao_nfe,
                'condicao_pagamento_sap': condicao_sap,
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
