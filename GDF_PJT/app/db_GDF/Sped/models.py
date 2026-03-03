"""
Schema SPED: tabela principal com tipo 'C' (Contribuição) / 'F' (Fiscal),
e tabelas Sped_Fiscal e Sped_Contribuicao para os registros de cada tipo.
"""
from django.db import models
from django.utils import timezone
from app.db_GDF.Public.models import Empresas


class Sped_Arquivo(models.Model):
    """
    Tabela principal do SPED. Campo tipo identifica:
    'C' = Contribuição (EFD Contribuições)
    'F' = Fiscal (EFD ICMS/IPI)
    """
    TIPO_CHOICES = [
        ('C', 'Contribuição'),
        ('F', 'Fiscal'),
    ]

    id_arquivo = models.AutoField(primary_key=True)
    tipo = models.CharField(
        max_length=1,
        choices=TIPO_CHOICES,
        help_text="C = Contribuição (EFD Contribuições), F = Fiscal (EFD ICMS/IPI)",
    )
    empresa = models.ForeignKey(
        Empresas,
        on_delete=models.CASCADE,
        related_name='sped_arquivos',
        null=True,
        blank=True,
    )
    competencia = models.DateField(
        help_text="Competência do arquivo (ex.: primeiro dia do mês)",
        null=True,
        blank=True,
    )
    nome_arquivo = models.CharField(max_length=255, blank=True, null=True)
    data_carga = models.DateTimeField(default=timezone.now)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = '"sped"."sped_arquivo"'
        indexes = [
            models.Index(fields=['tipo']),
            models.Index(fields=['empresa', 'competencia']),
            models.Index(fields=['data_carga']),
        ]
        ordering = ['-data_carga']

    def __str__(self):
        return f"SPED {self.get_tipo_display()} - {self.nome_arquivo or self.id_arquivo}"


class Sped_Fiscal(models.Model):
    """Registros/lines do SPED Fiscal (EFD ICMS/IPI). Vinculado a Sped_Arquivo com tipo='F'."""
    id_fiscal = models.AutoField(primary_key=True)
    arquivo = models.ForeignKey(
        Sped_Arquivo,
        on_delete=models.CASCADE,
        related_name='registros_fiscal',
    )
    bloco = models.CharField(max_length=10, blank=True, null=True)
    registro = models.CharField(max_length=20, blank=True, null=True)
    conteudo = models.TextField(blank=True, null=True)
    linha = models.IntegerField(blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = '"sped"."sped_fiscal"'
        indexes = [
            models.Index(fields=['arquivo']),
            models.Index(fields=['arquivo', 'bloco']),
        ]

    def __str__(self):
        return f"Fiscal #{self.arquivo_id} - {self.bloco or '-'}"


class Sped_Contribuicao(models.Model):
    """Registros/lines do SPED Contribuição (EFD Contribuições). Vinculado a Sped_Arquivo com tipo='C'."""
    id_contribuicao = models.AutoField(primary_key=True)
    arquivo = models.ForeignKey(
        Sped_Arquivo,
        on_delete=models.CASCADE,
        related_name='registros_contribuicao',
    )
    bloco = models.CharField(max_length=10, blank=True, null=True)
    registro = models.CharField(max_length=20, blank=True, null=True)
    conteudo = models.TextField(blank=True, null=True)
    linha = models.IntegerField(blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = '"sped"."sped_contribuicao"'
        indexes = [
            models.Index(fields=['arquivo']),
            models.Index(fields=['arquivo', 'bloco']),
        ]

    def __str__(self):
        return f"Contribuição #{self.arquivo_id} - {self.bloco or '-'}"
