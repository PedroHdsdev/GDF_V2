# Migration 0053: Remove tabelas do schema reprocessamento para reformulação por grupo de empresa.
# Após esta migration, 0054 recria as tabelas com lote vinculado a grupo (grp_empresa).

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial_squashed_0052_rename_public_tables'),
    ]

    operations = [
        # 1) Dropar tabelas no banco (ordem: FKs primeiro)
        migrations.RunSQL(
            sql="""
                DROP TABLE IF EXISTS "reprocessamento"."condicao_pagamento_lote" CASCADE;
                DROP TABLE IF EXISTS "reprocessamento"."divergencia" CASCADE;
                DROP TABLE IF EXISTS "reprocessamento"."reprocessamento_job" CASCADE;
                DROP TABLE IF EXISTS "reprocessamento"."reprocessamento_lote" CASCADE;
                DROP TABLE IF EXISTS "reprocessamento"."condicao_param" CASCADE;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        # 2) Remover modelos do estado do Django para que 0054 possa recriá-los
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.DeleteModel(name='CondicaoPagamentoLote'),
                migrations.DeleteModel(name='Divergencia'),
                migrations.DeleteModel(name='ReprocessamentoJob'),
                migrations.DeleteModel(name='ReprocessamentoLote'),
                migrations.DeleteModel(name='CondicaoParam'),
            ],
        ),
    ]
