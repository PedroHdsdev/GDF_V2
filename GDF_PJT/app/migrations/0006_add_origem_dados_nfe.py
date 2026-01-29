# Generated manually on 2026-01-29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_nfe_empresa'),
    ]

    operations = [
        migrations.AddField(
            model_name='nfe',
            name='origem_dados',
            field=models.CharField(
                max_length=8,
                choices=[
                    ('LOCAL', 'Maquina Local'),
                    ('SAP', 'Importação SAP'),
                    ('SPED', 'Importação SPED'),
                    ('OUTROS', 'Outros'),
                ],
                default='LOCAL',
            ),
        ),
    ]
