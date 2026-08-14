from django.db import migrations


def remove_duplicate_empresa_table(apps, schema_editor):
    """Move foreign keys to the official table before removing the legacy one."""
    schema_editor.execute(
        """
        DO $$
        DECLARE
            fk record;
            constraint_definition text;
            empresa_count bigint;
        BEGIN
            IF to_regclass('public.empresa') IS NULL THEN
                RETURN;
            END IF;

            EXECUTE 'SELECT count(*) FROM public.empresa' INTO empresa_count;
            IF empresa_count > 0 THEN
                RAISE EXCEPTION
                    'A tabela public.empresa ainda possui % registro(s). Transfira/consolide os dados em public.empresas antes de executar esta migração.',
                    empresa_count;
            END IF;

            FOR fk IN
                SELECT
                    con.conname AS constraint_name,
                    nsp.nspname AS table_schema,
                    tbl.relname AS table_name,
                    pg_get_constraintdef(con.oid) AS definition
                FROM pg_constraint con
                JOIN pg_class tbl ON tbl.oid = con.conrelid
                JOIN pg_namespace nsp ON nsp.oid = tbl.relnamespace
                WHERE con.contype = 'f'
                  AND con.confrelid = 'public.empresa'::regclass
            LOOP
                constraint_definition := replace(
                    fk.definition,
                    'REFERENCES public.empresa',
                    'REFERENCES public.empresas'
                );

                EXECUTE format(
                    'ALTER TABLE %I.%I DROP CONSTRAINT %I',
                    fk.table_schema,
                    fk.table_name,
                    fk.constraint_name
                );
                EXECUTE format(
                    'ALTER TABLE %I.%I ADD CONSTRAINT %I %s',
                    fk.table_schema,
                    fk.table_name,
                    fk.constraint_name,
                    constraint_definition
                );
            END LOOP;

            DROP TABLE public.empresa;
        END
        $$;
        """
    )


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0096_align_model_options_and_indexes'),
    ]

    operations = [
        migrations.RunPython(
            remove_duplicate_empresa_table,
            reverse_code=migrations.RunPython.noop,
        ),
    ]