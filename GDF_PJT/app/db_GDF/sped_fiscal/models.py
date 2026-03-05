"""
SPED Fiscal (EFD ICMS/IPI) — schema sped_fiscal.
cod_ver 017+
"""
from django.db import models
from django.utils import timezone
from app.db_GDF.Public.models import Empresas, Clientes


class SpedFiscalArquivo(models.Model):
    """Cabeçalho do arquivo SPED Fiscal (EFD ICMS/IPI)."""
    id_arquivo = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(
        Clientes,
        on_delete=models.CASCADE,
        related_name='sped_fiscal_arquivos',
        null=True,
        blank=True,
        db_column='cod_cliente',
        to_field='cod_cliente',
    )
    empresa = models.ForeignKey(
        Empresas,
        on_delete=models.CASCADE,
        related_name='sped_fiscal_arquivos',
        null=True,
        blank=True,
    )
    competencia = models.DateField(null=True, blank=True)
    nome_arquivo = models.CharField(max_length=255, blank=True, null=True)
    hash_conteudo = models.CharField(max_length=64, blank=True, null=True)
    data_carga = models.DateTimeField(default=timezone.now)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = '"sped_fiscal"."sped_arquivo"'
        indexes = [
            models.Index(fields=['cliente', 'competencia'], name='sf_arquivo_cli_comp'),
            models.Index(fields=['empresa', 'competencia'], name='sf_arquivo_emp_comp'),
            models.Index(fields=['data_carga'], name='sf_arquivo_data_carga'),
            models.Index(fields=['hash_conteudo'], name='sf_arquivo_hash'),
        ]
        ordering = ['-data_carga']

    def __str__(self):
        return f"SPED Fiscal - {self.nome_arquivo or self.id_arquivo}"


