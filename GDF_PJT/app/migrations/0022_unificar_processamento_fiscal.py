"""
Unifica Processamento Fiscal em uma única solução (PROCESSAMENTO):
- Remove a solução duplicada PROC_FISCAL e suas subsoluções.
- Garante em PROCESSAMENTO as 3 subsoluções: Carga XML, Carga SPED, Relatório.
- Remove Reprocessamento da solução PROCESSAMENTO (passa a ser solução própria no futuro).
- Preserva SubsolucoesAcesso: grupos que tinham acesso às subs de PROC_FISCAL ganham acesso às de PROCESSAMENTO.
"""
from django.db import migrations


def unificar_processamento(apps, schema_editor):
    conn = schema_editor.connection
    with conn.cursor() as cursor:
        # Guardar grupos que tinham acesso às subsoluções de PROC_FISCAL (antes de apagar)
        cursor.execute("""
            SELECT DISTINCT sa."Group_id" FROM subsolucoes_acesso sa
            INNER JOIN subsolucoes s ON s.id = sa.subsolucao_id
            WHERE s.solucao_id = 'PROC_FISCAL'
        """)
        group_ids_processamento_fiscal = [row[0] for row in cursor.fetchall()]

        # 1) Remover acesso a Reprocessamento e depois a subsolução Pro_Reproc. em PROCESSAMENTO
        cursor.execute("""
            DELETE FROM subsolucoes_acesso
            WHERE subsolucao_id IN (
                SELECT id FROM subsolucoes
                WHERE solucao_id = 'PROCESSAMENTO' AND "cod_subSolucoes" = 'Pro_Reproc.'
            )
        """)
        cursor.execute("""
            DELETE FROM subsolucoes
            WHERE solucao_id = 'PROCESSAMENTO' AND "cod_subSolucoes" = 'Pro_Reproc.'
        """)
        # 2) Em PROCESSAMENTO: atualizar descrição de Carga XML (padronizar)
        cursor.execute("""
            UPDATE subsolucoes
            SET descricao = 'Carga XML'
            WHERE solucao_id = 'PROCESSAMENTO' AND "cod_subSolucoes" = 'Pro_CargaXml'
        """)
        # 3) Em PROCESSAMENTO: adicionar Carga SPED e Relatório se não existirem
        for cod, desc in [('Pro_CargaSped', 'Carga SPED'), ('Pro_Relatorio', 'Relatório')]:
            cursor.execute("""
                INSERT INTO subsolucoes ("cod_subSolucoes", descricao, solucao_id)
                SELECT %s, %s, 'PROCESSAMENTO'
                WHERE NOT EXISTS (
                    SELECT 1 FROM subsolucoes
                    WHERE "cod_subSolucoes" = %s AND solucao_id = 'PROCESSAMENTO'
                )
            """, [cod, desc, cod])
        # 4) Remover referências em subsolucoes_acesso às subsoluções de PROC_FISCAL (antes de apagar)
        cursor.execute("""
            DELETE FROM subsolucoes_acesso
            WHERE subsolucao_id IN (SELECT id FROM subsolucoes WHERE solucao_id = 'PROC_FISCAL')
        """)
        # 5) Remover subsoluções e solução duplicada PROC_FISCAL
        cursor.execute("DELETE FROM subsolucoes WHERE solucao_id = 'PROC_FISCAL'")
        # Remover acesso à solução PROC_FISCAL (cliente já tem PROCESSAMENTO; evita FK ao apagar)
        cursor.execute("DELETE FROM solucoes_acesso WHERE solucao_id = 'PROC_FISCAL'")
        cursor.execute("DELETE FROM solucoes WHERE cod_solucao = 'PROC_FISCAL'")
        # 6) Garantir descrição da solução
        cursor.execute("""
            UPDATE solucoes SET descricao = 'Processamento Fiscal'
            WHERE cod_solucao = 'PROCESSAMENTO'
        """)
        # 7) Dar acesso aos grupos que tinham PROC_FISCAL às 3 subsoluções em PROCESSAMENTO
        for cod in ('Pro_CargaXml', 'Pro_CargaSped', 'Pro_Relatorio'):
            cursor.execute("SELECT id FROM subsolucoes WHERE solucao_id = 'PROCESSAMENTO' AND \"cod_subSolucoes\" = %s", [cod])
            row = cursor.fetchone()
            if not row:
                continue
            sub_id = row[0]
            for gid in group_ids_processamento_fiscal:
                cursor.execute("""
                    INSERT INTO subsolucoes_acesso ("Group_id", subsolucao_id)
                    SELECT %s, %s
                    WHERE NOT EXISTS (
                        SELECT 1 FROM subsolucoes_acesso
                        WHERE "Group_id" = %s AND subsolucao_id = %s
                    )
                """, [gid, sub_id, gid, sub_id])
        # 8) Grupos que já tinham acesso a PROCESSAMENTO (Pro_CargaXml) continuam com o mesmo subsolucao_id; adicionar Pro_CargaSped e Pro_Relatorio para eles
        cursor.execute("""
            SELECT DISTINCT sa."Group_id" FROM subsolucoes_acesso sa
            INNER JOIN subsolucoes s ON s.id = sa.subsolucao_id
            WHERE s.solucao_id = 'PROCESSAMENTO' AND s."cod_subSolucoes" = 'Pro_CargaXml'
        """)
        group_ids_ja_processamento = [row[0] for row in cursor.fetchall()]
        for cod in ('Pro_CargaSped', 'Pro_Relatorio'):
            cursor.execute("SELECT id FROM subsolucoes WHERE solucao_id = 'PROCESSAMENTO' AND \"cod_subSolucoes\" = %s", [cod])
            row = cursor.fetchone()
            if not row:
                continue
            sub_id = row[0]
            for gid in group_ids_ja_processamento:
                cursor.execute("""
                    INSERT INTO subsolucoes_acesso ("Group_id", subsolucao_id)
                    SELECT %s, %s
                    WHERE NOT EXISTS (
                        SELECT 1 FROM subsolucoes_acesso
                        WHERE "Group_id" = %s AND subsolucao_id = %s
                    )
                """, [gid, sub_id, gid, sub_id])


def reverter_unificar(apps, schema_editor):
    # Reverter: recriar PROC_FISCAL e suas 3 subsoluções (opcional; deixar no-op ou refazer 0021)
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0021_solucao_processamento_fiscal'),
    ]

    operations = [
        migrations.RunPython(unificar_processamento, reverter_unificar),
    ]
