from django.db import models
from django.utils import timezone
from app.db_GDF.Public.models import Empresa, ClienteGdf, Filial


class NFSe_Endereco(models.Model):
    id_endereco = models.AutoField(primary_key=True)
    logradouro = models.CharField(max_length=60, blank=True, null=True)
    numero = models.CharField(max_length=60, blank=True, null=True)
    complemento = models.CharField(max_length=60, blank=True, null=True)
    bairro = models.CharField(max_length=60, blank=True, null=True)
    codigo_municipio = models.CharField(max_length=7, blank=True, null=True)
    nome_municipio = models.CharField(max_length=60, blank=True, null=True)
    uf = models.CharField(max_length=2, blank=True, null=True)
    cep = models.CharField(max_length=8, blank=True, null=True)
    pais = models.CharField(max_length=4, default='1058', blank=True, null=True)
    nome_pais = models.CharField(max_length=60, default='Brasil', blank=True, null=True)
    telefone = models.CharField(max_length=14, blank=True, null=True)
    email = models.EmailField(max_length=60, blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = '"nfse"."nfse_endereco"'

    def __str__(self):
        return f"{self.logradouro}, {self.numero} - {self.bairro}"


class NFSe_Prestador(models.Model):
    id_prestador = models.AutoField(primary_key=True)
    cnpj = models.CharField(max_length=14, unique=True)
    razao_social = models.CharField(max_length=120)
    nome_fantasia = models.CharField(max_length=60, blank=True, null=True)
    ie = models.CharField(max_length=14, blank=True, null=True)
    endereco = models.OneToOneField(NFSe_Endereco, on_delete=models.SET_NULL, null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = '"nfse"."nfse_prestador"'

    def __str__(self):
        return f"{self.razao_social} - {self.cnpj}"


class NFSe_Tomador(models.Model):
    id_tomador = models.AutoField(primary_key=True)
    tipo = models.CharField(max_length=1, choices=[('1', 'CNPJ'), ('2', 'CPF')], default='1')
    documento = models.CharField(max_length=14)
    razao_social = models.CharField(max_length=120, blank=True, null=True)
    endereco = models.OneToOneField(NFSe_Endereco, on_delete=models.SET_NULL, null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = '"nfse"."nfse_tomador"'

    def __str__(self):
        return f"{self.razao_social or 'S/N'} - {self.documento}"


class NFSe_Identificacao(models.Model):
    id_identificacao = models.AutoField(primary_key=True)
    numero = models.CharField(max_length=20)
    emissao = models.DateTimeField()
    competencia = models.DateTimeField(blank=True, null=True)
    codigo_prefeitura = models.CharField(max_length=7, blank=True, null=True)
    chave = models.CharField(max_length=44, unique=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = '"nfse"."nfse_identificacao"'
        indexes = [
            models.Index(fields=['chave', 'numero']),
            models.Index(fields=['emissao']),
        ]

    def __str__(self):
        return f"NFSe {self.numero} - {self.chave}"


class NFSe_RPS(models.Model):
    """Recibo Provisório de Serviço"""
    id_rps = models.AutoField(primary_key=True)
    numero_rps = models.CharField(max_length=12)
    serie_rps = models.CharField(max_length=5, default="RPS")
    tipo_rps = models.CharField(max_length=10, choices=[
        ("RPS", "Recibo Provisório de Serviço"),
        ("RPS-M", "RPS Misto"),
        ("RPS-C", "RPS Conjugado"),
    ], default="RPS")
    data_emissao_rps = models.DateField()
    status_rps = models.CharField(max_length=20, choices=[
        ("NORMAL", "Normal"),
        ("CANCELADO", "Cancelado"),
        ("PROCESSADO", "Processado"),
    ], default="NORMAL")
    
    # Vinculação com NFSe
    nfse_identificacao = models.ForeignKey(NFSe_Identificacao, on_delete=models.CASCADE, related_name='rps_list')
    numero_nfse_gerada = models.CharField(max_length=12, blank=True, null=True)
    
    # Complementários
    valor_rps = models.DecimalField(max_digits=15, decimal_places=2)
    substituida_por = models.CharField(max_length=12, blank=True, null=True)
    
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = '"nfse"."nfse_rps"'
        unique_together = [('numero_rps', 'serie_rps', 'nfse_identificacao')]

    def __str__(self):
        return f"RPS {self.numero_rps}/{self.serie_rps}"


class NFSe_Retencao(models.Model):
    """Detalhamento de retenções por NFSe"""
    id_retencao = models.AutoField(primary_key=True)
    nfse_identificacao = models.OneToOneField(NFSe_Identificacao, on_delete=models.CASCADE, related_name='retencao')
    
    # IR
    base_calculo_ir = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, null=True)
    aliquota_ir = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True, null=True)
    valor_ir = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # ISS
    base_calculo_issqn = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, null=True)
    aliquota_issqn = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True, null=True)
    valor_issqn = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # INSS
    base_calculo_inss = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, null=True)
    aliquota_inss = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True, null=True)
    valor_inss = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # COFINS
    base_calculo_cofins = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, null=True)
    aliquota_cofins = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True, null=True)
    valor_cofins = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # PIS
    base_calculo_pis = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, null=True)
    aliquota_pis = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True, null=True)
    valor_pis = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # CSLL
    base_calculo_csll = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, null=True)
    aliquota_csll = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True, null=True)
    valor_csll = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    valor_total_retencoes = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = '"nfse"."nfse_retencao"'

    def __str__(self):
        return f"Retenções - Total: R$ {self.valor_total_retencoes}"


