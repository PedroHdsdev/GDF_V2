#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GDF_PJT.settings')

import sys
sys.path.insert(0, r'c:\Users\pedro.silva\Documents\Visual Studio Code\GDF_V2\GDF_PJT')

django.setup()

from app.classes.Gdf import Cl_Gdf
from app.db_GDF.Public.models import Clientes, GrupoCliente

# Buscar um cliente
cliente = Clientes.objects.first()
if cliente:
    print(f"\n✓ Cliente encontrado: {cliente.cod_cliente} - {cliente.razao}")
    
    # Buscar grupos do cliente
    grupos = GrupoCliente.objects.filter(cliente__cod_cliente=cliente.cod_cliente)
    print(f"✓ Grupos vinculados ao cliente: {grupos.count()}")
    for g in grupos:
        print(f"  - {g.group.name} (ID: {g.group.id})")
    
    # Testar método get_usuarios
    print("\n[TEST] Chamando get_usuarios...")
    cl_gdf = Cl_Gdf()
    usuarios, empresas, grupos_dict, _ = cl_gdf.get_usuarios(i_cod_Cliente=cliente.cod_cliente)
    
    print(f"✓ Usuários: {len(usuarios)}")
    print(f"✓ Empresas: {len(empresas)}")
    print(f"✓ Grupos: {len(grupos_dict)}")
    print(f"\nGrupos retornados:")
    for g in grupos_dict:
        print(f"  - {g}")
else:
    print("Nenhum cliente encontrado!")
