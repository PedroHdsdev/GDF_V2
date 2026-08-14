from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0089_migrate_and_drop_plain_cert_password"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    DO $$
                    BEGIN
                        IF to_regclass('public.cert') IS NOT NULL THEN
                            IF EXISTS (
                                SELECT 1
                                FROM information_schema.columns
                                WHERE table_schema = 'public'
                                  AND table_name = 'cert'
                                  AND column_name = 'senha_certificado_enc'
                            ) THEN
                                IF NOT EXISTS (
                                    SELECT 1
                                    FROM information_schema.columns
                                    WHERE table_schema = 'public'
                                      AND table_name = 'cert'
                                      AND column_name = 'senha_cert'
                                ) THEN
                                    ALTER TABLE public.cert RENAME COLUMN senha_certificado_enc TO senha_cert;
                                END IF;
                            ELSIF NOT EXISTS (
                                SELECT 1
                                FROM information_schema.columns
                                WHERE table_schema = 'public'
                                  AND table_name = 'cert'
                                  AND column_name = 'senha_cert'
                            ) THEN
                                ALTER TABLE public.cert ADD COLUMN senha_cert varchar(1024);
                            END IF;
                        END IF;
                    END
                    $$;
                    """,
                    reverse_sql="""
                    DO $$
                    BEGIN
                        IF to_regclass('public.cert') IS NOT NULL THEN
                            IF EXISTS (
                                SELECT 1
                                FROM information_schema.columns
                                WHERE table_schema = 'public'
                                  AND table_name = 'cert'
                                  AND column_name = 'senha_cert'
                            ) THEN
                                IF NOT EXISTS (
                                    SELECT 1
                                    FROM information_schema.columns
                                    WHERE table_schema = 'public'
                                      AND table_name = 'cert'
                                      AND column_name = 'senha_certificado_enc'
                                ) THEN
                                    ALTER TABLE public.cert RENAME COLUMN senha_cert TO senha_certificado_enc;
                                END IF;
                            END IF;
                        END IF;
                    END
                    $$;
                    """,
                )
            ],
            state_operations=[
                migrations.RenameField(
                    model_name="cert",
                    old_name="senha_certificado_enc",
                    new_name="senha_cert",
                )
            ],
        )
    ]
