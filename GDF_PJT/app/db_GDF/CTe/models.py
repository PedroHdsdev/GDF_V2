from django.db import models
from django.utils import timezone
from app.db_GDF.Public.models import Empresas, Clientes


class CTe_Endereco(models.Model):
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
        db_table = '"cte"."cte_endereco"'

    def __str__(self):
        return f"{self.logradouro}, {self.numero} - {self.bairro}"


class CTe_Emitente(models.Model):
    id_emitente = models.AutoField(primary_key=True)
    cnpj = models.CharField(max_length=14, unique=True)
    razao_social = models.CharField(max_length=120)
    nome_fantasia = models.CharField(max_length=60, blank=True, null=True)
    ie = models.CharField(max_length=14, blank=True, null=True)
    endereco = models.OneToOneField(CTe_Endereco, on_delete=models.SET_NULL, null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = '"cte"."cte_emitente"'

    def __str__(self):
        return f"{self.razao_social} - {self.cnpj}"


class CTe_Destinatario(models.Model):
    id_destinatario = models.AutoField(primary_key=True)
    tipo = models.CharField(max_length=1, choices=[('1', 'CNPJ'), ('2', 'CPF')], default='1')
    documento = models.CharField(max_length=14)
    razao_social = models.CharField(max_length=120, blank=True, null=True)
    endereco = models.OneToOneField(CTe_Endereco, on_delete=models.SET_NULL, null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = '"cte"."cte_destinatario"'

    def __str__(self):
        return f"{self.razao_social or 'S/N'} - {self.documento}"


class CTe_Identificacao(models.Model):
    id_identificacao = models.AutoField(primary_key=True)
    numero = models.CharField(max_length=9)
    serie = models.CharField(max_length=3)
    emissao = models.DateTimeField()
    chave_acesso = models.CharField(max_length=44, unique=True)
    modelo = models.CharField(max_length=2, default='57')
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = '"cte"."cte_identificacao"'
        indexes = [
            models.Index(fields=['chave_acesso', 'numero', 'serie']),
            models.Index(fields=['emissao']),
        ]

    def __str__(self):
        return f"CT-e {self.numero}/{self.serie} - {self.chave_acesso}"


class CTe_Valor(models.Model):
    id_valor = models.AutoField(primary_key=True)
    cte_identificacao = models.OneToOneField(CTe_Identificacao, on_delete=models.CASCADE, related_name='valor')
    valor_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = '"cte"."cte_valor"'

    def __str__(self):
        return f"Valor: R$ {self.valor_total}"


class CTe_Transporte(models.Model):
    id_transporte = models.AutoField(primary_key=True)
    cte_identificacao = models.OneToOneField(CTe_Identificacao, on_delete=models.CASCADE, related_name='transporte')
    modal = models.CharField(max_length=1, blank=True, null=True)
    placa = models.CharField(max_length=8, blank=True, null=True)
    uf_placa = models.CharField(max_length=2, blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = '"cte"."cte_transporte"'

    def __str__(self):
        return f"Transporte CTe {self.id_transporte}"


class CTe(models.Model):
    id_cte = models.AutoField(primary_key=True)
    identificacao = models.OneToOneField(CTe_Identificacao, on_delete=models.CASCADE, related_name='cte')
    emitente = models.ForeignKey(CTe_Emitente, on_delete=models.SET_NULL, null=True, blank=True)
    destinatario = models.ForeignKey(CTe_Destinatario, on_delete=models.SET_NULL, null=True, blank=True)
    empresa = models.ForeignKey(Empresas, on_delete=models.CASCADE, null=True, blank=True)
    cliente = models.ForeignKey(
        Clientes,
        on_delete=models.CASCADE,
        related_name='cte_docs',
        null=True,
        blank=True,
        db_column='cod_cliente',
        to_field='cod_cliente',
    )
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = '"cte"."cte"'

    def __str__(self):
        return f"CTe {self.identificacao.numero}/{self.identificacao.serie}"


class CTe_Evento(models.Model):
    """Eventos vinculados ao CT-e (cancelamento, CCe, etc.) - carregados via XML de evento."""
    id_evento = models.AutoField(primary_key=True)
    cte_identificacao = models.ForeignKey(CTe_Identificacao, on_delete=models.CASCADE, related_name='eventos')
    tipo_evento = models.CharField(max_length=6)  # 110111=cancelamento, 110110=CCe, etc
    descricao_evento = models.CharField(max_length=100, blank=True, null=True)
    justificativa = models.TextField(blank=True, null=True)  # xJust (cancelamento) ou xCorrecao (CCe)
    data_evento = models.DateTimeField(blank=True, null=True)
    numero_sequencia = models.IntegerField(default=1)
    xml_evento = models.TextField(blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = '"cte"."cte_evento"'
        unique_together = [['cte_identificacao', 'tipo_evento', 'numero_sequencia']]
        indexes = [
            models.Index(fields=['cte_identificacao', 'tipo_evento']),
        ]

    def __str__(self):
        return f"Evento {self.tipo_evento} - CT-e {self.cte_identificacao.numero}/{self.cte_identificacao.serie}"


class CTe_Carga(models.Model):
    """Informações de carga do CT-e"""
    id_carga = models.AutoField(primary_key=True)
    cte_identificacao = models.OneToOneField(CTe_Identificacao, on_delete=models.CASCADE, related_name='carga')
    
    natureza_carga = models.CharField(max_length=80, blank=True, null=True)
    descricao = models.TextField(blank=True, null=True)
    weight_total = models.DecimalField(max_digits=15, decimal_places=3, blank=True, null=True, help_text="Peso total em kg")
    weight_cubagem = models.DecimalField(max_digits=15, decimal_places=3, blank=True, null=True, help_text="Peso/cubagem em kg")
    quantidade_volumes = models.IntegerField(blank=True, null=True)
    tipo_embalagem = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('CAIXA', 'Caixa'),
        ('PALLETES', 'Palletes'),
        ('VOLUMES_SOLTOS', 'Volumes Soltos'),
        ('TAMBORES', 'Tambores'),
        ('OUTROS', 'Outros'),
    ])
    
    valor_carga_nfe = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    valor_carga_contenidor = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    produto_perigoso = models.BooleanField(default=False)
    classe_risco = models.CharField(max_length=2, blank=True, null=True, help_text="Classe de risco ABNT")
    numero_onu = models.CharField(max_length=4, blank=True, null=True)
    
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = '"cte"."cte_carga"'

    def __str__(self):
        return f"Carga - {self.natureza_carga or 'S/N'}"


class CTe_Servico(models.Model):
    """Informações de serviços e taxas do CT-e"""
    id_servico = models.AutoField(primary_key=True)
    cte_identificacao = models.OneToOneField(CTe_Identificacao, on_delete=models.CASCADE, related_name='servico')
    
    valor_padrao_servico = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    valor_vale_pedagio = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, null=True)
    
    # Retenção Regime Especial (GRIS)
    valor_base_gris = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    aliquota_gris = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    valor_gris = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    
    # Seguro
    valor_seguro = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, null=True)
    numero_apólice = models.CharField(max_length=30, blank=True, null=True)
    
    # Outras taxas
    taxa_coleta = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, null=True)
    taxa_entrega = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, null=True)
    taxa_saida_entrega = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, null=True)
    taxa_adicional = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, null=True)
    
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = '"cte"."cte_servico"'

    def __str__(self):
        return f"Serviço - Valor: R$ {self.valor_padrao_servico}"


