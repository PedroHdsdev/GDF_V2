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
