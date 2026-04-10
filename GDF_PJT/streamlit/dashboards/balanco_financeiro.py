"""Dashboard Balanço financeiro — integração com SAP (/PRCIT/GDF_RFC_BALANCE) via backend Django."""
from __future__ import annotations

import html as html_module
from datetime import datetime

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from core.auth import AuthResult
from core.django_backend import balanco_financeiro_api_url, post_json_bearer

from .balanco_financeiro_analise import render_analise_gerencial

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
    """Linhas de contas RACCT (filhas lógicas do nó de balanço, sem filhos na árvore)."""
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
            ccell = f'<span class="bal-conta bal-conta-acc" title="RACCT">{racct}</span>'
        else:
            ccell = '<span class="bal-conta bal-conta-acc bal-conta-vazia">—</span>'
        dcell = f'<span class="bal-desc bal-desc-acc">{txt_acc}</span>' if txt_acc else (
            '<span class="bal-desc bal-desc-acc bal-desc-vazia">—</span>'
        )
        partes.append(
            f'<div class="bal-acc-row" style="padding-left:{pad}px">'
            f'<span class="bal-ico bal-ico-acc">&#8226;</span>{ccell}{dcell}'
            f'<span class="bal-val">{val}</span></div>'
        )
    return f'<div class="bal-acc-block" aria-label="Contas contábeis">{"".join(partes)}</div>'


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
        titulo_linha = f"Linha balanço · id {node.get('id', '') or '—'}"
        if stufe is not None and str(stufe).strip() != "":
            titulo_linha += f" · nível {stufe}"
        titulo_linha_esc = html_module.escape(titulo_linha, quote=True)
        tem_filhos_arvore = len(filhos) > 0
        tem_contas = len(contas) > 0
        tem_expansivel = tem_filhos_arvore or tem_contas

        if conta_raw:
            conta_cell = f'<span class="bal-conta" title="{titulo_linha_esc}">{conta}</span>'
        else:
            conta_cell = f'<span class="bal-conta bal-conta-vazia" title="{titulo_linha_esc}">—</span>'
        desc_cell = f'<span class="bal-desc">{texto}</span>' if texto else f'<span class="bal-desc bal-desc-vazia">{nid}</span>'
        val_cell = f'<span class="bal-val">{valor}</span>'

        if tem_expansivel:
            aberto = " open" if (expandir_todos or depth < profundidade_aberta_padrao) else ""
            icone = "&#128193;"  # pasta
            spad = 6 + depth * 12
            inner_filhos = "".join(render_no(c, depth + 1) for c in filhos)
            inner_acc = _accounts_para_html(contas, depth + 1)
            inner = f'<div class="bal-kids">{inner_filhos}{inner_acc}</div>'
            return (
                f'<details class="bal-node" data-depth="{depth}"{aberto}>'
                f'<summary class="bal-sum" style="padding-left:{spad}px"><span class="bal-ico">{icone}</span>'
                f'{conta_cell}{desc_cell}{val_cell}</summary>'
                f"{inner}</details>"
            )
        icone = "&#128196;"  # documento
        pad = max(0, depth) * 18
        return (
            f'<div class="bal-leaf" style="padding-left:{pad}px" data-depth="{depth}">'
            f'<span class="bal-leaf-row"><span class="bal-ico">{icone}</span>'
            f'{conta_cell}{desc_cell}{val_cell}</span></div>'
        )

    corpo = "".join(render_no(n, 0) for n in nodes if isinstance(n, dict))
    return f"""<div class="bal-hier-root">{corpo}</div>"""