class NFSe_Pagamento(models.Model):
    """Informações de pagamento da NFSe"""
    id_pagamento = models.AutoField(primary_key=True)
    nfse_identificacao = models.OneToOneField(NFSe_Identificacao, on_delete=models.CASCADE, related_name='pagamento')
    
    # Forma de pagamento
    forma_pagamento = models.CharField(max_length=30, choices=[
        ("DINHEIRO", "Dinheiro"),
        ("CHEQUE", "Cheque"),
        ("DEPOSITO_BANCARIO", "Depósito Bancário"),
        ("TRANSFERENCIA_BANCARIA", "Transferência Bancária"),
        ("CARTAO_CREDITO", "Cartão de Crédito"),
        ("CARTAO_DEBITO", "Cartão de Débito"),
        ("BOLETO", "Boleto"),
        ("CREDITO_ADIANTAMENTO", "Crédito de Adiantamento"),
    ], default="DINHEIRO")
    
    descricao_forma_pagamento = models.CharField(max_length=90, blank=True, null=True)
    
    # Informações bancárias
    banco = models.CharField(max_length=3, blank=True, null=True)  # código banco
    agencia = models.CharField(max_length=6, blank=True, null=True)
    conta = models.CharField(max_length=20, blank=True, null=True)
    tipo_conta = models.CharField(max_length=15, choices=[
        ("CC", "Conta Corrente"),
        ("CP", "Conta Poupança"),
    ], blank=True, null=True)
    documento_titular = models.CharField(max_length=14, blank=True, null=True)  # CPF/CNPJ
    
    # Valor e condições
    valor_total_pagamento = models.DecimalField(max_digits=15, decimal_places=2)
    data_pagamento = models.DateField(blank=True, null=True)
    
    # Parcelamento
    condicao_pagamento = models.CharField(max_length=50, choices=[
        ("VISTA", "À Vista"),
        ("PRAZO", "À Prazo"),
        ("PARCELADO", "Parcelado"),
    ], default="VISTA")
    
    num_parcelas = models.PositiveIntegerField(default=1, blank=True, null=True)
    data_primeira_parcela = models.DateField(blank=True, null=True)
    intervalo_dias_parcelas = models.PositiveIntegerField(blank=True, null=True)
    
    # Juros/Descontos
    valor_desconto = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    percentual_desconto = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True, null=True)
    
    valor_juros = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    percentual_juros = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True, null=True)
    
    valor_multa = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    percentual_multa = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True, null=True)
    
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = '"nfse"."nfse_pagamento"'

    def __str__(self):
        return f"Pagamento {self.forma_pagamento} - R$ {self.valor_total_pagamento}"


