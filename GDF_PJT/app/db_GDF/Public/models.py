from django.db import models

class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)
    class Meta:
        managed = False
        db_table = 'public"."auth_group'

class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)
    class Meta:
        managed = False
        db_table = 'public"."auth_group_permissions'
        unique_together = (('group', 'permission'),)

class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)
    class Meta:
        managed = False
        db_table = 'public"."auth_permission'
        unique_together = (('content_type', 'codename'),)

class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()
    class Meta:
        managed = False
        db_table = 'public"."auth_user'

class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    class Meta:
        managed = False
        db_table = 'public"."auth_user_groups'
        unique_together = (('user', 'group'),)

class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)
    class Meta:
        managed = False
        db_table = 'public"."auth_user_user_permissions'
        unique_together = (('user', 'permission'),)

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
        db_table = 'public"."cert'

class Clientes(models.Model):
    cod_cliente = models.CharField(primary_key=True, max_length=10)
    razao = models.CharField(unique=True, max_length=120, blank=True, null=True)
    cnpj = models.CharField(max_length=14)
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()
    class Meta:
        managed = False
        db_table = 'public"."clientes'

class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    class Meta:
        managed = False
        db_table = 'public"."django_admin_log'

class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    class Meta:
        managed = False
        db_table = 'public"."django_content_type'
        unique_together = (('app_label', 'model'),)

class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()
    class Meta:
        managed = False
        db_table = 'public"."django_migrations'

class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()
    class Meta:
        managed = False
        db_table = 'public"."django_session'

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
        db_table = 'public"."empresas'

class GrpEmpresas(models.Model):
    grp_empresa = models.CharField(primary_key=True, max_length=5)
    nome = models.CharField(max_length=80, blank=True, null=True)
    cliente = models.ForeignKey(Clientes, models.DO_NOTHING, blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'public"."grp_empresas'

class GrupoCliente(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING, db_column='Group_id')  # Field name made lowercase.
    cliente = models.ForeignKey(Clientes, models.DO_NOTHING, blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'public"."grupo_cliente'

class Solucoes(models.Model):
    cod_solucoes = models.CharField(primary_key=True, max_length=15)
    descricao = models.CharField(max_length=50, blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'public"."solucoes'

class SolucoesAcesso(models.Model):
    id = models.BigAutoField(primary_key=True)
    clientess = models.ForeignKey(Clientes, models.DO_NOTHING, blank=True, null=True)
    solucoes = models.ForeignKey(Solucoes, models.DO_NOTHING, blank=True, null=True)
    is_active = models.BooleanField(blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'public"."solucoes_acesso'

class Subsolucoes(models.Model):
    id = models.BigAutoField(primary_key=True)
    cod_subsolucoes = models.CharField(db_column='cod_subSolucoes', max_length=10)  # Field name made lowercase.
    descricao = models.CharField(max_length=50, blank=True, null=True)
    solucoes = models.ForeignKey(Solucoes, models.DO_NOTHING, blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'public"."subsolucoes'

class SubsolucoesAcesso(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING, db_column='Group_id')  # Field name made lowercase.
    subsolucoes = models.ForeignKey(Subsolucoes, models.DO_NOTHING, blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'public"."subsolucoes_acesso'

class UserEmpresas(models.Model):
    id = models.BigAutoField(primary_key=True)
    empresas = models.ForeignKey(Empresas, models.DO_NOTHING)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    class Meta:
        managed = False
        db_table = 'public"."user_empresas'
        unique_together = (('empresas', 'user'),)