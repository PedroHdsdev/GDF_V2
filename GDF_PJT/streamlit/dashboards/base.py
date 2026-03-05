"""
Classe base abstrata para todos os Dashboards.
Define o fluxo comum: auth, filtros, dados, render.
"""
from abc import ABC, abstractmethod
import streamlit as st

from core.auth import AuthResult, authenticate
from core.filters import SidebarFilters
from core.data_processor import DataProcessor, DashboardData


class BaseDashboard(ABC):
    """Classe base para dashboards do GDF."""

    TIPO_RELATORIO: str = ""  # Subclasses devem definir: "Vendas" ou "Compras"

    def __init__(self, auth: AuthResult):
        self.auth = auth
        self.empresas_qs = None
        self.filters = None
        self.data: DashboardData | None = None

    def run(self) -> bool:
        """
        Executa o fluxo completo do dashboard.
        Retorna True se renderizou com sucesso, False se deve parar (erro/sem dados).
        """
        if not self._load_empresas():
            return False

        self._render_header()
        filter_values = self._render_filters()
        self.data = self._load_data(filter_values)

        if self.data is None:
            st.warning("⚠️ Nenhum dado encontrado para os filtros selecionados")
            return False

        if self.data.df_merged.empty:
            st.warning("⚠️ Nenhum dado disponível para gráficos")
            return False

        self.render_content()
        self._render_data_table()
        self._render_footer()
        return True

    def _load_empresas(self) -> bool:
        """Carrega empresas do usuário. Retorna False se sem acesso."""
        from django.contrib.auth.models import User
        from app.db_GDF.Public.models import Empresas

        try:
            user = User.objects.get(username=self.auth.username)
            if self.auth.acesso_total and self.auth.cod_cliente:
                self.empresas_qs = Empresas.objects.filter(
                    cliente__cod_cliente=self.auth.cod_cliente
                ).distinct()
            else:
                self.empresas_qs = Empresas.objects.filter(
                    userempresas__user=user
                ).distinct()
                if self.auth.cod_cliente:
                    self.empresas_qs = self.empresas_qs.filter(
                        cliente__cod_cliente=self.auth.cod_cliente
                    )

            if not self.empresas_qs.exists():
                st.error("❌ Usuário sem empresa vinculada")
                return False
            return True
        except User.DoesNotExist:
            st.error("❌ Usuário inválido")
            return False

    def _render_header(self):
        """Renderiza título e informações do usuário (layout alinhado ao Django)."""
        # Hero/card principal (estilo Django home-welcome)
        with st.container():
            col_title, col_meta = st.columns([2, 1])
            with col_title:
                st.markdown(f"## 📊 Dashboard de {self.TIPO_RELATORIO}")
            with col_meta:
                st.caption(f"Relatório: **{self.auth.tipo_relatorio}**")

        # Sidebar: info do usuário (estilo Django sidebar)
        st.sidebar.markdown("### 👤 Sessão")
        st.sidebar.markdown(f"**{self.auth.username}**")
        if self.auth.cod_cliente:
            st.sidebar.markdown(f"**{self.auth.cod_cliente}**")
        st.sidebar.divider()

    def _render_filters(self) -> dict:
        """Renderiza filtros e retorna valores selecionados."""
        self.filters = SidebarFilters(self.empresas_qs)
        return self.filters.render()

    def _load_data(self, filter_values: dict) -> DashboardData | None:
        """Carrega e processa os dados conforme filtros."""
        processor = DataProcessor(self.TIPO_RELATORIO)
        return processor.process(
            empresas_queryset=self.empresas_qs,
            empresa_selecionada=filter_values["empresa_selecionada"],
            usar_periodo=filter_values["usar_periodo"],
            data_inicio=filter_values["data_inicio"],
            data_fim=filter_values["data_fim"],
        )

    @abstractmethod
    def render_content(self):
        """Renderiza o conteúdo específico do dashboard (gráficos, tabs, etc)."""
        pass

    def _render_data_table(self):
        """Renderiza tabela de dados completos."""
        st.markdown("---")
        with st.expander("📋 Ver dados completos"):
            cols = ['numero', 'serie', 'emissao', 'Faturamento', 'Total Impostos', 'Valor Líquido', 'Quantidade Total']
            available = [c for c in cols if c in self.data.df_merged.columns]
            st.dataframe(
                self.data.df_merged[available],
                use_container_width=True,
                height=400
            )

    def _render_footer(self):
        """Renderiza rodapé."""
        import pandas as pd
        st.caption(f"Dashboard GDF | Atualizado em {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}")
