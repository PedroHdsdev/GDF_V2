# Migration 0062: Garante ON DELETE CASCADE em todas as FKs que referenciam a tabela empresa (PostgreSQL).
# Corrige ex.: usuario_empresa.empresa_id -> empresa(cod_empresa), filial, nfe, cte, nfse, parametro_carga_*, job_*, sped_*, reprocessamento_lote, etc.

from django.db import migrations


def _ensure_empresa_fk_cascade(apps, schema_editor):
    """PostgreSQL: lista FKs que referenciam empresa (ou empresas) sem CASCADE e recria com CASCADE."""
    from django.db import connection
    if connection.vendor != 'postgresql':
        return
    # Tabela atual é "empresa"; nome antigo pode ser "empresas"
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                nsp_con.nspname AS table_schema,
                rel_con.relname AS table_name,
                con.conname AS constraint_name,
                rel_ref.relname AS ref_table
            FROM pg_catalog.pg_constraint con
            JOIN pg_catalog.pg_class rel_con ON rel_con.oid = con.conrelid
            JOIN pg_catalog.pg_namespace nsp_con ON nsp_con.oid = rel_con.relnamespace
            JOIN pg_catalog.pg_class rel_ref ON rel_ref.oid = con.confrelid
            JOIN pg_catalog.pg_namespace nsp_ref ON nsp_ref.oid = rel_ref.relnamespace
            WHERE con.contype = 'f'
              AND nsp_ref.nspname = 'public'
              AND (rel_ref.relname = 'empresa' OR rel_ref.relname = 'empresas')
              AND con.confdeltype != 'c'
        """)
        missing = cursor.fetchall()
    for table_schema, table_name, constraint_name, ref_table in missing:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT a.attname
                FROM pg_catalog.pg_constraint con
                JOIN pg_catalog.pg_class rel ON rel.oid = con.conrelid
                JOIN pg_catalog.pg_namespace nsp ON nsp.oid = rel.relnamespace
                JOIN pg_catalog.pg_attribute a ON a.attrelid = con.conrelid
                    AND a.attnum = ANY(con.conkey) AND NOT a.attisdropped AND a.attnum > 0
                WHERE con.conname = %s AND nsp.nspname = %s AND rel.relname = %s
                ORDER BY array_position(con.conkey, a.attnum)
            """, [constraint_name, table_schema, table_name])
            cols = [r[0] for r in cursor.fetchall()]
        if not cols:
            continue
        col_list = ', '.join(f'"{c}"' for c in cols)
        full_table = f'"{table_schema}"."{table_name}"'
        with connection.cursor() as c2:
            c2.execute(
                f'ALTER TABLE {full_table} DROP CONSTRAINT IF EXISTS "{constraint_name}"',
                [],
            )
            c2.execute(
                f'ALTER TABLE {full_table} ADD CONSTRAINT "{constraint_name}" '
                f'FOREIGN KEY ({col_list}) REFERENCES public.empresa(cod_empresa) ON DELETE CASCADE',
                [],
            )


def _noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0061_ensure_all_fk_cliente_gdf_cascade'),
    ]

    operations = [
        migrations.RunPython(_ensure_empresa_fk_cascade, _noop_reverse),
    ]
