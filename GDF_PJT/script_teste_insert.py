"""
Script para testar a criação de registros nas tabelas do SQLite
Execute: python manage.py shell < script_teste_insert.py
Ou dentro do shell: exec(open('script_teste_insert.py').read())
"""

from django.utils import timezone
from GDF_PJT.app.db_GDF.Public.models import (
    Clientes, Empresas, GrpEmpresas, Cert,
    Solucoes, SolucoesAcesso, Subsolucoes,
    GrupoCliente, UserEmpresas, SubsolucoesAcesso,
)

def testar_criacao_registros():
    print("=" * 60)
    print("TESTE DE CRIAÇÃO DE REGISTROS")
    print("=" * 60)
    
    try:
        # 1. Criar Cliente
        print("\n1. Criando Cliente...")
        cliente = Clientes.objects.create(
            cod_cliente='CLI001',
            razao='Cliente Teste LTDA',
            cnpj='12345678000190',
            is_active=True
        )
        print(f"✓ Cliente criado: {cliente.cod_cliente} - {cliente.razao}")
        
        # 2. Criar Solução
        print("\n2. Criando Solução...")
        solucao = Solucoes.objects.create(
            cod_solucoes='SOL001',
            descricao='Solução de Teste'
        )
        print(f"✓ Solução criada: {solucao.cod_solucoes} - {solucao.descricao}")
        
        # 3. Criar Solução Acesso
        print("\n3. Criando Solução Acesso...")
        sol_acesso = SolucoesAcesso.objects.create(
            clientess=cliente,
            solucoes=solucao,
            is_active=True
        )
        print(f"✓ Solução Acesso criada: ID {sol_acesso.id}")
        
        # 4. Criar Grupo de Empresas
        print("\n4. Criando Grupo de Empresas...")
        grp_empresa = GrpEmpresas.objects.create(
            grp_empresa='GRP01',
            nome='Grupo Teste',
            cliente=cliente
        )
        print(f"✓ Grupo Empresa criado: {grp_empresa.grp_empresa} - {grp_empresa.nome}")
        
        # 5. Criar Certificado (opcional)
        print("\n5. Criando Certificado...")
        cert = Cert.objects.create(
            raiz_cnpj='12345678',
            cpf_cnpj='12345678000190',
            proprietario='Proprietário Teste'
        )
        print(f"✓ Certificado criado: {cert.raiz_cnpj}")
        
        # 6. Criar Empresa
        print("\n6. Criando Empresa...")
        empresa = Empresas.objects.create(
            cod_empresa='EMP001',
            cnpj='12345678000190',
            razao='Empresa Teste LTDA',
            fantasia='Empresa Teste',
            cliente=cliente,
            grp_empresa=grp_empresa
        )
        print(f"✓ Empresa criada: {empresa.cod_empresa} - {empresa.razao}")
        
        # 7. Criar Sub-solução
        print("\n7. Criando Sub-solução...")
        subsolucao = Subsolucoes.objects.create(
            cod_subsolucoes='SUB001',
            descricao='Sub-solução Teste',
            solucoes=solucao
        )
        print(f"✓ Sub-solução criada: {subsolucao.cod_subsolucoes}")
        
        # 8. Verificar se AuthGroup existe (do Django)
        print("\n8. Verificando AuthGroup...")
        grupo_django = AuthGroup.objects.first()
        if grupo_django:
            print(f"✓ Grupo Django encontrado: {grupo_django.name} (ID: {grupo_django.id})")
            
            # Criar GrupoCliente
            print("\n9. Criando GrupoCliente...")
            grupo_cliente = GrupoCliente.objects.create(
                group=grupo_django,
                cliente=cliente
            )
            print(f"✓ GrupoCliente criado: ID {grupo_cliente.id}")
            
            # Criar SubsolucoesAcesso
            print("\n10. Criando SubsolucoesAcesso...")
            subsol_acesso = SubsolucoesAcesso.objects.create(
                group=grupo_django,
                subsolucoes=subsolucao
            )
            print(f"✓ SubsolucoesAcesso criado: ID {subsol_acesso.id}")
        else:
            print("⚠ Nenhum AuthGroup encontrado. Pule as etapas 9 e 10.")
        
        # Verificar registros criados
        print("\n" + "=" * 60)
        print("RESUMO DOS REGISTROS CRIADOS:")
        print("=" * 60)
        print(f"Clientes: {Clientes.objects.count()}")
        print(f"Empresas: {Empresas.objects.count()}")
        print(f"GrpEmpresas: {GrpEmpresas.objects.count()}")
        print(f"Solucoes: {Solucoes.objects.count()}")
        print(f"SolucoesAcesso: {SolucoesAcesso.objects.count()}")
        print(f"Subsolucoes: {Subsolucoes.objects.count()}")
        print(f"Cert: {Cert.objects.count()}")
        
        if grupo_django:
            print(f"GrupoCliente: {GrupoCliente.objects.count()}")
            print(f"SubsolucoesAcesso: {SubsolucoesAcesso.objects.count()}")
        
        print("\n✓ TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
        
    except Exception as e:
        print(f"\n✗ ERRO: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    testar_criacao_registros()
