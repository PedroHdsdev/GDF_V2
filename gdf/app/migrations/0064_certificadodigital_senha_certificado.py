# Migration 0064: Adiciona coluna senha_certificado na tabela certificado_digital (pitografar senha do certificado).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0063_condicaopagamentolote_status_choices'),
    ]

    operations = [
        migrations.AddField(
            model_name='certificadodigital',
            name='senha_certificado',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
