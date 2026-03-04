# -*- coding: utf-8 -*-
"""
NFe, CTe e NFSe vinculados ao cliente (empresa e cliente na carga).
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0040_sped_arquivo_cliente'),
    ]

    operations = [
        migrations.AddField(
            model_name='nfe',
            name='cliente',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='nfe_docs',
                to='app.clientes',
                db_column='cod_cliente',
                to_field='cod_cliente',
            ),
        ),
        migrations.AddIndex(
            model_name='nfe',
            index=models.Index(fields=['cliente'], name='nfe_cliente_idx'),
        ),
        migrations.AddField(
            model_name='cte',
            name='cliente',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='cte_docs',
                to='app.clientes',
                db_column='cod_cliente',
                to_field='cod_cliente',
            ),
        ),
        migrations.AddIndex(
            model_name='cte',
            index=models.Index(fields=['cliente'], name='cte_cliente_idx'),
        ),
        migrations.AddField(
            model_name='nfse',
            name='cliente',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='nfse_docs',
                to='app.clientes',
                db_column='cod_cliente',
                to_field='cod_cliente',
            ),
        ),
        migrations.AddIndex(
            model_name='nfse',
            index=models.Index(fields=['cliente'], name='nfse_cliente_idx'),
        ),
    ]