class CTe_Veiculo(models.Model):
    """Informações detalhadas do veículo do CT-e"""
    id_veiculo = models.AutoField(primary_key=True)
    cte_identificacao = models.OneToOneField(CTe_Identificacao, on_delete=models.CASCADE, related_name='veiculo')
    
    placa = models.CharField(max_length=8)
    rntrc = models.CharField(max_length=20, blank=True, null=True)
    dv_placa = models.CharField(max_length=1, blank=True, null=True)
    uf_placa = models.CharField(max_length=2)
    
    tipo_veiculo = models.CharField(max_length=2, choices=[
        ('01', 'Wagon'),
        ('02', 'Carreta'),
        ('03', 'Truck'),
        ('04', 'Carroceria'),
        ('05', 'Bitrem'),
        ('06', 'Tritrem'),
        ('07', 'Carreta Tanque'),
        ('08', 'Cavalo Mecanico'),
        ('09', 'Veiculo 3.5 a 4.2T'),
        ('10', 'Veiculo acima 4.2T'),
    ], blank=True, null=True)
    
    modelo = models.CharField(max_length=60, blank=True, null=True)
    ano_fabricacao = models.IntegerField(blank=True, null=True)
    
    tara = models.IntegerField(blank=True, null=True, help_text="Tara em kg")
    capacidade_maxima = models.IntegerField(blank=True, null=True, help_text="Capacidade máxima em kg")
    
    eixos = models.IntegerField(blank=True, null=True, help_text="Número de eixos")
    combustivel = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('DIESEL', 'Diesel'),
        ('GASOLINA', 'Gasolina'),
        ('GNV', 'GNV'),
        ('ELETRICO', 'Elétrico'),
        ('HIBRIDO', 'Híbrido'),
    ])
    
    cor = models.CharField(max_length=20, blank=True, null=True)
    lacre_numero = models.CharField(max_length=60, blank=True, null=True)
    
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = '"cte"."cte_veiculo"'

    def __str__(self):
        return f"Veículo {self.placa} - {self.modelo}"


