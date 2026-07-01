from django.db import migrations


def migrate_plain_to_encrypted(apps, schema_editor):
    Cert = apps.get_model("app", "Cert")

    try:
        from app.security.cert_password_crypto import encrypt_cert_password
    except Exception:
        return

    qs = Cert.objects.exclude(senha_certificado__isnull=True).exclude(senha_certificado="")
    for cert in qs.iterator():
        if cert.senha_certificado_enc:
            continue
        cert.senha_certificado_enc = encrypt_cert_password(cert.senha_certificado)
        cert.save(update_fields=["senha_certificado_enc"])


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0088_cert_add_senha_certificado_enc"),
    ]

    operations = [
        migrations.RunPython(migrate_plain_to_encrypted, migrations.RunPython.noop),
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
                                  AND column_name = 'senha_certificado'
                            ) THEN
                                ALTER TABLE public.cert DROP COLUMN senha_certificado;
                            END IF;
                        END IF;
                    END
                    $$;
                    """,
                    reverse_sql="""
                    DO $$
                    BEGIN
                        IF to_regclass('public.cert') IS NOT NULL THEN
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
                    END
                    $$;
                    """,
                )
            ],
            state_operations=[
                migrations.RemoveField(
                    model_name="cert",
                    name="senha_certificado",
                ),
            ],
        ),
    ]
