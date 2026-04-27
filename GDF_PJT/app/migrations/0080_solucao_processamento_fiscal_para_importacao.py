# Renomeia a descrição da solução "Processamento Fiscal" para "Importação"
# (subsoluções Pro_CargaXml, Pro_CargaSped, Pro_Relatorio).

from django.db import migrations


def aplicar(apps, schema_editor):
    Subsolucao = apps.get_model("app", "Subsolucao")
    sub = (
        Subsolucao.objects.filter(cod_subsolucao="Pro_CargaXml")
        .select_related("solucao")
        .first()
    )
    if not sub or not sub.solucao:
        return
    sol = sub.solucao
    sol.descricao = "Importação"
    sol.save(update_fields=["descricao"])


def reverter(apps, schema_editor):
    Subsolucao = apps.get_model("app", "Subsolucao")
    sub = (
        Subsolucao.objects.filter(cod_subsolucao="Pro_CargaXml")
        .select_related("solucao")
        .first()
    )
    if not sub or not sub.solucao:
        return
    sol = sub.solucao
    if (sol.descricao or "").strip() == "Importação":
        sol.descricao = "Processamento Fiscal"
        sol.save(update_fields=["descricao"])


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0079_int_rfc_sob_ferramentas"),
    ]

    operations = [
        migrations.RunPython(aplicar, reverter),
    ]
