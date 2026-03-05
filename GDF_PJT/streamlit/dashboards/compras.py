"""Dashboard de Compras."""
import streamlit as st

from .base import BaseDashboard
from .widgets.charts import (
    render_evolucao_temporal,
    render_comparativo,
    render_ranking,
    render_grupo_mercadorias,
    render_por_tipo_pagamento,
    render_compras_analise,
)

from charts import graficos_compras as tc


class DashboardCompras(BaseDashboard):
    """Dashboard específico para relatório de Compras."""

    TIPO_RELATORIO = "Compras"

    def render_content(self):
        """Renderiza gráficos e seções de Compras."""
        st.subheader("📈 Análise de Dados")

        tab_evolucao, tab_comparacao = st.tabs(["📈 Evolução Temporal", "⚖️ Comparar Períodos"])

        with tab_evolucao:
            render_evolucao_temporal(
                self.data.df_merged,
                tc,
                self.TIPO_RELATORIO
            )

        with tab_comparacao:
            render_comparativo(self.data.df_merged, tc, self.TIPO_RELATORIO)

        # Ranking de fornecedores
        with st.tabs(["📊 Ranking de Fornecedores"])[0]:
            st.markdown("### 🏆 Ranking por valor (dependência de fornecedores / clientes)")
            render_ranking(self.data.df_merged, self.TIPO_RELATORIO)

        # Grupo de mercadorias
        with st.tabs(["📦 Grupo de Mercadorias"])[0]:
            st.markdown("### 📦 Análise por Grupo de Mercadorias")
            render_grupo_mercadorias(self.data.df_produtos)

        # Por tipo de pagamento (standalone)
        st.markdown("---")
        st.subheader("💳 Por tipo de pagamento")
        render_por_tipo_pagamento(self.data.df_pagamento)

        # Análise de NF-e de entrada
        st.markdown("---")
        st.subheader("📊 Análise de NF-e de Entrada (Compras)")
        render_compras_analise(self.data.df_merged, self.data.df_produtos)
