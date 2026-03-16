"""Dashboard de Compras – analítico com filtros globais."""
import streamlit as st
import pandas as pd
import altair as alt

from .base import BaseDashboard
from .widgets.charts import render_por_tipo_pagamento, render_condicoes_pagamento
from core.filters import SidebarFilters, render_compras_extra_filters
from core.data_processor import DataProcessor, apply_compras_filters

try:
    from config.constants import CHART_PALETTE, CHART_COLORS
except ImportError:
    CHART_PALETTE = ["#0ea5e9", "#f97316", "#8b5cf6", "#ec4899", "#14b8a6"]
    CHART_COLORS = {"primary": "#0ea5e9", "secondary": "#f97316"}

_MESES_PT = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']


class DashboardCompras(BaseDashboard):
    """Dashboard analítico de Compras com filtros globais."""

    TIPO_RELATORIO = "Compras"

    def run(self) -> bool:
        """Fluxo: empresas → header → filtros básicos → carrega dados → filtros extras → aplica filtros → conteúdo."""
        if not self._load_empresas():
            return False

        self._render_header()

        self.filters = SidebarFilters(self.empresas_qs)
        filter_basic = self.filters.render()

        full_data = self._load_data(filter_basic)
        if full_data is None:
            st.warning("⚠️ Nenhum dado encontrado para os filtros selecionados")
            return False
        if full_data.df_merged.empty:
            st.warning("⚠️ Nenhum dado disponível para o período e empresa")
            return False

        filter_extra = render_compras_extra_filters(full_data)
        self.data = apply_compras_filters(full_data, filter_extra)

        if self.data.df_merged.empty:
            st.warning("⚠️ Nenhum dado após aplicar os filtros (fornecedor/produto/NCM/UF/filial)")
            return False

        self.render_content()
        self._render_data_table()
        self._render_footer()
        return True

    def render_content(self):
        """Renderiza as 9 seções do dashboard analítico de compras."""
        df = self.data.df_merged
        df_p = self.data.df_produtos

        # 1. Visão geral de compras
        st.subheader("📊 1. Visão geral de compras")
        self._render_kpis(df)
        self._render_evolucao_compras(df)

        # 2. Top fornecedores
        st.subheader("🏆 2. Top fornecedores")
        self._render_top_fornecedores(df)

        # 3. Compras por categoria/NCM
        st.subheader("📦 3. Compras por categoria de produto (NCM)")
        self._render_compras_por_ncm(df_p)

        # 4. Análise de preço médio
        st.subheader("💰 4. Análise de preço médio")
        self._render_preco_medio(df_p, df)

        # 5. Impostos pagos
        st.subheader("📋 5. Impostos pagos")
        self._render_impostos(df)

        # 6. Análise por UF
        st.subheader("🗺️ 6. Análise por UF (fornecedor)")
        self._render_por_uf(df)

        # 7. Frequência de compras
        st.subheader("📅 7. Frequência de compras")
        self._render_frequencia_compras(df)

        # 8. Itens mais comprados
        st.subheader("📌 8. Itens mais comprados")
        self._render_itens_mais_comprados(df_p)

        # 9. Comparação entre filiais
        st.subheader("🏢 9. Comparação entre filiais")
        self._render_comparacao_filiais(df)

        # 10. Pagamentos
        st.subheader("💰 10. Pagamentos")
        tab_cond_pag, tab_tipo_pag = st.tabs([
            "📋 Condições de pagamento mais usadas",
            "💳 Por tipo de pagamento",
        ])
        with tab_cond_pag:
            render_condicoes_pagamento(self.data.df_parcelas, self.data.df_merged)
        with tab_tipo_pag:
            render_por_tipo_pagamento(self.data.df_pagamento)

    def _render_kpis(self, df: pd.DataFrame):
        total = df["Faturamento"].fillna(0).sum()
        n_nf = df["id_identificacao"].nunique()
        n_forn = df["cnpj_fornecedor"].dropna().nunique() if "cnpj_fornecedor" in df.columns else 0
        n_itens = df["Quantidade Total"].fillna(0).sum()
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total comprado (período)", f"R$ {total:,.2f}")
        col2.metric("Quantidade de notas fiscais", f"{int(n_nf):,}")
        col3.metric("Quantidade de fornecedores", f"{int(n_forn):,}")
        col4.metric("Quantidade total de itens", f"{int(n_itens):,}")

    def _render_evolucao_compras(self, df: pd.DataFrame):
        if df.empty or "emissao" not in df.columns:
            return
        df = df.copy()
        df["emissao"] = pd.to_datetime(df["emissao"])
        df["ano_mes"] = df["emissao"].dt.to_period("M").astype(str)
        ev = df.groupby("ano_mes", as_index=False).agg(
            valor_total=("Faturamento", "sum")
        ).sort_values("ano_mes")
        ev["valor_total"] = pd.to_numeric(ev["valor_total"], errors="coerce").fillna(0)
        if ev.empty:
            st.caption("Sem dados para evolução.")
            return
        chart = (
            alt.Chart(ev)
            .mark_line(point=True, strokeWidth=2)
            .encode(
                x=alt.X("ano_mes:N", title="Mês"),
                y=alt.Y("valor_total:Q", title="Valor total (R$)"),
                tooltip=[
                    alt.Tooltip("ano_mes:N", title="Mês"),
                    alt.Tooltip("valor_total:Q", title="Valor (R$)", format=",.2f"),
                ],
            )
            .properties(height=320, title="Evolução das compras ao longo do tempo (valor total por mês)")
        )
        st.altair_chart(chart, use_container_width=True)

    def _render_top_fornecedores(self, df: pd.DataFrame):
        if "cnpj_fornecedor" not in df.columns or "nome_fornecedor" not in df.columns:
            st.caption("Dados de fornecedor não disponíveis.")
            return
        agg = (
            df.groupby(["cnpj_fornecedor", "nome_fornecedor"], as_index=False)["Faturamento"]
            .sum()
        )
        agg["Faturamento"] = pd.to_numeric(agg["Faturamento"], errors="coerce").fillna(0)
        agg = agg.nlargest(15, "Faturamento")
        agg["label"] = agg["nome_fornecedor"].fillna("S/N").str[:45] + " (" + agg["cnpj_fornecedor"].astype(str).str[-6:] + ")"
        if agg.empty:
            st.caption("Sem dados.")
            return
        chart = (
            alt.Chart(agg)
            .mark_bar(cornerRadius=6)
            .encode(
                y=alt.Y("label:N", sort=alt.EncodingSortField("Faturamento", order="descending"), title="Fornecedor"),
                x=alt.X("Faturamento:Q", title="Valor total (R$)"),
                color=alt.value(CHART_COLORS.get("primary", "#0ea5e9")),
                tooltip=[
                    alt.Tooltip("label:N", title="Fornecedor"),
                    alt.Tooltip("Faturamento:Q", title="Valor (R$)", format=",.2f"),
                ],
            )
            .properties(height=max(300, len(agg) * 32), title="Fornecedores com maior valor total de compras")
        )
        st.altair_chart(chart, use_container_width=True)

    def _render_compras_por_ncm(self, df_p: pd.DataFrame):
        if df_p.empty or "ncm" not in df_p.columns:
            st.caption("Dados de NCM não disponíveis.")
            return
        df_p = df_p.copy()
        df_p["valor_total"] = pd.to_numeric(df_p["valor_total"], errors="coerce").fillna(0)
        df_p["ncm"] = df_p["ncm"].fillna("Sem NCM").astype(str)
        agg = df_p.groupby("ncm", as_index=False)["valor_total"].sum().sort_values("valor_total", ascending=False).head(20)
        if agg.empty:
            st.caption("Sem dados.")
            return
        chart = (
            alt.Chart(agg)
            .mark_bar(cornerRadius=6)
            .encode(
                y=alt.Y("ncm:N", sort=alt.EncodingSortField("valor_total", order="descending"), title="NCM"),
                x=alt.X("valor_total:Q", title="Total comprado (R$)"),
                color=alt.value(CHART_COLORS.get("secondary", "#f97316")),
                tooltip=[
                    alt.Tooltip("ncm:N", title="NCM"),
                    alt.Tooltip("valor_total:Q", title="Valor (R$)", format=",.2f"),
                ],
            )
            .properties(height=max(300, len(agg) * 28), title="Total comprado por NCM")
        )
        st.altair_chart(chart, use_container_width=True)

    def _render_preco_medio(self, df_p: pd.DataFrame, df: pd.DataFrame):
        if df_p.empty or "valor_unitario" not in df_p.columns:
            st.caption("Dados de valor unitário não disponíveis.")
            return
        df_p = df_p.copy()
        df_p["valor_unitario"] = pd.to_numeric(df_p["valor_unitario"], errors="coerce").fillna(0)
        if "id_identificacao" in df_p.columns and "cnpj_fornecedor" in df.columns:
            merge = df[["id_identificacao", "cnpj_fornecedor", "nome_fornecedor"]].drop_duplicates()
            df_p = df_p.merge(merge, on="id_identificacao", how="left")
        media_produto = df_p.groupby("descricao", as_index=False).agg(
            media=("valor_unitario", "mean"),
            qtd=("valor_unitario", "count"),
        )
        media_produto = media_produto[media_produto["qtd"] >= 1].nlargest(20, "qtd")
        if media_produto.empty:
            st.caption("Sem dados.")
            return
        chart = (
            alt.Chart(media_produto)
            .mark_bar(cornerRadius=6)
            .encode(
                y=alt.Y("descricao:N", sort=alt.EncodingSortField("media", order="descending"), title="Produto"),
                x=alt.X("media:Q", title="Preço médio unitário (R$)"),
                tooltip=[
                    alt.Tooltip("descricao:N", title="Produto"),
                    alt.Tooltip("media:Q", title="Preço médio (R$)", format=",.2f"),
                    alt.Tooltip("qtd:Q", title="Ocorrências"),
                ],
            )
            .properties(height=max(300, len(media_produto) * 26), title="Preço médio por produto (valor unitário)")
        )
        st.altair_chart(chart, use_container_width=True)

    def _render_impostos(self, df: pd.DataFrame):
        def _sum(col):
            if col not in df.columns:
                return 0.0
            return pd.to_numeric(df[col], errors="coerce").fillna(0).sum()
        icms = _sum("valor_icms")
        ipi = _sum("valor_ipi")
        pis = _sum("valor_pis")
        cofins = _sum("valor_cofins")
        imp = pd.DataFrame({
            "Imposto": ["ICMS", "IPI", "PIS", "COFINS"],
            "Valor": [icms, ipi, pis, cofins],
        })
        imp["Valor"] = pd.to_numeric(imp["Valor"], errors="coerce").fillna(0)
        imp = imp[imp["Valor"] > 0]
        if imp.empty:
            st.caption("Nenhum imposto registrado no período.")
            return
        chart = (
            alt.Chart(imp)
            .mark_bar(cornerRadius=6)
            .encode(
                x=alt.X("Imposto:N", title="Imposto"),
                y=alt.Y("Valor:Q", title="Valor (R$)"),
                color=alt.Color("Imposto:N", scale=alt.Scale(range=CHART_PALETTE[:4]), legend=None),
                tooltip=[
                    alt.Tooltip("Imposto:N"),
                    alt.Tooltip("Valor:Q", format=",.2f"),
                ],
            )
            .properties(height=300, title="Total de impostos pagos nas compras")
        )
        st.altair_chart(chart, use_container_width=True)

    def _render_por_uf(self, df: pd.DataFrame):
        if "uf_fornecedor" not in df.columns:
            st.caption("UF do fornecedor não disponível.")
            return
        uf = df.copy()
        uf["uf_fornecedor"] = uf["uf_fornecedor"].fillna("").astype(str).str.upper()
        uf = uf[uf["uf_fornecedor"] != ""]
        if uf.empty:
            st.caption("Sem dados de UF.")
            return
        agg = uf.groupby("uf_fornecedor", as_index=False)["Faturamento"].sum()
        agg["Faturamento"] = pd.to_numeric(agg["Faturamento"], errors="coerce").fillna(0)
        agg = agg.sort_values("Faturamento", ascending=False)
        chart = (
            alt.Chart(agg)
            .mark_bar(cornerRadius=6)
            .encode(
                x=alt.X("uf_fornecedor:N", title="UF"),
                y=alt.Y("Faturamento:Q", title="Valor total (R$)"),
                color=alt.value(CHART_COLORS.get("primary", "#0ea5e9")),
                tooltip=[
                    alt.Tooltip("uf_fornecedor:N", title="UF"),
                    alt.Tooltip("Faturamento:Q", title="Valor (R$)", format=",.2f"),
                ],
            )
            .properties(height=320, title="Valor total de compras por estado do fornecedor")
        )
        st.altair_chart(chart, use_container_width=True)

    def _render_frequencia_compras(self, df: pd.DataFrame):
        if df.empty or "cnpj_fornecedor" not in df.columns or "nome_fornecedor" not in df.columns:
            st.caption("Dados insuficientes.")
            return
        df = df.copy()
        df["emissao"] = pd.to_datetime(df["emissao"])
        df["ano_mes"] = df["emissao"].dt.to_period("M").astype(str)
        freq = (
            df.groupby(["cnpj_fornecedor", "nome_fornecedor", "ano_mes"], as_index=False)["id_identificacao"]
            .nunique()
            .rename(columns={"id_identificacao": "qtd_notas"})
        )
        freq["label"] = freq["nome_fornecedor"].fillna("S/N").str[:35]
        agg_forn = df.groupby("cnpj_fornecedor", as_index=False).agg(
            Faturamento=("Faturamento", "sum")
        )
        agg_forn["Faturamento"] = pd.to_numeric(agg_forn["Faturamento"], errors="coerce").fillna(0)
        top_forn = agg_forn.sort_values("Faturamento", ascending=False).head(10)["cnpj_fornecedor"].tolist()
        freq = freq[freq["cnpj_fornecedor"].isin(top_forn)]
        if freq.empty:
            st.caption("Sem dados para frequência.")
            return
        chart = (
            alt.Chart(freq)
            .mark_line(point=True)
            .encode(
                x=alt.X("ano_mes:N", title="Mês"),
                y=alt.Y("qtd_notas:Q", title="Quantidade de notas"),
                color=alt.Color("label:N", legend=alt.Legend(title="Fornecedor")),
                tooltip=[
                    alt.Tooltip("ano_mes:N", title="Mês"),
                    alt.Tooltip("label:N", title="Fornecedor"),
                    alt.Tooltip("qtd_notas:Q", title="Qtd. notas"),
                ],
            )
            .properties(height=350, title="Quantidade de notas por fornecedor ao longo do tempo (Top 10 por valor)")
        )
        st.altair_chart(chart, use_container_width=True)

    def _render_itens_mais_comprados(self, df_p: pd.DataFrame):
        if df_p.empty:
            st.caption("Sem dados de itens.")
            return
        df_p = df_p.copy()
        df_p["quantidade"] = pd.to_numeric(df_p["quantidade"], errors="coerce").fillna(0)
        df_p["valor_total"] = pd.to_numeric(df_p["valor_total"], errors="coerce").fillna(0)
        by_qtd = df_p.groupby("descricao", as_index=False).agg(
            quantidade=("quantidade", "sum"),
            valor_total=("valor_total", "sum"),
        ).nlargest(15, "quantidade")
        by_qtd["descricao"] = by_qtd["descricao"].str[:50]
        if by_qtd.empty:
            st.caption("Sem dados.")
            return
        chart = (
            alt.Chart(by_qtd)
            .mark_bar(cornerRadius=6)
            .encode(
                y=alt.Y("descricao:N", sort=alt.EncodingSortField("quantidade", order="descending"), title="Produto"),
                x=alt.X("quantidade:Q", title="Quantidade comprada"),
                color=alt.value(CHART_COLORS.get("secondary", "#f97316")),
                tooltip=[
                    alt.Tooltip("descricao:N", title="Produto"),
                    alt.Tooltip("quantidade:Q", title="Quantidade"),
                    alt.Tooltip("valor_total:Q", title="Valor total (R$)", format=",.2f"),
                ],
            )
            .properties(height=max(300, len(by_qtd) * 28), title="Produtos com maior quantidade comprada")
        )
        st.altair_chart(chart, use_container_width=True)

    def _render_comparacao_filiais(self, df: pd.DataFrame):
        if "cod_filial" not in df.columns:
            st.caption("Dados de filial não disponíveis.")
            return
        fil = df.copy()
        fil["cod_filial"] = fil["cod_filial"].fillna("Sem filial").astype(str)
        agg = fil.groupby("cod_filial", as_index=False)["Faturamento"].sum()
        agg["Faturamento"] = pd.to_numeric(agg["Faturamento"], errors="coerce").fillna(0)
        agg = agg.sort_values("Faturamento", ascending=False)
        if agg.empty:
            st.caption("Sem dados de filial.")
            return
        chart = (
            alt.Chart(agg)
            .mark_bar(cornerRadius=6)
            .encode(
                x=alt.X("cod_filial:N", title="Filial"),
                y=alt.Y("Faturamento:Q", title="Valor total (R$)"),
                color=alt.Color("cod_filial:N", scale=alt.Scale(range=CHART_PALETTE), legend=None),
                tooltip=[
                    alt.Tooltip("cod_filial:N", title="Filial"),
                    alt.Tooltip("Faturamento:Q", title="Valor (R$)", format=",.2f"),
                ],
            )
            .properties(height=320, title="Valor total de compras por filial")
        )
        st.altair_chart(chart, use_container_width=True)

    def _render_data_table(self):
        """Tabela de dados completos (notas)."""
        st.markdown("---")
        with st.expander("📋 Ver dados completos"):
            cols = [
                "numero", "serie", "emissao", "Faturamento", "Total Impostos", "Valor Líquido",
                "Quantidade Total", "nome_fornecedor", "uf_fornecedor", "cod_filial",
            ]
            available = [c for c in cols if c in self.data.df_merged.columns]
            st.dataframe(
                self.data.df_merged[available],
                use_container_width=True,
                height=400,
            )
