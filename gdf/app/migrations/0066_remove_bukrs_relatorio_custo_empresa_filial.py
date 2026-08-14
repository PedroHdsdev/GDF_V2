# Migration 0066: Remove tabela Bukrs; vincula RelatorioCusto a Empresa e Filial do GDF.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0065_sap_schema_bukrs_relatorio_custo'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='relatoriocusto',
            name='sap_relcusto_bukrs_idx',
        ),
        # Remove unique constraint (bukrs_id, docnum, mjahr, mblnr) via SQL
        migrations.RunSQL(
            sql="""
                DO $$
                DECLARE r RECORD;
                BEGIN
                    FOR r IN (
                        SELECT c.conname
                        FROM pg_constraint c
                        JOIN pg_namespace n ON n.oid = c.connamespace
                        WHERE n.nspname = 'sap'
                          AND c.conrelid = '"sap"."relatorio_custo"'::regclass
                          AND c.contype = 'u'
                    ) LOOP
                        EXECUTE 'ALTER TABLE "sap"."relatorio_custo" DROP CONSTRAINT IF EXISTS ' || quote_ident(r.conname);
                    END LOOP;
                END $$;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        # Alterações no banco via SQL; state atualizado em seguida sem tocar no unique antigo
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(
                    model_name='relatoriocusto',
                    name='bukrs',
                ),
                migrations.AddField(
                    model_name='relatoriocusto',
                    name='empresa',
                    field=models.ForeignKey(
                        blank=True,
                        db_column='cod_empresa_id',
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='relatorios_custo_sap',
                        to='app.empresa',
                        to_field='cod_empresa',
                        verbose_name='Empresa',
                    ),
                ),
                migrations.AddField(
                    model_name='relatoriocusto',
                    name='filial',
                    field=models.ForeignKey(
                        blank=True,
                        db_column='filial_id',
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='relatorios_custo_sap',
                        to='app.filial',
                        verbose_name='Filial',
                    ),
                ),
                migrations.AlterUniqueTogether(
                    name='relatoriocusto',
                    unique_together={('empresa', 'docnum', 'mjahr', 'mblnr')},
                ),
                migrations.AddIndex(
                    model_name='relatoriocusto',
                    index=models.Index(fields=['empresa', 'docnum', 'mjahr', 'mblnr'], name='sap_relcusto_empresa_idx'),
                ),
                migrations.DeleteModel(
                    name='Bukrs',
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql='ALTER TABLE "sap"."relatorio_custo" DROP COLUMN IF EXISTS bukrs_id;',
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    sql='''
                        ALTER TABLE "sap"."relatorio_custo"
                        ADD COLUMN IF NOT EXISTS cod_empresa_id VARCHAR(10) REFERENCES empresa(cod_empresa) ON DELETE RESTRICT,
                        ADD COLUMN IF NOT EXISTS filial_id BIGINT REFERENCES filial(id) ON DELETE RESTRICT;
                    ''',
                    reverse_sql='ALTER TABLE "sap"."relatorio_custo" DROP COLUMN IF EXISTS cod_empresa_id, DROP COLUMN IF EXISTS filial_id;',
                ),
                migrations.RunSQL(
                    sql='ALTER TABLE "sap"."relatorio_custo" ADD CONSTRAINT sap_relcusto_emp_uniq UNIQUE (cod_empresa_id, docnum, mjahr, mblnr);',
                    reverse_sql='ALTER TABLE "sap"."relatorio_custo" DROP CONSTRAINT IF EXISTS sap_relcusto_emp_uniq;',
                ),
                migrations.RunSQL(
                    sql='CREATE INDEX IF NOT EXISTS sap_relcusto_empresa_idx ON "sap"."relatorio_custo"(cod_empresa_id, docnum, mjahr, mblnr);',
                    reverse_sql='DROP INDEX IF EXISTS "sap".sap_relcusto_empresa_idx;',
                ),
                migrations.RunSQL(
                    sql='DROP TABLE IF EXISTS "sap"."bukrs";',
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
        ),
    ]
