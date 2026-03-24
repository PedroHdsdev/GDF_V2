"""Constantes e configurações do Dashboard."""
import json
import os

# Paleta e tema dos gráficos (alinhado ao GDF: sky #0ea5e9, sun #f97316)
CHART_COLORS = {
    "primary": "#0ea5e9",      # sky - principal
    "secondary": "#f97316",   # sun - destaque
    "success": "#10b981",      # verde
    "warning": "#eab308",      # amarelo
    "neutral": "#64748b",      # slate
}
CHART_PALETTE = [
    CHART_COLORS["primary"],
    CHART_COLORS["secondary"],
    "#8b5cf6",
    "#ec4899",
    "#14b8a6",
    CHART_COLORS["warning"],
    CHART_COLORS["success"],
    "#6366f1",
    "#f43f5e",
]
CHART_PALETTE_GRADIENT = ["#0ea5e9", "#38bdf8", "#7dd3fc", "#bae6fd"]

try:
    from app.db_GDF.Sap.custo_constants import (
        CUSTO_DASHBOARD_DETAIL_LIMIT,
        RELATORIO_CUSTO_CFOP_LIST,
    )
except ImportError:
    CUSTO_DASHBOARD_DETAIL_LIMIT = 10_000
    RELATORIO_CUSTO_CFOP_LIST = [
        "1201AA",
        "1202AA",
        "1410AA",
        "1411AA",
        "2202AA",
        "2410AA",
        "2411AA",
        "5101AA",
        "5102AA",
        "5401AA",
        "5403AA",
        "5910AA",
        "6101AA",
        "6102AA",
        "6401AA",
        "6403AA",
        "6910AA",
    ]


def _load_tipo_pagamento():
    """Carrega dicionário de tipos de pagamento do JSON."""
    # config/constants.py -> sobe para GDF_PJT (pasta que contém json)
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    json_dir = os.path.join(base_dir, "json")
    path = os.path.join(json_dir, "Tipo_pagamento.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


TIPO_PAGAMENTO_DESC = _load_tipo_pagamento()


def descricao_tipo_pagamento(codigo):
    """Retorna a descrição do tipo de pagamento pelo código (XML)."""
    import pandas as pd
    if codigo is None or pd.isna(codigo):
        return "Não informado"
    return TIPO_PAGAMENTO_DESC.get(str(codigo).strip(), f"Outros ({codigo})")
