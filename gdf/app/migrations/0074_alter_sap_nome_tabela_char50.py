# Amplia sap_nome_tabela (NAME_TABLE na RFC) para 30 caracteres.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0073_nfe_sap_chave_tabela"),
    ]

    operations = [
        migrations.AlterField(
            model_name="nfe",
            name="sap_nome_tabela",
            field=models.CharField(
                blank=True,
                help_text="Nome da tabela SAP onde o documento foi localizado (NAME_TABLE na RFC).",
                max_length=30,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="cte",
            name="sap_nome_tabela",
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name="nfse",
            name="sap_nome_tabela",
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
    ]
