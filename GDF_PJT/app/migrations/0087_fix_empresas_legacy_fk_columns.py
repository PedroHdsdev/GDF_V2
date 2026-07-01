from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0086_align_empresas_table_state_only"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                -- empresas.cert (legado sem coluna de certificado)
                IF to_regclass('public.empresas') IS NOT NULL THEN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_schema = 'public'
                          AND table_name = 'empresas'
                          AND column_name = 'cert'
                    ) THEN
                        ALTER TABLE public.empresas ADD COLUMN cert varchar(8);
                    END IF;

                    IF to_regclass('public.cert') IS NOT NULL THEN
                        IF NOT EXISTS (
                            SELECT 1
                            FROM pg_constraint
                            WHERE conname = 'empresas_cert_fk'
                              AND conrelid = 'public.empresas'::regclass
                        ) THEN
                            ALTER TABLE public.empresas
                            ADD CONSTRAINT empresas_cert_fk
                            FOREIGN KEY (cert) REFERENCES public.cert(raiz_cnpj)
                            ON DELETE NO ACTION ON UPDATE NO ACTION;
                        END IF;
                    END IF;
                END IF;
            END
            $$;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterField(
                    model_name="empresas",
                    name="grp_empresa",
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        db_column="grp_empresa",
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="app.grpempresas",
                    ),
                ),
                migrations.AlterField(
                    model_name="empresas",
                    name="cert",
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        db_column="cert",
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="app.cert",
                    ),
                ),
            ],
        ),
    ]
