from django.db import models
from django.utils import timezone
from app.db_GDF.Public.models import Empresas, Clientes


class NFe_Endereco(models.Model):
    """Tabela base para armazenar endereços reutilizáveis"""
    id_endereco = models.AutoField(primary_key=True)
    logradouro = models.CharField(max_length=60, blank=True, null=True)
    numero = models.CharField(max_length=60, blank=True, null=True)
    complemento = models.CharField(max_length=60, blank=True, null=True)
    bairro = models.CharField(max_length=60, blank=True, null=True)
    codigo_municipio = models.CharField(max_length=7, blank=True, null=True)
    nome_municipio = models.CharField(max_length=60, blank=True, null=True)
    uf = models.CharField(max_length=2, blank=True, null=True)
    cep = models.CharField(max_length=8, blank=True, null=True)
    pais = models.CharField(max_length=4, default='1058', blank=True, null=True)  # Código IBGE para Brasil
    nome_pais = models.CharField(max_length=60, default='Brasil', blank=True, null=True)
    telefone = models.CharField(max_length=14, blank=True, null=True)
    email = models.EmailField(max_length=60, blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = '"nfe"."nfe_endereco"'
        indexes = [
            models.Index(fields=['codigo_municipio', 'uf']),
        ]

    def __str__(self):
        return f"{self.logradouro}, {self.numero} - {self.bairro}"


class NFe_Emitente(models.Model):
    """Dados do emitente da NF-e"""
    id_emitente = models.AutoField(primary_key=True)
    cnpj = models.CharField(max_length=14, unique=True)
    razao_social = models.CharField(max_length=120)
    nome_fantasia = models.CharField(max_length=60, blank=True, null=True)
    ie = models.CharField(max_length=14, blank=True, null=True)
    ie_st = models.CharField(max_length=14, blank=True, null=True)  # IE Substituto Tributário
    im = models.CharField(max_length=60, blank=True, null=True)  # Inscrição Municipal
    cnae_fiscal = models.CharField(max_length=7, blank=True, null=True)
    crt = models.CharField(max_length=1, choices=[('1', 'Simples Nacional'), ('2', 'Simples Nacional com Excesso'), ('3', 'Regime Normal')], blank=True, null=True)
    endereco = models.OneToOneField(NFe_Endereco, on_delete=models.SET_NULL, null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = '"nfe"."nfe_emitente"'
        indexes = [
            models.Index(fields=['cnpj', 'razao_social']),
        ]

    def __str__(self):
        return f"{self.razao_social} - {self.cnpj}"


class NFe_Destinatario(models.Model):
    """Dados do destinatário da NF-e"""
    id_destinatario = models.AutoField(primary_key=True)
    tipo = models.CharField(max_length=1, choices=[('1', 'CNPJ'), ('2', 'CPF')], default='1')
    documento = models.CharField(max_length=14)
    razao_social = models.CharField(max_length=120, blank=True, null=True)
    nome_fantasia = models.CharField(max_length=60, blank=True, null=True)
    ie = models.CharField(max_length=14, blank=True, null=True)  # Opcional para CPF
    isuf = models.CharField(max_length=9, blank=True, null=True)  # Inscrição SUFRAMA
    im = models.CharField(max_length=60, blank=True, null=True)
    email = models.EmailField(max_length=60, blank=True, null=True)
    endereco = models.OneToOneField(NFe_Endereco, on_delete=models.SET_NULL, null=True, blank=True)
    indicador_ie = models.CharField(max_length=1, choices=[('1', 'Contribuinte ICMS'), ('2', 'Não contribuinte'), ('9', 'Exterior')], default='1')
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = '"nfe"."nfe_destinatario"'
        indexes = [
            models.Index(fields=['documento', 'tipo']),
        ]

    def __str__(self):
        return f"{self.razao_social or 'S/N'} - {self.documento}"


class NFe_Identificacao(models.Model):
    """Identificação e informações gerais da NF-e"""
    id_identificacao = models.AutoField(primary_key=True)
    numero = models.CharField(max_length=9)
    serie = models.CharField(max_length=3)
    emissao = models.DateTimeField()
    saida_entrada = models.DateTimeField(blank=True, null=True)
    tipo_documento = models.CharField(max_length=1, choices=[('0', 'Entrada'), ('1', 'Saída')], default='1')
    tipo_operacao = models.CharField(max_length=1, choices=[('0', 'Entrada'), ('1', 'Saída')], default='1')
    municipio = models.CharField(max_length=7)
    tipo_impressao = models.CharField(max_length=1, choices=[('1', 'DANFE Normal'), ('2', 'DANFE Simplificado'), ('3', 'DANFE NFC-e'), ('4', 'DANFE NFC-e em contingência'), ('5', 'DANFE Consumidor')], default='1')
    tipo_emissao = models.CharField(max_length=1, choices=[('1', 'Normal'), ('2', 'Contingência'), ('3', 'Regime Especial NFF'), ('4', 'NF-e avulsa'), ('5', 'NF-e avulsa consumidor'), ('6', 'Contingência NFF'), ('7', 'Autorização pela SVC-RS'), ('8', 'Autorização pela SVC-SP')], default='1')
    ambiente = models.CharField(max_length=1, choices=[('1', 'Produção'), ('2', 'Homologação')], default='2')
    finalidade = models.CharField(max_length=1, choices=[('1', 'NF-e normal'), ('2', 'NF-e complementar'), ('3', 'NF-e ajuste'), ('4', 'Devolução/Retorno')], default='1')
    consumidor_final = models.BooleanField(default=True)  # S=Sim, N=Não
    presencial = models.CharField(max_length=1, choices=[('0', 'Não se aplica'), ('1', 'Presencial'), ('2', 'Internet'), ('3', 'Telefone'), ('4', 'Notafiscal'), ('5', 'Outros')], default='0')
    chave_acesso = models.CharField(max_length=44, unique=True)
    dv_chave = models.CharField(max_length=1)
    digito_rastreamento = models.CharField(max_length=1, blank=True, null=True)
    referencia_nfe = models.CharField(max_length=44, blank=True, null=True)  # Para NF-e de referência
    codigo_municipio = models.CharField(max_length=7, blank=True, null=True)
    natureza_operacao = models.CharField(max_length=60, blank=True, null=True)
    uf = models.CharField(max_length=2, blank=True, null=True)
    modelo = models.CharField(max_length=2, default='55', blank=True, null=True)
    forma_emissao = models.CharField(max_length=1, blank=True, null=True)
    finalidade_emissao = models.CharField(max_length=1, blank=True, null=True)
    presenca_comprador = models.CharField(max_length=1, blank=True, null=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        managed = True
        db_table = '"nfe"."nfe_identificacao"'
        indexes = [
            models.Index(fields=['chave_acesso', 'numero', 'serie']),
            models.Index(fields=['emissao']),
        ]

    def __str__(self):
        return f"NF-e {self.numero}/{self.serie} - {self.chave_acesso}"


class NFe_Produto(models.Model):
    """Produtos/Serviços contidos na NF-e"""
    id_produto = models.AutoField(primary_key=True)
    descricao = models.CharField(max_length=120)
    ncm = models.CharField(max_length=8, blank=True, null=True)  # Nomenclatura Comum do Mercosul
    cfop = models.CharField(max_length=4, blank=True, null=True)  # Código Fiscal de Operações
    cest = models.CharField(max_length=7, blank=True, null=True)  # Código Especificador da Substituição Tributária
    nfe_serie = models.ForeignKey(NFe_Identificacao, on_delete=models.CASCADE, related_name='produtos')
    numero_item = models.IntegerField()
    
    # Dados do produto
    codigo_interno = models.CharField(max_length=60, blank=True, null=True)
    ean = models.CharField(max_length=14, blank=True, null=True)
    ean_tributavel = models.CharField(max_length=14, blank=True, null=True)
    
    # Quantidades e valores
    quantidade = models.DecimalField(max_digits=15, decimal_places=4)
    quantidade_tributavel = models.DecimalField(max_digits=15, decimal_places=4, blank=True, null=True)
    valor_unitario = models.DecimalField(max_digits=15, decimal_places=2)
    valor_unitario_tributavel = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    valor_total = models.DecimalField(max_digits=15, decimal_places=2)
    valor_desconto = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, null=True)
    valor_outras_despesas = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, null=True)
    
    # Unidade
    unidade = models.CharField(max_length=6, blank=True, null=True)  # UN, KG, L, etc
    
    # Informações complementares
    indicador_total = models.BooleanField(default=True)
    origem = models.CharField(max_length=1, choices=[('0', 'Nacional'), ('1', 'Estrangeira - Importação Direta'), ('2', 'Estrangeira - Adquirida no Mercado Interno')], default='0')
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = '"nfe"."nfe_produto"'
        indexes = [
            models.Index(fields=['nfe_serie', 'numero_item']),
            models.Index(fields=['ncm']),
        ]

    def __str__(self):
        return f"{self.numero_item} - {self.descricao}"


class NFe_ICMS(models.Model):
    """Informações de ICMS do produto"""
    id_icms = models.AutoField(primary_key=True)
    produto = models.OneToOneField(NFe_Produto, on_delete=models.CASCADE, related_name='icms')
    
    origem = models.CharField(max_length=1, choices=[('0', 'Nacional'), ('3', 'Exterior'), ('4', 'Exterior - Importação'), ('5', 'Exterior - Adquirida'), ('8', 'Nacional com conteúdo importado')], default='0')
    # CST (2 dígitos) ou CSOSN/Simples Nacional (3 dígitos: 101, 102, 201, 900, etc.)
    cst = models.CharField(max_length=3, choices=[
        ('00', 'Tributada integralmente'),
        ('10', 'Tributada e com cobrança do ICMS por ST'),
        ('20', 'Com redução de base de cálculo'),
        ('30', 'Isenta ou não tributada e com cobrança do ICMS por ST'),
        ('40', 'Isenta'),
        ('41', 'Não tributada'),
        ('50', 'Suspensão'),
        ('51', 'Diferimento'),
        ('60', 'ICMS cobrado anteriormente por ST'),
        ('70', 'Com redução de base de cálculo e cobrança do ICMS por ST'),
        ('90', 'Outras operações'),
    ])
    
    aliquota = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    aliquota_st = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)  # ST
    valor_base_calculo = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    valor_icms = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    percentual_reducao = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    valor_base_st = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    valor_icms_st = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    valor_base_st_dest = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)  # Crédito ST
    valor_icms_st_dest = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    excecao_tipi_cst = models.CharField(max_length=2, blank=True, null=True)  # Campo EX TIPI
    uf = models.CharField(max_length=2, blank=True, null=True)

    class Meta:
        managed = True
        db_table = '"nfe"."nfe_icms"'

    def __str__(self):
        return f"ICMS - CST {self.cst}"


