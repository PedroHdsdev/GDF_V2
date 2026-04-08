# Adiciona subsolução "Balanço financeiro (SAP)" (Db_BalancoFin) à solução Dashboard.

from django.db import migrations


def add_subsolucao_db_balanco_financeiro(apps, schema_editor):
    Subsolucao = apps.get_model("app", "Subsolucao")
    sub_vendas = Subsolucao.objects.filter(cod_subsolucao="Db_Vendas").select_related("solucao").first()
    if sub_vendas and sub_vendas.solucao_id:
        solucao_dashboard = sub_vendas.solucao
        if not Subsolucao.objects.filter(
            cod_subsolucao="Db_BalancoFin", solucao=solucao_dashboard
        ).exists():
            Subsolucao.objects.create(
                cod_subsolucao="Db_BalancoFin",
                descricao="Balanço financeiro (SAP)",
                solucao=solucao_dashboard,
            )


def remove_subsolucao_db_balanco_financeiro(apps, schema_editor):
    Subsolucao = apps.get_model("app", "Subsolucao")
    Subsolucao.objects.filter(cod_subsolucao="Db_BalancoFin").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0071_remove_subsolucao_pro_carga_auto"),
    ]

    operations = [
        migrations.RunPython(
            add_subsolucao_db_balanco_financeiro,
            remove_subsolucao_db_balanco_financeiro,
        ),
    ]
