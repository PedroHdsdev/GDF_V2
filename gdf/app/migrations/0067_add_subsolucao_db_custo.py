# Migration 0067: Adiciona subsolução "Custo" (Db_Custo) à solução Dashboard.

from django.db import migrations


def add_subsolucao_db_custo(apps, schema_editor):
    Subsolucao = apps.get_model('app', 'Subsolucao')
    # Encontrar a solução que contém Db_Vendas (Dashboard)
    sub_vendas = Subsolucao.objects.filter(cod_subsolucao='Db_Vendas').select_related('solucao').first()
    if sub_vendas and sub_vendas.solucao_id:
        solucao_dashboard = sub_vendas.solucao
        if not Subsolucao.objects.filter(cod_subsolucao='Db_Custo', solucao=solucao_dashboard).exists():
            Subsolucao.objects.create(
                cod_subsolucao='Db_Custo',
                descricao='Custo',
                solucao=solucao_dashboard,
            )


def remove_subsolucao_db_custo(apps, schema_editor):
    Subsolucao = apps.get_model('app', 'Subsolucao')
    Subsolucao.objects.filter(cod_subsolucao='Db_Custo').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0066_remove_bukrs_relatorio_custo_empresa_filial'),
    ]

    operations = [
        migrations.RunPython(add_subsolucao_db_custo, remove_subsolucao_db_custo),
    ]
