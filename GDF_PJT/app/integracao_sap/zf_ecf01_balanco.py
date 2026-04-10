"""
RFC /PRCIT/GDF_RFC_BALANCE – Balanço financeiro (equivalente lógico a ZF_ECF01).

O SAP devolve o balanço em ``R_RETURN`` (string JSON). Há dois formatos suportados após o parse:

- **Árvore recursiva:** raízes com ``id``, ``text``, ``valor``, ``accounts``, ``children``;
  em ``accounts``, descrição em ``txt`` ou ``txt_acc``.
- **Lista plana:** ``parent_id``, ``txt_balance``, ``stufe``, etc.

A normalização em ``SapRfc`` unifica para ``id``, ``conta``, ``text``, ``valor``, ``children``,
``accounts`` (com ``txt_acc`` preenchido a partir de ``txt`` quando necessário).
A normalização está em ``SapRfc.consultar_balanco_financeiro``.
Este módulo mantém tipagem (TypedDict) e ``executar_balanco_financeiro`` para API/Streamlit.
"""
from __future__ import annotations

from typing import Any, List, TypedDict

from app.classes.SapRfc import SapRfc

RFC_NAME = "/PRCIT/GDF_RFC_BALANCE"


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
    arvore: List[dict[str, Any]]
    total_nos: int
    t_balance: List[dict[str, Any]]
    total_linhas: int
    colunas: List[str]
    periodo: dict[str, Any]
    opcoes_arvore: dict[str, Any]


def executar_balanco_financeiro(cod_cliente: str, **params: Any) -> ZfEcf01Resultado:
    """
    Executa GDF_RFC_BALANCE e devolve ``arvore`` (JSON parseado de R_RETURN) e metadados.

    params: i_bukrs, i_ktopl, i_versn, i_year; intervalo i_month_b / i_month_v (RFC I_MONTH_B / I_MONTH_V)
    ou alias i_month_ini / i_month_fim; período único: i_month + i_year.
    """
    return SapRfc.consultar_balanco_financeiro(cod_cliente, **params)