class SpedFiscalReg_0000(models.Model):
    """Registro 0000 - Abertura do arquivo digital."""
    id = models.AutoField(primary_key=True)
    arquivo = models.ForeignKey(SpedFiscalArquivo, on_delete=models.CASCADE, related_name='reg_0000')
    linha = models.IntegerField(blank=True, null=True)
    cod_ver = models.CharField(max_length=3, blank=True, null=True)
    cod_fin = models.CharField(max_length=1, blank=True, null=True)
    dt_ini = models.DateField(blank=True, null=True)
    dt_fin = models.DateField(blank=True, null=True)
    nome = models.CharField(max_length=100, blank=True, null=True)
    cnpj = models.CharField(max_length=14, blank=True, null=True)
    cpf = models.CharField(max_length=11, blank=True, null=True)
    uf = models.CharField(max_length=2, blank=True, null=True)
    ie = models.CharField(max_length=14, blank=True, null=True)
    cod_mun = models.CharField(max_length=7, blank=True, null=True)
    im = models.CharField(max_length=15, blank=True, null=True)
    suframa = models.CharField(max_length=9, blank=True, null=True)
    ind_perfil = models.CharField(max_length=1, blank=True, null=True)
    ind_ativ = models.CharField(max_length=1, blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = '"sped_fiscal"."sped_reg_0000"'
        indexes = [models.Index(fields=['arquivo'], name='sf_reg_0000_arquivo')]


class SpedFiscalReg_0001(models.Model):
    """Registro 0001 - Abertura do bloco 0."""
    id = models.AutoField(primary_key=True)
    arquivo = models.ForeignKey(SpedFiscalArquivo, on_delete=models.CASCADE, related_name='reg_0001')
    linha = models.IntegerField(blank=True, null=True)
    ind_mov = models.CharField(max_length=1, blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = '"sped_fiscal"."sped_reg_0001"'
        indexes = [models.Index(fields=['arquivo'], name='sf_reg_0001_arquivo')]


class SpedFiscalReg_0005(models.Model):
    """Registro 0005 - Dados complementares do informante."""
    id = models.AutoField(primary_key=True)
    arquivo = models.ForeignKey(SpedFiscalArquivo, on_delete=models.CASCADE, related_name='reg_0005')
    linha = models.IntegerField(blank=True, null=True)
    fantasia = models.CharField(max_length=60, blank=True, null=True)
    cep = models.CharField(max_length=8, blank=True, null=True)
    end = models.CharField(max_length=60, blank=True, null=True)
    num = models.CharField(max_length=10, blank=True, null=True)
    compl = models.CharField(max_length=60, blank=True, null=True)
    bairro = models.CharField(max_length=60, blank=True, null=True)
    fone = models.CharField(max_length=11, blank=True, null=True)
    fax = models.CharField(max_length=11, blank=True, null=True)
    email = models.CharField(max_length=60, blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = '"sped_fiscal"."sped_reg_0005"'
        indexes = [models.Index(fields=['arquivo'], name='sf_reg_0005_arquivo')]


class SpedFiscalReg_0150(models.Model):
    """Registro 0150 - Cadastro do participante."""
    id = models.AutoField(primary_key=True)
    arquivo = models.ForeignKey(SpedFiscalArquivo, on_delete=models.CASCADE, related_name='reg_0150')
    linha = models.IntegerField(blank=True, null=True)
    cod_part = models.CharField(max_length=60, db_index=True, blank=True, null=True)
    nome = models.CharField(max_length=100, blank=True, null=True)
    cod_pais = models.CharField(max_length=3, blank=True, null=True)
    cnpj = models.CharField(max_length=14, blank=True, null=True)
    cpf = models.CharField(max_length=11, blank=True, null=True)
    ie = models.CharField(max_length=14, blank=True, null=True)
    cod_mun = models.CharField(max_length=7, blank=True, null=True)
    end = models.CharField(max_length=60, blank=True, null=True)
    num = models.CharField(max_length=10, blank=True, null=True)
    compl = models.CharField(max_length=60, blank=True, null=True)
    bairro = models.CharField(max_length=60, blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = '"sped_fiscal"."sped_reg_0150"'
        indexes = [models.Index(fields=['arquivo'], name='sf_reg_0150_arquivo'), models.Index(fields=['cod_part'], name='sf_reg_0150_codpart')]


class SpedFiscalReg_0190(models.Model):
    """Registro 0190 - Identificação das unidades de medida."""
    id = models.AutoField(primary_key=True)
    arquivo = models.ForeignKey(SpedFiscalArquivo, on_delete=models.CASCADE, related_name='reg_0190')
    linha = models.IntegerField(blank=True, null=True)
    unid = models.CharField(max_length=6, blank=True, null=True)
    descr = models.CharField(max_length=255, blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = '"sped_fiscal"."sped_reg_0190"'
        indexes = [models.Index(fields=['arquivo'], name='sf_reg_0190_arquivo')]


class SpedFiscalReg_0200(models.Model):
    """Registro 0200 - Cadastro do item."""
    id = models.AutoField(primary_key=True)
    arquivo = models.ForeignKey(SpedFiscalArquivo, on_delete=models.CASCADE, related_name='reg_0200')
    linha = models.IntegerField(blank=True, null=True)
    cod_item = models.CharField(max_length=60, db_index=True, blank=True, null=True)
    descr_item = models.CharField(max_length=255, blank=True, null=True)
    cod_barra = models.CharField(max_length=14, blank=True, null=True)
    cod_ant_item = models.CharField(max_length=60, blank=True, null=True)
    unid_inv = models.CharField(max_length=6, blank=True, null=True)
    tipo_item = models.CharField(max_length=2, blank=True, null=True)
    cod_ncm = models.CharField(max_length=8, blank=True, null=True)
    ex_ipi = models.CharField(max_length=3, blank=True, null=True)
    cod_gen = models.CharField(max_length=2, blank=True, null=True)
    cod_lst = models.CharField(max_length=5, blank=True, null=True)
    aliq_icms = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = '"sped_fiscal"."sped_reg_0200"'
        indexes = [models.Index(fields=['arquivo'], name='sf_reg_0200_arquivo'), models.Index(fields=['cod_item'], name='sf_reg_0200_coditem')]


class SpedFiscalReg_C001(models.Model):
    """Registro C001 - Abertura do bloco C."""
    id = models.AutoField(primary_key=True)
    arquivo = models.ForeignKey(SpedFiscalArquivo, on_delete=models.CASCADE, related_name='reg_c001')
    linha = models.IntegerField(blank=True, null=True)
    ind_mov = models.CharField(max_length=1, blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = '"sped_fiscal"."sped_reg_c001"'
        indexes = [models.Index(fields=['arquivo'], name='sf_reg_c001_arquivo')]


class SpedFiscalReg_C100(models.Model):
    """Registro C100 - Documento fiscal (Nota Fiscal)."""
    id = models.AutoField(primary_key=True)
    arquivo = models.ForeignKey(SpedFiscalArquivo, on_delete=models.CASCADE, related_name='reg_c100')
    linha = models.IntegerField(blank=True, null=True)
    ind_oper = models.CharField(max_length=1, blank=True, null=True)
    ind_emit = models.CharField(max_length=1, blank=True, null=True)
    cod_part = models.CharField(max_length=60, blank=True, null=True)
    cod_mod = models.CharField(max_length=2, blank=True, null=True)
    cod_sit = models.CharField(max_length=2, blank=True, null=True)
    ser = models.CharField(max_length=3, blank=True, null=True)
    num_doc = models.CharField(max_length=9, blank=True, null=True)
    chv_nfe = models.CharField(max_length=44, blank=True, null=True)
    dt_doc = models.DateField(blank=True, null=True)
    dt_e_s = models.DateField(blank=True, null=True)
    vl_doc = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    ind_frt = models.CharField(max_length=1, blank=True, null=True)
    vl_frt = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    vl_seg = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    vl_out_da = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    vl_bc_icms = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    vl_icms = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    vl_bc_icms_st = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    vl_icms_st = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    vl_ipi = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    vl_pis = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    vl_cofins = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    vl_pis_st = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    vl_cofins_st = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = '"sped_fiscal"."sped_reg_c100"'
        indexes = [
            models.Index(fields=['arquivo'], name='sf_reg_c100_arquivo'),
            models.Index(fields=['chv_nfe'], name='sf_reg_c100_chv'),
            models.Index(fields=['dt_doc'], name='sf_reg_c100_dtdoc'),
        ]


class SpedFiscalReg_C170(models.Model):
    """Registro C170 - Item do documento fiscal."""
    id = models.AutoField(primary_key=True)
    arquivo = models.ForeignKey(SpedFiscalArquivo, on_delete=models.CASCADE, related_name='reg_c170')
    c100 = models.ForeignKey(
        SpedFiscalReg_C100,
        on_delete=models.CASCADE,
        related_name='itens_c170',
        null=True,
        blank=True,
    )
    linha = models.IntegerField(blank=True, null=True)
    num_item = models.CharField(max_length=3, blank=True, null=True)
    cod_item = models.CharField(max_length=60, blank=True, null=True)
    descr_compl = models.CharField(max_length=255, blank=True, null=True)
    qtd = models.DecimalField(max_digits=15, decimal_places=4, blank=True, null=True)
    unid = models.CharField(max_length=6, blank=True, null=True)
    vl_item = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    vl_desc = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    ind_mov = models.CharField(max_length=1, blank=True, null=True)
    cst_icms = models.CharField(max_length=3, blank=True, null=True)
    cfop = models.CharField(max_length=4, blank=True, null=True)
    cod_nat = models.CharField(max_length=10, blank=True, null=True)
    vl_bc_icms = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    aliq_icms = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    vl_icms = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    vl_bc_icms_st = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    aliq_st = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    vl_icms_st = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    cst_pis = models.CharField(max_length=2, blank=True, null=True)
    vl_bc_pis = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    aliq_pis = models.DecimalField(max_digits=15, decimal_places=4, blank=True, null=True)
    vl_pis = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    cst_cofins = models.CharField(max_length=2, blank=True, null=True)
    vl_bc_cofins = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    aliq_cofins = models.DecimalField(max_digits=15, decimal_places=4, blank=True, null=True)
    vl_cofins = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = '"sped_fiscal"."sped_reg_c170"'
        indexes = [models.Index(fields=['arquivo'], name='sf_reg_c170_arquivo'), models.Index(fields=['c100'], name='sf_reg_c170_c100')]


class SpedFiscalReg_C190(models.Model):
    """Registro C190 - Registro analítico do documento (ICMS por CST)."""
    id = models.AutoField(primary_key=True)
    arquivo = models.ForeignKey(SpedFiscalArquivo, on_delete=models.CASCADE, related_name='reg_c190')
    c100 = models.ForeignKey(
        SpedFiscalReg_C100,
        on_delete=models.CASCADE,
        related_name='itens_c190',
        null=True,
        blank=True,
    )
    linha = models.IntegerField(blank=True, null=True)
    cst_icms = models.CharField(max_length=3, blank=True, null=True)
    cfop = models.CharField(max_length=4, blank=True, null=True)
    aliq_icms = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    vl_opr = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    vl_bc_icms = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    vl_icms = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    vl_bc_icms_st = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    vl_icms_st = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    vl_red_bc = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    vl_ipi = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    cod_obs = models.CharField(max_length=6, blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = '"sped_fiscal"."sped_reg_c190"'
        indexes = [models.Index(fields=['arquivo'], name='sf_reg_c190_arquivo'), models.Index(fields=['c100'], name='sf_reg_c190_c100')]


class SpedFiscalReg_D100(models.Model):
    """Registro D100 - Documento de transporte (CT-e, NF-e de serviço)."""
    id = models.AutoField(primary_key=True)
    arquivo = models.ForeignKey(SpedFiscalArquivo, on_delete=models.CASCADE, related_name='reg_d100')
    linha = models.IntegerField(blank=True, null=True)
    ind_oper = models.CharField(max_length=1, blank=True, null=True)
    ind_emit = models.CharField(max_length=1, blank=True, null=True)
    cod_part = models.CharField(max_length=60, blank=True, null=True)
    cod_mod = models.CharField(max_length=2, blank=True, null=True)
    cod_sit = models.CharField(max_length=2, blank=True, null=True)
    ser = models.CharField(max_length=3, blank=True, null=True)
    sub_ser = models.CharField(max_length=3, blank=True, null=True)
    num_doc = models.CharField(max_length=9, blank=True, null=True)
    chv_cte = models.CharField(max_length=44, blank=True, null=True)
    dt_doc = models.DateField(blank=True, null=True)
    dt_a_p = models.DateField(blank=True, null=True)
    tp_ct_e = models.CharField(max_length=1, blank=True, null=True)
    chv_cte_ref = models.CharField(max_length=44, blank=True, null=True)
    vl_doc = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    vl_desc = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    ind_frt = models.CharField(max_length=1, blank=True, null=True)
    vl_frt = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    vl_seg = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    vl_out_da = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    vl_bc_icms = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    vl_icms = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    vl_nf = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    cod_inf = models.CharField(max_length=6, blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = '"sped_fiscal"."sped_reg_d100"'
        indexes = [
            models.Index(fields=['arquivo'], name='sf_reg_d100_arquivo'),
            models.Index(fields=['chv_cte'], name='sf_reg_d100_chv'),
            models.Index(fields=['dt_doc'], name='sf_reg_d100_dtdoc'),
        ]


class SpedFiscalRegistro(models.Model):
    """Registros sem tabela específica: tipo, linha e campos em JSON."""
    id = models.AutoField(primary_key=True)
    arquivo = models.ForeignKey(SpedFiscalArquivo, on_delete=models.CASCADE, related_name='registros')
    registro = models.CharField(max_length=20, db_index=True)
    linha = models.IntegerField(blank=True, null=True)
    campos = models.JSONField(default=dict, blank=True)
    conteudo = models.TextField(blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = '"sped_fiscal"."sped_registro"'
        indexes = [
            models.Index(fields=['arquivo'], name='sf_registro_arquivo'),
            models.Index(fields=['arquivo', 'registro'], name='sf_registro_arq_reg'),
        ]
