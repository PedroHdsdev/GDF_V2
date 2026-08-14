# Migration 0056: Remove GrupoEmpresa, adiciona Filial (ClienteGdf → Empresa → Filial), lote por empresa.

import django.db.models.deletion
from django.db import migrations, models


class RemoveFieldIfExists(migrations.RemoveField):
    """RemoveField que não falha se o campo já não estiver no estado (ex.: merge com outro branch)."""

    def state_forwards(self, app_label, state):
        model_state = state.models.get((app_label, self.model_name_lower))
        if model_state and self.name in model_state.fields:
            super().state_forwards(app_label, state)


class DeleteModelIfExists(migrations.DeleteModel):
    """DeleteModel que não falha se o modelo já não estiver no estado."""

    def state_forwards(self, app_label, state):
        if (app_label, self.name.lower()) in state.models:
            super().state_forwards(app_label, state)


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0055_merge_reprocessamento_heads'),
    ]

    operations = [
        # 1) Banco: remover coluna grp_empresa de empresa e tabela grupo_empresa
        migrations.RunSQL(
            sql="ALTER TABLE empresa DROP COLUMN IF EXISTS grp_empresa_id CASCADE;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS grupo_empresa CASCADE;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        # 2) Banco: reprocessamento_lote passa a ter cod_empresa_id (FK empresa)
        migrations.RunSQL(
            sql="""
                ALTER TABLE "reprocessamento"."reprocessamento_lote"
                DROP COLUMN IF EXISTS grp_empresa_id CASCADE;
                ALTER TABLE "reprocessamento"."reprocessamento_lote"
                ADD COLUMN IF NOT EXISTS cod_empresa_id VARCHAR(10) REFERENCES empresa(cod_empresa);
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        # 3) Criar tabela filial
        migrations.CreateModel(
            name='Filial',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('cod_filial', models.CharField(db_index=True, max_length=10)),
                ('nome', models.CharField(blank=True, max_length=120, null=True)),
                ('cnpj', models.CharField(blank=True, max_length=14, null=True)),
                ('ativo', models.BooleanField(default=True)),
                ('empresa', models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name='filiais', to='app.empresa')),
            ],
            options={
                'db_table': 'filial',
                'managed': True,
                'verbose_name': 'Filial',
                'verbose_name_plural': 'Filiais',
            },
        ),
        migrations.AddConstraint(
            model_name='filial',
            constraint=models.UniqueConstraint(fields=('empresa', 'cod_filial'), name='filial_empresa_cod_filial_uniq'),
        ),
        migrations.AddIndex(
            model_name='filial',
            index=models.Index(fields=['empresa', 'cod_filial'], name='filial_empresa_cod_fil_idx'),
        ),
        # 4) Estado: remover grp_empresa de Empresa e apagar modelo GrupoEmpresa (só se existir no estado)
        migrations.SeparateDatabaseAndState(
            state_operations=[
                RemoveFieldIfExists(model_name='empresa', name='grp_empresa'),
                DeleteModelIfExists(name='GrupoEmpresa'),
            ],
            database_operations=[],
        ),
        # 5) Estado: ReprocessamentoLote deixa de ter grp_empresa e ganha empresa (só se existir no estado)
        migrations.SeparateDatabaseAndState(
            state_operations=[
                RemoveFieldIfExists(model_name='reprocessamentolote', name='grp_empresa'),
                migrations.AddField(
                    model_name='reprocessamentolote',
                    name='empresa',
                    field=models.ForeignKey(
                        db_column='cod_empresa_id',
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='reprocessamento_lotes',
                        to='app.empresa',
                        to_field='cod_empresa',
                    ),
                ),
            ],
            database_operations=[],
        ),
        migrations.AddIndex(
            model_name='reprocessamentolote',
            index=models.Index(fields=['empresa_id', 'competencia'], name='reprocessam_empresa_comp_idx'),
        ),
    ]