class NFe_IPI(models.Model):
    """Informações de IPI do produto"""
    id_ipi = models.AutoField(primary_key=True)
    produto = models.OneToOneField(NFe_Produto, on_delete=models.CASCADE, related_name='ipi')
    
    cst = models.CharField(max_length=2, choices=[
        ('00', 'Entrada tributada'),
        ('01', 'Entrada não tributada'),
        ('02', 'Saída tributada'),
        ('03', 'Saída não tributada'),
        ('04', 'Saída isenta'),
        ('05', 'Outras operações'),
        ('49', 'Outras operações'),
        ('50', 'Compra para o exterior'),
        ('99', 'Outras operações'),
    ], blank=True, null=True)
    
    enquadramento_legal = models.CharField(max_length=3, blank=True, null=True)
    aliquota = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    valor_base_calculo = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    valor_ipi = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    selagem = models.CharField(max_length=1, choices=[('S', 'Sim'), ('N', 'Não')], default='N')

    class Meta:
        managed = True
        db_table = '"nfe"."nfe_ipi"'

    def __str__(self):
        return f"IPI - CST {self.cst}"


class NFe_PIS(models.Model):
    """Informações de PIS do produto"""
    id_pis = models.AutoField(primary_key=True)
    produto = models.OneToOneField(NFe_Produto, on_delete=models.CASCADE, related_name='pis')
    
    cst = models.CharField(max_length=2, choices=[
        ('01', 'Operação tributável'),
        ('02', 'Operação tributável com alíquota zero'),
        ('03', 'Operação isenta'),
        ('04', 'Operação isenta da contribuição'),
        ('05', 'Operação com suspensão da contribuição'),
        ('06', 'Importação de bem estrangeiro'),
        ('07', 'Aquisição em licitação'),
        ('08', 'Aquisição mediante dação em pagamento'),
        ('09', 'Outras operações'),
        ('49', 'Outras operações'),
        ('50', 'Saída com suspensão'),
        ('51', 'Outras operações'),
        ('52', 'Outras operações'),
        ('53', 'Outras operações'),
        ('54', 'Outras operações'),
        ('55', 'Outras operações'),
        ('56', 'Outras operações'),
        ('60', 'Aquisição com suspensão'),
        ('61', 'Outras operações'),
        ('62', 'Outras operações'),
        ('63', 'Outras operações'),
        ('64', 'Outras operações'),
        ('65', 'Outras operações'),
        ('66', 'Outras operações'),
        ('67', 'Outras operações'),
        ('68', 'Outras operações'),
        ('69', 'Outras operações'),
        ('70', 'Aquisição com suspensão'),
        ('71', 'Aquisição com suspensão'),
        ('72', 'Aquisição com suspensão'),
        ('73', 'Aquisição com suspensão'),
        ('74', 'Aquisição com suspensão'),
        ('75', 'Aquisição com suspensão'),
        ('98', 'Outras operações'),
        ('99', 'Outras operações'),
    ])
    
    aliquota = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    valor_base_calculo = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    valor_pis = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    quantidade_vendida = models.DecimalField(max_digits=15, decimal_places=4, blank=True, null=True)
    aliquota_quantidade = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = True
        db_table = '"nfe"."nfe_pis"'

    def __str__(self):
        return f"PIS - CST {self.cst}"


