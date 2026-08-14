"""Dashboard Demonstrativos contábeis — integração com SAP (/PRCIT/GDF_RFC_BALANCE) via backend Django."""
from __future__ import annotations

import html as html_module
import unicodedata
from datetime import datetime

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from core.auth import AuthResult
from core.django_backend import demonstrativos_contabeis_api_url, post_json_bearer

# Alinhado a SapRfc._ZF_ECF01_MAX_NUMERO_PERIODO (I_MONTH_B / I_MONTH_V na GDF_RFC_BALANCE).
_MAX_PERIODO_SAP = 99


def _format_valor_br_sap(v: object) -> str:
    """Exibe número como no SAP BR: 150.037.234,87 e negativo com menos à direita (…-)."""
    if v is None:
        return "—"
    try:
        x = float(v)
    except (TypeError, ValueError):
        return html_module.escape(str(v))
    neg = x < 0
    x = abs(x)
    intpart = int(x + 1e-9)
    frac = int(round((x - int(intpart)) * 100 + 1e-9)) % 100
    s = str(intpart)
    if len(s) > 3:
        parts: list[str] = []
        while s:
            parts.insert(0, s[-3:])
            s = s[:-3]
        s_int = ".".join(parts)
    else:
        s_int = s
    out = f"{s_int},{frac:02d}"
    return f"{out}-" if neg else out


def _contar_nos_local(nodes: list) -> int:
    n = 0
    for node in nodes:
        if not isinstance(node, dict):
            continue
        n += 1
        ch = node.get("children")
        if isinstance(ch, list) and ch:
            n += _contar_nos_local(ch)
    return n


def _contas_do_no(node: dict) -> list[dict]:
    raw = node.get("accounts")
    if not isinstance(raw, list):
        return []
    return [a for a in raw if isinstance(a, dict)]


def _descricao_conta_racct(acc: dict) -> str:
    """Texto da conta: API normalizada usa ``txt_acc``; JSON ABAP recursivo pode mandar ``txt``."""
    for k in ("txt_acc", "txt", "TXT", "Txt"):
        v = acc.get(k)
        if v is not None and str(v).strip():
            return str(v).strip()
    return ""


def _accounts_para_html(accounts: list[dict], depth: int) -> str:
    """Linhas de contas RACCT (filhas lógicas do nó do demonstrativo, sem filhos na árvore)."""
    if not accounts:
        return ""
    pad = 8 + depth * 12
    partes: list[str] = []
    for a in accounts:
        racct_raw = str(a.get("racct", "") or "").strip()
        racct = html_module.escape(racct_raw)
        txt_acc = html_module.escape(_descricao_conta_racct(a))
        val = _format_valor_br_sap(a.get("valor"))
        if racct_raw:
            ccell = f'<span class="dctb-conta dctb-conta-acc" title="RACCT">{racct}</span>'
        else:
            ccell = '<span class="dctb-conta dctb-conta-acc dctb-conta-vazia">—</span>'
        dcell = f'<span class="dctb-desc dctb-desc-acc">{txt_acc}</span>' if txt_acc else (
            '<span class="dctb-desc dctb-desc-acc dctb-desc-vazia">—</span>'
        )
        partes.append(
            f'<div class="dctb-acc-row" style="padding-left:{pad}px">'
            f'<span class="dctb-ico dctb-ico-acc">&#8226;</span>{ccell}{dcell}'
            f'<span class="dctb-val">{val}</span></div>'
        )
    return f'<div class="dctb-acc-block" aria-label="Contas contábeis">{"".join(partes)}</div>'


def _arvore_para_html_hierarquia(
    nodes: list,
    *,
    expandir_todos: bool,
    profundidade_aberta_padrao: int = 2,
) -> str:
    """Gera HTML com <details> para árvore tipo SAP (pastas / filhos + contas em ``accounts``)."""

    def render_no(node: dict, depth: int) -> str:
        if not isinstance(node, dict):
            return ""
        nid = html_module.escape(str(node.get("id", "") or ""))
        conta_raw = str(node.get("conta", "") or "").strip()
        conta = html_module.escape(conta_raw)
        texto = html_module.escape(str(node.get("text", "") or ""))
        valor = _format_valor_br_sap(node.get("valor"))
        ch = node.get("children")
        filhos = ch if isinstance(ch, list) else []
        filhos = [c for c in filhos if isinstance(c, dict)]
        contas = _contas_do_no(node)
        stufe = node.get("stufe")
        titulo_linha = f"Linha do demonstrativo · id {node.get('id', '') or '—'}"
        if stufe is not None and str(stufe).strip() != "":
            titulo_linha += f" · nível {stufe}"
        titulo_linha_esc = html_module.escape(titulo_linha, quote=True)
        tem_filhos_arvore = len(filhos) > 0
        tem_contas = len(contas) > 0
        tem_expansivel = tem_filhos_arvore or tem_contas

        if conta_raw:
            conta_cell = f'<span class="dctb-conta" title="{titulo_linha_esc}">{conta}</span>'
        else:
            conta_cell = f'<span class="dctb-conta dctb-conta-vazia" title="{titulo_linha_esc}">—</span>'
        desc_cell = f'<span class="dctb-desc">{texto}</span>' if texto else f'<span class="dctb-desc dctb-desc-vazia">{nid}</span>'
        val_cell = f'<span class="dctb-val">{valor}</span>'

        if tem_expansivel:
            aberto = " open" if (expandir_todos or depth < profundidade_aberta_padrao) else ""
            icone = "&#128193;"  # pasta
            spad = 6 + depth * 12
            inner_filhos = "".join(render_no(c, depth + 1) for c in filhos)
            inner_acc = _accounts_para_html(contas, depth + 1)
            inner = f'<div class="dctb-kids">{inner_filhos}{inner_acc}</div>'
            return (
                f'<details class="dctb-node" data-depth="{depth}"{aberto}>'
                f'<summary class="dctb-sum" style="padding-left:{spad}px"><span class="dctb-ico">{icone}</span>'
                f'{conta_cell}{desc_cell}{val_cell}</summary>'
                f"{inner}</details>"
            )
        icone = "&#128196;"  # documento
        pad = max(0, depth) * 18
        return (
            f'<div class="dctb-leaf" style="padding-left:{pad}px" data-depth="{depth}">'
            f'<span class="dctb-leaf-row"><span class="dctb-ico">{icone}</span>'
            f'{conta_cell}{desc_cell}{val_cell}</span></div>'
        )

    corpo = "".join(render_no(n, 0) for n in nodes if isinstance(n, dict))
    return f"""<div class="dctb-hier-root">{corpo}</div>"""


