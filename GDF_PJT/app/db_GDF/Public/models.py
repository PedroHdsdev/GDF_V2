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
        managed  = True
        db_table = 'cert'
        indexes = [
            models.Index(fields=['cpf_cnpj']),
        ]

class Clientes(models.Model):
    cod_cliente = models.CharField(primary_key=True, max_length=10)
    razao = models.CharField(unique=True, max_length=120, blank=True, null=True)
    cnpj = models.CharField(unique=True, max_length=14)
    is_active = models.BooleanField()
    date_joined = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        managed  = True
        db_table = 'clientes'
        indexes = [
            models.Index(fields=['cnpj', 'razao']),
        ]
    
    def __str__(self):
        return f"{self.cod_cliente} - {self.razao}"


class Empresas(models.Model):
    cod_empresa = models.CharField(primary_key=True, max_length=10)
    cnpj = models.CharField(unique=True, max_length=14)
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
    cert = models.ForeignKey(Cert, models.DO_NOTHING, blank=True, null=True)
    cliente = models.ForeignKey(Clientes, models.CASCADE, blank=True, null=True)

    class Meta:
        managed  = True
        db_table = 'empresas'
        indexes = [
            models.Index(fields=['cnpj', 'razao', 'fantasia']),
        ]
    
    def __str__(self):
        return f"{self.cod_empresa} - {self.fantasia or self.razao}"

class GrpEmpresas(models.Model):
    grp_empresa = models.CharField(primary_key=True, max_length=5)
    descricao = models.CharField(max_length=80, blank=True, null=True)
    cliente = models.ForeignKey(Clientes, models.CASCADE, blank=True, null=True)

    class Meta:
        managed  = True
        db_table = 'grp_empresas'

class GrupoCliente(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(Group, models.CASCADE, db_column='Group_id') 
    cliente = models.ForeignKey(Clientes, models.CASCADE, blank=True, null=True)

    class Meta:
        managed  = True
        db_table = 'grupo_cliente'
        unique_together = ('group', 'cliente')


class Solucoes(models.Model):
    cod_solucao = models.CharField(primary_key=True, max_length=15)
    descricao = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed  = True
        db_table = 'solucoes'
    
    def __str__(self):
        return f"{self.cod_solucao} - {self.descricao}"

class SolucoesAcesso(models.Model):
    id = models.BigAutoField(primary_key=True)
    cliente = models.ForeignKey(Clientes, models.CASCADE, blank=True, null=True)
    solucao = models.ForeignKey(Solucoes, models.CASCADE, blank=True, null=True)
    is_active = models.BooleanField(blank=True, null=True)

    class Meta:
        managed  = True
        db_table = 'solucoes_acesso'
        unique_together = ('cliente', 'solucao')

class Subsolucoes(models.Model):
    id = models.BigAutoField(primary_key=True)
    cod_subsolucao = models.CharField(db_column='cod_subSolucoes', max_length=15)  # Field name made lowercase.
    descricao = models.CharField(max_length=50, blank=True, null=True)
    solucao = models.ForeignKey(Solucoes, models.CASCADE, blank=True, null=True)

    class Meta:
        managed  = True
        db_table = 'subsolucoes'
    
    def __str__(self):
        return f"{self.cod_subsolucao} - {self.descricao}"

class SubsolucoesAcesso(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(Group, models.CASCADE, db_column='Group_id')  # Field name made lowercase.
    subsolucao = models.ForeignKey(Subsolucoes, models.CASCADE, blank=True, null=True)

    class Meta:
        managed  = True
        db_table = 'subsolucoes_acesso'
        unique_together = ('group', 'subsolucao')

class UserEmpresas(models.Model):
    id = models.BigAutoField(primary_key=True)
    empresa = models.ForeignKey(Empresas, models.CASCADE)
    user = models.ForeignKey(User, models.CASCADE)

    class Meta:
        managed  = True
        db_table = 'user_empresas'
        unique_together = ('empresa', 'user')
