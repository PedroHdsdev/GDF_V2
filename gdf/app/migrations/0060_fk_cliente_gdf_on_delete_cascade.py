# Migration 0060: Garante ON DELETE CASCADE nas FKs que referenciam cliente_gdf (PostgreSQL).
# Corrige constraints em qualquer schema (nfe, cte, nfse, reprocessamento, sped_*, public, etc.).

from django.db import migrations


def _recreate_fk_cascade(apps, schema_editor):
    """PostgreSQL: para cada FK que aponta para cliente_gdf (em qualquer schema), recria com ON DELETE CASCADE."""
    from django.db import connection
    if connection.vendor != 'postgresql':
        return
    # 1) Via information_schema (todas as tabelas/schemas que referenciam cliente_gdf ou clientes)
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                tc.table_schema,
                tc.table_name,
                kcu.column_name,
                tc.constraint_name,
                COALESCE(ccu.table_schema, 'public') AS ref_schema,
                ccu.column_name AS ref_column
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
                AND tc.constraint_schema = kcu.constraint_schema
            JOIN information_schema.constraint_column_usage ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.constraint_schema = tc.constraint_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND (ccu.table_name = 'cliente_gdf' OR ccu.table_name = 'clientes')
              AND ccu.column_name = 'cod_cliente'
        """)
        rows = cursor.fetchall()
    for table_schema, table_name, column_name, constraint_name, ref_schema, ref_column in rows:
        full_table = f'"{table_schema}"."{table_name}"'
        ref_schema = ref_schema or 'public'
        # Identificadores vêm do banco (não user input); montar SQL para evitar escape de %s como literal
        with connection.cursor() as c2:
            c2.execute(
                f'ALTER TABLE {full_table} DROP CONSTRAINT IF EXISTS "{constraint_name}"',
                [],
            )
            c2.execute(
                f'ALTER TABLE {full_table} ADD CONSTRAINT "{constraint_name}" '
                f'FOREIGN KEY ("{column_name}") REFERENCES "{ref_schema}"."cliente_gdf"("{ref_column}") ON DELETE CASCADE',
                [],
            )
    # 2) Via pg_constraint: garantir que nenhum FK para cliente_gdf ficou sem CASCADE (qualquer schema)
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
    if missing:
        # Recriar FKs que pg_constraint encontrou sem CASCADE (ex.: tabelas em outros schemas)
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


def _reverse_recreate_fk_cascade(apps, schema_editor):
    """Reverse: não recriamos a constraint antiga; deixar estado anterior seria complexo."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0059_add_filial_to_nfe_cte_nfse'),
    ]

    operations = [
        migrations.RunPython(_recreate_fk_cascade, _reverse_recreate_fk_cascade),
    ]
