# Migration 0061: Garante que TODAS as FKs para cliente_gdf (em qualquer schema) tenham ON DELETE CASCADE.
# Usa pg_catalog.pg_constraint para achar qualquer FK que aponte para public.cliente_gdf e não tenha CASCADE.

from django.db import migrations


def _ensure_cascade_via_pg_constraint(apps, schema_editor):
    """PostgreSQL: lista FKs que referenciam cliente_gdf sem CASCADE e recria com CASCADE."""
    from django.db import connection
    if connection.vendor != 'postgresql':
        return
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                nsp_con.nspname AS table_schema,
                rel_con.relname AS table_name,
                con.conname AS constraint_name,
                con.confdeltype
            FROM pg_catalog.pg_constraint con
            JOIN pg_catalog.pg_class rel_con ON rel_con.oid = con.conrelid
            JOIN pg_catalog.pg_namespace nsp_con ON nsp_con.oid = rel_con.relnamespace
            WHERE con.contype = 'f'
              AND con.confrelid = (
                SELECT c.oid FROM pg_catalog.pg_class c
                JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public' AND c.relname = 'cliente_gdf'
              )
              AND con.confdeltype != 'c'
        """)
        missing = cursor.fetchall()
    for table_schema, table_name, constraint_name, _ in missing:
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
                f'FOREIGN KEY ({col_list}) REFERENCES public.cliente_gdf(cod_cliente) ON DELETE CASCADE',
                [],
            )


def _noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0060_fk_cliente_gdf_on_delete_cascade'),
    ]

    operations = [
        migrations.RunPython(_ensure_cascade_via_pg_constraint, _noop_reverse),
    ]
