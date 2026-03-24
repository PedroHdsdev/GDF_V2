"""Gráficos do dashboard de Custo — usam lists_custo (métricas SAP / relatório de custo)."""
from .base import GraficoBase
from . import lists_custo as tl_c
from .graficos_vendas import Grafico_linha as _GraficoLinhaVendas
from .graficos_vendas import Grafico_comparacao as _GraficoComparacaoVendas


class Grafico_linha(_GraficoLinhaVendas):
    def __init__(self, df):
        GraficoBase.__init__(self, df, tl_c)


class Grafico_comparacao(_GraficoComparacaoVendas):
    def __init__(self, df):
        GraficoBase.__init__(self, df, tl_c)
