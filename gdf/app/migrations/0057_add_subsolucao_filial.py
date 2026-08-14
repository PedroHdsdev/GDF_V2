# Migration 0057: Adiciona subsolução "Filial" (Dm_Filiais) à solução de Administração.

from django.db import migrations


def add_subsolucao_filial(apps, schema_editor):
    Solucao = apps.get_model('app', 'Solucao')
    Subsolucao = apps.get_model('app', 'Subsolucao')
    # Encontrar a solução que contém a subsolução Dm_Empresas (Administração)
    sub_empresas = Subsolucao.objects.filter(cod_subsolucao='Dm_Empresas').select_related('solucao').first()
    if sub_empresas and sub_empresas.solucao_id:
        solucao_adm = sub_empresas.solucao
        if not Subsolucao.objects.filter(cod_subsolucao='Dm_Filiais', solucao=solucao_adm).exists():
            Subsolucao.objects.create(
                cod_subsolucao='Dm_Filiais',
                descricao='Filial',
                solucao=solucao_adm,
            )


def remove_subsolucao_filial(apps, schema_editor):
    Subsolucao = apps.get_model('app', 'Subsolucao')
    Subsolucao.objects.filter(cod_subsolucao='Dm_Filiais').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0056_remove_grupo_empresa_add_filial'),
    ]

    operations = [
        migrations.RunPython(add_subsolucao_filial, remove_subsolucao_filial),
    ]
