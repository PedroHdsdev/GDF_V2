"""Create DB schemas required by NFe/CTe/NFSe models.

This migration ensures the PostgreSQL schemas exist before the model
tables are created. It is idempotent and safe to run multiple times.
"""
from django.db import migrations


class Migration(migrations.Migration):
    initial = False

    dependencies = [
        ('app', '0013_remove_modelos_add_empresa_fk'),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                'CREATE SCHEMA IF NOT EXISTS "nfe"; '
                'CREATE SCHEMA IF NOT EXISTS "cte"; '
                'CREATE SCHEMA IF NOT EXISTS "nfse";'
            ),
            reverse_sql=(
                'DROP SCHEMA IF EXISTS "nfse" CASCADE; '
                'DROP SCHEMA IF EXISTS "cte" CASCADE; '
                'DROP SCHEMA IF EXISTS "nfe" CASCADE;'
            ),
        ),
    ]
