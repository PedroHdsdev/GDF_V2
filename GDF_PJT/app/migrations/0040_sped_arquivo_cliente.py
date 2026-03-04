# -*- coding: utf-8 -*-
"""
SPED vinculado ao cliente (um cliente pode ter várias empresas).
Permite encontrar SPED mesmo quando empresa não foi resolvida na carga.
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0039_condicaoparam_cliente_fk'),
    ]

    operations = [
        migrations.AddField(
            model_name='sped_arquivo',
            name='cliente',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='sped_arquivos',
                to='app.clientes',
                db_column='cod_cliente',
                to_field='cod_cliente',
            ),
        ),
        migrations.AddIndex(
            model_name='sped_arquivo',
            index=models.Index(fields=['cliente', 'competencia'], name='sped_arquiv_cliente_comp_idx'),
        ),
    ]
