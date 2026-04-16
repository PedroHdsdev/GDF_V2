# Amplia cod_subsolucao e renomeia subsolução do dashboard para Demonstrativos contábeis.

from django.db import migrations, models


def renomear_para_demonstrativos_contabeis(apps, schema_editor):
    Subsolucao = apps.get_model("app", "Subsolucao")
    Subsolucao.objects.filter(cod_subsolucao="Db_BalancoFin").update(
        cod_subsolucao="Db_DemonstrContabeis",
        descricao="Demonstrativos contábeis (SAP)",
    )


def reverter_subsolucao_para_codigo_antigo(apps, schema_editor):
    """Reverte apenas o código/descrição usados antes da migração 0075."""
    Subsolucao = apps.get_model("app", "Subsolucao")
    Subsolucao.objects.filter(cod_subsolucao="Db_DemonstrContabeis").update(
        cod_subsolucao="Db_BalancoFin",
        descricao="Balanço financeiro (SAP)",
    )


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0074_alter_sap_nome_tabela_char50"),
    ]

    operations = [
        migrations.AlterField(
            model_name="subsolucao",
            name="cod_subsolucao",
            field=models.CharField(db_column="cod_subSolucoes", max_length=25),
        ),
        migrations.RunPython(
            renomear_para_demonstrativos_contabeis,
            reverter_subsolucao_para_codigo_antigo,
        ),
    ]
