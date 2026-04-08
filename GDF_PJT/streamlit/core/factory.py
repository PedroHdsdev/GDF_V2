"""
Factory para criação de Dashboards Streamlit.
Cada solução pode ter um ou mais dashboards de análise; todos são registrados aqui.
Para adicionar um novo dashboard (de qualquer solução):
  1. Crie uma classe herdando de BaseDashboard em dashboards/
  2. Registre em DASHBOARD_REGISTRY com uma chave (ex.: "Vendas", "Compras", "Reprocessamento")
  3. No Django: view que gera token com tipo_relatorio=chave; o iframe usa só ?token=... (o dashboard vem do token).
"""
from core.auth import AuthResult
from dashboards.vendas import DashboardVendas
from dashboards.compras import DashboardCompras
from dashboards.custo import DashboardCusto
from dashboards.balanco_financeiro import DashboardBalancoFin


# Registro de dashboards: chave -> classe (solução Dashboard hoje; outras soluções podem registrar no futuro)
DASHBOARD_REGISTRY = {
    "Vendas": DashboardVendas,
    "Compras": DashboardCompras,
    "Custo": DashboardCusto,
    "BalancoFin": DashboardBalancoFin,
}


def create_dashboard(auth: AuthResult, dashboard_key: str | None = None):
    """
    Cria e retorna a instância do dashboard apropriado.
    dashboard_key: chave no DASHBOARD_REGISTRY (ex.: "Vendas", "Compras"). Se None, usa auth.tipo_relatorio.
    """
    key = (dashboard_key or auth.tipo_relatorio or "Vendas").strip()
    cls = DASHBOARD_REGISTRY.get(key, DashboardVendas)
    return cls(auth)
