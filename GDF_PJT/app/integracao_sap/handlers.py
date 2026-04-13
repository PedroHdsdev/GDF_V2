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
# Máximo de chaves únicas consultadas por execução da RFC /PRCIT/GDF_RFC_CONSULTA (evita timeout e carga excessiva no SAP).
RFC_CONSULTA_MAX_CHAVES_POR_EXECUCAO = 5000


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
    RFC /PRCIT/GDF_RFC_CONSULTA: busca no GDF todos os documentos com tem_sap=False (NFe, CT-e, NFS-e),
    consulta o SAP em lotes (chunks); interpreta R_RETURN (JSON) e atualiza tem_sap / sap_nome_tabela quando status=true.
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
        ch = (nfe.identificacao.chave_acesso or "").strip()
        if ch:
            entries.append(("nfe", nfe.id_nfe, ch))

    for cte in (
        CTe.objects.filter(gdfcliente__cod_cliente=cod_cliente, tem_sap=False)
        .select_related("identificacao")
        .order_by("data_atualizacao")
        .iterator(chunk_size=300)
    ):
        ch = (cte.identificacao.chave_acesso or "").strip()
        if ch:
            entries.append(("cte", cte.id_cte, ch))

    for nfse in (
        NFSe.objects.filter(gdfcliente__cod_cliente=cod_cliente, tem_sap=False)
        .select_related("identificacao")
        .order_by("data_atualizacao")
        .iterator(chunk_size=300)
    ):
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
            "limite_chaves_por_execucao": RFC_CONSULTA_MAX_CHAVES_POR_EXECUCAO,
            "total_atualizados": 0,
            "total_linhas": 0,
            "linhas": [],
            "linhas_consulta_sap": [],
        }

    refs_by_chave: DefaultDict[str, List[Tuple[str, int]]] = defaultdict(list)
    ordered_unique: List[str] = []
    seen_ch = set()
    for tipo, pk, ch in entries:
        refs_by_chave[ch].append((tipo, pk))
        if ch not in seen_ch:
            seen_ch.add(ch)
            ordered_unique.append(ch)

    total_chaves_unicas_total = len(ordered_unique)
    consultar_estas = ordered_unique
    if total_chaves_unicas_total > RFC_CONSULTA_MAX_CHAVES_POR_EXECUCAO:
        consultar_estas = ordered_unique[:RFC_CONSULTA_MAX_CHAVES_POR_EXECUCAO]

    total_chaves_unicas = total_chaves_unicas_total
    n_chaves_nesta_execucao = len(consultar_estas)
    linhas_consulta_sap: List[Dict[str, Any]] = []
    total_atualizados = 0

    try:
        with transaction.atomic():
            for i in range(0, len(consultar_estas), RFC_CONSULTA_SYNC_CHUNK):
                chunk = consultar_estas[i : i + RFC_CONSULTA_SYNC_CHUNK]
                ok, err, m, ord_chunk = SapRfc.consultar_chaves_no_sap_batch(cod_cliente, chunk)
                if not ok:
                    raise RuntimeError(err)
                for ch in ord_chunk:
                    row = _lookup_linha_sap(m, ch) or {}
                    tem_s = bool(row.get("tem_sap"))
                    st_val = row.get("status", "") or ""
                    nt_full = (row.get("name_table") or "").strip()
                    refs = refs_by_chave.get(ch, [])
                    tipos_set = {t.upper() for t, _ in refs}
                    tipos_str = ", ".join(sorted(tipos_set)) if tipos_set else "—"
                    atualizados_ch = 0
                    if tem_s:
                        nt_db = nt_full[:30] if nt_full else None
                        now = timezone.now()
                        for tipo, pk in refs:
                            if tipo == "nfe":
                                n = NFe.objects.filter(pk=pk, tem_sap=False).update(
                                    tem_sap=True,
                                    sap_nome_tabela=nt_db,
                                    data_atualizacao=now,
                                )
                            elif tipo == "cte":
                                n = CTe.objects.filter(pk=pk, tem_sap=False).update(
                                    tem_sap=True,
                                    sap_nome_tabela=nt_db,
                                    data_atualizacao=now,
                                )
                            else:
                                n = NFSe.objects.filter(pk=pk, tem_sap=False).update(
                                    tem_sap=True,
                                    sap_nome_tabela=nt_db,
                                    data_atualizacao=now,
                                )
                            atualizados_ch += n
                        total_atualizados += atualizados_ch
                    linhas_consulta_sap.append(
                        {
                            "chave": ch,
                            "tem_sap": tem_s,
                            "status": st_val,
                            "name_table": nt_full,
                            "tipos": tipos_str,
                            "qtd_docs": len(refs),
                            "atualizado_gdf": atualizados_ch,
                        }
                    )
    except Exception as e:
        return {
            "sucesso": False,
            "mensagem": str(e),
            "total_pendentes": total_pendentes,
            "total_chaves_unicas": total_chaves_unicas,
            "total_chaves_consultadas": n_chaves_nesta_execucao,
            "limite_chaves_por_execucao": RFC_CONSULTA_MAX_CHAVES_POR_EXECUCAO,
            "linhas_consulta_sap": linhas_consulta_sap,
        }

    msg_ok = (
        f"Consultadas {n_chaves_nesta_execucao} chave(s) única(s) no SAP nesta execução; "
        f"{total_atualizados} documento(s) atualizado(s) no GDF."
    )
    if total_chaves_unicas_total > n_chaves_nesta_execucao:
        restante = total_chaves_unicas_total - n_chaves_nesta_execucao
        msg_ok += (
            f" Há {restante} chave(s) única(s) ainda pendentes (limite {RFC_CONSULTA_MAX_CHAVES_POR_EXECUCAO} por execução); "
            "execute novamente para continuar."
        )

    return {
        "sucesso": True,
        "mensagem": msg_ok,
        "total_pendentes": total_pendentes,
        "total_chaves_unicas": total_chaves_unicas,
        "total_chaves_consultadas": n_chaves_nesta_execucao,
        "limite_chaves_por_execucao": RFC_CONSULTA_MAX_CHAVES_POR_EXECUCAO,
        "total_atualizados": total_atualizados,
        "total_linhas": len(linhas_consulta_sap),
        "linhas": [],
        "linhas_consulta_sap": linhas_consulta_sap,
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
        descricao="RFC /PRCIT/GDF_RFC_CONSULTA: localiza NF-e, CT-e e NFS-e com tem_sap = Não, consulta em lotes (até 5000 chaves únicas por execução); o SAP devolve R_RETURN (JSON). Grava tem_sap / sap_nome_tabela quando status=true (ordem: NFe → CT-e → NFS-e).",
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
