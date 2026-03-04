"""
Cria a solução Reprocessamento e a subsolução Painel.
- Solução: Reprocessamento (cod_solucao = REPROCESSAMENTO)
- Subsolução: Painel (Reproc_Painel) – confronto SPED x NFe, divergências e reprocessamento.
"""
from django.db import migrations


def criar_solucao_reprocessamento(apps, schema_editor):
    conn = schema_editor.connection
    with conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO solucoes (cod_solucao, descricao)
            VALUES ('REPROCESSAMENTO', 'Reprocessamento')
            ON CONFLICT (cod_solucao) DO UPDATE SET descricao = EXCLUDED.descricao
        """)
        cursor.execute("""
            SELECT setval(pg_get_serial_sequence('subsolucoes', 'id'),
                COALESCE((SELECT MAX(id) FROM subsolucoes), 1))
        """)
        cursor.execute("""
            INSERT INTO subsolucoes ("cod_subSolucoes", descricao, solucao_id)
            SELECT 'Reproc_Painel', 'Painel', 'REPROCESSAMENTO'
            WHERE NOT EXISTS (
                SELECT 1 FROM subsolucoes
                WHERE "cod_subSolucoes" = 'Reproc_Painel' AND solucao_id = 'REPROCESSAMENTO'
            )
        """)


def reverter(apps, schema_editor):
    conn = schema_editor.connection
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM subsolucoes WHERE solucao_id = 'REPROCESSAMENTO'")
        cursor.execute("DELETE FROM solucoes WHERE cod_solucao = 'REPROCESSAMENTO'")


class Migration(migrations.Migration):
    dependencies = [
        ('app', '0025_reprocessamento_schema_e_tabelas'),
    ]
    operations = [
        migrations.RunPython(criar_solucao_reprocessamento, reverter),
    ]
