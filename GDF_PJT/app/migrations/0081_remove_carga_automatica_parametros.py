# Remove tabelas e vínculos de carga automática (XML/SPED): parametro_carga_* e FK parametro nos jobs.
# Grupo Django "CargaAutomatica" deixa de ser usado (apagado se existir).

from django.db import migrations


def remover_grupo_carga_automatica(apps, schema_editor):
    from django.contrib.auth.models import Group

    Group.objects.filter(name="CargaAutomatica").delete()


def recriar_grupo_stub(apps, schema_editor):
    from django.contrib.auth.models import Group

    Group.objects.get_or_create(name="CargaAutomatica")


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0080_solucao_processamento_fiscal_para_importacao"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="jobcargaxml",
            name="parametro",
        ),
        migrations.RemoveField(
            model_name="jobcargasped",
            name="parametro",
        ),
        migrations.DeleteModel(
            name="ParametroCargaXml",
        ),
        migrations.DeleteModel(
            name="ParametroCargaSped",
        ),
        migrations.RunPython(remover_grupo_carga_automatica, recriar_grupo_stub),
    ]
