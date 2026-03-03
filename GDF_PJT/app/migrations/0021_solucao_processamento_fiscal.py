"""
Cria a solução Processamento Fiscal e suas subsoluções na tabela:
- Solução: Processamento Fiscal (cod_solucao = PROC_FISCAL)
- Subsoluções: Carga XML (Pro_CargaXml), Carga SPED (Pro_CargaSped), Relatório (Pro_Relatorio)
O redirect no menu usa cod_subsolucao como URL name (ex.: Pro_CargaXml).
Usa RunSQL para evitar conflito de sequence em id.
"""
from django.db import migrations


def criar_solucao_e_subsolucoes(apps, schema_editor):
    conn = schema_editor.connection
    with conn.cursor() as cursor:
        # Solucoes tem PK cod_solucao (sem coluna id)
        cursor.execute("""
            INSERT INTO solucoes (cod_solucao, descricao)
            VALUES ('PROC_FISCAL', 'Processamento Fiscal')
            ON CONFLICT (cod_solucao) DO UPDATE SET descricao = EXCLUDED.descricao
        """)
        # Subsoluções: solucao_id é a FK para solucoes (armazena cod_solucao)
        subs = [
            ('Pro_CargaXml', 'Carga XML'),
            ('Pro_CargaSped', 'Carga SPED'),
            ('Pro_Relatorio', 'Relatório'),
        ]
        cursor.execute("SELECT setval(pg_get_serial_sequence('subsolucoes', 'id'), COALESCE((SELECT MAX(id) FROM subsolucoes), 1))")
        for cod, desc in subs:
            cursor.execute("""
                INSERT INTO subsolucoes ("cod_subSolucoes", descricao, solucao_id)
                SELECT %s, %s, 'PROC_FISCAL'
                WHERE NOT EXISTS (
                    SELECT 1 FROM subsolucoes
                    WHERE "cod_subSolucoes" = %s AND solucao_id = 'PROC_FISCAL'
                )
            """, [cod, desc, cod])


def reverter_solucao_e_subsolucoes(apps, schema_editor):
    conn = schema_editor.connection
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM subsolucoes WHERE solucao_id = 'PROC_FISCAL'")
        cursor.execute("DELETE FROM solucoes WHERE cod_solucao = 'PROC_FISCAL'")


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0020_sped_tabelas'),
    ]

    operations = [
        migrations.RunPython(criar_solucao_e_subsolucoes, reverter_solucao_e_subsolucoes),
    ]
