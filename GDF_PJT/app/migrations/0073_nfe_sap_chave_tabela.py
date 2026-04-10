# NF-e / CT-e / NFS-e: indicador SAP + tabela; remove origem_dados da NF-e e do parâmetro de carga.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0072_add_subsolucao_db_balanco_financeiro"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="nfe",
            name="origem_dados",
        ),
        migrations.AddField(
            model_name="nfe",
            name="tem_sap",
            field=models.BooleanField(
                default=False,
                help_text="True se a chave foi encontrada no SAP.",
            ),
        ),
        migrations.AddField(
            model_name="nfe",
            name="sap_nome_tabela",
            field=models.CharField(
                blank=True,
                help_text="Nome da tabela SAP onde o documento foi localizado.",
                max_length=20,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="cte",
            name="tem_sap",
            field=models.BooleanField(
                default=False,
                help_text="True se a chave foi encontrada no SAP.",
            ),
        ),
        migrations.AddField(
            model_name="cte",
            name="sap_nome_tabela",
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name="nfse",
            name="tem_sap",
            field=models.BooleanField(
                default=False,
                help_text="True se a chave foi encontrada no SAP.",
            ),
        ),
        migrations.AddField(
            model_name="nfse",
            name="sap_nome_tabela",
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.RemoveField(
            model_name="parametrocargaxml",
            name="origem_dados",
        ),
    ]
