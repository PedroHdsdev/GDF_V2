# Renomeia a descrição da solução (ex-Administração) para Configuração.

from django.db import migrations


def aplicar(apps, schema_editor):
    Subsolucao = apps.get_model("app", "Subsolucao")
    sub_emp = (
        Subsolucao.objects.filter(cod_subsolucao="Dm_Empresas")
        .select_related("solucao")
        .first()
    )
    if not sub_emp or not sub_emp.solucao:
        return
    sol = sub_emp.solucao
    sol.descricao = "Configuração"
    sol.save(update_fields=["descricao"])


def reverter(apps, schema_editor):
    Subsolucao = apps.get_model("app", "Subsolucao")
    sub_emp = (
        Subsolucao.objects.filter(cod_subsolucao="Dm_Empresas")
        .select_related("solucao")
        .first()
    )
    if not sub_emp or not sub_emp.solucao:
        return
    sol = sub_emp.solucao
    if (sol.descricao or "").strip() == "Configuração":
        sol.descricao = "Administração"
        sol.save(update_fields=["descricao"])


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0075_subsolucao_demonstrativos_contabeis"),
    ]

    operations = [
        migrations.RunPython(aplicar, reverter),
    ]
