from django.contrib import admin
from app.db_GDF.Public.models import AuthUser, Empresas, GrupoCliente, GrpEmpresas
from app.db_GDF.Public.models import Solucoes, Subsolucoes, SolucoesAcesso, SubsolucoesAcesso

admin.site.register(AuthUser)
admin.site.register(Empresas)
admin.site.register(GrupoCliente)
admin.site.register(GrpEmpresas)  

admin.site.register(Solucoes)
admin.site.register(Subsolucoes)
admin.site.register(SolucoesAcesso)
admin.site.register(SubsolucoesAcesso)