class NFe_COFINS(models.Model):
    """Informações de COFINS do produto"""
    id_cofins = models.AutoField(primary_key=True)
    produto = models.OneToOneField(NFe_Produto, on_delete=models.CASCADE, related_name='cofins')
    
    cst = models.CharField(max_length=2, choices=[
        ('01', 'Operação tributável'),
        ('02', 'Operação tributável com alíquota zero'),
        ('03', 'Operação isenta'),
        ('04', 'Operação isenta da contribuição'),
        ('05', 'Operação com suspensão da contribuição'),
        ('06', 'Importação de bem estrangeiro'),
        ('07', 'Aquisição em licitação'),
        ('08', 'Aquisição mediante dação em pagamento'),
        ('09', 'Outras operações'),
        ('49', 'Outras operações'),
        ('50', 'Saída com suspensão'),
        ('51', 'Outras operações'),
        ('52', 'Outras operações'),
        ('53', 'Outras operações'),
        ('54', 'Outras operações'),
        ('55', 'Outras operações'),
        ('56', 'Outras operações'),
        ('60', 'Aquisição com suspensão'),
        ('61', 'Outras operações'),
        ('62', 'Outras operações'),
        ('63', 'Outras operações'),
        ('64', 'Outras operações'),
        ('65', 'Outras operações'),
        ('66', 'Outras operações'),
        ('67', 'Outras operações'),
        ('68', 'Outras operações'),
        ('69', 'Outras operações'),
        ('70', 'Aquisição com suspensão'),
        ('71', 'Aquisição com suspensão'),
        ('72', 'Aquisição com suspensão'),
        ('73', 'Aquisição com suspensão'),
        ('74', 'Aquisição com suspensão'),
        ('75', 'Aquisição com suspensão'),
        ('98', 'Outras operações'),
        ('99', 'Outras operações'),
    ])
    
    aliquota = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    valor_base_calculo = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    valor_cofins = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    quantidade_vendida = models.DecimalField(max_digits=15, decimal_places=4, blank=True, null=True)
    aliquota_quantidade = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = True
        db_table = '"nfe"."nfe_cofins"'

    def __str__(self):
        return f"COFINS - CST {self.cst}"


