from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0087_fix_empresas_legacy_fk_columns"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    DO $$
                    BEGIN
                        IF to_regclass('public.cert') IS NOT NULL THEN
                            IF NOT EXISTS (
                                SELECT 1
                                FROM information_schema.columns
                                WHERE table_schema = 'public'
                                  AND table_name = 'cert'
                                  AND column_name = 'senha_certificado_enc'
                            ) THEN
                                ALTER TABLE public.cert ADD COLUMN senha_certificado_enc varchar(1024);
                            END IF;
                        END IF;
                    END
                    $$;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                )
            ],
            state_operations=[
                migrations.AddField(
                    model_name="cert",
                    name="senha_certificado_enc",
                    field=models.CharField(blank=True, max_length=1024, null=True),
                ),
            ],
        )
    ]