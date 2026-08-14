"""Dashboard de Custo (Relatório de Custo SAP)."""
import streamlit as st

from .base import BaseDashboard
from .widgets.charts import (
    render_evolucao_temporal,
    render_comparativo,
    render_ranking,
    render_grupo_mercadorias,
)

from charts import graficos_custo as tv
from charts.lists_custo import NOME_METRICA_MARGEM

class DashboardCusto(BaseDashboard):
    """Dashboard de Custo: dados de sap.relatorio_custo com evolução temporal."""

    TIPO_RELATORIO = "Custo"

    def render_content(self):
        """Renderiza gráfico de evolução temporal e comparativo (como no relatório de vendas)."""
        st.subheader("📈 Análise de Dados")
        tab_evolucao, tab_comparacao = st.tabs([
            "📈 Evolução Temporal",
            "⚖️ Comparar Períodos",
        ])
        with tab_evolucao:
            render_evolucao_temporal(self.data.df_merged, tv, self.TIPO_RELATORIO)
        with tab_comparacao:
            # Comparativo usa dados agregados por ano/mês (sem breakdown por empresa)
            df_comp = self.data.df_merged
            if "empresa" in df_comp.columns:
                metricas_agg = [c for c in [
                    "Faturamento", "Total Impostos", "Valor Líquido",
                    NOME_METRICA_MARGEM, "CMV Gerencial", "Quantidade Total",
                ] if c in df_comp.columns]
                df_comp = df_comp.groupby(["ano", "mes", "mes_nome"], as_index=False).agg(
                    {c: "sum" for c in metricas_agg}
                )
            render_comparativo(df_comp, tv, self.TIPO_RELATORIO)

        st.subheader("📊 Ranking")
        render_ranking(
            self.data.df_merged,
            self.TIPO_RELATORIO,
            df_custo_rank_cliente=self.data.df_custo_rank_cliente,
            df_custo_rank_cidade=self.data.df_custo_rank_cidade,
        )

        st.subheader("📦 Grupo de Mercadorias")
        render_grupo_mercadorias(self.data.df_produtos, self.TIPO_RELATORIO)

    def _render_data_table(self):
        """Tabela linha a linha do relatório de custo (já filtrada pelos CFOPs permitidos)."""
        st.markdown("---")
        with st.expander("📋 Ver dados completos"):
            df = self.data.df_custo_linhas
            if df.empty:
                st.caption("Nenhuma linha para exibir.")
                return
            if getattr(self.data, "custo_detail_truncated", False):
                st.caption(
                    f"Amostra das **{self.data.custo_detail_limit:,}** linhas mais recentes do filtro "
                    "(volume total não é carregado no dashboard por desempenho). "
                    "Use exportação/consulta direta no banco para o conjunto completo."
                )
            exibir = df[[
                c for c in [
                    "empresa", "pstdat", "docnum", "matnr", "maktx", "matkl", "wgbez", "cfop",
                    "nome_cliente", "cidade",
                    "Faturamento", "Total Impostos", "Valor Líquido",
                    "Quantidade Total", NOME_METRICA_MARGEM, "CMV Gerencial",
                ]
                if c in df.columns
            ]].copy()
            exibir = exibir.rename(columns={
                "empresa": "Empresa",
                "pstdat": "Data postagem",
                "docnum": "Documento",
                "matnr": "Material",
                "maktx": "Texto breve material",
                "matkl": "Grupo mercadorias",
                "wgbez": "Denom. grupo mercadorias",
                "cfop": "CFOP",
                "nome_cliente": "Cliente",
                "cidade": "Cidade",
                "Faturamento": "Faturamento (vlr_tot_doc)",
                "Total Impostos": "Total impostos",
                "Valor Líquido": "Valor líquido",
                "Quantidade Total": "Quantidade",
                NOME_METRICA_MARGEM: "Margem contr. gerencial",
                "CMV Gerencial": "CMV gerencial",
            })
            st.dataframe(exibir, use_container_width=True, height=400)
