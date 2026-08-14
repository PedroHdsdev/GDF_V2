# Adiciona subsolução "Demonstrativos contábeis (SAP)" (Db_DemonstrContabeis) à solução Dashboard.
# Nome do ficheiro mantém o histórico da migração original.

from django.db import migrations


def add_subsolucao_db_demonstrativos_contabeis(apps, schema_editor):
    Subsolucao = apps.get_model("app", "Subsolucao")
    sub_vendas = Subsolucao.objects.filter(cod_subsolucao="Db_Vendas").select_related("solucao").first()
    if sub_vendas and sub_vendas.solucao_id:
        solucao_dashboard = sub_vendas.solucao
        if not Subsolucao.objects.filter(
            cod_subsolucao="Db_DemonstrContabeis", solucao=solucao_dashboard
        ).exists():
            Subsolucao.objects.create(
                cod_subsolucao="Db_DemonstrContabeis",
                descricao="Demonstrativos contábeis (SAP)",
                solucao=solucao_dashboard,
            )


def remove_subsolucao_db_demonstrativos_contabeis(apps, schema_editor):
    Subsolucao = apps.get_model("app", "Subsolucao")
    Subsolucao.objects.filter(cod_subsolucao="Db_DemonstrContabeis").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0071_remove_subsolucao_pro_carga_auto"),
    ]

    operations = [
        migrations.RunPython(
            add_subsolucao_db_demonstrativos_contabeis,
            remove_subsolucao_db_demonstrativos_contabeis,
        ),
    ]
