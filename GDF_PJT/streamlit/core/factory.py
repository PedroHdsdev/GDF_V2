"""
Factory para criação de Dashboards.
Para adicionar novo tipo: registre o mapeamento em DASHBOARD_REGISTRY.
"""
from core.auth import AuthResult
from dashboards.vendas import DashboardVendas
from dashboards.compras import DashboardCompras


# Registro de dashboards disponíveis: tipo_relatorio -> classe
DASHBOARD_REGISTRY = {
    "Vendas": DashboardVendas,
    "Compras": DashboardCompras,
}


def create_dashboard(auth: AuthResult):
    """
    Cria e retorna a instância do dashboard apropriado.
    Usa o tipo_relatorio do auth para selecionar a classe.
    """
    tipo = auth.tipo_relatorio or "Vendas"
    cls = DASHBOARD_REGISTRY.get(tipo, DashboardVendas)
    return cls(auth)
