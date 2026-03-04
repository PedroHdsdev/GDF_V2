"""
Modelos do módulo Reprocessamento.
Confronto SPED Fiscal (EFD ICMS/IPI) x XMLs NF-e, divergências e rastreabilidade.
Schema: reprocessamento (banco default, escalável e auditável).
"""
from django.db import models
from django.utils import timezone


class ReprocessamentoLote(models.Model):
    """
    Lote de confronto: uma execução de comparação SPED x NFe para uma empresa/competência.
    Rastreabilidade: quem, quando, escopo e resultado.
    """
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('EM_CONFRONTO', 'Em confronto'),
        ('CONCLUIDO', 'Concluído'),
        ('ERRO', 'Erro'),
        ('CANCELADO', 'Cancelado'),
    ]

    id_lote = models.BigAutoField(primary_key=True)
    # Escopo: empresa e competência (sempre por mês: 1º dia do mês)
    cod_empresa = models.CharField(max_length=10, db_index=True)  # FK lógica; evita cross-schema FK
    # Indica se o confronto foi "todas as empresas" ou "várias empresas" (para exibição no painel)
    escopo_empresas = models.CharField(
        max_length=10,
        choices=[('UMA', 'Uma empresa'), ('VARIAS', 'Várias empresas'), ('TODAS', 'Todas as empresas')],
        default='UMA',
    )
    competencia = models.DateField(
        help_text='Competência do confronto (mês): armazenada como 1º dia do mês (ex.: 2025-03-01 = mar/2025)',
        db_index=True,
    )
    # Identificação do arquivo SPED usado (opcional; pode ser id do sped.sped_arquivo)
    id_arquivo_sped = models.IntegerField(blank=True, null=True, db_index=True)
    # Contagens após confronto
    total_nfe_esperado = models.IntegerField(default=0, blank=True, null=True)
    total_nfe_encontrado = models.IntegerField(default=0, blank=True, null=True)
    total_divergencias = models.IntegerField(default=0, blank=True, null=True)
    # Status e auditoria
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE', db_index=True)
    mensagem_erro = models.TextField(blank=True, null=True)
    usuario_criacao = models.CharField(max_length=120, blank=True, null=True)
    usuario_atualizacao = models.CharField(max_length=120, blank=True, null=True)
    data_inicio = models.DateTimeField(blank=True, null=True)
    data_fim = models.DateTimeField(blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = '"reprocessamento"."reprocessamento_lote"'
        indexes = [
            models.Index(fields=['cod_empresa', 'competencia']),
            models.Index(fields=['status', 'data_criacao']),
        ]
        ordering = ['-data_criacao']
        verbose_name = 'Lote de reprocessamento'
        verbose_name_plural = 'Lotes de reprocessamento'

    def __str__(self):
        return f"Lote #{self.id_lote} {self.cod_empresa} {self.competencia} ({self.get_status_display()})"


class Divergencia(models.Model):
    """
    Uma divergência encontrada no confronto SPED x NFe.
    Tipos: estrutural (documento faltando/sobrando), fiscal (valor, CFOP, etc.).
    """
    TIPO_CHOICES = [
        ('NFE_AUSENTE_SPED', 'NF-e ausente no SPED'),
        ('SPED_AUSENTE_NFE', 'Registro SPED sem NF-e'),
        ('VALOR_DIFERENTE', 'Valor divergente'),
        ('CFOP_DIFERENTE', 'CFOP divergente'),
        ('DATA_EMISSAO_DIFERENTE', 'Data de emissão divergente'),
        ('CANCELAMENTO', 'Cancelamento/denegação'),
        ('OUTRO', 'Outra inconsistência'),
    ]
    STATUS_CHOICES = [
        ('ABERTA', 'Aberta'),
        ('EM_REPROCESSAMENTO', 'Em reprocessamento'),
        ('RESOLVIDA', 'Resolvida'),
        ('IGNORADA', 'Ignorada'),
    ]

    id_divergencia = models.BigAutoField(primary_key=True)
    lote = models.ForeignKey(
        ReprocessamentoLote,
        on_delete=models.CASCADE,
        related_name='divergencias',
        db_index=True,
    )
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES, db_index=True)
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='ABERTA', db_index=True)
    # Referências: chave NF-e (44 chars) e/ou referência ao registro SPED
    chave_nfe = models.CharField(max_length=44, blank=True, null=True, db_index=True)
    numero_nfe = models.CharField(max_length=20, blank=True, null=True)
    serie_nfe = models.CharField(max_length=5, blank=True, null=True)
    registro_sped = models.CharField(max_length=20, blank=True, null=True)
    linha_sped = models.IntegerField(blank=True, null=True)
    # Descrição legível e dados para reprocessamento
    descricao = models.TextField(blank=True, null=True)
    valor_esperado = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    valor_encontrado = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    detalhe_json = models.JSONField(blank=True, null=True)  # payload opcional para auditoria
    # Rastreabilidade de reprocessamento
    id_nfe = models.IntegerField(blank=True, null=True, db_index=True)  # nfe.nfe.id_nfe se existir
    data_reprocessamento = models.DateTimeField(blank=True, null=True)
    usuario_reprocessamento = models.CharField(max_length=120, blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = '"reprocessamento"."divergencia"'
        indexes = [
            models.Index(fields=['lote', 'tipo']),
            models.Index(fields=['chave_nfe']),
            models.Index(fields=['status']),
        ]
        ordering = ['-data_criacao']
        verbose_name = 'Divergência'
        verbose_name_plural = 'Divergências'

    def __str__(self):
        return f"Divergência #{self.id_divergencia} {self.get_tipo_display()} - {self.chave_nfe or self.registro_sped or '-'}"


class ReprocessamentoJob(models.Model):
    """
    Job de execução (confronto em lote ou reprocessamento em massa).
    Auditoria: início, fim, status, quantidade processada.
    """
    TIPO_CHOICES = [
        ('CONFRONTO', 'Confronto SPED x NFe'),
        ('REPROCESSAR_ITEM', 'Reprocessar item'),
        ('REPROCESSAR_LOTE', 'Reprocessar lote'),
    ]
    STATUS_CHOICES = [
        ('AGUARDANDO', 'Aguardando'),
        ('EM_EXECUCAO', 'Em execução'),
        ('CONCLUIDO', 'Concluído'),
        ('ERRO', 'Erro'),
        ('CANCELADO', 'Cancelado'),
    ]

    id_job = models.BigAutoField(primary_key=True)
    tipo = models.CharField(max_length=25, choices=TIPO_CHOICES, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AGUARDANDO', db_index=True)
    # Escopo
    id_lote = models.BigIntegerField(blank=True, null=True, db_index=True)
    ids_divergencias = models.JSONField(blank=True, null=True)  # lista de id_divergencia
    # Resultado
    total_processados = models.IntegerField(default=0)
    total_erros = models.IntegerField(default=0)
    mensagem = models.TextField(blank=True, null=True)
    usuario = models.CharField(max_length=120, blank=True, null=True)
    data_inicio = models.DateTimeField(blank=True, null=True)
    data_fim = models.DateTimeField(blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = '"reprocessamento"."reprocessamento_job"'
        indexes = [
            models.Index(fields=['tipo', 'status']),
            models.Index(fields=['data_criacao']),
        ]
        ordering = ['-data_criacao']
        verbose_name = 'Job de reprocessamento'
        verbose_name_plural = 'Jobs de reprocessamento'

    def __str__(self):
        return f"Job #{self.id_job} {self.get_tipo_display()} ({self.get_status_display()})"


class CondicaoPagamentoLote(models.Model):
    """
    Tabela de chaves NF-e (44) e condições de pagamento por lote.
    Usada para ajustar no SAP a condição de pagamento do pedido de compra via RFC.
    condicao_pagamento_sap: preenchida antes do RFC e/ou atualizada com o retorno do SAP.
    """
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('ENVIADO_SAP', 'Enviado ao SAP'),
        ('PROCESSADO_SAP', 'Processado no SAP'),
    ]

    id_reg = models.BigAutoField(primary_key=True)
    lote = models.ForeignKey(
        ReprocessamentoLote,
        on_delete=models.CASCADE,
        related_name='condicoes_pagamento',
        db_index=True,
    )
    chave_nfe = models.CharField(max_length=44, db_index=True)
    numero_nfe = models.CharField(max_length=20, blank=True, null=True)
    serie_nfe = models.CharField(max_length=5, blank=True, null=True)
    # Condição extraída da NF-e (ex.: "3x em 28/35/42 dias")
    condicao_pagamento_nfe = models.CharField(max_length=120, blank=True, null=True)
    # Condição SAP: preenchida antes do RFC e atualizada com o retorno após processamento
    condicao_pagamento_sap = models.CharField(max_length=60, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE', db_index=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = '"reprocessamento"."condicao_pagamento_lote"'
        unique_together = [['lote', 'chave_nfe']]
        indexes = [
            models.Index(fields=['lote', 'status']),
        ]
        ordering = ['chave_nfe']
        verbose_name = 'Condição de pagamento (lote)'
        verbose_name_plural = 'Condições de pagamento (lote)'

    def __str__(self):
        return f"{self.chave_nfe} — {self.condicao_pagamento_nfe or '-'}"

class CondicaoParam(models.Model):
    condicao_pagamento_nfe = models.CharField(max_length=120, blank=True, null=True)
    condicao_pagamento_sap = models.CharField(max_length=60, blank=True, null=True)

    class Meta:
        managed = True
        db_table = '"reprocessamento"."condicao_param"'
        unique_together = [['condicao_pagamento_nfe', 'condicao_pagamento_sap']]
        indexes = [
            models.Index(fields=['condicao_pagamento_nfe', 'condicao_pagamento_sap']),
        ]
        ordering = ['condicao_pagamento_nfe']
        verbose_name = 'Condição de pagamento'
        verbose_name_plural = 'Condições de pagamento'
    
    def __str__(self):
        return f"{self.condicao_pagamento_nfe} — {self.condicao_pagamento_sap or '-'}"