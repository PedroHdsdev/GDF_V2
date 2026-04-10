"""
Handlers de RFC para integração SAP.

Cada handler registra uma RFC que alimenta tabelas do schema sap.
Para adicionar novos RFCs:

  1. Crie uma função que recebe (cod_cliente, **params) e retorna dict com sucesso, mensagem, etc.
  2. Crie RfcHandler com params e handler_fn
  3. Chame registry.register(handler) em register_all
"""
from collections import defaultdict
from typing import Any, DefaultDict, Dict, List, Tuple

from django.db import transaction
from django.utils import timezone

from app.db_GDF.CTe.models import CTe
from app.db_GDF.NFe.models import NFe
from app.db_GDF.NFSe.models import NFSe

from app.integracao_sap.rfc_registry import (
    RfcHandler,
    RfcParam,
    RfcParamType,
)


def _handler_relatorio_custo_impl(cod_cliente: str, **params) -> Dict[str, Any]:
    """Chama RFC /PRCIT/GDF_RFC_CUSTO e persiste em sap.relatorio_custo."""
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


RFC_CONSULTA_SYNC_CHUNK = 80
RFC_CONSULTA_SYNC_MAX = 5000


def _lookup_linha_sap(m: Dict[str, Dict[str, Any]], ch: str):
    ch_norm = (ch or "").strip()
    if not ch_norm:
        return None
    digits = "".join(c for c in ch_norm if c.isdigit())
    return (
        m.get(ch_norm)
        or m.get(ch_norm[:48])
        or (m.get(digits) if len(digits) == 44 else None)
    )


def _handler_gdf_rfc_consulta_impl(cod_cliente: str, **params) -> Dict[str, Any]:
    """
    RFC /PRCIT/GDF_RFC_CONSULTA: busca no GDF documentos com tem_sap=False (NFe, CT-e, NFS-e),
    consulta o SAP em lotes e atualiza tem_sap / sap_nome_tabela quando encontrado.
    """
    from app.classes.SapRfc import SapRfc

    if not SapRfc.is_available():
        return {"sucesso": False, "mensagem": SapRfc.pyrfc_mensagem_indisponivel()}

    entries: List[Tuple[str, int, str]] = []

    for nfe in (
        NFe.objects.filter(gdfcliente__cod_cliente=cod_cliente, tem_sap=False)
        .select_related("identificacao")
        .order_by("data_atualizacao")
        .iterator(chunk_size=300)
    ):
        if len(entries) >= RFC_CONSULTA_SYNC_MAX:
            break
        ch = (nfe.identificacao.chave_acesso or "").strip()
        if ch:
            entries.append(("nfe", nfe.id_nfe, ch))

    for cte in (
        CTe.objects.filter(gdfcliente__cod_cliente=cod_cliente, tem_sap=False)
        .select_related("identificacao")
        .order_by("data_atualizacao")
        .iterator(chunk_size=300)
    ):
        if len(entries) >= RFC_CONSULTA_SYNC_MAX:
            break
        ch = (cte.identificacao.chave_acesso or "").strip()
        if ch:
            entries.append(("cte", cte.id_cte, ch))

    for nfse in (
        NFSe.objects.filter(gdfcliente__cod_cliente=cod_cliente, tem_sap=False)
        .select_related("identificacao")
        .order_by("data_atualizacao")
        .iterator(chunk_size=300)
    ):
        if len(entries) >= RFC_CONSULTA_SYNC_MAX:
            break
        ch = (nfse.identificacao.chave or "").strip()
        if ch:
            entries.append(("nfse", nfse.id_nfse, ch))

    total_pendentes = len(entries)
    if total_pendentes == 0:
        return {
            "sucesso": True,
            "mensagem": "Nenhum documento pendente (tem_sap = Não) para este cliente.",
            "total_pendentes": 0,
            "total_chaves_unicas": 0,
            "total_chaves_consultadas": 0,
            "total_atualizados": 0,
            "total_linhas": 0,
            "linhas": [],
        }

    refs_by_chave: DefaultDict[str, List[Tuple[str, int]]] = defaultdict(list)
    ordered_unique: List[str] = []
    seen_ch = set()
    for tipo, pk, ch in entries:
        refs_by_chave[ch].append((tipo, pk))
        if ch not in seen_ch:
            seen_ch.add(ch)
            ordered_unique.append(ch)

    total_chaves_unicas = len(ordered_unique)
    amostra: List[Dict[str, Any]] = []
    total_atualizados = 0

    try:
        with transaction.atomic():
            for i in range(0, len(ordered_unique), RFC_CONSULTA_SYNC_CHUNK):
                chunk = ordered_unique[i : i + RFC_CONSULTA_SYNC_CHUNK]
                ok, err, m, ord_chunk = SapRfc.consultar_chaves_no_sap_batch(cod_cliente, chunk)
                if not ok:
                    raise RuntimeError(err)
                for ch in ord_chunk:
                    row = _lookup_linha_sap(m, ch)
                    if not row or not row.get("tem_sap"):
                        continue
                    nt = (row.get("name_table") or "").strip()[:30] or None
                    now = timezone.now()
                    for tipo, pk in refs_by_chave.get(ch, []):
                        if tipo == "nfe":
                            n = NFe.objects.filter(pk=pk, tem_sap=False).update(
                                tem_sap=True,
                                sap_nome_tabela=nt,
                                data_atualizacao=now,
                            )
                        elif tipo == "cte":
                            n = CTe.objects.filter(pk=pk, tem_sap=False).update(
                                tem_sap=True,
                                sap_nome_tabela=nt,
                                data_atualizacao=now,
                            )
                        else:
                            n = NFSe.objects.filter(pk=pk, tem_sap=False).update(
                                tem_sap=True,
                                sap_nome_tabela=nt,
                                data_atualizacao=now,
                            )
                        total_atualizados += n
                        if n and len(amostra) < 40:
                            amostra.append(
                                {
                                    "tipo": tipo.upper(),
                                    "chave": ch,
                                    "tem_sap": True,
                                    "status": row.get("status", ""),
                                    "name_table": nt or "",
                                }
                            )
    except Exception as e:
        return {
            "sucesso": False,
            "mensagem": str(e),
            "total_pendentes": total_pendentes,
            "total_chaves_unicas": total_chaves_unicas,
        }

    return {
        "sucesso": True,
        "mensagem": (
            f"Consultadas {total_chaves_unicas} chave(s) única(s) no SAP; "
            f"{total_atualizados} documento(s) atualizado(s) no GDF."
        ),
        "total_pendentes": total_pendentes,
        "total_chaves_unicas": total_chaves_unicas,
        "total_chaves_consultadas": total_chaves_unicas,
        "total_atualizados": total_atualizados,
        "total_linhas": len(amostra),
        "linhas": amostra,
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

    registry.register(RfcHandler(
        codigo="RFC_GDF_RFC_CONSULTA",
        nome="Reconsultar SAP (pendentes)",
        descricao="RFC /PRCIT/GDF_RFC_CONSULTA: localiza NF-e, CT-e e NFS-e com tem_sap = Não, consulta o SAP em lotes e grava tem_sap / tabela quando encontrar. Até 5000 documentos por execução (ordem: NFe → CT-e → NFS-e).",
        tabela_sap="/PRCIT/GDF_RFC_CONSULTA",
        params=[],
        handler_fn=_handler_gdf_rfc_consulta_impl,
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