def _css_hierarquia_demonstrativos() -> str:
    return """
<style>
.dctb-hier-wrap {
  font-family: system-ui, "Segoe UI", Roboto, sans-serif;
  font-size: 13px;
  border: 1px solid rgba(80, 80, 120, 0.35);
  border-radius: 6px;
  overflow: hidden;
  background: var(--background-color, #fff);
  color: var(--text-color, #1a1a1a);
}
.dctb-hier-head {
  display: grid;
  grid-template-columns: 22px minmax(96px, 12%) 1fr minmax(108px, 22%);
  gap: 8px;
  align-items: center;
  padding: 10px 14px;
  background: linear-gradient(180deg, #2d4a6f 0%, #1e3a5f 100%);
  color: #f5f7fa;
  font-weight: 600;
  letter-spacing: 0.02em;
  border-bottom: 1px solid rgba(0,0,0,0.2);
}
.dctb-hier-head .dctb-col-num { text-align: right; }
.dctb-hier-head .dctb-h-spacer { visibility: hidden; width: 22px; }
.dctb-hier-body {
  max-height: min(72vh, 900px);
  overflow: auto;
  padding: 6px 8px 12px;
}
.dctb-node { margin: 0; border-left: 2px solid rgba(46, 74, 111, 0.2); margin-left: 6px; padding-left: 4px; }
.dctb-node > .dctb-sum {
  list-style: none;
  cursor: pointer;
  display: grid;
  grid-template-columns: 22px minmax(88px, 12%) 1fr minmax(100px, 22%);
  gap: 6px 10px;
  align-items: center;
  padding: 6px 8px;
  border-radius: 4px;
  margin: 2px 0;
}
.dctb-node > .dctb-sum:hover { background: rgba(46, 74, 111, 0.08); }
.dctb-node > .dctb-sum::-webkit-details-marker { display: none; }
.dctb-kids { margin-left: 8px; padding-left: 4px; border-left: 1px dashed rgba(46, 74, 111, 0.25); }
.dctb-leaf { padding: 4px 8px; margin: 1px 0; border-radius: 4px; }
.dctb-leaf:hover { background: rgba(46, 74, 111, 0.06); }
.dctb-leaf-row {
  display: grid;
  grid-template-columns: 22px minmax(88px, 12%) 1fr minmax(100px, 22%);
  gap: 6px 10px;
  align-items: center;
}
.dctb-ico { font-size: 15px; line-height: 1; opacity: 0.92; }
.dctb-conta {
  font-family: "Consolas", "Monaco", ui-monospace, monospace;
  font-size: 12px;
  color: #2c5282;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.dctb-conta-vazia { color: #a0aec0; }
.dctb-desc { min-width: 0; word-break: break-word; font-weight: 500; }
.dctb-desc-vazia { color: #718096; font-weight: 400; }
.dctb-val {
  font-variant-numeric: tabular-nums;
  text-align: right;
  justify-self: end;
  font-family: "Consolas", "Monaco", monospace;
  white-space: nowrap;
}
.dctb-acc-block {
  margin-top: 4px;
  padding-top: 4px;
  border-top: 1px dashed rgba(46, 74, 111, 0.2);
}
.dctb-acc-row {
  display: grid;
  grid-template-columns: 22px minmax(88px, 12%) 1fr minmax(100px, 22%);
  gap: 6px 10px;
  align-items: center;
  padding: 4px 8px 4px 0;
  margin: 1px 0;
  border-radius: 4px;
  font-size: 12px;
  color: #4a5568;
}
.dctb-acc-row:hover { background: rgba(46, 74, 111, 0.05); }
.dctb-ico-acc { font-size: 11px; color: #718096; text-align: center; }
.dctb-conta-acc { color: #2d5a3d; }
.dctb-desc-acc { font-weight: 400; }
.dctb-ind-root > .dctb-sum { font-weight: 700; }
.dctb-ind-item > .dctb-sum { font-weight: 600; }
.dctb-ind-fonte {
  display: grid;
  grid-template-columns: 1fr minmax(108px, 22%);
  gap: 8px 12px;
  align-items: start;
  padding: 6px 8px 6px 28px;
  margin: 2px 0;
  font-size: 12px;
  color: #4a5568;
  border-left: 2px solid rgba(46, 74, 111, 0.15);
  margin-left: 8px;
}
.dctb-ind-fonte:hover { background: rgba(46, 74, 111, 0.04); }
.dctb-ind-fonte .dctb-lbl { min-width: 0; word-break: break-word; font-weight: 600; color: #2c5282; }
.dctb-ind-fonte .dctb-val { font-variant-numeric: tabular-nums; text-align: right; font-family: Consolas, Monaco, monospace; white-space: nowrap; }
/* Indicadores: mais área útil; tipografia igual ao Balanço (herda .dctb-hier-wrap). */
.dctb-hier-wrap.dctb-hier--ind .dctb-hier-body {
  max-height: min(88vh, 1200px);
}
.dctb-ind-secao {
  margin-top: 4px;
  border-left: 2px solid rgba(46, 74, 111, 0.18);
  margin-left: 2px;
  padding-left: 2px;
}
.dctb-ind-secao > .dctb-sum { font-weight: 700; }
</style>
"""


