"""
Migration 0085 — Cria todas as tabelas do app que ainda não existem no banco.

Contexto: este banco de produção já tinha as tabelas cert, empresas e grp_empresas
pré-criadas. Todas as migrations anteriores (0001–0084) foram marcadas como aplicadas
via --fake. Esta migration cria as tabelas ausentes usando schema_editor com tratamento
de dependências de FK em múltiplas passagens.
"""

from django.db import migrations


def create_schemas(apps, schema_editor):
    """Garante que todos os schemas PostgreSQL existem antes das CREATE TABLEs."""
    from django.db import connection
    with connection.cursor() as c:
        for schema in ('nfe', 'cte', 'nfse', 'sped_fiscal', 'sped_contribuicao',
                       'reprocessamento', 'sap'):
            c.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')


def create_missing_tables(apps, schema_editor):
    """
    Cria apenas as tabelas que ainda não existem no banco, respeitando a ordem
    de dependências FK via múltiplas passagens. Usa savepoints para isolar
    falhas individuais sem abortar a transação inteira.
    """
    from django.db import connection, transaction
    from django.apps import apps as real_apps

    # Tabelas existentes (qualquer schema)
    with connection.cursor() as c:
        c.execute("""
            SELECT lower(table_name)
            FROM information_schema.tables
            WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
              AND table_type = 'BASE TABLE'
        """)
        existing = set(row[0] for row in c.fetchall())

    def table_key(model):
        """Extrai o nome da tabela sem prefixo de schema e sem aspas."""
        tbl = model._meta.db_table
        # Formato: '"schema"."tabela"' → 'tabela'
        if '"."' in tbl:
            return tbl.replace('"', '').split('.')[-1].lower()
        return tbl.strip('"').lower()

    def fk_deps(model):
        """Retorna o conjunto de table_keys que este modelo referencia por FK."""
        deps = set()
        for field in model._meta.local_fields:
            rel = getattr(field, 'related_model', None)
            if rel and rel is not model and rel._meta.managed:
                deps.add(table_key(rel))
        for field in model._meta.local_many_to_many:
            rel = getattr(field, 'related_model', None)
            if rel and rel is not model and rel._meta.managed:
                deps.add(table_key(rel))
        return deps

    # Todos os modelos managed do app (usa a registry real, não histórica)
    all_models = [
        m for m in real_apps.get_models()
        if m._meta.managed and m._meta.app_label == 'app'
    ]

    to_create = [m for m in all_models if table_key(m) not in existing]
    created = set()
    failed = []

    # Múltiplas passagens para respeitar dependências FK
    for _pass in range(len(to_create) + 5):
        remaining = []
        progress = False
        for model in to_create:
            key = table_key(model)
            if key in created:
                continue
            # Checa se todas as deps já existem (no banco ou foram criadas agora)
            deps = fk_deps(model) - existing
            if not deps.issubset(created):
                remaining.append(model)
                continue
            try:
                with transaction.atomic():
                    schema_editor.create_model(model)
                created.add(key)
                progress = True
                print(f'  OK  {model._meta.db_table}')
            except Exception as exc:
                # Savepoint foi revertido; transação principal continua limpa
                remaining.append(model)
                print(f'  ERR {model._meta.db_table}: {exc}')
        to_create = remaining
        if not progress:
            break

    if to_create:
        print(f'AVISO: {len(to_create)} tabelas não foram criadas:')
        for m in to_create:
            print(f'  - {m._meta.db_table} (deps: {fk_deps(m) - existing - created})')
    else:
        print(f'Todas as tabelas criadas ({len(created)} novas).')


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0084_ensure_legacy_columns_prd_safe'),
        ('auth', '0012_alter_user_first_name_max_length'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.RunPython(
            create_schemas,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RunPython(
            create_missing_tables,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