class CTe_Motorista(models.Model):
    """Informações de motorista do CT-e"""
    id_motorista = models.AutoField(primary_key=True)
    cte_identificacao = models.OneToOneField(CTe_Identificacao, on_delete=models.CASCADE, related_name='motorista')
    
    cpf = models.CharField(max_length=11)
    nome = models.CharField(max_length=120)
    email = models.EmailField(max_length=60, blank=True, null=True)
    telefone = models.CharField(max_length=14, blank=True, null=True)
    
    cnh = models.CharField(max_length=12, blank=True, null=True)
    cnh_categoria = models.CharField(max_length=3, choices=[
        ('A', 'Categoria A'),
        ('B', 'Categoria B'),
        ('C', 'Categoria C'),
        ('D', 'Categoria D'),
        ('E', 'Categoria E'),
        ('ACC', 'Categoria ACC'),
        ('AD', 'Categoria AD'),
        ('AE', 'Categoria AE'),
    ], blank=True, null=True)
    cnh_validade = models.DateField(blank=True, null=True)
    cnh_uf = models.CharField(max_length=2, blank=True, null=True)
    
    banco = models.CharField(max_length=5, blank=True, null=True)
    agencia = models.CharField(max_length=6, blank=True, null=True)
    conta = models.CharField(max_length=12, blank=True, null=True)
    
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = '"cte"."cte_motorista"'

    def __str__(self):
        return f"Motorista {self.nome} - CPF {self.cpf}"


class CTe_Percurso(models.Model):
    """Informações de percurso e roteiro do CT-e"""
    id_percurso = models.AutoField(primary_key=True)
    cte_identificacao = models.OneToOneField(CTe_Identificacao, on_delete=models.CASCADE, related_name='percurso')
    
    municipio_origem = models.CharField(max_length=7, blank=True, null=True)
    municipio_destino = models.CharField(max_length=7, blank=True, null=True)
    
    # Paradas intermediárias
    parada_1 = models.CharField(max_length=7, blank=True, null=True)
    parada_2 = models.CharField(max_length=7, blank=True, null=True)
    parada_3 = models.CharField(max_length=7, blank=True, null=True)
    parada_4 = models.CharField(max_length=7, blank=True, null=True)
    parada_5 = models.CharField(max_length=7, blank=True, null=True)
    
    # Informação de cobrança de pedágio
    disp_cobranca_pedagio = models.CharField(max_length=1, choices=[
        ('N', 'Não há cobrança'),
        ('P', 'Pagamento na sedutora'),
        ('T', 'Pagamento por TAG'),
        ('O', 'Cobrança na origem'),
        ('D', 'Cobrança no destino'),
    ], default='N')
    
    valor_pedagio_estimado = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    
    chapa_veiculo = models.CharField(max_length=20, blank=True, null=True)
    odometro_inicio = models.IntegerField(blank=True, null=True)
    odometro_fim = models.IntegerField(blank=True, null=True)
    
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = '"cte"."cte_percurso"'

    def __str__(self):
        return f"Percurso {self.municipio_origem} → {self.municipio_destino}"


class CTe_Fiscal(models.Model):
    """Informações fiscais do CT-e"""
    id_fiscal = models.AutoField(primary_key=True)
    cte_identificacao = models.OneToOneField(CTe_Identificacao, on_delete=models.CASCADE, related_name='fiscal')
    
    cfop = models.CharField(max_length=4, blank=True, null=True)
    natureza_operacao = models.CharField(max_length=80, blank=True, null=True)
    regime_tributario = models.CharField(max_length=20, choices=[
        ('NORMAL', 'Regime Normal'),
        ('ISSQN', 'ISSQN'),
        ('SUBSTITUTO', 'Substituto Tributário'),
        ('MEI', 'MEI'),
        ('SIMPLES', 'Simples Nacional'),
    ], blank=True, null=True)
    
    # ICMS
    valor_base_icms = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    aliquota_icms = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    valor_icms = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    
    # PIS
    valor_base_pis = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    aliquota_pis = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    valor_pis = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    
    # COFINS
    valor_base_cofins = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    aliquota_cofins = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    valor_cofins = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    
    # IRRF (Imposto de Renda Pessoa Física)
    valor_irrf = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    
    # Retenção por Substituto Tributário
    cst_icms = models.CharField(max_length=2, blank=True, null=True)
    
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = '"cte"."cte_fiscal"'

    def __str__(self):
        return f"Fiscal - CFOP {self.cfop}"