def _render_painel_hierarquia(
    arvore: list,
    *,
    expandir_todos: bool,
    profundidade_aberta: int,
) -> None:
    inner = _arvore_para_html_hierarquia(
        arvore,
        expandir_todos=expandir_todos,
        profundidade_aberta_padrao=profundidade_aberta,
    )
    full = (
        _css_hierarquia_demonstrativos()
        + '<div class="dctb-hier-wrap">'
        + '<div class="dctb-hier-head"><span class="dctb-h-spacer">·</span>'
        + "<span>Linha / RACCT</span><span>Descrição</span>"
        + '<span class="dctb-col-num">Tot. período</span></div>'
        + '<div class="dctb-hier-body">'
        + inner
        + "</div></div>"
    )
    n = _contar_nos_local(arvore)
    altura = min(920, max(280, 120 + min(n, 120) * 5))
    components.html(full, height=altura, scrolling=True)


def _flatten_arvore_demonstrativo(nodes: list, depth: int = 0) -> list[dict]:
    """Desdobra a árvore (linhas do demonstrativo + contas em ``accounts``) para tabela plana."""
    rows: list[dict] = []
    for n in nodes:
        if not isinstance(n, dict):
            continue
        rows.append(
            {
                "tipo": "linha_demonstrativo",
                "id": n.get("id"),
                "stufe": n.get("stufe"),
                "conta_linha": n.get("conta"),
                "descricao": n.get("text"),
                "racct": None,
                "txt_acc": None,
                "valor": n.get("valor"),
                "profundidade": depth,
            }
        )
        for a in _contas_do_no(n):
            rows.append(
                {
                    "tipo": "conta",
                    "id": n.get("id"),
                    "stufe": None,
                    "conta_linha": None,
                    "descricao": None,
                    "racct": a.get("racct"),
                    "txt_acc": _descricao_conta_racct(a) or a.get("txt_acc"),
                    "valor": a.get("valor"),
                    "profundidade": depth + 1,
                }
            )
        ch = n.get("children")
        if isinstance(ch, list) and ch:
            rows.extend(_flatten_arvore_demonstrativo(ch, depth + 1))
    return rows


