"""
Handlers de RFC para integração SAP.

Cada handler registra uma RFC que alimenta tabelas do schema sap.
Para adicionar novos RFCs:

  1. Crie uma função que recebe (cod_cliente, **params) e retorna dict com sucesso, mensagem, etc.
  2. Crie RfcHandler com params e handler_fn
  3. Chame registry.register(handler) em register_all
"""
from typing import Dict, Any, List

from app.integracao_sap.rfc_registry import (
    RfcHandler,
    RfcParam,
    RfcParamType,
)


def _handler_relatorio_custo_impl(cod_cliente: str, **params) -> Dict[str, Any]:
    """Chama RFC /BRGMN/CUSTR_IMP_CUSTO e persiste em sap.relatorio_custo."""
    from app.classes.SapRfc import SapRfc

    bukrs = str(params.get("bukrs") or "").strip()
    branch = str(params.get("branch") or "").strip()
    psdat_ini = params.get("psdat_ini")
    psdat_fim = params.get("psdat_fim")
    persistir = params.get("persistir", True)
    if isinstance(persistir, str):
        persistir = persistir.lower() in ("true", "1", "yes", "sim")

    if not bukrs:
        return {
            "sucesso": False,
            "mensagem": "Empresa (bukrs) é obrigatória.",
        }

    if not psdat_ini or not psdat_fim:
        return {
            "sucesso": False,
            "mensagem": "Data inicial e final são obrigatórias.",
        }

    if not SapRfc.is_available():
        return {
            "sucesso": False,
            "mensagem": SapRfc.pyrfc_mensagem_indisponivel(),
        }

    result = SapRfc.importar_relatorio_custo(
        cod_cliente=cod_cliente,
        bukrs=bukrs,
        branch=branch,
        psdat_ini=psdat_ini,
        psdat_fim=psdat_fim,
        persistir=persistir,
    )

    return {
        "sucesso": result.get("sucesso", False),
        "mensagem": result.get("mensagem", ""),
        "total_linhas": result.get("total_linhas", 0),
        "total_gravados": result.get("total_gravados", 0),
    }


def register_all(registry) -> None:
    """Registra todos os handlers de RFC no registry."""
    registry.register(RfcHandler(
        codigo="RFC_RELATORIO_CUSTO",
        nome="Relatório de Custo",
        descricao="Importa dados de custo do SAP e grava em sap.relatorio_custo.",
        tabela_sap="sap.relatorio_custo",
        params=[
            RfcParam("bukrs", "Empresa (Cód. SAP)", RfcParamType.STRING, required=True, help_text="Código da empresa no SAP (ex: 1000)"),
            RfcParam("branch", "Filial (Cód. SAP)", RfcParamType.STRING, required=False, help_text="Opcional. Deixe vazio para carregar todas as filiais da empresa."),
            RfcParam("psdat_ini", "Data inicial", RfcParamType.DATE, required=True),
            RfcParam("psdat_fim", "Data final", RfcParamType.DATE, required=True),
            RfcParam("persistir", "Persistir no banco", RfcParamType.BOOLEAN, required=False, default=True),
        ],
        handler_fn=_handler_relatorio_custo_impl,
    ))

    # Exemplo: adicione novos RFCs aqui:
    # registry.register(RfcHandler(
    #     codigo="RFC_OUTRO",
    #     nome="Outro RFC",
    #     descricao="...",
    #     tabela_sap="sap.outra_tabela",
    #     params=[...],
    #     handler_fn=_handler_outro_impl,
    # ))
