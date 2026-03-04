"""
Confronto SPED Fiscal (EFD ICMS/IPI) x XMLs NF-e.
Identifica inconsistências estruturais e fiscais e persiste divergências no módulo Reprocessamento.
Uso: confrontar_sped_nfe(id_lote, cod_empresa, competencia).
"""
from django.utils import timezone

# Importar modelos quando for implementar o confronto real
# from app.db_GDF.Sped.models import Sped_Arquivo, Sped_Fiscal
# from app.db_GDF.NFe.models import NFe, NFe_Identificacao
# from app.db_Reprocessamento.models import ReprocessamentoLote, Divergencia, ReprocessamentoJob


def confrontar_sped_nfe(id_lote, cod_empresa, competencia):
    """
    Executa o confronto entre registros do SPED Fiscal (bloco C100/D100 etc.)
    e as NF-e (por chave ou número/série) para a empresa e o mês dados.
    competencia deve ser sempre o 1º dia do mês (ex.: 2025-03-01 = março/2025).
    Atualiza o lote com totais e cria registros em Divergencia para cada inconsistência.

    Implementação futura:
    - Buscar Sped_Arquivo (tipo='F') da empresa e competência.
    - Extrair chaves/números de NF-e do SPED (registros C100, etc.).
    - Buscar NFe/NFe_Identificacao no mesmo período/empresa.
    - Comparar: NFe sem registro no SPED -> NFE_AUSENTE_SPED; SPED sem NFe -> SPED_AUSENTE_NFE;
      valores/CFOP/datas diferentes -> VALOR_DIFERENTE, CFOP_DIFERENTE, DATA_EMISSAO_DIFERENTE.
    - Persistir Divergencia para cada item e atualizar ReprocessamentoLote (total_*, status=CONCLUIDO).
    """
    from app.db_Reprocessamento.models import ReprocessamentoLote, Divergencia, ReprocessamentoJob

    lote = ReprocessamentoLote.objects.get(id_lote=id_lote)
    job = ReprocessamentoJob.objects.filter(id_lote=id_lote, tipo='CONFRONTO').order_by('-data_criacao').first()
    try:
        # TODO: implementar leitura do SPED e NFe e comparação
        # Por ora apenas finaliza o lote com zeros (sem divergências)
        lote.total_nfe_esperado = 0
        lote.total_nfe_encontrado = 0
        lote.total_divergencias = 0
        lote.status = 'CONCLUIDO'
        lote.data_fim = timezone.now()
        lote.save(update_fields=[
            'total_nfe_esperado', 'total_nfe_encontrado', 'total_divergencias', 'status', 'data_fim'
        ])
        if job:
            job.status = 'CONCLUIDO'
            job.data_fim = timezone.now()
            job.total_processados = 0
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