class NFe_Total(models.Model):
    """Totalizações da NF-e"""
    id_total = models.AutoField(primary_key=True)
    nfe_identificacao = models.OneToOneField(NFe_Identificacao, on_delete=models.CASCADE, related_name='totalizacao')
    
    valor_subtotal_produtos = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    valor_frete = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, null=True)
    valor_seguro = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, null=True)
    valor_desconto = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, null=True)
    valor_outras_despesas = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, null=True)
    valor_total_tributos = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, null=True)
    
    valor_base_icms = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, null=True)
    valor_icms = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, null=True)
    valor_icms_st = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, null=True)
    valor_ipi = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, null=True)
    valor_pis = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, null=True)
    valor_cofins = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, null=True)
    
    valor_total_nfe = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    valor_servicos = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, null=True)
    valor_base_pis = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, null=True)
    valor_base_cofins = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, null=True)
    
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = '"nfe"."nfe_total"'

    def __str__(self):
        return f"Total: R$ {self.valor_total_nfe}"


class NFe_Transporte(models.Model):
    """Informações de transporte da NF-e"""
    id_transporte = models.AutoField(primary_key=True)
    nfe_identificacao = models.OneToOneField(NFe_Identificacao, on_delete=models.CASCADE, related_name='transporte')
    
    modalidade = models.CharField(max_length=1, choices=[
        ('0', 'Contratação do Frete por conta do Remetente'),
        ('1', 'Contratação do Frete por conta do Destinatário'),
        ('2', 'Contratação do Frete por conta de Terceiros'),
        ('3', 'Transporte Próprio por conta do Remetente'),
        ('4', 'Transporte Próprio por conta do Destinatário'),
        ('9', 'Sem ocorrência de transporte'),
    ], default='9')
    
    valor_frete = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, null=True)
    
    # Transportador
    transportador_tipo = models.CharField(max_length=1, choices=[('1', 'CNPJ'), ('2', 'CPF')], blank=True, null=True)
    transportador_documento = models.CharField(max_length=14, blank=True, null=True)
    transportador_razao = models.CharField(max_length=120, blank=True, null=True)
    transportador_inscricao = models.CharField(max_length=14, blank=True, null=True)
    transportador_endereco = models.CharField(max_length=60, blank=True, null=True)
    transportador_uf = models.CharField(max_length=2, blank=True, null=True)
    transportador_telefone = models.CharField(max_length=14, blank=True, null=True)
    
    # Veículo
    veiculo_placa = models.CharField(max_length=8, blank=True, null=True)
    veiculo_uf = models.CharField(max_length=2, blank=True, null=True)
    veiculo_rntc = models.CharField(max_length=20, blank=True, null=True)
    veiculo_tara = models.IntegerField(blank=True, null=True)
    veiculo_capac_max = models.IntegerField(blank=True, null=True)
    
    # Reboque
    reboque_placa = models.CharField(max_length=8, blank=True, null=True)
    reboque_uf = models.CharField(max_length=2, blank=True, null=True)
    reboque_rntc = models.CharField(max_length=20, blank=True, null=True)
    reboque_tara = models.IntegerField(blank=True, null=True)
    reboque_capac_max = models.IntegerField(blank=True, null=True)
    
    lacre_numero = models.CharField(max_length=60, blank=True, null=True)
    lacre_uf = models.CharField(max_length=2, blank=True, null=True)
    
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = '"nfe"."nfe_transporte"'

    def __str__(self):
        return f"Transporte - Modalidade {self.modalidade}"