def _css_hierarquia_balanco() -> str:
    return """
<style>
.bal-hier-wrap {
  font-family: system-ui, "Segoe UI", Roboto, sans-serif;
  font-size: 13px;
  border: 1px solid rgba(80, 80, 120, 0.35);
  border-radius: 6px;
  overflow: hidden;
  background: var(--background-color, #fff);
  color: var(--text-color, #1a1a1a);
}
.bal-hier-head {
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
.bal-hier-head .bal-col-num { text-align: right; }
.bal-hier-head .bal-h-spacer { visibility: hidden; width: 22px; }
.bal-hier-body {
  max-height: min(72vh, 900px);
  overflow: auto;
  padding: 6px 8px 12px;
}
.bal-node { margin: 0; border-left: 2px solid rgba(46, 74, 111, 0.2); margin-left: 6px; padding-left: 4px; }
.bal-node > .bal-sum {
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
.bal-node > .bal-sum:hover { background: rgba(46, 74, 111, 0.08); }
.bal-node > .bal-sum::-webkit-details-marker { display: none; }
.bal-kids { margin-left: 8px; padding-left: 4px; border-left: 1px dashed rgba(46, 74, 111, 0.25); }
.bal-leaf { padding: 4px 8px; margin: 1px 0; border-radius: 4px; }
.bal-leaf:hover { background: rgba(46, 74, 111, 0.06); }
.bal-leaf-row {
  display: grid;
  grid-template-columns: 22px minmax(88px, 12%) 1fr minmax(100px, 22%);
  gap: 6px 10px;
  align-items: center;
}
.bal-ico { font-size: 15px; line-height: 1; opacity: 0.92; }
.bal-conta {
  font-family: "Consolas", "Monaco", ui-monospace, monospace;
  font-size: 12px;
  color: #2c5282;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.bal-conta-vazia { color: #a0aec0; }
.bal-desc { min-width: 0; word-break: break-word; font-weight: 500; }
.bal-desc-vazia { color: #718096; font-weight: 400; }
.bal-val {
  font-variant-numeric: tabular-nums;
  text-align: right;
  justify-self: end;
  font-family: "Consolas", "Monaco", monospace;
  white-space: nowrap;
}
.bal-acc-block {
  margin-top: 4px;
  padding-top: 4px;
  border-top: 1px dashed rgba(46, 74, 111, 0.2);
}
.bal-acc-row {
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
.bal-acc-row:hover { background: rgba(46, 74, 111, 0.05); }
.bal-ico-acc { font-size: 11px; color: #718096; text-align: center; }
.bal-conta-acc { color: #2d5a3d; }
.bal-desc-acc { font-weight: 400; }
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
        _css_hierarquia_balanco()
        + '<div class="bal-hier-wrap">'
        + '<div class="bal-hier-head"><span class="bal-h-spacer">·</span>'
        + "<span>Linha / RACCT</span><span>Descrição</span>"
        + '<span class="bal-col-num">Tot. período</span></div>'
        + '<div class="bal-hier-body">'
        + inner
        + "</div></div>"
    )
    n = _contar_nos_local(arvore)
    altura = min(920, max(280, 120 + min(n, 120) * 5))
    components.html(full, height=altura, scrolling=True)


def _flatten_arvore_balanco(nodes: list, depth: int = 0) -> list[dict]:
    """Desdobra a árvore (linhas de balanço + contas em ``accounts``) para tabela plana."""
    rows: list[dict] = []
    for n in nodes:
        if not isinstance(n, dict):
            continue
        rows.append(
            {
                "tipo": "balanço",
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
            rows.extend(_flatten_arvore_balanco(ch, depth + 1))
    return rows


class DashboardBalancoFin:
    """Painel de balanço financeiro com filtros e tabela de resultados."""

    TIPO_RELATORIO = "BalancoFin"

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

        st.markdown("## Balanço financeiro")

        st.markdown("**Filtros**")
        labels = [
            f"{e.cod_empresa} — {(e.fantasia or e.razao or '')[:40]}"
            for e in empresas
        ]
        idx = st.selectbox(
            "Empresa",
            range(len(empresas)),
            format_func=lambda i: labels[i],
            key="balanco_fin_empresa",
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
                key="balanco_fin_i_month_b",
            )
        with col_pf:
            i_month_v = st.number_input(
                "I_MONTH_V (final)",
                min_value=1,
                max_value=_MAX_PERIODO_SAP,
                value=12,
                step=1,
                help="Período final (RFC I_MONTH_V). Igual ao inicial = um período só.",
                key="balanco_fin_i_month_v",
            )
        with col_y:
            i_year = st.number_input(
                "Ano (exercício)",
                min_value=1900,
                max_value=9999,
                value=int(agora.year),
                step=1,
                key="balanco_fin_i_year",
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
                key="balanco_fin_ktopl",
            )
        with col_ver:
            i_versn = st.text_input(
                "Versão",
                max_chars=4,
                placeholder="ex.: 0001",
                key="balanco_fin_versn",
            )

        consultar = st.button("Consultar", type="primary", key="balanco_fin_consultar")

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
                st.error("Token do dashboard ausente. Abra o balanço pelo menu do GDF.")
            else:
                api_url = balanco_financeiro_api_url()
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
                    st.session_state["balanco_fin_arvore"] = arv
                    st.session_state["balanco_fin_total_nos"] = int(
                        out.get("total_nos") or _contar_nos_local(arv)
                    )
                    st.session_state["balanco_fin_r_return"] = (out.get("r_return") or "").strip()
                    st.session_state["balanco_fin_snapshot"] = filtros_snapshot
                    st.session_state["balanco_fin_atualizado"] = pd.Timestamp.now().strftime(
                        "%d/%m/%Y %H:%M:%S"
                    )

        if "balanco_fin_arvore" not in st.session_state:
            if not consultar:
                st.info("Selecione os filtros acima e clique em **Consultar** para carregar os dados.")
            return True

        arvore = st.session_state["balanco_fin_arvore"]
        if not isinstance(arvore, list):
            arvore = []
            st.session_state["balanco_fin_arvore"] = arvore

        snap = st.session_state.get("balanco_fin_snapshot")
        if snap is not None and snap != filtros_snapshot:
            st.warning(
                "Os filtros mudaram em relação à última consulta. A visualização abaixo usa **os dados já carregados**; "
                "clique em **Consultar** para buscar de novo no SAP."
            )

        if not arvore:
            st.warning("Nenhum nó retornado no JSON de R_RETURN para a última consulta.")
            r_raw = (st.session_state.get("balanco_fin_r_return") or "").strip()
            if r_raw:
                with st.expander("R_RETURN (bruto)"):
                    st.text(r_raw[:8000] + ("…" if len(r_raw) > 8000 else ""))
            st.caption(
                f"Última atualização: {st.session_state.get('balanco_fin_atualizado', '—')}"
            )
            return True

        snap_an = st.session_state.get("balanco_fin_snapshot")
        if isinstance(snap_an, tuple) and len(snap_an) >= 4:
            _y, _mb, _mv = int(snap_an[1]), int(snap_an[2]), int(snap_an[3])
        else:
            _y, _mb, _mv = int(agora.year), int(i_month_b_rfc), int(i_month_v_rfc)
        consulta_key = ""
        if isinstance(snap_an, tuple) and len(snap_an) >= 6:
            consulta_key = "|".join(str(x) for x in snap_an[:6])

        render_analise_gerencial(
            arvore,
            ano=_y,
            mes_ini=_mb,
            mes_fim=_mv,
            consulta_key=consulta_key,
        )

        st.divider()
        st.markdown("### Detalhamento da árvore (RFC)")
        total_nos = int(
            st.session_state.get("balanco_fin_total_nos") or _contar_nos_local(arvore)
        )
        st.metric("Nós na árvore", total_nos)

        st.markdown("#### Resultado")
        st.caption(
            "Visualização apenas nos dados da última consulta (sem nova chamada RFC). "
            "A árvore segue ``children`` do JSON (formato recursivo ABAP) ou o montado a partir de "
            "``parent_id`` (lista plana). Ao expandir, aparecem sublinhas e, por último, contas RACCT em ``accounts``."
        )
        modo_viz = st.radio(
            "Visualização",
            ["Hierárquica (estilo SAP)", "Tabela plana"],
            horizontal=True,
            key="balanco_modo_viz",
            help="Alterar esta opção não consulta o SAP de novo — só muda como os dados em memória são exibidos.",
        )

        if modo_viz.startswith("Hierárquica"):
            c1, c2, c3 = st.columns([1, 1, 1])
            with c1:
                expandir_todos = st.checkbox(
                    "Expandir todos os níveis",
                    value=False,
                    key="balanco_hier_expandir_todos",
                )
            with c2:
                niveis_abertos = st.number_input(
                    "Níveis abertos inicialmente",
                    min_value=0,
                    max_value=12,
                    value=2,
                    step=1,
                    help="Com 'Expandir todos' desligado, abre automaticamente até este nível (0 = só raiz fechada).",
                    key="balanco_hier_niveis_abertos",
                )
            with c3:
                st.caption("Use ▶ nas pastas para abrir grupos (Ativo, Passivo, etc.).")
            _render_painel_hierarquia(
                arvore,
                expandir_todos=bool(expandir_todos),
                profundidade_aberta=int(niveis_abertos),
            )
        else:
            flat = _flatten_arvore_balanco(arvore)
            df = pd.DataFrame(flat)
            st.dataframe(df, use_container_width=True, height=min(520, 120 + 28 * min(len(df), 15)))

        with st.expander("Árvore JSON (R_RETURN parseado)"):
            st.json(arvore)

        st.caption(
            f"Última atualização (RFC): {st.session_state.get('balanco_fin_atualizado', '—')}"
        )
        return True
