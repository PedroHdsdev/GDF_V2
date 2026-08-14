# Altera o rótulo do modelo ClienteGdf para Mandante, sem mexer no nome técnico do campo gdfcliente.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0091_renomear_reproc_painel_para_confronto_sped_xml"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="clientegdf",
            options={
                "verbose_name": "Mandante",
                "verbose_name_plural": "Mandantes",
            },
        ),
    ]