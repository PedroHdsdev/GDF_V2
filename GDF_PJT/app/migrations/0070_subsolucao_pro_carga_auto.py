# Grupo Django (auth_group) para permissão de parâmetros de carga automática XML/SPED.
# Atribua usuários a este grupo no Admin (Usuários → grupos).

from django.db import migrations


def create_grupo_carga_automatica(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.get_or_create(name="CargaAutomatica")


def remove_grupo_carga_automatica(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name="CargaAutomatica").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0069_relatorio_custo_dashboard_index"),
    ]

    operations = [
        migrations.RunPython(create_grupo_carga_automatica, remove_grupo_carga_automatica),
    ]
