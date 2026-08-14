"""
Modelos do schema SAP (dados importados do SAP para o PostgreSQL).

Tabelas em db_table: "sap"."nome_tabela".
RelatorioCusto vincula-se a Empresa e Filial do GDF (schema public).
"""
from django.db import models

from app.db_GDF.Public.models import Empresa, Filial


class RelatorioCusto(models.Model):
    """
    Relatório de custo importado do SAP.
    Dados de documentos fiscais com custos, impostos, margens, CMV, etc.
    Vinculado à Empresa e Filial do GDF.
    """
    id = models.AutoField(primary_key=True)
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name="Empresa",
        related_name="relatorios_custo_sap",
        db_column="cod_empresa_id",
        to_field="cod_empresa",
    )
    filial = models.ForeignKey(
        Filial,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name="Filial",
        related_name="relatorios_custo_sap",
        db_column="filial_id",
    )
    docnum = models.CharField("Nº Documento", max_length=20)
    mjahr = models.CharField("Ano do Documento", max_length=4, blank=True, null=True)
    mblnr = models.CharField("Nº Documento de Material", max_length=10, blank=True, null=True)
    matnr = models.CharField("Nº do Material", max_length=18, blank=True, null=True)
    nfenum = models.CharField("Número de Documento (9 posições)", max_length=9, blank=True, null=True)
    series = models.CharField("Série", max_length=3, blank=True, null=True)
    docsta = models.CharField("Status do Documento", max_length=1)
    kunnr = models.CharField("Nº Cliente", max_length=10, blank=True, null=True)
    name1 = models.CharField("Cliente", max_length=35, blank=True, null=True)
    ort01 = models.CharField("Cidade", max_length=35, blank=True, null=True)
    chave_acesso = models.CharField("Chave de Acesso", max_length=44, blank=True, null=True)
    itmnum = models.CharField("Nº Item do Documento", max_length=6, blank=True, null=True)
    pstdat = models.DateField("Data de Postagem", blank=True, null=True)
    werks = models.CharField("Local de Negócios", max_length=4, blank=True, null=True)
    name = models.CharField("Nome", max_length=30, blank=True, null=True)
    stcd1 = models.CharField("CNPJ", max_length=16, blank=True, null=True)
    uf_origem = models.CharField("UF de Origem", max_length=3, blank=True, null=True)
    uf_destino = models.CharField("UF de Destino", max_length=3, blank=True, null=True)
    cancel = models.CharField("Status de Cancelamento", max_length=50, blank=True, null=True)
    maktx = models.CharField("Texto Breve do Material", max_length=40, blank=True, null=True)
    mtart = models.CharField("Tipo de Material", max_length=4, blank=True, null=True)
    matkl = models.CharField("Grupo de Mercadorias", max_length=9, blank=True, null=True)
    wgbez = models.CharField("Denominação do Grupo de Mercadorias", max_length=20, blank=True, null=True)
    cfop = models.CharField("CFOP", max_length=10, blank=True, null=True)
    qtd_prod = models.DecimalField("Quantidade de Produto", max_digits=16, decimal_places=3, blank=True, null=True)
    unid_medida = models.CharField("Unidade de Medida de Venda", max_length=3, blank=True, null=True)
    meins = models.CharField("Unidade de Medida Básica", max_length=3, blank=True, null=True)
    umrez = models.DecimalField("Contador Conversão UM", max_digits=8, decimal_places=0, blank=True, null=True)
    menge_umb = models.DecimalField("Qtd Convertida p/ UM Básica", max_digits=16, decimal_places=3, blank=True, null=True)
    prc_unitario = models.DecimalField("Preço Unitário", max_digits=18, decimal_places=2, blank=True, null=True)
    prc_unit_cst_liq = models.DecimalField("Preço Unitário Custo Líquido", max_digits=18, decimal_places=2, blank=True, null=True)
    prc_unit_cst_adm = models.DecimalField("Preço Unitário Custo ADM", max_digits=18, decimal_places=2, blank=True, null=True)
    bc_icms = models.DecimalField("Base de Cálculo ICMS", max_digits=18, decimal_places=2, blank=True, null=True)
    pct_icms = models.DecimalField("Alíquota ICMS", max_digits=8, decimal_places=2, blank=True, null=True)
    vlr_icms = models.DecimalField("Valor ICMS", max_digits=18, decimal_places=2, blank=True, null=True)
    bc_icms_st = models.DecimalField("Base ICMS ST", max_digits=18, decimal_places=2, blank=True, null=True)
    alq_st = models.DecimalField("Alíquota ICMS ST", max_digits=8, decimal_places=2, blank=True, null=True)
    vlr_st = models.DecimalField("Valor ICMS ST", max_digits=18, decimal_places=2, blank=True, null=True)
    bc_ipi = models.DecimalField("Base IPI", max_digits=18, decimal_places=2, blank=True, null=True)
    pct_ipi = models.DecimalField("Alíquota IPI", max_digits=8, decimal_places=2, blank=True, null=True)
    vlr_ipi = models.DecimalField("Valor IPI", max_digits=18, decimal_places=2, blank=True, null=True)
    bc_pis = models.DecimalField("Base PIS", max_digits=18, decimal_places=2, blank=True, null=True)
    pct_pis = models.DecimalField("Alíquota PIS", max_digits=8, decimal_places=2, blank=True, null=True)
    vlr_pis = models.DecimalField("Valor PIS", max_digits=18, decimal_places=2, blank=True, null=True)
    bc_cof = models.DecimalField("Base COFINS", max_digits=18, decimal_places=2, blank=True, null=True)
    pct_cof = models.DecimalField("Alíquota COFINS", max_digits=8, decimal_places=2, blank=True, null=True)
    vlr_cof = models.DecimalField("Valor COFINS", max_digits=18, decimal_places=2, blank=True, null=True)
    tp_doc = models.CharField("Tipo de Documento", max_length=2, blank=True, null=True)
    total_impostos = models.DecimalField("Total de Impostos", max_digits=10, decimal_places=2, blank=True, null=True)
    vlr_desconto = models.DecimalField("Valor de Desconto", max_digits=18, decimal_places=2, blank=True, null=True)
    vlr_frete = models.DecimalField("Valor do Frete", max_digits=18, decimal_places=2, blank=True, null=True)
    vlr_liquido = models.DecimalField("Valor Líquido", max_digits=18, decimal_places=2, blank=True, null=True)
    vlr_tot_doc = models.DecimalField("Valor Total do Documento", max_digits=18, decimal_places=2, blank=True, null=True)
    cmv = models.DecimalField("CMV", max_digits=18, decimal_places=2, blank=True, null=True)
    lucro_0 = models.DecimalField("Lucro 0", max_digits=18, decimal_places=2, blank=True, null=True)
    margem_0 = models.DecimalField("Margem 0", max_digits=18, decimal_places=2, blank=True, null=True)
    margem_contrib = models.DecimalField("Margem Contribuição", max_digits=18, decimal_places=2, blank=True, null=True)
    cmv_gerencial = models.DecimalField("CMV Gerencial", max_digits=18, decimal_places=2, blank=True, null=True)
    lucro_0_gerencial = models.DecimalField("Lucro 0 Gerencial", max_digits=18, decimal_places=2, blank=True, null=True)
    margem_real = models.DecimalField("Margem Real", max_digits=18, decimal_places=2, blank=True, null=True)
    lucro_real = models.DecimalField("Lucro Real", max_digits=18, decimal_places=2, blank=True, null=True)
    margem_contrib_ger = models.DecimalField("Margem Contribuição Gerencial", max_digits=18, decimal_places=2, blank=True, null=True)
    cmv_media = models.DecimalField("CMV Média", max_digits=18, decimal_places=2, blank=True, null=True)
    per_taxa_adm = models.DecimalField("Percentual Taxa ADM", max_digits=6, decimal_places=2, blank=True, null=True)
    vlr_taxa_adm = models.DecimalField("Valor Taxa ADM", max_digits=18, decimal_places=2, blank=True, null=True)
    per_taxa_frt = models.DecimalField("Percentual Taxa Frete", max_digits=6, decimal_places=2, blank=True, null=True)
    vlr_taxa_frt = models.DecimalField("Valor Taxa Frete", max_digits=18, decimal_places=2, blank=True, null=True)
    cmv_ue = models.DecimalField("CMV Última Entrada", max_digits=18, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = True
        db_table = '"sap"."relatorio_custo"'
        verbose_name = "Relatório de Custo"
        verbose_name_plural = "Relatórios de Custo"
        unique_together = (("empresa", "docnum", "mjahr", "mblnr"),)
        indexes = [
            models.Index(fields=["empresa", "docnum", "mjahr", "mblnr"]),
            models.Index(fields=["pstdat"]),
            models.Index(fields=["chave_acesso"]),
            # Índice parcial para o dashboard (CFOP + empresa + período): ver migration 0069.
        ]
        ordering = ["-pstdat", "docnum"]

    def __str__(self):
        return f"{self.docnum} {self.mjahr or ''} {self.mblnr or ''}"
