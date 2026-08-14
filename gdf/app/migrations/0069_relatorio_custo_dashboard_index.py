# Índice parcial para filtros do dashboard: empresa + período + CFOPs permitidos.
# Reduz drasticamente o tamanho do índice vs. full table quando a maioria dos CFOPs está fora da lista.

from django.db import migrations

from app.db_GDF.Sap.custo_constants import RELATORIO_CUSTO_CFOP_LIST


def _sql_create_index():
    cfops = "', '".join(RELATORIO_CUSTO_CFOP_LIST)
    return f"""
        CREATE INDEX IF NOT EXISTS sap_relcusto_dash_emp_pstdat_cfop_partial
        ON sap.relatorio_custo (cod_empresa_id, pstdat DESC)
        WHERE cfop IN ('{cfops}');
    """


def _sql_drop_index():
    return 'DROP INDEX IF EXISTS sap.sap_relcusto_dash_emp_pstdat_cfop_partial;'


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0068_add_solucao_integracao_subsolucao_int_rfc'),
    ]

    operations = [
        migrations.RunSQL(
            sql=_sql_create_index(),
            reverse_sql=_sql_drop_index(),
        ),
    ]