class NFSe_Credenciamento(models.Model):
    """Informações de credenciamento para emissão de RPS/NFSe"""
    id_credenciamento = models.AutoField(primary_key=True)
    nfse_identificacao = models.OneToOneField(NFSe_Identificacao, on_delete=models.CASCADE, related_name='credenciamento')
    
    # Inscrição municipal
    inscricao_municipal = models.CharField(max_length=20)
    optante_simples_nacional = models.BooleanField(default=False)
    
    # Certificado digital
    numero_certificado = models.CharField(max_length=100, blank=True, null=True)
    data_validade = models.DateField(blank=True, null=True)
    
    # Ambiente
    ambiente_emissao = models.CharField(max_length=20, choices=[
        ("PRODUCAO", "Produção"),
        ("HOMOLOGACAO", "Homologação"),
    ], default="PRODUCAO")
    
    # Prefeitura
    codigo_municipio = models.CharField(max_length=7)
    nome_municipio = models.CharField(max_length=60)
    uf = models.CharField(max_length=2)
    
    # Status e autorizações
    ativo = models.BooleanField(default=True)
    data_ultima_consulta = models.DateTimeField(blank=True, null=True)
    
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = '"nfse"."nfse_credenciamento"'

    def __str__(self):
        return f"Credenciamento {self.inscricao_municipal} - {self.nome_municipio}/{self.uf}"


class NFSe_Servico(models.Model):
    id_servico = models.AutoField(primary_key=True)
    descricao = models.CharField(max_length=240)
    quantidade = models.DecimalField(max_digits=15, decimal_places=4, default=1)
    valor_unitario = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    valor_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    nfse_identificacao = models.ForeignKey(NFSe_Identificacao, on_delete=models.CASCADE, related_name='servicos')
    
    # Código do serviço
    codigo_servico = models.CharField(max_length=20, blank=True, null=True)
    aliquota_issqn = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    valor_issqn = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    municipio_incidencia = models.CharField(max_length=7, blank=True, null=True)
    
    # Retenção de impostos
    valor_ir_retido = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, null=True)
    valor_issqn_retido = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, null=True)
    valor_inss_retido = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, null=True)
    valor_cofins_retido = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, null=True)
    valor_pis_retido = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, null=True)
    valor_csll_retido = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, null=True)
    
    # Indicadores
    optante_simples = models.BooleanField(default=False)
    normalizacao = models.BooleanField(default=False)
    
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = '"nfse"."nfse_servico"'

    def __str__(self):
        return f"{self.descricao} - R$ {self.valor_total}"


class NFSe(models.Model):
    id_nfse = models.AutoField(primary_key=True)
    identificacao = models.OneToOneField(NFSe_Identificacao, on_delete=models.CASCADE, related_name='nfse')
    prestador = models.ForeignKey(NFSe_Prestador, on_delete=models.SET_NULL, null=True, blank=True)
    tomador = models.ForeignKey(NFSe_Tomador, on_delete=models.SET_NULL, null=True, blank=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, null=True, blank=True)
    filial = models.ForeignKey(
        Filial,
        on_delete=models.SET_NULL,
        related_name='nfse_docs_filial',
        null=True,
        blank=True,
        db_column='filial_id',
    )
    gdfcliente = models.ForeignKey(
        ClienteGdf,
        on_delete=models.CASCADE,
        related_name='nfse_docs',
        null=True,
        blank=True,
        db_column='cod_cliente',
        to_field='cod_cliente',
    )
    tem_sap = models.BooleanField(default=False, help_text='True se a chave foi encontrada no SAP.')
    sap_nome_tabela = models.CharField(max_length=30, blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = '"nfse"."nfse"'

    def __str__(self):
        return f"NFSe {self.identificacao.numero}"


class NFSe_Evento(models.Model):
    """Eventos vinculados à NFSe (cancelamento, etc.) - carregados via XML de evento."""
    id_evento = models.AutoField(primary_key=True)
    nfse_identificacao = models.ForeignKey(NFSe_Identificacao, on_delete=models.CASCADE, related_name='eventos')
    tipo_evento = models.CharField(max_length=20, blank=True, null=True)
    descricao_evento = models.CharField(max_length=100, blank=True, null=True)
    justificativa = models.TextField(blank=True, null=True)
    data_evento = models.DateTimeField(blank=True, null=True)
    numero_sequencia = models.IntegerField(default=1)
    xml_evento = models.TextField(blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = '"nfse"."nfse_evento"'
        unique_together = [['nfse_identificacao', 'tipo_evento', 'numero_sequencia']]
        indexes = [
            models.Index(fields=['nfse_identificacao', 'tipo_evento']),
        ]

    def __str__(self):
        return f"Evento {self.tipo_evento or '?'} - NFSe {self.nfse_identificacao.numero}"
