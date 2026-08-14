# Migration 0063: Atualiza STATUS_CHOICES de CondicaoPagamentoLote (adiciona R=Erro Processamento).
# Remove duplicata do "E" e adiciona "R" para Erro Processamento.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0062_fk_empresa_on_delete_cascade'),
    ]

    operations = [
        migrations.AlterField(
            model_name='condicaopagamentolote',
            name='status',
            field=models.CharField(
                choices=[
                    ('P', 'Pendente'),
                    ('E', 'Enviado ao SAP'),
                    ('S', 'Processado no SAP'),
                    ('U', 'Atualizado no SAP (U)'),
                    ('I', 'Processado no SAP (I)'),
                    ('R', 'Erro Processamento (R)'),
                ],
                db_index=True,
                default='P',
                max_length=1,
            ),
        ),
    ]
