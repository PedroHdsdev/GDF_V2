from django.db import models
from django.contrib.auth.models import User, Group


class Cert(models.Model):
    raiz_cnpj = models.CharField(primary_key=True, max_length=8)
    nm_arquivo_pfx = models.CharField(max_length=100, blank=True, null=True)
    ini_validade = models.DateTimeField(blank=True, null=True)
    fim_validade = models.DateTimeField(blank=True, null=True)
    emissor = models.CharField(max_length=100, blank=True, null=True)
    proprietario = models.CharField(max_length=100, blank=True, null=True)
    cpf_cnpj = models.CharField(max_length=14, blank=True, null=True)
    arquivo_cert = models.BinaryField(blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'cert'

class Clientes(models.Model):
    cod_cliente = models.CharField(primary_key=True, max_length=10)
    razao = models.CharField(unique=True, max_length=120, blank=True, null=True)
    cnpj = models.CharField(max_length=14)
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()
    class Meta:
        managed = False
        db_table = 'clientes'
    
    def __str__(self):
        return f"{self.cod_cliente} - {self.razao}"


class Empresas(models.Model):
    cod_empresa = models.CharField(primary_key=True, max_length=10)
    cnpj = models.CharField(max_length=14)
    razao = models.CharField(unique=True, max_length=120, blank=True, null=True)
    fantasia = models.CharField(max_length=60, blank=True, null=True)
    ie = models.CharField(max_length=13, blank=True, null=True)
    im = models.CharField(max_length=13, blank=True, null=True)
    tipo = models.CharField(max_length=1, blank=True, null=True)
    matriz = models.BooleanField(blank=True, null=True)
    crt = models.CharField(max_length=1, blank=True, null=True)
    cnae = models.CharField(max_length=7, blank=True, null=True)
    iest = models.CharField(max_length=18, blank=True, null=True)
    suframa = models.CharField(max_length=10, blank=True, null=True)
    grp_empresa = models.ForeignKey('GrpEmpresas', models.DO_NOTHING, blank=True, null=True)
    chave_acesso = models.CharField(max_length=40, blank=True, null=True)
    id_user = models.IntegerField(blank=True, null=True)
    cert = models.ForeignKey(Cert, models.DO_NOTHING, blank=True, null=True)
    cliente = models.ForeignKey(Clientes, models.DO_NOTHING, blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'empresas'
    
    def __str__(self):
        return f"{self.cod_empresa} - {self.fantasia or self.razao}"

class GrpEmpresas(models.Model):
    grp_empresa = models.CharField(primary_key=True, max_length=5)
    nome = models.CharField(max_length=80, blank=True, null=True)
    cliente = models.ForeignKey(Clientes, models.DO_NOTHING, blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'grp_empresas'

class GrupoCliente(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(Group, models.DO_NOTHING, db_column='Group_id')  # Field name made lowercase.
    cliente = models.ForeignKey(Clientes, models.DO_NOTHING, blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'grupo_cliente'

class Solucoes(models.Model):
    cod_solucoes = models.CharField(primary_key=True, max_length=15)
    descricao = models.CharField(max_length=50, blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'solucoes'
    
    def __str__(self):
        return f"{self.cod_solucoes} - {self.descricao}"

class SolucoesAcesso(models.Model):
    id = models.BigAutoField(primary_key=True)
    clientess = models.ForeignKey(Clientes, models.DO_NOTHING, blank=True, null=True)
    solucoes = models.ForeignKey(Solucoes, models.DO_NOTHING, blank=True, null=True)
    is_active = models.BooleanField(blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'solucoes_acesso'

class Subsolucoes(models.Model):
    id = models.BigAutoField(primary_key=True)
    cod_subsolucoes = models.CharField(db_column='cod_subSolucoes', max_length=15)  # Field name made lowercase.
    descricao = models.CharField(max_length=50, blank=True, null=True)
    solucoes = models.ForeignKey(Solucoes, models.DO_NOTHING, blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'subsolucoes'
    
    def __str__(self):
        return f"{self.cod_subsolucoes} - {self.descricao}"

class SubsolucoesAcesso(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(Group, models.DO_NOTHING, db_column='Group_id')  # Field name made lowercase.
    subsolucoes = models.ForeignKey(Subsolucoes, models.DO_NOTHING, blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'subsolucoes_acesso'

class UserEmpresas(models.Model):
    id = models.BigAutoField(primary_key=True)
    empresas = models.ForeignKey(Empresas, models.DO_NOTHING)
    user = models.ForeignKey(User, models.DO_NOTHING)
    class Meta:
        managed = False
        db_table = 'user_empresas'
        unique_together = (('empresas', 'user'),)
