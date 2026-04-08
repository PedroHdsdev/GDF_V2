"""
RFC ZF_ECF01 – Balanço financeiro.

A comunicação e o processamento de ``T_BALANCE`` (mapeamento de campos, sinal via
``IND_DC``, saldos UM01O–UM12O) estão em ``SapRfc.consultar_balanco_financeiro``.
Este módulo mantém tipagem (TypedDict) e ``executar_balanco_financeiro`` para API/Streamlit.
"""
from __future__ import annotations

from typing import Any, List, TypedDict

from app.classes.SapRfc import SapRfc

RFC_NAME = "ZF_ECF01"


class ZfEcf01Params(TypedDict):
    """Parâmetros de importação da RFC (nomes técnicos SAP)."""

    I_BUKRS: str
    I_MONTH_B: str
    I_MONTH_V: str
    I_YEAR: str
    I_KTOPL: str
    I_VERSN: str


class ZfEcf01Resultado(TypedDict, total=False):
    """Resposta normalizada para API/UI (JSON-serializável)."""

    sucesso: bool
    mensagem: str
    r_return: str
    t_balance: List[dict[str, Any]]
    total_linhas: int
    colunas: List[str]


def executar_balanco_financeiro(cod_cliente: str, **params: Any) -> ZfEcf01Resultado:
    """
    Executa ZF_ECF01 e devolve T_BALANCE normalizado.

    params: i_bukrs, i_ktopl, i_versn, i_year; intervalo i_month_b / i_month_v (RFC I_MONTH_B / I_MONTH_V)
    ou alias i_month_ini / i_month_fim; período único: i_month + i_year.
    """
    return SapRfc.consultar_balanco_financeiro(cod_cliente, **params)
