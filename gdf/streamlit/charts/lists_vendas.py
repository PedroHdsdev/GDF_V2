"""Listas e constantes para gráficos de Vendas."""

# Nome canônico da margem de contribuição (mesma métrica em todo o projeto)
NOME_METRICA_MARGEM = "Margem Contrib. Gerencial"

# Métricas que usam escala em milhares (k) no format_valor
Metrica_valores_k = [
    "Faturamento",
    "V.CMV",
    "Valor Líquido",
    "Total de Impostos",
    "Total Impostos",
    "Quantidade Total",
    "CMV Gerencial",
]

# Métricas em percentual (após conversão margem/faturamento*100 em G_multiplas_metricas)
Metrica_valores_p = [
    NOME_METRICA_MARGEM,
]

METRICAS_MARGEM_PCT = (NOME_METRICA_MARGEM,)
