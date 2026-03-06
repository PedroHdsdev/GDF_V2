# Migration 0059: Adiciona FK filial em NFe, CTe e NFSe (ClienteGDF → Empresa → Filial na carga XML).

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0058_fix_reprocessamento_lote_empresa_column'),
    ]

    operations = [
        migrations.AddField(
            model_name='nfe',
            name='filial',
            field=models.ForeignKey(
                blank=True,
                db_column='filial_id',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='nfe_docs_filial',
                to='app.filial',
            ),
        ),
        migrations.AddField(
            model_name='cte',
            name='filial',
            field=models.ForeignKey(
                blank=True,
                db_column='filial_id',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='cte_docs_filial',
                to='app.filial',
            ),
        ),
        migrations.AddField(
            model_name='nfse',
            name='filial',
            field=models.ForeignKey(
                blank=True,
                db_column='filial_id',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='nfse_docs_filial',
                to='app.filial',
            ),
        ),
    ]
