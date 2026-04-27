# Rótulo da subsolução Dm_Clientes: ex. "Cliente GDF" -> "Mandante" (menu, engrenagem, sidebar).

from django.db import migrations


def aplicar(apps, schema_editor):
    Subsolucao = apps.get_model("app", "Subsolucao")
    Subsolucao.objects.filter(cod_subsolucao="Dm_Clientes").update(descricao="Mandante")


def reverter(apps, schema_editor):
    Subsolucao = apps.get_model("app", "Subsolucao")
    (
        Subsolucao.objects.filter(
            cod_subsolucao="Dm_Clientes",
            descricao="Mandante",
        ).update(descricao="Clientes GDF")
    )


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0076_solucao_administracao_para_configuracao"),
    ]

    operations = [
        migrations.RunPython(aplicar, reverter),
    ]
