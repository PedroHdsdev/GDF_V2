"""Dashboard de Vendas."""
import streamlit as st

from .base import BaseDashboard
from .widgets.charts import (
    render_evolucao_temporal,
    render_comparativo,
    render_ranking,
    render_grupo_mercadorias,
    render_por_tipo_pagamento,
    render_condicoes_pagamento,
)

from charts import graficos_vendas as tv


class DashboardVendas(BaseDashboard):
    """Dashboard específico para relatório de Vendas."""

    TIPO_RELATORIO = "Vendas"

    def render_content(self):
        """Renderiza gráficos e seções de Vendas."""
        # Análise de Dados
        st.subheader("📈 Análise de Dados")
        tab_evolucao, tab_comparacao = st.tabs(["📈 Evolução Temporal", "⚖️ Comparar Períodos"])
        with tab_evolucao:
            render_evolucao_temporal(self.data.df_merged, tv, self.TIPO_RELATORIO)
        with tab_comparacao:
            render_comparativo(self.data.df_merged, tv, self.TIPO_RELATORIO)

        # Ranking
        st.subheader("📊 Ranking")
        with st.tabs(["📊 Ranking"])[0]:
            render_ranking(self.data.df_merged, self.TIPO_RELATORIO)

        # Grupo de Mercadorias
        st.subheader("📦 Grupo de Mercadorias")
        with st.tabs(["📦 Grupo de Mercadorias"])[0]:
            render_grupo_mercadorias(self.data.df_produtos)

        # Pagamentos
        st.subheader("💰 Pagamentos")
        tab_cond_pag, tab_tipo_pag = st.tabs([
            "📋 Condições de pagamento mais usadas",
            "💳 Por tipo de pagamento",
        ])
        with tab_cond_pag:
            render_condicoes_pagamento(self.data.df_parcelas, self.data.df_merged)
        with tab_tipo_pag:
            render_por_tipo_pagamento(self.data.df_pagamento)