class NFe_Cobranca(models.Model):
    """Informações de cobrança da NF-e"""
    id_cobranca = models.AutoField(primary_key=True)
    nfe_identificacao = models.OneToOneField(NFe_Identificacao, on_delete=models.CASCADE, related_name='cobranca')
    
    # Dados bancários
    banco = models.CharField(max_length=5, blank=True, null=True)
    agencia = models.CharField(max_length=6, blank=True, null=True)
    agencia_dv = models.CharField(max_length=1, blank=True, null=True)
    conta = models.CharField(max_length=12, blank=True, null=True)
    conta_dv = models.CharField(max_length=1, blank=True, null=True)
    cnpj_banco = models.CharField(max_length=14, blank=True, null=True)
    
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = '"nfe"."nfe_cobranca"'

    def __str__(self):
        return f"Cobrança - Banco {self.banco}"


class NFe_Parcela(models.Model):
    """Parcelas de pagamento"""
    id_parcela = models.AutoField(primary_key=True)
    nfe_cobranca = models.ForeignKey(NFe_Cobranca, on_delete=models.CASCADE, related_name='parcelas')
    
    numero_parcela = models.IntegerField()
    data_vencimento = models.DateField()
    valor_parcela = models.DecimalField(max_digits=15, decimal_places=2)
    dias_desconto = models.IntegerField(blank=True, null=True)
    percentual_desconto = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    valor_desconto = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    data_desconto = models.DateField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = '"nfe"."nfe_parcela"'
        indexes = [
            models.Index(fields=['nfe_cobranca', 'numero_parcela']),
        ]

    def __str__(self):
        return f"Parcela {self.numero_parcela} - R$ {self.valor_parcela}"


