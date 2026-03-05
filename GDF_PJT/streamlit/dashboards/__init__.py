"""
Dashboards do GDF.

Para adicionar novo tipo de dashboard:
1. Crie um arquivo em dashboards/ (ex: novo_tipo.py)
2. Estenda BaseDashboard e defina TIPO_RELATORIO
3. Implemente render_content() com os gráficos e seções
4. Registre em factory.DASHBOARD_REGISTRY
"""
from .base import BaseDashboard
from .vendas import DashboardVendas
from .compras import DashboardCompras

__all__ = ["BaseDashboard", "DashboardVendas", "DashboardCompras"]
