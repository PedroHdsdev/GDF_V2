# Solução "Reprocessamento" deixa de existir como título de menu: passa a "Ferramentas",
# com a subsolução Reproc_Painel rotulada como o painel de reprocessamento.

from django.db import migrations


def aplicar(apps, schema_editor):
    Subsolucao = apps.get_model("app", "Subsolucao")
    sub = (
        Subsolucao.objects.filter(cod_subsolucao="Reproc_Painel")
        .select_related("solucao")
        .first()
    )
    if not sub or not sub.solucao:
        return
    sol = sub.solucao
    sol.descricao = "Ferramentas"
    sol.save(update_fields=["descricao"])
    sub.descricao = "Reprocessamento"
    sub.save(update_fields=["descricao"])


def reverter(apps, schema_editor):
    Subsolucao = apps.get_model("app", "Subsolucao")
    sub = (
        Subsolucao.objects.filter(cod_subsolucao="Reproc_Painel")
        .select_related("solucao")
        .first()
    )
    if not sub or not sub.solucao:
        return
    sol = sub.solucao
    if (sol.descricao or "").strip() == "Ferramentas":
        sol.descricao = "Reprocessamento"
        sol.save(update_fields=["descricao"])
    if (sub.descricao or "").strip() == "Reprocessamento":
        sub.descricao = "Painel"
        sub.save(update_fields=["descricao"])


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0077_subsolucao_cliente_gdf_para_mandante"),
    ]

    operations = [
        migrations.RunPython(aplicar, reverter),
    ]
