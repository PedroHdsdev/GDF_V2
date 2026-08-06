# Renomeia a subsolução do painel para Confronto SPED x XML.

from django.db import migrations


def aplicar(apps, schema_editor):
    Subsolucao = apps.get_model("app", "Subsolucao")
    sub = Subsolucao.objects.filter(cod_subsolucao="Reproc_Painel").first()
    if not sub:
        return
    sub.cod_subsolucao = "Confronto_Sped_Xml"
    sub.descricao = "Confronto SPED x XML"
    sub.save(update_fields=["cod_subsolucao", "descricao"])


def reverter(apps, schema_editor):
    Subsolucao = apps.get_model("app", "Subsolucao")
    sub = Subsolucao.objects.filter(cod_subsolucao="Confronto_Sped_Xml").first()
    if not sub:
        return
    sub.cod_subsolucao = "Reproc_Painel"
    sub.descricao = "Reprocessamento"
    sub.save(update_fields=["cod_subsolucao", "descricao"])


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0090_rename_senha_certificado_enc_to_senha_cert"),
    ]

    operations = [
        migrations.RunPython(aplicar, reverter),
    ]