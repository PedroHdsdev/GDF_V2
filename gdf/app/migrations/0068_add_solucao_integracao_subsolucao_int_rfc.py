# Migration 0068: Cria solução Integração e subsolução Int_Rfc (RFC SAP para alimentar schema sap).

from django.db import migrations


def add_solucao_integracao_int_rfc(apps, schema_editor):
    Solucao = apps.get_model('app', 'Solucao')
    Subsolucao = apps.get_model('app', 'Subsolucao')

    solucao_int, _ = Solucao.objects.get_or_create(
        cod_solucao='Int',
        defaults={'descricao': 'Integração'},
    )
    if not Subsolucao.objects.filter(cod_subsolucao='Int_Rfc', solucao=solucao_int).exists():
        Subsolucao.objects.create(
            cod_subsolucao='Int_Rfc',
            descricao='RFC SAP',
            solucao=solucao_int,
        )


def remove_solucao_integracao_int_rfc(apps, schema_editor):
    Subsolucao = apps.get_model('app', 'Subsolucao')
    Solucao = apps.get_model('app', 'Solucao')

    Subsolucao.objects.filter(cod_subsolucao='Int_Rfc').delete()
    # Remover solução Int apenas se não tiver outras subsoluções
    sol_int = Solucao.objects.filter(cod_solucao='Int').first()
    if sol_int and not Subsolucao.objects.filter(solucao=sol_int).exists():
        sol_int.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0067_add_subsolucao_db_custo'),
    ]

    operations = [
        migrations.RunPython(add_solucao_integracao_int_rfc, remove_solucao_integracao_int_rfc),
    ]
