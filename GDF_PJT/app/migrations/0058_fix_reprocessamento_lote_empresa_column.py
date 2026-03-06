# Migration 0058: Garante que reprocessamento_lote tenha cod_empresa_id (e não grp_empresa_id).
# Use quando o banco ainda tiver grp_empresa_id porque a 0056 não aplicou o RunSQL nessa tabela.

from django.db import migrations


def apply_reprocessamento_lote_empresa_sql(apps, schema_editor):
    """Drop grp_empresa_id se existir; adiciona cod_empresa_id se não existir."""
    with schema_editor.connection.cursor() as cursor:
        # Verificar se a coluna cod_empresa_id já existe
        cursor.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = 'reprocessamento'
              AND table_name = 'reprocessamento_lote'
              AND column_name = 'cod_empresa_id';
        """)
        if cursor.fetchone():
            return  # já migrado
        # Remover grp_empresa_id se existir
        cursor.execute("""
            ALTER TABLE "reprocessamento"."reprocessamento_lote"
            DROP COLUMN IF EXISTS grp_empresa_id CASCADE;
        """)
        # Adicionar cod_empresa_id (já verificamos que não existe)
        cursor.execute("""
            ALTER TABLE "reprocessamento"."reprocessamento_lote"
            ADD COLUMN cod_empresa_id VARCHAR(10)
            REFERENCES "empresa"("cod_empresa");
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS reprocessamento_lote_cod_empresa_id_idx
            ON "reprocessamento"."reprocessamento_lote" (cod_empresa_id);
        """)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0057_add_subsolucao_filial'),
    ]

    operations = [
        migrations.RunPython(apply_reprocessamento_lote_empresa_sql, noop_reverse),
    ]
