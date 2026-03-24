"""
Constantes compartilhadas: dashboard de custo (Streamlit) e índices/migrações Django.
"""

# CFOPs exibidos no dashboard — alinhado ao filtro da query e ao índice parcial (migration).
RELATORIO_CUSTO_CFOP_LIST = [
    "1201AA",
    "1202AA",
    "1410AA",
    "1411AA",
    "2202AA",
    "2410AA",
    "2411AA",
    "5101AA",
    "5102AA",
    "5401AA",
    "5403AA",
    "5910AA",
    "6101AA",
    "6102AA",
    "6401AA",
    "6403AA",
    "6910AA",
]

# Linhas máx. carregadas para a tabela "Ver dados completos" (evita OOM com milhões de linhas).
CUSTO_DASHBOARD_DETAIL_LIMIT = 10_000
