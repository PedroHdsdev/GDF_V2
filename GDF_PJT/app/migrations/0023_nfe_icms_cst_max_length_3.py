# Suporte a CSOSN (Simples Nacional): CST pode ser 2 ou 3 dígitos (101, 102, 201, 900, etc.)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0022_unificar_processamento_fiscal'),
    ]

    operations = [
        migrations.AlterField(
            model_name='nfe_icms',
            name='cst',
            field=models.CharField(
                max_length=3,
                choices=[
                    ('00', 'Tributada integralmente'),
                    ('10', 'Tributada e com cobrança do ICMS por ST'),
                    ('20', 'Com redução de base de cálculo'),
                    ('30', 'Isenta ou não tributada e com cobrança do ICMS por ST'),
                    ('40', 'Isenta'),
                    ('41', 'Não tributada'),
                    ('50', 'Suspensão'),
                    ('51', 'Diferimento'),
                    ('60', 'ICMS cobrado anteriormente por ST'),
                    ('70', 'Com redução de base de cálculo e cobrança do ICMS por ST'),
                    ('90', 'Outras operações'),
                ],
            ),
        ),
    ]
