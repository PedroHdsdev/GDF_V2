# Remove subsolução Pro_CargaAuto (abordagem antiga) se existir, após migração para grupo Django.

from django.db import migrations


def remove_pro_carga_auto_subsolucao(apps, schema_editor):
    Subsolucao = apps.get_model("app", "Subsolucao")
    AcessoSubsolucaoGrupo = apps.get_model("app", "AcessoSubsolucaoGrupo")
    sub = Subsolucao.objects.filter(cod_subsolucao="Pro_CargaAuto").first()
    if sub:
        AcessoSubsolucaoGrupo.objects.filter(subsolucao=sub).delete()
        sub.delete()

    Group = apps.get_model("auth", "Group")
    Group.objects.get_or_create(name="CargaAutomatica")


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0070_subsolucao_pro_carga_auto"),
    ]

    operations = [
        migrations.RunPython(remove_pro_carga_auto_subsolucao, noop_reverse),
    ]
