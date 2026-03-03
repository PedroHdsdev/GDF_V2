"""Cria o schema 'sped' no PostgreSQL para as tabelas SPED (fiscal e contribuição)."""
from django.db import migrations


class Migration(migrations.Migration):
    initial = False

    dependencies = [
        ('app', '0018_cargasped_param_job'),
    ]

    operations = [
        migrations.RunSQL(
            sql='CREATE SCHEMA IF NOT EXISTS "sped";',
            reverse_sql='DROP SCHEMA IF EXISTS "sped" CASCADE;',
        ),
    ]
