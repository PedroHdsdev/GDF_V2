"""
Modelos do schema Public (cadastros gerais, clientes, empresas, permissões e integrações).

Tabelas no banco (db_table) alinhadas aos nomes dos modelos (snake_case).
"""
from django.db import models
from django.contrib.auth.models import User, Group


# ---------------------------------------------------------------------------
# Certificado digital
# ---------------------------------------------------------------------------
class Cert(models.Model):
    """Certificado digital (.pfx) por raiz do CNPJ."""
    raiz_cnpj = models.CharField(primary_key=True, max_length=8)
    nm_arquivo_pfx = models.CharField(max_length=100, blank=True, null=True)
    ini_validade = models.DateTimeField(blank=True, null=True)
    fim_validade = models.DateTimeField(blank=True, null=True)
    emissor = models.CharField(max_length=100, blank=True, null=True)
    proprietario = models.CharField(max_length=100, blank=True, null=True)
    cpf_cnpj = models.CharField(max_length=14, blank=True, null=True)
    arquivo_cert = models.BinaryField(blank=True, null=True)
    senha_cert = models.CharField(max_length=1024, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'cert'
        verbose_name = 'Certificado digital'
        verbose_name_plural = 'Certificados digitais'
        indexes = [models.Index(fields=['cpf_cnpj'])]


# ---------------------------------------------------------------------------
# Cliente GDF e empresas
# ---------------------------------------------------------------------------
class ClienteGdf(models.Model):
    """
    Cliente do sistema GDF (contratante; pode ter várias empresas).
    Tabela principal: ao apagar um cliente no PostgreSQL, todos os registros vinculados
    são apagados em cascata via on_delete=models.CASCADE das FKs (Empresa → Filial,
    NFe, CTe, NFSe, reprocessamento, parâmetros/jobs de carga, SPED, permissões, etc.).
    Não expor exclusão de cliente ao usuário; uso apenas admin/backoffice.
    """
    cod_cliente = models.CharField(primary_key=True, max_length=10)
    razao = models.CharField(unique=True, max_length=120, blank=True, null=True)
    cnpj = models.CharField(unique=True, max_length=14)
    is_active = models.BooleanField()
    date_joined = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'cliente_gdf'
        verbose_name = 'Cliente GDF'
        verbose_name_plural = 'Clientes GDF'
        indexes = [models.Index(fields=['cnpj', 'razao'])]

    def __str__(self):
        return f"{self.cod_cliente} - {self.razao}"

# ---------------------------------------------------------------------------
# Grupo de empresas
# ---------------------------------------------------------------------------
class GrpEmpresas(models.Model):
    grp_empresa = models.CharField(primary_key=True, max_length=5)
    nome = models.CharField(max_length=80, blank=True, null=True)
    cliente = models.ForeignKey(
        ClienteGdf, models.CASCADE, blank=True, null=True, db_column='gdfcliente_id'
    )

    class Meta:
        managed = True
        db_table = 'grp_empresas'
        verbose_name = 'Grupo de empresas'
        verbose_name_plural = 'Grupos de empresas'

class Empresas(models.Model):
    """Empresa (estabelecimento) vinculada a um cliente GDF."""
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

    grp_empresa = models.ForeignKey(
        GrpEmpresas, models.DO_NOTHING, blank=True, null=True, db_column='grp_empresa'
    )

    chave_acesso = models.CharField(max_length=40, blank=True, null=True)
    cert = models.ForeignKey(
        Cert, models.DO_NOTHING, blank=True, null=True, db_column='cert'
    )
    gdfcliente = models.ForeignKey(
        ClienteGdf, models.CASCADE, blank=True, null=True, db_column='gdfcliente_id'
    )

    class Meta:
        managed = True
        db_table = 'empresas'
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        indexes = [models.Index(fields=['cnpj', 'razao', 'fantasia'])]

    def __str__(self):
        return f"{self.cod_empresa} - {self.fantasia or self.razao}"


class Filial(models.Model):
    """Filial vinculada a uma empresa (ClienteGdf → Empresa → Filial)."""
    id = models.BigAutoField(primary_key=True)
    cod_filial = models.CharField(max_length=10, db_index=True)
    empresa = models.ForeignKey(
        Empresas, models.CASCADE, related_name='filiais', db_index=True
    )
    nome = models.CharField(max_length=120, blank=True, null=True)
    cnpj = models.CharField(max_length=14, blank=True, null=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = 'filial'
        verbose_name = 'Filial'
        verbose_name_plural = 'Filiais'
        unique_together = (('empresa', 'cod_filial'),)
        indexes = [models.Index(fields=['empresa', 'cod_filial'])]

    def __str__(self):
        return f"{self.cod_filial} - {self.nome or self.empresa_id}"


# ---------------------------------------------------------------------------
# Permissões: grupo do Django ↔ cliente GDF | usuário ↔ empresa
# ---------------------------------------------------------------------------
class PermissaoGrupoCliente(models.Model):
    """Quais grupos (Django auth) têm acesso a qual cliente GDF."""
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(Group, models.CASCADE, db_column='Group_id')
    gdfcliente = models.ForeignKey(
        ClienteGdf, models.CASCADE, blank=True, null=True, db_column='gdfcliente_id'
    )

    class Meta:
        managed = True
        db_table = 'permissao_grupo_cliente'
        verbose_name = 'Permissão grupo-cliente'
        verbose_name_plural = 'Permissões grupo-cliente'
        unique_together = ('group', 'gdfcliente')


class UsuarioEmpresa(models.Model):
    """Vínculo entre usuário (Django auth) e empresa."""
    id = models.BigAutoField(primary_key=True)
    empresa = models.ForeignKey(Empresas, models.CASCADE)
    user = models.ForeignKey(User, models.CASCADE)

    class Meta:
        managed = True
        db_table = 'usuario_empresa'
        verbose_name = 'Usuário-Empresa'
        verbose_name_plural = 'Usuários-Empresas'
        unique_together = ('empresa', 'user')


# ---------------------------------------------------------------------------
# Soluções e subsoluções (módulos/funcionalidades por cliente/grupo)
# ---------------------------------------------------------------------------
class Solucao(models.Model):
    """Solução (módulo) disponível no sistema."""
    cod_solucao = models.CharField(primary_key=True, max_length=15)
    descricao = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'solucao'
        verbose_name = 'Solução'
        verbose_name_plural = 'Soluções'

    def __str__(self):
        return f"{self.cod_solucao} - {self.descricao}"


class AcessoSolucaoCliente(models.Model):
    """Quais soluções cada cliente GDF tem acesso."""
    id = models.BigAutoField(primary_key=True)
    gdfcliente = models.ForeignKey(
        ClienteGdf, models.CASCADE, blank=True, null=True, db_column='gdfcliente_id'
    )
    solucao = models.ForeignKey(Solucao, models.CASCADE, blank=True, null=True)
    is_active = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'acesso_solucao_cliente'
        verbose_name = 'Acesso solução (cliente)'
        verbose_name_plural = 'Acessos solução (cliente)'
        unique_together = ('gdfcliente', 'solucao')


class Subsolucao(models.Model):
    """Subsolução (submódulo) vinculada a uma solução."""
    id = models.BigAutoField(primary_key=True)
    cod_subsolucao = models.CharField(max_length=25, db_column='cod_subSolucoes')
    descricao = models.CharField(max_length=50, blank=True, null=True)
    solucao = models.ForeignKey(Solucao, models.CASCADE, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'subsolucao'
        verbose_name = 'Subsolução'
        verbose_name_plural = 'Subsoluções'

    def __str__(self):
        return f"{self.cod_subsolucao} - {self.descricao}"


class AcessoSubsolucaoGrupo(models.Model):
    """Quais subsoluções cada grupo (Django auth) tem acesso."""
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(Group, models.CASCADE, db_column='Group_id')
    subsolucao = models.ForeignKey(Subsolucao, models.CASCADE, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'acesso_subsolucao_grupo'
        verbose_name = 'Acesso subsolução (grupo)'
        verbose_name_plural = 'Acessos subsolução (grupo)'
        unique_together = ('group', 'subsolucao')


# ---------------------------------------------------------------------------
# Jobs de carga XML (NFe, CTe, NFSe) — somente carga manual (upload)
# ---------------------------------------------------------------------------


class JobCargaXml(models.Model):
    """Execução (job) de carga de XML."""
    STATUS_CHOICES = [
        ('PENDING', 'Pendente'),
        ('RUNNING', 'Executando'),
        ('SUCCESS', 'Sucesso'),
        ('ERROR', 'Erro'),
    ]
    id = models.BigAutoField(primary_key=True)
    gdfcliente = models.ForeignKey(
        ClienteGdf, models.CASCADE, db_column='gdfcliente_id'
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    total_arquivos = models.IntegerField(default=0)
    total_sucesso = models.IntegerField(default=0)
    total_erro = models.IntegerField(default=0)
    mensagem = models.TextField(blank=True, null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    finished_at = models.DateTimeField(blank=True, null=True)
    usuario_execucao = models.ForeignKey(
        User, models.SET_NULL, null=True, blank=True, related_name='cargaxml_jobs'
    )

    class Meta:
        managed = True
        db_table = 'job_carga_xml'
        verbose_name = 'Job carga XML'
        verbose_name_plural = 'Jobs carga XML'
        indexes = [
            models.Index(fields=['gdfcliente', 'status']),
            models.Index(fields=['gdfcliente', 'started_at']),
        ]


# ---------------------------------------------------------------------------
# Jobs de carga SPED (EFD ICMS, EFD Contribuições, etc.) — somente carga manual
# ---------------------------------------------------------------------------


class JobCargaSped(models.Model):
    """Execução (job) de carga SPED."""
    STATUS_CHOICES = [
        ('PENDING', 'Pendente'),
        ('RUNNING', 'Executando'),
        ('SUCCESS', 'Sucesso'),
        ('ERROR', 'Erro'),
    ]
    id = models.BigAutoField(primary_key=True)
    gdfcliente = models.ForeignKey(
        ClienteGdf, models.CASCADE, db_column='gdfcliente_id'
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    total_arquivos = models.IntegerField(default=0)
    total_sucesso = models.IntegerField(default=0)
    total_erro = models.IntegerField(default=0)
    mensagem = models.TextField(blank=True, null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    finished_at = models.DateTimeField(blank=True, null=True)
    usuario_execucao = models.ForeignKey(
        User, models.SET_NULL, null=True, blank=True, related_name='cargasped_jobs'
    )

    class Meta:
        managed = True
        db_table = 'job_carga_sped'
        verbose_name = 'Job carga SPED'
        verbose_name_plural = 'Jobs carga SPED'
        indexes = [
            models.Index(fields=['gdfcliente', 'status']),
            models.Index(fields=['gdfcliente', 'started_at']),
        ]


# ---------------------------------------------------------------------------
# Integração SAP
# ---------------------------------------------------------------------------
class ConexaoSap(models.Model):
    """Conexão SAP por cliente GDF."""
    id = models.AutoField(primary_key=True)
    ashost = models.CharField(max_length=100)
    sysnr = models.CharField(max_length=10)
    client = models.CharField(max_length=10)
    username = models.CharField(max_length=50)
    passwd = models.CharField(max_length=50)
    lang = models.CharField(max_length=5)
    active = models.BooleanField(default=True)
    gdfcliente = models.ForeignKey(
        ClienteGdf, models.CASCADE, blank=True, null=True, db_column='gdfcliente_id'
    )

    class Meta:
        managed = True
        db_table = 'conexao_sap'
        verbose_name = 'Conexão SAP'
        verbose_name_plural = 'Conexões SAP'


# Aliases legados (imports antigos no código)
Empresa = Empresas
CertificadoDigital = Cert
