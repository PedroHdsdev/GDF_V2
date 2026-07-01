from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0083_empresas_grpempresas_spedcontribuicaoarquivo_and_more"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                -- cert.arquivo_cert
                IF to_regclass('public.cert') IS NOT NULL THEN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_schema = 'public'
                          AND table_name = 'cert'
                          AND column_name = 'arquivo_cert'
                    ) THEN
                        ALTER TABLE public.cert ADD COLUMN arquivo_cert bytea;
                    END IF;

                    -- cert.senha_certificado
                    IF NOT EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_schema = 'public'
                          AND table_name = 'cert'
                          AND column_name = 'senha_certificado'
                    ) THEN
                        ALTER TABLE public.cert ADD COLUMN senha_certificado varchar(255);
                    END IF;
                END IF;

                -- empresa.gdfcliente_id (schema atual do código)
                IF to_regclass('public.empresa') IS NOT NULL THEN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_schema = 'public'
                          AND table_name = 'empresa'
                          AND column_name = 'gdfcliente_id'
                    ) THEN
                        ALTER TABLE public.empresa ADD COLUMN gdfcliente_id varchar(10);
                    END IF;
                END IF;

                -- empresas.gdfcliente_id (banco legado ainda no plural)
                IF to_regclass('public.empresas') IS NOT NULL THEN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_schema = 'public'
                          AND table_name = 'empresas'
                          AND column_name = 'gdfcliente_id'
                    ) THEN
                        ALTER TABLE public.empresas ADD COLUMN gdfcliente_id varchar(10);
                    END IF;
                END IF;
            END
            $$;
            """,
            reverse_sql=migrations.RunSQL.noop,
        )
    ]
