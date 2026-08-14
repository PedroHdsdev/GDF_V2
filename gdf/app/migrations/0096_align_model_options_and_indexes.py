from django.db import migrations


def align_indexes(apps, schema_editor):
    schema_editor.execute(
        "DROP INDEX IF EXISTS public.empresa_cnpj_9e4098_idx;"
    )
    schema_editor.execute(
        """
        DO $$
        BEGIN
            IF to_regclass('public.cliente_gdf_cnpj_3df010_idx') IS NOT NULL
               AND to_regclass('public.mandante_cnpj_5f2fba_idx') IS NULL THEN
                ALTER INDEX public.cliente_gdf_cnpj_3df010_idx
                RENAME TO mandante_cnpj_5f2fba_idx;
            END IF;

            IF to_regclass('public.conexao_sap_gdf_tipo_24f592_idx') IS NOT NULL
               AND to_regclass('public.conexao_sap_gdfclie_a17ac6_idx') IS NULL THEN
                ALTER INDEX public.conexao_sap_gdf_tipo_24f592_idx
                RENAME TO conexao_sap_gdfclie_a17ac6_idx;
            END IF;
        END
        $$;
        """
    )


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0095_add_tipo_conexao_conexao_sap'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='clientegdf',
            options={'managed': True, 'verbose_name': 'Mandante', 'verbose_name_plural': 'Mandantes'},
        ),
        migrations.AlterModelOptions(
            name='empresas',
            options={'managed': True, 'verbose_name': 'Empresa', 'verbose_name_plural': 'Empresas'},
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[migrations.RunPython(align_indexes, migrations.RunPython.noop)],
            state_operations=[
                migrations.RemoveIndex(
                    model_name='empresas',
                    name='empresa_cnpj_9e4098_idx',
                ),
                migrations.RenameIndex(
                    model_name='clientegdf',
                    new_name='mandante_cnpj_5f2fba_idx',
                    old_name='cliente_gdf_cnpj_3df010_idx',
                ),
                migrations.RenameIndex(
                    model_name='conexaosap',
                    new_name='conexao_sap_gdfclie_a17ac6_idx',
                    old_name='conexao_sap_gdf_tipo_24f592_idx',
                ),
            ],
        ),
    ]