# Migration 0054: Recria tabelas do schema reprocessamento com lote por grupo de empresa.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0053_drop_reprocessamento_tables'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReprocessamentoLote',
            fields=[
                ('id_lote', models.BigAutoField(primary_key=True, serialize=False)),
                ('competencia', models.DateField(db_index=True, help_text='Competência do confronto (mês): 1º dia do mês (ex.: 2025-03-01 = mar/2025)')),
                ('id_arquivo_sped', models.IntegerField(blank=True, db_index=True, null=True)),
                ('total_nfe_esperado', models.IntegerField(blank=True, default=0, null=True)),
                ('total_nfe_encontrado', models.IntegerField(blank=True, default=0, null=True)),
                ('total_divergencias', models.IntegerField(blank=True, default=0, null=True)),
                ('status', models.CharField(choices=[('PENDENTE', 'Pendente'), ('EM_CONFRONTO', 'Em confronto'), ('CONCLUIDO', 'Concluído'), ('ERRO', 'Erro'), ('CANCELADO', 'Cancelado')], db_index=True, default='PENDENTE', max_length=20)),
                ('mensagem_erro', models.TextField(blank=True, null=True)),
                ('usuario_criacao', models.CharField(blank=True, max_length=120, null=True)),
                ('usuario_atualizacao', models.CharField(blank=True, max_length=120, null=True)),
                ('data_inicio', models.DateTimeField(blank=True, null=True)),
                ('data_fim', models.DateTimeField(blank=True, null=True)),
                ('data_criacao', models.DateTimeField(auto_now_add=True)),
                ('data_atualizacao', models.DateTimeField(auto_now=True)),
                ('grp_empresa', models.ForeignKey(db_column='grp_empresa_id', db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name='reprocessamento_lotes', to='app.grupoempresa', to_field='grp_empresa')),
            ],
            options={
                'db_table': '"reprocessamento"."reprocessamento_lote"',
                'ordering': ['-data_criacao'],
                'managed': True,
                'verbose_name': 'Lote de reprocessamento',
                'verbose_name_plural': 'Lotes de reprocessamento',
            },
        ),
        migrations.CreateModel(
            name='ReprocessamentoJob',
            fields=[
                ('id_job', models.BigAutoField(primary_key=True, serialize=False)),
                ('tipo', models.CharField(choices=[('CONFRONTO', 'Confronto SPED x NFe'), ('REPROCESSAR_ITEM', 'Reprocessar item'), ('REPROCESSAR_LOTE', 'Reprocessar lote')], db_index=True, max_length=25)),
                ('status', models.CharField(choices=[('AGUARDANDO', 'Aguardando'), ('EM_EXECUCAO', 'Em execução'), ('CONCLUIDO', 'Concluído'), ('ERRO', 'Erro'), ('CANCELADO', 'Cancelado')], db_index=True, default='AGUARDANDO', max_length=20)),
                ('id_lote', models.BigIntegerField(blank=True, db_index=True, null=True)),
                ('ids_divergencias', models.JSONField(blank=True, null=True)),
                ('total_processados', models.IntegerField(default=0)),
                ('total_erros', models.IntegerField(default=0)),
                ('mensagem', models.TextField(blank=True, null=True)),
                ('usuario', models.CharField(blank=True, max_length=120, null=True)),
                ('data_inicio', models.DateTimeField(blank=True, null=True)),
                ('data_fim', models.DateTimeField(blank=True, null=True)),
                ('data_criacao', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': '"reprocessamento"."reprocessamento_job"',
                'ordering': ['-data_criacao'],
                'managed': True,
                'verbose_name': 'Job de reprocessamento',
                'verbose_name_plural': 'Jobs de reprocessamento',
            },
        ),
        migrations.CreateModel(
            name='CondicaoParam',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('condicao_pagamento_nfe', models.CharField(blank=True, max_length=120, null=True)),
                ('condicao_pagamento_sap', models.CharField(blank=True, max_length=60, null=True)),
                ('tipo_pagamento', models.CharField(blank=True, max_length=2, null=True)),
                ('gdfcliente', models.ForeignKey(blank=True, db_column='cod_cliente', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='condicoes_param_reprocessamento', to='app.clientegdf', to_field='cod_cliente')),
            ],
            options={
                'db_table': '"reprocessamento"."condicao_param"',
                'ordering': ['condicao_pagamento_nfe', 'tipo_pagamento'],
                'managed': True,
                'verbose_name': 'Condição de pagamento',
                'verbose_name_plural': 'Condições de pagamento',
            },
        ),
        migrations.CreateModel(
            name='Divergencia',
            fields=[
                ('id_divergencia', models.BigAutoField(primary_key=True, serialize=False)),
                ('cod_empresa', models.CharField(blank=True, db_index=True, help_text='Empresa à qual a divergência se refere (quando aplicável).', max_length=10, null=True)),
                ('tipo', models.CharField(choices=[('NFE_AUSENTE_SPED', 'NF-e ausente no SPED'), ('SPED_AUSENTE_NFE', 'Registro SPED sem NF-e'), ('VALOR_DIFERENTE', 'Valor divergente'), ('CFOP_DIFERENTE', 'CFOP divergente'), ('DATA_EMISSAO_DIFERENTE', 'Data de emissão divergente'), ('CANCELAMENTO', 'Cancelamento/denegação'), ('OUTRO', 'Outra inconsistência')], db_index=True, max_length=30)),
                ('status', models.CharField(choices=[('ABERTA', 'Aberta'), ('EM_REPROCESSAMENTO', 'Em reprocessamento'), ('RESOLVIDA', 'Resolvida'), ('IGNORADA', 'Ignorada')], db_index=True, default='ABERTA', max_length=25)),
                ('chave_nfe', models.CharField(blank=True, db_index=True, max_length=44, null=True)),
                ('numero_nfe', models.CharField(blank=True, max_length=20, null=True)),
                ('serie_nfe', models.CharField(blank=True, max_length=5, null=True)),
                ('registro_sped', models.CharField(blank=True, max_length=20, null=True)),
                ('linha_sped', models.IntegerField(blank=True, null=True)),
                ('descricao', models.TextField(blank=True, null=True)),
                ('valor_esperado', models.DecimalField(blank=True, decimal_places=2, max_digits=18, null=True)),
                ('valor_encontrado', models.DecimalField(blank=True, decimal_places=2, max_digits=18, null=True)),
                ('detalhe_json', models.JSONField(blank=True, null=True)),
                ('id_nfe', models.IntegerField(blank=True, db_index=True, null=True)),
                ('data_reprocessamento', models.DateTimeField(blank=True, null=True)),
                ('usuario_reprocessamento', models.CharField(blank=True, max_length=120, null=True)),
                ('data_criacao', models.DateTimeField(auto_now_add=True)),
                ('data_atualizacao', models.DateTimeField(auto_now=True)),
                ('lote', models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name='divergencias', to='app.reprocessamentolote')),
            ],
            options={
                'db_table': '"reprocessamento"."divergencia"',
                'ordering': ['-data_criacao'],
                'managed': True,
                'verbose_name': 'Divergência',
                'verbose_name_plural': 'Divergências',
            },
        ),
        migrations.CreateModel(
            name='CondicaoPagamentoLote',
            fields=[
                ('id_reg', models.BigAutoField(primary_key=True, serialize=False)),
                ('cod_empresa', models.CharField(blank=True, db_index=True, help_text='Empresa da NFe (para envio SAP por empresa quando necessário).', max_length=10, null=True)),
                ('chave_nfe', models.CharField(db_index=True, max_length=44)),
                ('numero_nfe', models.CharField(blank=True, max_length=20, null=True)),
                ('serie_nfe', models.CharField(blank=True, max_length=5, null=True)),
                ('condicao_pagamento_nfe', models.CharField(blank=True, max_length=120, null=True)),
                ('condicao_pagamento_sap', models.CharField(blank=True, max_length=60, null=True)),
                ('tipo_pagamento', models.CharField(blank=True, max_length=2, null=True)),
                ('status', models.CharField(choices=[('P', 'Pendente'), ('E', 'Enviado ao SAP'), ('S', 'Processado no SAP'), ('U', 'Atualizado no SAP (U)'), ('I', 'Processado no SAP (I)')], db_index=True, default='P', max_length=1)),
                ('data_criacao', models.DateTimeField(auto_now_add=True)),
                ('data_atualizacao', models.DateTimeField(auto_now=True)),
                ('lote', models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name='condicoes_pagamento', to='app.reprocessamentolote')),
            ],
            options={
                'db_table': '"reprocessamento"."condicao_pagamento_lote"',
                'ordering': ['chave_nfe'],
                'managed': True,
                'verbose_name': 'Condição de pagamento (lote)',
                'verbose_name_plural': 'Condições de pagamento (lote)',
            },
        ),
        migrations.AddIndex(
            model_name='reprocessamentolote',
            index=models.Index(fields=['grp_empresa_id', 'competencia'], name='reprocessam_grp_emp_grp_emp_idx'),
        ),
        migrations.AddIndex(
            model_name='reprocessamentolote',
            index=models.Index(fields=['status', 'data_criacao'], name='reprocessam_status_a78c27_idx'),
        ),
        migrations.AddIndex(
            model_name='reprocessamentojob',
            index=models.Index(fields=['tipo', 'status'], name='reprocessam_tipo_77a21c_idx'),
        ),
        migrations.AddIndex(
            model_name='reprocessamentojob',
            index=models.Index(fields=['data_criacao'], name='reprocessam_data_cr_6a8a2e_idx'),
        ),
        migrations.AddIndex(
            model_name='divergencia',
            index=models.Index(fields=['lote', 'tipo'], name='divergencia_lote_id_ac33e1_idx'),
        ),
        migrations.AddIndex(
            model_name='divergencia',
            index=models.Index(fields=['chave_nfe'], name='divergencia_chave_n_a3c59f_idx'),
        ),
        migrations.AddIndex(
            model_name='divergencia',
            index=models.Index(fields=['status'], name='divergencia_status_7a9e1c_idx'),
        ),
        migrations.AddIndex(
            model_name='condicaopagamentolote',
            index=models.Index(fields=['lote', 'status'], name='condicao_pa_lote_id_682219_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='condicaopagamentolote',
            unique_together={('lote', 'chave_nfe')},
        ),
        migrations.AlterUniqueTogether(
            name='condicaoparam',
            unique_together={('gdfcliente', 'condicao_pagamento_nfe', 'tipo_pagamento')},
        ),
        migrations.AddIndex(
            model_name='condicaoparam',
            index=models.Index(fields=['gdfcliente', 'condicao_pagamento_nfe', 'tipo_pagamento'], name='condicao_pa_gdfclie_condica_idx'),
        ),
    ]
