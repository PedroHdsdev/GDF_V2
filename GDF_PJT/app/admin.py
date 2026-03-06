from django.contrib             import admin
from app.db_GDF.Public.models   import (
    CertificadoDigital, ClienteGdf, Empresa, PermissaoGrupoCliente, GrupoEmpresa,
    Solucao, Subsolucao, AcessoSolucaoCliente, AcessoSubsolucaoGrupo, UsuarioEmpresa,
)

# ============================================================================
# CLIENTES GDF
# ============================================================================
@admin.register(ClienteGdf)
class ClienteGdfAdmin(admin.ModelAdmin):
    list_display = ('cod_cliente', 'razao', 'cnpj', 'is_active', 'date_joined')
    list_filter = ('is_active', 'date_joined')
    search_fields = ('cod_cliente', 'razao', 'cnpj')
    readonly_fields = ('date_joined',)
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('cod_cliente', 'razao', 'cnpj', 'is_active')
        }),
        ('Datas', {
            'fields': ('date_joined',)
        }),
    )


# ============================================================================
# CERTIFICADOS DIGITAIS
# ============================================================================
@admin.register(CertificadoDigital)
class CertificadoDigitalAdmin(admin.ModelAdmin):
    list_display = ('raiz_cnpj', 'proprietario', 'cpf_cnpj', 'ini_validade', 'fim_validade')
    list_filter = ('ini_validade', 'fim_validade')
    search_fields = ('raiz_cnpj', 'proprietario', 'cpf_cnpj', 'emissor')
    fieldsets = (
        ('Informações do Certificado', {
            'fields': ('raiz_cnpj', 'nm_arquivo_pfx')
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
class SubsolucaoInline(admin.TabularInline):
    model = Subsolucao
    extra = 1
    fields = ('cod_subsolucao', 'descricao')


@admin.register(Solucao)
class SolucaoAdmin(admin.ModelAdmin):
    list_display = ('cod_solucao', 'descricao')
    search_fields = ('cod_solucao', 'descricao')
    readonly_fields = ('cod_solucao',)
    inlines = [SubsolucaoInline]
    fieldsets = (
        ('Informações da Solução', {
            'fields': ('cod_solucao', 'descricao')
        }),
    )


@admin.register(Subsolucao)
class SubsolucaoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cod_subsolucao', 'descricao', 'solucao')
    list_filter = ('solucao',)
    search_fields = ('cod_subsolucao', 'descricao')
    fieldsets = (
        ('Informações da Subsolução', {
            'fields': ('cod_subsolucao', 'descricao', 'solucao')
        }),
    )


# ============================================================================
# ACESSOS ÀS SOLUÇÕES
# ============================================================================
@admin.register(AcessoSolucaoCliente)
class AcessoSolucaoClienteAdmin(admin.ModelAdmin):
    list_display = ('id', 'gdfcliente', 'solucao', 'is_active')
    list_filter = ('is_active', 'solucao', 'gdfcliente')
    search_fields = ('gdfcliente__razao', 'solucao__cod_solucao')
    fieldsets = (
        ('Acesso à Solução', {
            'fields': ('gdfcliente', 'solucao', 'is_active')
        }),
    )


@admin.register(AcessoSubsolucaoGrupo)
class AcessoSubsolucaoGrupoAdmin(admin.ModelAdmin):
    list_display = ('id', 'group', 'get_subsolucao_chave', 'get_subsolucao_nome')
    list_filter = ('group', 'subsolucao__solucao')
    search_fields = ('group__name', 'subsolucao__cod_subsolucao', 'subsolucao__descricao')
    fieldsets = (
        ('Acesso à Subsolução', {
            'fields': ('group', 'subsolucao')
        }),
    )

    def get_subsolucao_chave(self, obj):
        return obj.subsolucao.cod_subsolucao if obj.subsolucao else '-'
    get_subsolucao_chave.short_description = 'Chave da Subsolução'

    def get_subsolucao_nome(self, obj):
        return obj.subsolucao.descricao if obj.subsolucao else '-'
    get_subsolucao_nome.short_description = 'Nome da Subsolução'


# ============================================================================
# GRUPOS DE EMPRESAS
# ============================================================================
@admin.register(GrupoEmpresa)
class GrupoEmpresaAdmin(admin.ModelAdmin):
    list_display = ('grp_empresa', 'descricao', 'gdfcliente')
    list_filter = ('gdfcliente',)
    search_fields = ('grp_empresa', 'descricao', 'gdfcliente__razao')
    fieldsets = (
        ('Informações do Grupo', {
            'fields': ('grp_empresa', 'descricao', 'gdfcliente')
        }),
    )


# ============================================================================
# EMPRESAS
# ============================================================================
class UsuarioEmpresaInline(admin.TabularInline):
    model = UsuarioEmpresa
    extra = 1
    raw_id_fields = ('user',)


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('cod_empresa', 'razao', 'fantasia', 'cnpj', 'gdfcliente', 'grp_empresa')
    list_filter = ('gdfcliente', 'grp_empresa', 'tipo', 'matriz')
    search_fields = ('cod_empresa', 'razao', 'fantasia', 'cnpj')
    inlines = [UsuarioEmpresaInline]
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('cod_empresa', 'razao', 'fantasia', 'cnpj', 'gdfcliente', 'grp_empresa')
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
    )


# ============================================================================
# PERMISSÃO GRUPO-CLIENTE
# ============================================================================
@admin.register(PermissaoGrupoCliente)
class PermissaoGrupoClienteAdmin(admin.ModelAdmin):
    list_display = ('id', 'group', 'gdfcliente')
    list_filter = ('group', 'gdfcliente')
    search_fields = ('group__name', 'gdfcliente__razao')
    fieldsets = (
        ('Permissão de Grupo', {
            'fields': ('group', 'gdfcliente')
        }),
    )


# ============================================================================
# USUÁRIO-EMPRESA (vínculo entre usuários e empresas)
# ============================================================================
@admin.register(UsuarioEmpresa)
class UsuarioEmpresaAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'empresa')
    list_filter = ('empresa', 'user')
    search_fields = ('user__username', 'empresa__razao')
    raw_id_fields = ('user', 'empresa')
    fieldsets = (
        ('Vínculo Usuário-Empresa', {
            'fields': ('user', 'empresa')
        }),
    )
