"""Listas e métricas para o dashboard de Custo (Relatório SAP).

Margem de contribuição: um único nome de coluna no DataFrame — ver data_processor._process_custo.
"""

# Mesmo conceito que em vendas/compras; nome canônico no projeto.
NOME_METRICA_MARGEM = "Margem Contrib. Gerencial"

# Métricas com escala em milhares (k) no format_valor
Metrica_valores_k = [
    "Faturamento",
    "Valor Líquido",
    "Total Impostos",
    "Quantidade Total",
    "CMV Gerencial",
]

# Percentual após conversão margem/faturamento×100 em G_multiplas_metricas
Metrica_valores_p = [
    NOME_METRICA_MARGEM,
]

METRICAS_MARGEM_PCT = (NOME_METRICA_MARGEM,)