def _texto_norm_busca(s: object) -> str:
    """Minúsculas sem acentos, para casar rótulos do SAP (Ativo / Passivo / etc.)."""
    t = unicodedata.normalize("NFKD", str(s or "").lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def _float_valor_no(v: object) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _iter_nos_arvore_com_caminho(
    nodes: list,
    ancestrais: tuple[str, ...] = (),
) -> list[tuple[dict, tuple[str, ...], str, str]]:
    """(nó, textos ancestrais sem o nó atual, text_norm, conta_norm) em pré-ordem."""
    out: list[tuple[dict, tuple[str, ...], str, str]] = []
    for n in nodes:
        if not isinstance(n, dict):
            continue
        txt_raw = str(n.get("text") or "")
        conta_raw = str(n.get("conta") or "")
        tnorm = _texto_norm_busca(txt_raw)
        cnorm = _texto_norm_busca(conta_raw)
        out.append((n, ancestrais, tnorm, cnorm))
        ch = n.get("children")
        if isinstance(ch, list) and ch:
            prox = ancestrais + (tnorm,) if tnorm else ancestrais
            out.extend(_iter_nos_arvore_com_caminho(ch, prox))
    return out


def _full_path_norm(ancestrais: tuple[str, ...], tnorm: str, cnorm: str) -> str:
    return (" ".join(ancestrais) + " " + tnorm + " " + cnorm).strip()


def _primeiro_valor_no(
    nos_info: list[tuple[dict, tuple[str, ...], str, str]],
    pred,
) -> float | None:
    """Primeiro nó que satisfaz ``pred(full, tnorm, ancestrais)`` com ``valor`` numérico."""
    for n, ancestrais, tnorm, cnorm in nos_info:
        full = _full_path_norm(ancestrais, tnorm, cnorm)
        if pred(full, tnorm, ancestrais):
            fv = _float_valor_no(n.get("valor"))
            if fv is not None:
                return fv
    return None


def _valores_indicadores_demonstrativo(arvore: list) -> dict[str, float | None]:
    """
    Extrai totais da árvore por rótulos usuais (Ativo/Passivo/Patrimônio e linhas de resultado).
    Os indicadores dependem do texto enviado pelo SAP; ajuste os predicados se o plano for outro.
    """
    infos = _iter_nos_arvore_com_caminho(arvore if isinstance(arvore, list) else [])

    def ac_pred(full: str, tnorm: str, ancestrais: tuple[str, ...]) -> bool:
        if "passivo" in full:
            return False
        if "circulante" not in full:
            return False
        return "ativo" in full

    def pc_pred(full: str, tnorm: str, ancestrais: tuple[str, ...]) -> bool:
        if "nao circulante" in full or "nao-circulante" in full:
            return False
        if "circulante" not in full:
            return False
        return "passivo" in full

    def pnc_pred(full: str, tnorm: str, ancestrais: tuple[str, ...]) -> bool:
        if "nao circulante" not in full and "nao-circulante" not in full:
            return False
        return "passivo" in full

    def pl_pred(full: str, tnorm: str, ancestrais: tuple[str, ...]) -> bool:
        return "patrimonio" in tnorm and "liquido" in tnorm

    ac = _primeiro_valor_no(infos, ac_pred)
    pc = _primeiro_valor_no(infos, pc_pred)
    pnc = _primeiro_valor_no(infos, pnc_pred)
    pl = _primeiro_valor_no(infos, pl_pred)

    def imob_pred(full: str, tnorm: str, ancestrais: tuple[str, ...]) -> bool:
        return "imobiliz" in tnorm and "intangiv" not in tnorm

    def inv_pred(full: str, tnorm: str, ancestrais: tuple[str, ...]) -> bool:
        return "investiment" in tnorm

    def int_pred(full: str, tnorm: str, ancestrais: tuple[str, ...]) -> bool:
        return "intangiv" in tnorm

    def ativo_pred(full: str, tnorm: str, ancestrais: tuple[str, ...]) -> bool:
        if "passivo" in full and "ativo" not in tnorm:
            return False
        return (
            "ativo" in tnorm
            or "ativo" in tnorm
            or "ativos" in tnorm
            or "ativo" in tnorm
        )

    def lpa_pred(full: str, tnorm: str, ancestrais: tuple[str, ...]) -> bool:
        if "acumul" not in tnorm:
            return False
        if "patrimonio" in tnorm and "liquido" in tnorm:
            return False
        return "lucro" in tnorm or "prejuiz" in tnorm or "prejuizo" in tnorm

    def res_exercicio_pred(full: str, tnorm: str, ancestrais: tuple[str, ...]) -> bool:
        if "acumul" in tnorm:
            return False
        if "patrimonio" in tnorm and "liquido" in tnorm:
            return False
        return (
            ("resultado" in tnorm and "exercic" in tnorm)
            or ("resultado" in tnorm and "periodo" in tnorm)
            or "lucro liquido" in tnorm
            or "lucro ou prejuizo do exercicio" in tnorm
        )

    def rbo_pred(full: str, tnorm: str, ancestrais: tuple[str, ...]) -> bool:
        return (
            ("bruto" in tnorm and "operac" in tnorm)
            or "resultado bruto operacional" in tnorm
            or "lucro bruto operacional" in tnorm
            or ("lucro bruto" in tnorm and "operac" in tnorm)
        )

    imob = _primeiro_valor_no(infos, imob_pred)
    inv = _primeiro_valor_no(infos, inv_pred)
    intang = _primeiro_valor_no(infos, int_pred)
    anc = 0.0
    n_anc = 0
    for x in (imob, inv, intang):
        if x is not None:
            anc += x
            n_anc += 1
    anc_nao_circ = anc if n_anc else None

    at = _primeiro_valor_no(infos, ativo_pred)
    lpa = _primeiro_valor_no(infos, lpa_pred)
    res_ex = _primeiro_valor_no(infos, res_exercicio_pred)
    rbo = _primeiro_valor_no(infos, rbo_pred)

    return {
        "AC": ac,
        "PC": pc,
        "PNC": pnc,
        "PL": pl,
        "ANC": anc_nao_circ,
        "Imobilizado": imob,
        "Investimentos": inv,
        "Intangivel": intang,
        "LPA": lpa,
        "AT": at,
        "RE": res_ex,
        "RBO": rbo,
    }


def _div_seguro(num: float | None, den: float | None) -> float | None:
    if num is None or den is None:
        return None
    if abs(float(den)) < 1e-12:
        return None
    return float(num) / float(den)


def _format_br_numero(x: float | None, dec: int = 2) -> str:
    if x is None:
        return "—"
    neg = x < 0
    v = abs(x)
    s = format(v, f",.{dec}f").replace(",", "X").replace(".", ",").replace("X", ".")
    return f"-{s}" if neg else s


def _format_pct_br(x: float | None, dec: int = 2) -> str:
    """``x`` como taxa (ex.: 0,42); exibe percentual com vírgula decimal."""
    if x is None:
        return "—"
    return f"{x * 100:.{dec}f} %".replace(".", ",")


def _computos_indicadores_patrimoniais(arvore: list) -> dict[str, object]:
    """Valores-base da árvore RFC e indicadores derivados (uma única fonte para tabela e árvore)."""
    v = _valores_indicadores_demonstrativo(arvore)
    ac, pc, pnc, pl, anc = v["AC"], v["PC"], v["PNC"], v["PL"], v["ANC"]
    imobilizado = v["Imobilizado"]
    investimentos = v["Investimentos"]
    intangivel = v["Intangivel"]
    lpa = v.get("LPA")
    at = v.get("AT")
    res_ex = v.get("RE")
    rbo = v.get("RBO")
    ac_a, pc_a, pnc_a, pl_a = (
        abs(x) if x is not None else None for x in (ac, pc, pnc, pl)
    )
    pc_pnc = None
    if pc_a is not None and pnc_a is not None:
        pc_pnc = pc_a + pnc_a
    elif pc_a is not None:
        pc_pnc = pc_a
    elif pnc_a is not None:
        pc_pnc = pnc_a

    pl_pc_pnc = None
    if pl_a is not None and pc_pnc is not None:
        pl_pc_pnc = pl_a + pc_pnc
    elif pl_a is not None:
        pl_pc_pnc = pl_a
    elif pc_pnc is not None:
        pl_pc_pnc = pc_pnc

    pct = _div_seguro(pc_pnc, pl_pc_pnc)
    grau_divida = _div_seguro(pl_a, pc_pnc)
    comp_endiv = _div_seguro(pc_a, pc_pnc)
    # Imobilizado + Investimentos + Intangível (mesma soma usada nos dois indicadores abaixo)
    soma_imob_inv_int: float | None = None
    _n_soma = 0
    _acc_soma = 0.0
    for _x in (imobilizado, investimentos, intangivel):
        if _x is not None:
            _acc_soma += float(_x)
            _n_soma += 1
    if _n_soma:
        soma_imob_inv_int = _acc_soma
    # Imobilização do patrimônio líquido =
    # (Imobilizado + Investimentos + Intangível) / Patrimônio líquido (PL da árvore)
    imob_pl = _div_seguro(soma_imob_inv_int, pl)
    pl_pnc = None
    if pl_a is not None and pnc_a is not None:
        pl_pnc = pl_a + pnc_a
    elif pl_a is not None:
        pl_pnc = pl_a
    elif pnc_a is not None:
        pl_pnc = pnc_a
    # Imobilização dos recursos não correntes =
    # (Imobilizado + Investimentos + Intangível) / (|PL| + |PNC|)
    imob_rec_nc = _div_seguro(soma_imob_inv_int, pl_pnc)
    lc = _div_seguro(ac_a, pc_a)
    ccl = None
    if ac is not None and pc is not None:
        ccl = ac - pc

    roa = _div_seguro(lpa, at)
    roe = _div_seguro(res_ex, pl)
    giro_ativo = _div_seguro(res_ex, at)
    margem_bruta = _div_seguro(rbo, res_ex)

    return {
        "ac": ac,
        "pc": pc,
        "pnc": pnc,
        "pl": pl,
        "anc": anc,
        "imobilizado": imobilizado,
        "investimentos": investimentos,
        "intangivel": intangivel,
        "lpa": lpa,
        "at": at,
        "res_ex": res_ex,
        "rbo": rbo,
        "pct": pct,
        "grau_divida": grau_divida,
        "comp_endiv": comp_endiv,
        "imob_pl": imob_pl,
        "imob_rec_nc": imob_rec_nc,
        "lc": lc,
        "ccl": ccl,
        "roa": roa,
        "roe": roe,
        "giro_ativo": giro_ativo,
        "margem_bruta": margem_bruta,
    }


_ROTULO_CAMPO_INDICADOR: dict[str, str] = {
    "AC": "Ativo circulante (AC)",
    "PC": "Passivo circulante (PC)",
    "PNC": "Passivo não circulante (PNC)",
    "PL": "Patrimônio líquido (PL)",
    "ANC": "Ativo não circulante agregado (ANC)",
    "IMOB": "Imobilizado (Imob.)",
    "INV": "Investimentos (Inv.)",
    "INT": "Intangível (Int.)",
    "LPA": "Lucros ou prejuízos acumulados (LPA)",
    "AT": "Ativo (Ativo)",
    "RE": "Resultado do exercício (RE)",
    "RBO": "Resultado bruto operacional (RBO)",
}


def _campo_indicador(cod: str, valor: object) -> tuple[str, str]:
    rotulo = _ROTULO_CAMPO_INDICADOR.get(cod, f"{cod}")
    return (rotulo, _format_br_numero(valor))


def _grupos_indicadores_patrimoniais_de_m(m: dict[str, object]) -> list[dict[str, object]]:
    """Grupos do painel patrimonial (a partir de ``_computos_indicadores_patrimoniais``)."""
    ac = m["ac"]
    pc = m["pc"]
    pnc = m["pnc"]
    pl = m["pl"]
    imobilizado = m["imobilizado"]
    investimentos = m["investimentos"]
    intangivel = m["intangivel"]
    pct = m["pct"]
    grau_divida = m["grau_divida"]
    comp_endiv = m["comp_endiv"]
    imob_pl = m["imob_pl"]
    imob_rec_nc = m["imob_rec_nc"]
    lc = m["lc"]
    ccl = m["ccl"]
    return [
        {
            "titulo": "Participação de capital de terceiros (PCT)",
            "valor": _format_br_numero(pct, 6) if pct is not None else "—",
            "porcentagem": _format_pct_br(pct),
            "filhos": [
                _campo_indicador("PC", pc),
                _campo_indicador("PNC", pnc),
                _campo_indicador("PL", pl),
            ],
        },
        {
            "titulo": "Grau da dívida (garantia PL / capital de terceiros)",
            "valor": _format_br_numero(grau_divida, 4) if grau_divida is not None else "—",
            "porcentagem": "—",
            "filhos": [
                _campo_indicador("PL", pl),
                _campo_indicador("PC", pc),
                _campo_indicador("PNC", pnc),
            ],
        },
        {
            "titulo": "Composição do endividamento",
            "valor": _format_br_numero(comp_endiv, 6) if comp_endiv is not None else "—",
            "porcentagem": _format_pct_br(comp_endiv),
            "filhos": [
                _campo_indicador("PC", pc),
                _campo_indicador("PNC", pnc),
            ],
        },
        {
            "titulo": "Imobilização do patrimônio líquido",
            "valor": _format_br_numero(imob_pl, 6) if imob_pl is not None else "—",
            "porcentagem": _format_pct_br(imob_pl),
            "filhos": [
                _campo_indicador("IMOB", imobilizado),
                _campo_indicador("INV", investimentos),
                _campo_indicador("INT", intangivel),
                _campo_indicador("PL", pl),
            ],
        },
        {
            "titulo": "Imobilização dos recursos não correntes",
            "valor": _format_br_numero(imob_rec_nc, 6) if imob_rec_nc is not None else "—",
            "porcentagem": _format_pct_br(imob_rec_nc),
            "filhos": [
                _campo_indicador("IMOB", imobilizado),
                _campo_indicador("INV", investimentos),
                _campo_indicador("INT", intangivel),
                _campo_indicador("PL", pl),
                _campo_indicador("PNC", pnc),
            ],
        },
        {
            "titulo": "Índice de liquidez corrente (LC)",
            "valor": _format_br_numero(lc, 4) if lc is not None else "—",
            "porcentagem": "—",
            "filhos": [
                _campo_indicador("AC", ac),
                _campo_indicador("PC", pc),
            ],
        },
        {
            "titulo": "Capital circulante líquido (CCL)",
            "valor": _format_br_numero(ccl),
            "porcentagem": "—",
            "filhos": [
                _campo_indicador("AC", ac),
                _campo_indicador("PC", pc),
            ],
        },
    ]


def _grupos_indicadores_resultado_de_m(m: dict[str, object]) -> list[dict[str, object]]:
    """ROA, ROE, giro do ativo e margem bruta conforme fórmulas pedidas."""
    lpa = m["lpa"]
    at = m["at"]
    res_ex = m["res_ex"]
    rbo = m["rbo"]
    pl = m["pl"]
    roa = m["roa"]
    roe = m["roe"]
    giro_ativo = m["giro_ativo"]
    margem_bruta = m["margem_bruta"]
    return [
        {
            "titulo": "Retorno sobre o Ativo (ROA)",
            "valor": _format_br_numero(roa, 6) if roa is not None else "—",
            "porcentagem": _format_pct_br(roa),
            "filhos": [
                _campo_indicador("LPA", lpa),
                _campo_indicador("AT", at),
            ],
        },
        {
            "titulo": "Retorno sobre o Patrimônio Líquido (ROE)",
            "valor": _format_br_numero(roe, 6) if roe is not None else "—",
            "porcentagem": _format_pct_br(roe),
            "filhos": [
                _campo_indicador("RE", res_ex),
                _campo_indicador("PL", pl),
            ],
        },
        {
            "titulo": "Giro do Ativo (GA)",
            "valor": _format_br_numero(giro_ativo, 6) if giro_ativo is not None else "—",
            "porcentagem": _format_pct_br(giro_ativo),
            "filhos": [
                _campo_indicador("RE", res_ex),
                _campo_indicador("AT", at),
            ],
        },
        {
            "titulo": "Margem bruta",
            "valor": _format_br_numero(margem_bruta, 6) if margem_bruta is not None else "—",
            "porcentagem": _format_pct_br(margem_bruta),
            "filhos": [
                _campo_indicador("RBO", rbo),
                _campo_indicador("RE", res_ex),
            ],
        },
    ]


def _estrutura_blocos_indicadores(arvore: list) -> list[dict[str, object]]:
    """
    Blocos do painel: patrimoniais + resultado (mesmo ``components.html``).
    Cada bloco tem ``titulo`` e ``grupos`` (lista com título, valor, %, filhos).
    """
    m = _computos_indicadores_patrimoniais(arvore)
    return [
        {"titulo": "Indicadores patrimoniais", "grupos": _grupos_indicadores_patrimoniais_de_m(m)},
        {"titulo": "Indicadores de Resultado", "grupos": _grupos_indicadores_resultado_de_m(m)},
    ]


def _html_grupos_indicadores_detalhes(grupos: list[dict[str, object]]) -> str:
    """Lista de ``<details>`` por indicador (nível folha do painel)."""
    esc = html_module.escape
    out: list[str] = []
    for g in grupos:
        tit = esc(str(g["titulo"]))
        val = esc(str(g["valor"]))
        pct = esc(str(g["porcentagem"]))
        filhos_html: list[str] = []
        for rotulo, vtxt in g["filhos"]:
            d = esc(str(rotulo))
            vt = esc(str(vtxt)) if vtxt not in (None, "") else "—"
            filhos_html.append(
                f'<div class="dctb-ind-fonte"><span class="dctb-lbl">{d}</span>'
                f'<span class="dctb-val">{vt}</span></div>'
            )
        out.append(
            f'<details class="dctb-node dctb-ind-item" data-depth="1">'
            f'<summary class="dctb-sum" style="padding-left:14px">'
            f'<span class="dctb-ico">&#128196;</span>'
            f'<span class="dctb-conta"></span>'
            f'<span class="dctb-desc">{tit}</span>'
            f'<span class="dctb-val"><span class="dctb-ind-val-main">{val}</span><br/>'
            f'<span class="dctb-ind-pct">{pct}</span></span>'
            f"</summary>"
            f'<div class="dctb-kids">{"".join(filhos_html)}</div>'
            f"</details>"
        )
    return "".join(out)


def _html_corpo_indicadores_painel(blocos: list[dict[str, object]]) -> str:
    """Árvore <details>: raiz + secções (patrimoniais / resultado) + itens."""
    esc = html_module.escape
    secoes: list[str] = []
    for bloco in blocos:
        tit_sec = esc(str(bloco["titulo"]))
        grupos = bloco["grupos"]
        inner = _html_grupos_indicadores_detalhes(grupos)
        secoes.append(
            f'<details class="dctb-node dctb-ind-secao" open data-depth="0">'
            f'<summary class="dctb-sum" style="padding-left:12px">'
            f'<span class="dctb-ico">&#128193;</span>'
            f'<span class="dctb-conta"></span>'
            f'<span class="dctb-desc">{tit_sec}</span>'
            f'<span class="dctb-val"><span class="dctb-ind-pct">&nbsp;</span></span>'
            f"</summary>"
            f'<div class="dctb-kids">{inner}</div>'
            f"</details>"
        )
    return (
        f'<details class="dctb-node dctb-ind-root" open data-depth="0">'
        f'<summary class="dctb-sum" style="padding-left:10px">'
        f'<span class="dctb-ico">&#128193;</span>'
        f'<span class="dctb-conta"></span>'
        f'<span class="dctb-desc">Indicadores</span>'
        f'<span class="dctb-val"><span class="dctb-ind-pct" style="font-weight:700">Valor</span><br/>'
        f'<span class="dctb-ind-pct">%</span></span>'
        f"</summary>"
        f'<div class="dctb-kids">{"".join(secoes)}</div>'
        f"</details>"
    )


def _render_painel_indicadores_patrimoniais(arvore: list) -> None:
    """Painel em árvore (HTML); filhos = apenas siglas dos campos usados no cálculo."""
    blocos = _estrutura_blocos_indicadores(arvore)
    inner = _html_corpo_indicadores_painel(blocos)
    n_grupos = sum(len(b["grupos"]) for b in blocos)  # type: ignore[arg-type]
    n_filhos = sum(
        len(g["filhos"]) for b in blocos for g in b["grupos"]  # type: ignore[arg-type]
    )
    altura = min(920, max(360, 200 + n_grupos * 42 + n_filhos * 22))
    full = (
        _css_hierarquia_demonstrativos()
        + '<div class="dctb-hier-wrap dctb-hier--ind">'
        + '<div class="dctb-hier-head"><span class="dctb-h-spacer">·</span>'
        + "<span></span><span>Indicador</span>"
        + '<span class="dctb-col-num">Valor / %</span></div>'
        + '<div class="dctb-hier-body">'
        + inner
        + "</div></div>"
    )
    components.html(full, height=altura, scrolling=True)


class DashboardDemonstrativosContabeis:
    """Painel de demonstrativos contábeis com filtros e tabela de resultados."""

    TIPO_RELATORIO = "DemonstrativosContabeis"

    def __init__(self, auth: AuthResult):
        self.auth = auth

    def _load_empresas(self):
        from django.contrib.auth.models import User
        from app.db_GDF.Public.models import Empresa

        try:
            user = User.objects.get(username=self.auth.username)
        except User.DoesNotExist:
            st.error("Usuário inválido.")
            return None

        if self.auth.acesso_total and self.auth.cod_cliente:
            qs = Empresa.objects.filter(
                gdfcliente__cod_cliente=self.auth.cod_cliente
            ).distinct()
        else:
            qs = Empresa.objects.filter(usuarioempresa__user=user).distinct()
            if self.auth.cod_cliente:
                qs = qs.filter(gdfcliente__cod_cliente=self.auth.cod_cliente)

        if not qs.exists():
            st.error("Nenhuma empresa vinculada ao usuário.")
            return None
        return list(qs.order_by("cod_empresa"))

    def run(self) -> bool:
        if not self.auth.cod_cliente:
            st.error("Cliente não identificado no token. Selecione um cliente no GDF e abra o dashboard novamente.")
            return False

        empresas = self._load_empresas()
        if not empresas:
            return False

        st.sidebar.markdown("### Sessão")
        st.sidebar.markdown(f"**{self.auth.username}**")
        if self.auth.cod_cliente:
            st.sidebar.markdown(f"**{self.auth.cod_cliente}**")

        st.markdown("## Demonstrativos contábeis")

        st.markdown("**Filtros**")
        labels = [
            f"{e.cod_empresa} — {(e.fantasia or e.razao or '')[:40]}"
            for e in empresas
        ]
        idx = st.selectbox(
            "Empresa",
            range(len(empresas)),
            format_func=lambda i: labels[i],
            key="dem_cont_empresa",
        )
        i_bukrs = empresas[idx].cod_empresa

        agora = datetime.now()
        st.caption(
            "Período SAP enviado à RFC como I_MONTH_B (inicial) e I_MONTH_V (final), com I_YEAR — "
            "ex.: 1 a 12 ou 1 a 16. Uma única chamada à RFC."
        )
        col_pi, col_pf, col_y = st.columns(3)
        with col_pi:
            i_month_b = st.number_input(
                "I_MONTH_B (inicial)",
                min_value=1,
                max_value=_MAX_PERIODO_SAP,
                value=1,
                step=1,
                help="Período inicial (RFC I_MONTH_B).",
                key="dem_cont_i_month_b",
            )
        with col_pf:
            i_month_v = st.number_input(
                "I_MONTH_V (final)",
                min_value=1,
                max_value=_MAX_PERIODO_SAP,
                value=12,
                step=1,
                help="Período final (RFC I_MONTH_V). Igual ao inicial = um período só.",
                key="dem_cont_i_month_v",
            )
        with col_y:
            i_year = st.number_input(
                "Ano (exercício)",
                min_value=1900,
                max_value=9999,
                value=int(agora.year),
                step=1,
                key="dem_cont_i_year",
            )

        i_month_b_rfc = int(i_month_b)
        i_month_v_rfc = int(i_month_v)
        i_year_rfc = int(i_year)

        col_pc, col_ver = st.columns(2)
        with col_pc:
            i_ktopl = st.text_input(
                "Plano de contas",
                max_chars=4,
                placeholder="ex.: INT",
                key="dem_cont_ktopl",
            )
        with col_ver:
            i_versn = st.text_input(
                "Versão",
                max_chars=4,
                placeholder="ex.: 0001",
                key="dem_cont_versn",
            )

        consultar = st.button("Consultar", type="primary", key="dem_cont_consultar")

        st.divider()

        filtros_snapshot = (
            str(i_bukrs).strip(),
            int(i_year_rfc),
            int(i_month_b_rfc),
            int(i_month_v_rfc),
            (i_ktopl or "").strip(),
            (i_versn or "").strip(),
        )

        jwt_token = (st.query_params.get("token") or "").strip()
        if consultar:
            if not jwt_token:
                st.error("Token do dashboard ausente. Abra os demonstrativos contábeis pelo menu do GDF.")
            else:
                api_url = demonstrativos_contabeis_api_url()
                payload = {
                    "i_bukrs": filtros_snapshot[0],
                    "i_year": filtros_snapshot[1],
                    "i_month_b": filtros_snapshot[2],
                    "i_month_v": filtros_snapshot[3],
                    "i_ktopl": filtros_snapshot[4],
                    "i_versn": filtros_snapshot[5],
                }
                with st.spinner("Carregando dados…"):
                    out = post_json_bearer(api_url, jwt_token, payload)

                if not out.get("sucesso"):
                    st.error(out.get("mensagem") or "Não foi possível carregar os dados.")
                    r_err = (out.get("r_return") or "").strip()
                    if r_err:
                        with st.expander("Detalhe (R_RETURN)"):
                            st.text(r_err[:8000] + ("…" if len(r_err) > 8000 else ""))
                else:
                    st.success(out.get("mensagem") or "Dados atualizados.")
                    arv = out.get("arvore")
                    if not isinstance(arv, list):
                        arv = []
                    st.session_state["dem_cont_arvore"] = arv
                    st.session_state["dem_cont_total_nos"] = int(
                        out.get("total_nos") or _contar_nos_local(arv)
                    )
                    st.session_state["dem_cont_r_return"] = (out.get("r_return") or "").strip()
                    st.session_state["dem_cont_snapshot"] = filtros_snapshot
                    st.session_state["dem_cont_atualizado"] = pd.Timestamp.now().strftime(
                        "%d/%m/%Y %H:%M:%S"
                    )

        if "dem_cont_arvore" not in st.session_state:
            if not consultar:
                st.info("Selecione os filtros acima e clique em **Consultar** para carregar os dados.")
            return True

        arvore = st.session_state["dem_cont_arvore"]
        if not isinstance(arvore, list):
            arvore = []
            st.session_state["dem_cont_arvore"] = arvore

        snap = st.session_state.get("dem_cont_snapshot")
        if snap is not None and snap != filtros_snapshot:
            st.warning(
                "Os filtros mudaram em relação à última consulta. A visualização abaixo usa **os dados já carregados**; "
                "clique em **Consultar** para buscar de novo no SAP."
            )

        if not arvore:
            st.warning("Nenhum nó retornado no JSON de R_RETURN para a última consulta.")
            r_raw = (st.session_state.get("dem_cont_r_return") or "").strip()
            if r_raw:
                with st.expander("R_RETURN (bruto)"):
                    st.text(r_raw[:8000] + ("…" if len(r_raw) > 8000 else ""))
            st.caption(
                f"Última atualização: {st.session_state.get('dem_cont_atualizado', '—')}"
            )
            return True

        snap_an = st.session_state.get("dem_cont_snapshot")
        if isinstance(snap_an, tuple) and len(snap_an) >= 4:
            _y, _mb, _mv = int(snap_an[1]), int(snap_an[2]), int(snap_an[3])
        else:
            _y, _mb, _mv = int(agora.year), int(i_month_b_rfc), int(i_month_v_rfc)
        consulta_key = ""
        if isinstance(snap_an, tuple) and len(snap_an) >= 6:
            consulta_key = "|".join(str(x) for x in snap_an[:6])

#------------------------------------------------------------------------------------------------
# Balanço Patrimonial
#------------------------------------------------------------------------------------------------
        st.markdown("### Balanço Patrimonial")
        modo_viz = st.radio(
            "Visualização",
            ["Hierárquica (estilo SAP)", "Tabela plana"],
            horizontal=True,
            key="dem_cont_modo_viz",
            help="Alterar esta opção não consulta o SAP de novo — só muda como os dados em memória são exibidos.",
        )

        if modo_viz.startswith("Hierárquica"):
            c1, c2, c3 = st.columns([1, 1, 1])
            with c1:
                expandir_todos = st.checkbox(
                    "Expandir todos os níveis",
                    value=False,
                    key="dem_cont_hier_expandir_todos",
                )
            with c2:
                niveis_abertos = st.number_input(
                    "Níveis abertos inicialmente",
                    min_value=0,
                    max_value=12,
                    value=1,
                    step=1,
                    help="Com 'Expandir todos' desligado, abre automaticamente até este nível (0 = só raiz fechada).",
                    key="dem_cont_hier_niveis_abertos",
                )
            with c3:
                st.caption("Use ▶ nas pastas para abrir grupos (Ativo, Passivo, etc.).")
            _render_painel_hierarquia(
                arvore,
                expandir_todos=bool(expandir_todos),
                profundidade_aberta=int(niveis_abertos),
            )
        else:
            flat = _flatten_arvore_demonstrativo(arvore)
            df = pd.DataFrame(flat)
            st.dataframe(df, use_container_width=True, height=min(520, 120 + 28 * min(len(df), 15)))

#------------------------------------------------------------------------------------------------
# Indicadores patrimoniais (árvore; filhos = só siglas dos campos usados no cálculo)
#------------------------------------------------------------------------------------------------
        #st.markdown(
        #    '<div style="margin-top:-1.35rem;margin-bottom:0.1rem">'
        #    '<h4 style="margin:0;padding:0;font-size:1.125rem;font-weight:600;">'
        #    "Indicadores"
        #    "</h4></div>",
        #    unsafe_allow_html=True,
        #)
        st.divider()
        st.markdown("#### Indicadores")
        _render_painel_indicadores_patrimoniais(arvore)

        return True
