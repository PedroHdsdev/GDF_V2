"""Componentes de filtros reutilizáveis."""
import streamlit as st
from datetime import date, timedelta


# Presets de período para seleção rápida
PERIOD_PRESETS = {
    "Este mês": lambda: (
        date.today().replace(day=1),
        date.today(),
    ),
    "Mês passado": lambda: (
        (date.today().replace(day=1) - timedelta(days=1)).replace(day=1),
        date.today().replace(day=1) - timedelta(days=1),
    ),
    "Últimos 3 meses": lambda: (
        date.today() - timedelta(days=90),
        date.today(),
    ),
    "Últimos 6 meses": lambda: (
        date.today() - timedelta(days=180),
        date.today(),
    ),
    "Este ano": lambda: (
        date.today().replace(month=1, day=1),
        date.today(),
    ),
    "Ano passado": lambda: (
        date.today().replace(year=date.today().year - 1, month=1, day=1),
        date.today().replace(year=date.today().year - 1, month=12, day=31),
    ),
    "Personalizado": None,
}


class SidebarFilters:
    """Gerencia os filtros da sidebar."""

    def __init__(self, empresas_queryset):
        self.empresas_qs = empresas_queryset.order_by('cod_empresa')
        self.empresas_display = ["Todas as empresas"] + [
            f"{emp.cod_empresa} - {emp.razao}" for emp in self.empresas_qs
        ]

    def render(self):
        """Renderiza os filtros na sidebar."""
        st.sidebar.markdown("### 🔍 Filtros")
        st.sidebar.caption("Ajuste os critérios para refinar os dados exibidos.")

        # --- Empresa ---
        st.sidebar.markdown("**🏢 Empresa**")
        empresa_selecionada = st.sidebar.selectbox(
            "Selecione a empresa",
            options=self.empresas_display,
            label_visibility="collapsed",
            key="empresa_filter",
            help="Filtre por empresa específica ou visualize todas.",
        )

        st.sidebar.markdown("**📅 Período**")

        usar_periodo = st.sidebar.checkbox(
            "Filtrar por período",
            value=True,
            key="usar_periodo",
            help="Desative para incluir todos os dados disponíveis.",
        )

        data_inicio = None
        data_fim = None

        if usar_periodo:
            preset = st.sidebar.selectbox(
                "Período rápido",
                options=list(PERIOD_PRESETS.keys()),
                label_visibility="collapsed",
                key="period_preset",
                help="Selecione um período pré-definido ou personalize as datas.",
            )

            if preset == "Personalizado":
                col_dt1, col_dt2 = st.sidebar.columns(2)
                with col_dt1:
                    data_inicio = st.date_input(
                        "De",
                        value=date.today().replace(day=1),
                        format="DD/MM/YYYY",
                        label_visibility="visible",
                        key="data_inicio",
                    )
                with col_dt2:
                    data_fim = st.date_input(
                        "Até",
                        value=date.today(),
                        format="DD/MM/YYYY",
                        label_visibility="visible",
                        key="data_fim",
                    )
                if data_inicio and data_fim and data_inicio > data_fim:
                    data_inicio, data_fim = data_fim, data_inicio
            else:
                data_inicio, data_fim = PERIOD_PRESETS[preset]()

            if data_inicio and data_fim:
                st.sidebar.caption(f"📆 {data_inicio.strftime('%d/%m/%Y')} → {data_fim.strftime('%d/%m/%Y')}")

        st.sidebar.divider()

        return {
            "empresa_selecionada": empresa_selecionada,
            "usar_periodo": usar_periodo,
            "data_inicio": data_inicio,
            "data_fim": data_fim,
        }


def render_compras_extra_filters(data):
    """
    Renderiza filtros extras do dashboard de Compras (fornecedor, produto, NCM, UF, filial).
    Recebe DashboardData já carregado (período + empresa) e retorna dict com listas selecionadas.
    """
    if not getattr(data, "is_compras", False) or data.df_merged.empty:
        return {}

    df_m = data.df_merged
    df_p = data.df_produtos

    st.sidebar.markdown("**🔍 Filtros do relatório**")
    st.sidebar.caption("Refine os gráficos. Vazio = todos.")

    opts_fornecedores = []
    if "cnpj_fornecedor" in df_m.columns and "nome_fornecedor" in df_m.columns:
        u = df_m[["cnpj_fornecedor", "nome_fornecedor"]].drop_duplicates()
        u = u[u["cnpj_fornecedor"].notna() & (u["cnpj_fornecedor"].astype(str).str.strip() != "")]
        opts_fornecedores = u["cnpj_fornecedor"].astype(str).str.strip().unique().tolist()

    opts_produtos = []
    if not df_p.empty and "descricao" in df_p.columns:
        opts_produtos = df_p["descricao"].dropna().astype(str).str.strip().unique().tolist()
        opts_produtos = sorted([p for p in opts_produtos if p])[:500]

    opts_ncms = []
    if not df_p.empty and "ncm" in df_p.columns:
        opts_ncms = df_p["ncm"].fillna("").astype(str).str.strip().unique().tolist()
        opts_ncms = sorted([n for n in opts_ncms if n])[:300]

    opts_ufs = []
    if "uf_fornecedor" in df_m.columns:
        u = df_m["uf_fornecedor"].fillna("").astype(str).str.upper()
        opts_ufs = sorted(u[u != ""].unique().tolist())

    opts_filiais = []
    if "cod_filial" in df_m.columns:
        u = df_m[["cod_filial", "nome_filial"]].drop_duplicates()
        u = u[u["cod_filial"].notna() & (u["cod_filial"].astype(str).str.strip() != "")]
        opts_filiais = u["cod_filial"].astype(str).str.strip().unique().tolist()

    fornecedores = st.sidebar.multiselect(
        "Fornecedor",
        options=opts_fornecedores,
        default=[],
        key="compras_filtro_fornecedor",
        help="Deixe vazio para todos.",
    )
    produtos = st.sidebar.multiselect(
        "Produto",
        options=opts_produtos,
        default=[],
        key="compras_filtro_produto",
        help="Deixe vazio para todos.",
    )
    ncms = st.sidebar.multiselect(
        "Categoria / NCM",
        options=opts_ncms,
        default=[],
        key="compras_filtro_ncm",
        help="Deixe vazio para todos.",
    )
    ufs = st.sidebar.multiselect(
        "UF (fornecedor)",
        options=opts_ufs,
        default=[],
        key="compras_filtro_uf",
        help="Deixe vazio para todos.",
    )
    filiais = st.sidebar.multiselect(
        "Filial",
        options=opts_filiais,
        default=[],
        key="compras_filtro_filial",
        help="Deixe vazio para todas.",
    )

    st.sidebar.divider()

    return {
        "fornecedores": fornecedores,
        "produtos": produtos,
        "ncms": ncms,
        "ufs": ufs,
        "filiais": filiais,
    }