class NFe_Pagamento(models.Model):
    """Informações de pagamento da NF-e"""
    id_pagamento = models.AutoField(primary_key=True)
    nfe_identificacao = models.OneToOneField(NFe_Identificacao, on_delete=models.CASCADE, related_name='pagamento')
    
    meio_pagamento = models.CharField(max_length=2, choices=[
        ('01', 'Dinheiro'),
        ('02', 'Cheque'),
        ('03', 'Cartão de Crédito'),
        ('04', 'Cartão de Débito'),
        ('05', 'Crédito Loja'),
        ('10', 'Vale Documento'),
        ('11', 'Vale Refeição'),
        ('12', 'Vale Alimentação'),
        ('13', 'Vale-Vale'),
        ('14', 'Sala (Crediário)'),
        ('15', 'Transferência eletrônica de fundos (TEF)'),
        ('16', 'Programa de fidelização, cartão ou vale'),
        ('17', 'Sem pagamento'),
        ('18', 'Boleto Bancário'),
        ('19', 'Depósito Bancário'),
        ('20', 'Pagamento Instantâneo (PIX)'),
        ('21', 'Transação na nuvem'),
        ('99', 'Outros'),
    ])
    
    valor_pago = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Cartão de crédito/débito
    cartao_bandeira = models.CharField(max_length=2, choices=[
        ('01', 'Visa'),
        ('02', 'Mastercard'),
        ('03', 'American Express'),
        ('04', 'Sorocred'),
        ('05', 'Diners Club'),
        ('06', 'Elo'),
        ('07', 'Hipercard'),
        ('08', 'Aura'),
        ('09', 'Discover'),
        ('99', 'Outros'),
    ], blank=True, null=True)
    
    cartao_cnpj = models.CharField(max_length=14, blank=True, null=True)  # CNPJ da adquirente
    cartao_numero_autoriza = models.CharField(max_length=20, blank=True, null=True)
    
    # PIX
    pix_tipo_chave = models.CharField(max_length=1, choices=[
        ('1', 'CPF'),
        ('2', 'CNPJ'),
        ('3', 'Telefone'),
        ('4', 'Email'),
        ('5', 'Aleatória'),
    ], blank=True, null=True)
    pix_chave = models.CharField(max_length=140, blank=True, null=True)
    
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = '"nfe"."nfe_pagamento"'

    def __str__(self):
        return f"Pagamento - {self.get_meio_pagamento_display()}"


class NFe_Informacoes_Adicionais(models.Model):
    """Informações adicionais e complementares da NF-e"""
    id_info_adic = models.AutoField(primary_key=True)
    nfe_identificacao = models.OneToOneField(NFe_Identificacao, on_delete=models.CASCADE, related_name='informacoes_adicionais')
    
    informacoes_complementares = models.TextField(blank=True, null=True)
    informacoes_interesse_fisco = models.TextField(blank=True, null=True)
    xped = models.CharField(max_length=60, blank=True, null=True, help_text='Número do pedido de compra (tag xPed do XML)')
    resposta_json = models.TextField(blank=True, null=True)  # Resposta da autorização da SEFAZ
    
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = '"nfe"."nfe_informacoes_adicionais"'

    def __str__(self):
        return f"Informações Adicionais"


