"""
Concede acesso à solução Reprocessamento (e subsolução Painel) aos clientes e grupos
que já têm acesso ao Processamento Fiscal (Relatório), para o menu aparecer sem config manual.
"""
from django.db import migrations


def conceder_acesso_reprocessamento(apps, schema_editor):
    conn = schema_editor.connection
    with conn.cursor() as cursor:
        # Clientes que têm PROCESSAMENTO ganham REPROCESSAMENTO
        cursor.execute("""
            INSERT INTO solucoes_acesso (cliente_id, solucao_id, is_active)
            SELECT DISTINCT sa.cliente_id, 'REPROCESSAMENTO', true
            FROM solucoes_acesso sa
            WHERE sa.solucao_id = 'PROCESSAMENTO'
            AND NOT EXISTS (
                SELECT 1 FROM solucoes_acesso sa2
                WHERE sa2.cliente_id = sa.cliente_id AND sa2.solucao_id = 'REPROCESSAMENTO'
            )
        """)

        # Grupos que têm Pro_Relatorio ganham Reproc_Painel
        cursor.execute("SELECT id FROM subsolucoes WHERE \"cod_subSolucoes\" = 'Reproc_Painel' AND solucao_id = 'REPROCESSAMENTO'")
        row = cursor.fetchone()
        if not row:
            return
        id_reproc_painel = row[0]
        cursor.execute("SELECT id FROM subsolucoes WHERE \"cod_subSolucoes\" = 'Pro_Relatorio' AND solucao_id = 'PROCESSAMENTO'")
        row_rel = cursor.fetchone()
        if not row_rel:
            return
        id_pro_relatorio = row_rel[0]
        cursor.execute("""
            INSERT INTO subsolucoes_acesso ("Group_id", subsolucao_id)
            SELECT sa."Group_id", %s
            FROM subsolucoes_acesso sa
            WHERE sa.subsolucao_id = %s
            AND NOT EXISTS (
                SELECT 1 FROM subsolucoes_acesso sa2
                WHERE sa2."Group_id" = sa."Group_id" AND sa2.subsolucao_id = %s
            )
        """, [id_reproc_painel, id_pro_relatorio, id_reproc_painel])


def reverter(apps, schema_editor):
    conn = schema_editor.connection
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM subsolucoes_acesso WHERE subsolucao_id IN (SELECT id FROM subsolucoes WHERE \"cod_subSolucoes\" = 'Reproc_Painel')")
        cursor.execute("DELETE FROM solucoes_acesso WHERE solucao_id = 'REPROCESSAMENTO'")


class Migration(migrations.Migration):
    dependencies = [
        ('app', '0026_solucao_reprocessamento_painel'),
    ]
    operations = [
        migrations.RunPython(conceder_acesso_reprocessamento, reverter),
    ]
