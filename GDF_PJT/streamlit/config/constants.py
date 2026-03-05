"""Constantes e configurações do Dashboard."""
import json
import os


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