class NFe(models.Model):
    """Tabela principal de NF-e - Documento fiscal"""
    id_nfe = models.AutoField(primary_key=True)
    identificacao = models.OneToOneField(NFe_Identificacao, on_delete=models.CASCADE, related_name='nfe')
    empresa = models.ForeignKey(Empresas, on_delete=models.CASCADE, related_name='nfe_docs', null=True, blank=True)  # Ao apagar empresa (ex.: ao apagar cliente), apaga NFe vinculadas
    cliente = models.ForeignKey(
        Clientes,
        on_delete=models.CASCADE,
        related_name='nfe_docs',
        null=True,
        blank=True,
        db_column='cod_cliente',
        to_field='cod_cliente',
    )
    emitente = models.ForeignKey(NFe_Emitente, on_delete=models.PROTECT)
    destinatario = models.ForeignKey(NFe_Destinatario, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Status da NF-e
    status = models.CharField(max_length=20, choices=[
        ('DRAFT', 'Rascunho'),
        ('ASSINADA', 'Assinada'),
        ('ENVIADA', 'Enviada para autorização'),
        ('AUTORIZADA', 'Autorizada'),
        ('CANCELADA', 'Cancelada'),
        ('DENEGADA', 'Denegada'),
        ('REJEITADA', 'Rejeitada'),
        ('CONTINGENCIA', 'Em Contingência'),
    ], default='DRAFT')
    
    protocolo_autorizacao = models.CharField(max_length=15, blank=True, null=True)
    data_autorizacao = models.DateTimeField(blank=True, null=True)
    
    # XML
    xml_assinado = models.TextField(blank=True, null=True)
    xml_resposta = models.TextField(blank=True, null=True)
    
    # Rastreamento
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    usuario_criacao = models.CharField(max_length=120, blank=True, null=True)
    usuario_atualizacao = models.CharField(max_length=120, blank=True, null=True)
    origem_dados = models.CharField(max_length=8, choices=[
        ('LOCAL', 'Maquina Local'),
        ('SAP', 'Importação SAP'),
        ('SPED', 'Importação SPED'),
        ('OUTROS', 'Outros'),
    ], default='LOCAL')

    class Meta:
        managed = True
        db_table = '"nfe"."nfe"'
        indexes = [
            models.Index(fields=['status', 'data_criacao']),
            models.Index(fields=['identificacao']),
            models.Index(fields=['emitente', 'destinatario']),
            models.Index(fields=['empresa']),
            models.Index(fields=['cliente']),
        ]
        ordering = ['-data_criacao']

    def __str__(self):
        return f"NF-e {self.identificacao.numero}/{self.identificacao.serie} - {self.status}"


class NFe_Documento(models.Model):
    """Documentos vinculados a uma NF-e (ex: Compra, MIRO, MIGO)."""
    id_documento = models.AutoField(primary_key=True)
    nfe = models.ForeignKey(NFe, on_delete=models.CASCADE, related_name='documentos')
    tipo_documento = models.CharField(
        max_length=20,
        choices=[
            ('COMPRA', 'Compra'),
            ('MIRO', 'MIRO'),
            ('MIGO', 'MIGO'),
            ('OUTROS', 'Outros'),
        ],
        default='COMPRA'
    )
    numero_documento = models.CharField(max_length=40)
    data_documento = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, default='PENDENTE')
    observacao = models.CharField(max_length=255, blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = '"nfe"."nfe_documento"'
        indexes = [
            models.Index(fields=['nfe', 'tipo_documento']),
            models.Index(fields=['numero_documento']),
        ]

    def __str__(self):
        return f"{self.tipo_documento} - {self.numero_documento}"


class NFe_DocumentoItem(models.Model):
    """Itens dos documentos vinculados a uma NF-e."""
    id_item = models.AutoField(primary_key=True)
    documento = models.ForeignKey(NFe_Documento, on_delete=models.CASCADE, related_name='itens')
    nfe_produto = models.ForeignKey(
        NFe_Produto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documento_itens'
    )
    sequencia = models.IntegerField()
    material = models.CharField(max_length=60, blank=True, null=True)
    descricao = models.CharField(max_length=120, blank=True, null=True)
    quantidade = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    unidade = models.CharField(max_length=10, blank=True, null=True)
    valor_unitario = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    valor_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = '"nfe"."nfe_documento_item"'
        indexes = [
            models.Index(fields=['documento', 'sequencia']),
            models.Index(fields=['nfe_produto']),
        ]

    def __str__(self):
        return f"Item {self.sequencia} - {self.descricao or ''}"
