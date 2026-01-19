from django.contrib import admin
from django.contrib.auth.models import User, Group
from app.db_GDF.Public.models import (
    Cert, Clientes, Empresas, GrupoCliente, GrpEmpresas,
    Solucoes, Subsolucoes, SolucoesAcesso, SubsolucoesAcesso, UserEmpresas
)


# ============================================================================
# CLIENTES
# ============================================================================
@admin.register(Clientes)
class ClientesAdmin(admin.ModelAdmin):
    list_display = ('cod_cliente', 'razao', 'cnpj', 'is_active', 'date_joined')
    list_filter = ('is_active', 'date_joined')
    search_fields = ('cod_cliente', 'razao', 'cnpj')
    readonly_fields = ('cod_cliente', 'date_joined')
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('cod_cliente', 'razao', 'cnpj', 'is_active')
        }),
        ('Datas', {
            'fields': ('date_joined',)
        }),
    )


# ============================================================================
# CERTIFICADOS
# ============================================================================
@admin.register(Cert)
class CertAdmin(admin.ModelAdmin):
    list_display = ('raiz_cnpj', 'proprietario', 'cpf_cnpj', 'ini_validade', 'fim_validade')
    list_filter = ('ini_validade', 'fim_validade')
    search_fields = ('raiz_cnpj', 'proprietario', 'cpf_cnpj', 'emissor')
    readonly_fields = ('raiz_cnpj',)
    fieldsets = (
        ('Informações do Certificado', {
            'fields': ('raiz_cnpj', 'nm_arquivo_pfx', 'arquivo_cert')
        }),
        ('Datas de Validade', {
            'fields': ('ini_validade', 'fim_validade')
        }),
        ('Propriedade', {
            'fields': ('proprietario', 'cpf_cnpj', 'emissor')
        }),
    )


# ============================================================================
# SOLUÇÕES E SUBSOLUÇÕES
# ============================================================================
class SubsolucoesInline(admin.TabularInline):
    model = Subsolucoes
    extra = 1
    fields = ('cod_subsolucoes', 'descricao')


@admin.register(Solucoes)
class SolucoesAdmin(admin.ModelAdmin):
    list_display = ('cod_solucoes', 'descricao')
    search_fields = ('cod_solucoes', 'descricao')
    readonly_fields = ('cod_solucoes',)
    inlines = [SubsolucoesInline]
    fieldsets = (
        ('Informações da Solução', {
            'fields': ('cod_solucoes', 'descricao')
        }),
    )


@admin.register(Subsolucoes)
class SubsolucoesAdmin(admin.ModelAdmin):
    list_display = ('id', 'cod_subsolucoes', 'descricao', 'solucoes')
    list_filter = ('solucoes',)
    search_fields = ('cod_subsolucoes', 'descricao')
    fieldsets = (
        ('Informações da Subssolução', {
            'fields': ('cod_subsolucoes', 'descricao', 'solucoes')
        }),
    )


# ============================================================================
# ACESSOS ÀS SOLUÇÕES
# ============================================================================
@admin.register(SolucoesAcesso)
class SolucoesAcessoAdmin(admin.ModelAdmin):
    list_display = ('id', 'clientess', 'solucoes', 'is_active')
    list_filter = ('is_active', 'solucoes', 'clientess')
    search_fields = ('clientess__razao', 'solucoes__cod_solucoes')
    fieldsets = (
        ('Acesso à Solução', {
            'fields': ('clientess', 'solucoes', 'is_active')
        }),
    )


@admin.register(SubsolucoesAcesso)
class SubsolucoesAcessoAdmin(admin.ModelAdmin):
    list_display = ('id', 'group', 'get_subsolucao_chave', 'get_subsolucao_nome')
    list_filter = ('group', 'subsolucoes__solucoes')
    search_fields = ('group__name', 'subsolucoes__cod_subsolucoes', 'subsolucoes__descricao')
    fieldsets = (
        ('Acesso à Subssolução', {
            'fields': ('group', 'subsolucoes')
        }),
    )
    
    def get_subsolucao_chave(self, obj):
        return obj.subsolucoes.cod_subsolucoes if obj.subsolucoes else '-'
    get_subsolucao_chave.short_description = 'Chave da Subssolução'
    
    def get_subsolucao_nome(self, obj):
        return obj.subsolucoes.descricao if obj.subsolucoes else '-'
    get_subsolucao_nome.short_description = 'Nome da Subssolução'


# ============================================================================
# GRUPOS DE EMPRESAS
# ============================================================================
@admin.register(GrpEmpresas)
class GrpEmpresasAdmin(admin.ModelAdmin):
    list_display = ('grp_empresa', 'nome', 'cliente')
    list_filter = ('cliente',)
    search_fields = ('grp_empresa', 'nome', 'cliente__razao')
    readonly_fields = ('grp_empresa',)
    fieldsets = (
        ('Informações do Grupo', {
            'fields': ('grp_empresa', 'nome', 'cliente')
        }),
    )


# ============================================================================
# EMPRESAS
# ============================================================================
class UserEmpresasInline(admin.TabularInline):
    model = UserEmpresas
    extra = 1
    raw_id_fields = ('user',)


@admin.register(Empresas)
class EmpresasAdmin(admin.ModelAdmin):
    list_display = ('cod_empresa', 'razao', 'fantasia', 'cnpj', 'cliente', 'grp_empresa')
    list_filter = ('cliente', 'grp_empresa', 'tipo', 'matriz')
    search_fields = ('cod_empresa', 'razao', 'fantasia', 'cnpj')
    #readonly_fields = ('cod_empresa',)
    inlines = [UserEmpresasInline]
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('cod_empresa', 'razao', 'fantasia', 'cnpj', 'cliente', 'grp_empresa')
        }),
        ('Fiscalização', {
            'fields': ('ie', 'im', 'cnae', 'iest', 'suframa', 'crt')
        }),
        ('Organização', {
            'fields': ('tipo', 'matriz')
        }),
        ('Certificado e Chave', {
            'fields': ('cert', 'chave_acesso')
        }),
        ('Interno', {
            'fields': ('id_user',)
        }),
    )


# ============================================================================
# GRUPO CLIENTE (permissões de grupo por cliente)
# ============================================================================
@admin.register(GrupoCliente)
class GrupoClienteAdmin(admin.ModelAdmin):
    list_display = ('id', 'group', 'cliente')
    list_filter = ('group', 'cliente')
    search_fields = ('group__name', 'cliente__razao')
    fieldsets = (
        ('Permissão de Grupo', {
            'fields': ('group', 'cliente')
        }),
    )


# ============================================================================
# USUÁRIOS EMPRESAS (vínculo entre usuários e empresas)
# ============================================================================
@admin.register(UserEmpresas)
class UserEmpresasAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'empresas')
    list_filter = ('empresas', 'user')
    search_fields = ('user__username', 'empresas__razao')
    raw_id_fields = ('user', 'empresas')
    fieldsets = (
        ('Vínculo Usuário-Empresa', {
            'fields': ('user', 'empresas')
        }),
    )




