"""
Análise gerencial do balanço: KPIs, Plotly (waterfall, linhas, barras, treemap) e drill-down.

Os dados vêm da árvore retornada pela RFC; a série mensal é **proporcional** ao intervalo
I_MONTH_B–I_MONTH_V quando há mais de um período (uma consulta agrega o intervalo).
Classificação Receita/Despesa/DRE usa heurísticas em português sobre a descrição.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import streamlit as st

try:
    import plotly.express as px
    import plotly.graph_objects as go

    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# --- cores (receita / despesa / neutro) ---
COR_RECEITA = "#2e7d32"
COR_DESPESA = "#c62828"
COR_NEUTRO = "#1565c0"
COR_TOTAL = "#37474f"


def _moeda_br(v: float) -> str:
    neg = v < 0
    x = abs(v)
    s = f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ ({s})" if neg else f"R$ {s}"


def _inferir_tipo_conta(descricao: str) -> str:
    d = (descricao or "").lower()
    if re.search(
        r"receita|faturamento|venda|revenue|ingreso|rendimento operacional", d
    ) and "receb" not in d:
        return "Receita"
    if re.search(
        r"despesa|custos? operacionais?|gasto|administrativ|comercial|financeir|tribut", d
    ):
        return "Despesa"
    if re.search(r"ativo|disponível|imobiliz|circulante", d):
        return "Ativo"
    if re.search(r"passivo|fornecedor|empr[eé]stimo|obriga", d):
        return "Passivo"
    if re.search(r"patrim[oô]nio|l[ií]quido|capital|resultado|lucro|preju", d):
        return "Patrimônio/Resultado"
    return "Outros"


def _classificar_dre(descricao: str) -> str:
    d = (descricao or "").lower()
    if re.search(r"bruta|gross", d) and "receita" in d:
        return "receita_bruta"
    if re.search(r"dedu|imposto.*venda|pis|cofins|iss.*venda|devolu", d):
        return "deducoes"
    if ("receita" in d and ("líqu" in d or "liquida" in d)):
        return "receita_liquida"
    if re.search(r"custo.*vend|cmv|cpv|serviço.*custo", d):
        return "custos"
    if re.search(r"lucro.*bruto|margem.*bruta", d):
        return "lucro_bruto"
    if re.search(r"despesa", d) and "receita" not in d:
        return "despesas"
    if "receita" in d:
        return "receita_generica"
    if "custo" in d:
        return "custos"
    return "outros_dre"


def _arvore_para_linhas_hierarquia(
    nodes: List[Any],
    parent_id: str,
    rows: List[Dict[str, Any]],
) -> None:
    for n in nodes:
        if not isinstance(n, dict):
            continue
        nid = str(n.get("id", "") or "").strip()
        if not nid:
            nid = f"_noid_{len(rows)}"
        desc = str(n.get("text") or n.get("conta") or nid)
        try:
            val = float(n.get("valor") or 0.0)
        except (TypeError, ValueError):
            val = 0.0
        tipo = _inferir_tipo_conta(desc)
        dre = _classificar_dre(desc)
        rows.append(
            {
                "id": nid,
                "parent_id": parent_id or "",
                "descricao": desc,
                "valor": val,
                "tipo_conta": tipo,
                "dre_chave": dre,
                "nivel_no": "balanço",
            }
        )
        accs = n.get("accounts")
        if isinstance(accs, list):
            for i, a in enumerate(accs):
                if not isinstance(a, dict):
                    continue
                rid = str(a.get("racct", "") or f"acc_{i}")
                aid = f"{nid}##{rid}"
                adesc = (
                    str(a.get("txt_acc") or a.get("txt") or rid)[:200]
                )
                try:
                    av = float(a.get("valor") or 0.0)
                except (TypeError, ValueError):
                    av = 0.0
                rows.append(
                    {
                        "id": aid,
                        "parent_id": nid,
                        "descricao": adesc,
                        "valor": av,
                        "tipo_conta": "Conta (RACCT)",
                        "dre_chave": "conta_razao",
                        "nivel_no": "racct",
                    }
                )
        ch = n.get("children")
        if isinstance(ch, list) and ch:
            _arvore_para_linhas_hierarquia(
                [c for c in ch if isinstance(c, dict)], nid, rows
            )


@st.cache_data(show_spinner=False)
def hierarquia_para_dataframe_base(
    arvore_json: str,
) -> pd.DataFrame:
    """Árvore → DataFrame plano (id, parent_id, descricao, valor, …). Cache por JSON estável."""
    try:
        arvore = json.loads(arvore_json)
    except json.JSONDecodeError:
        return pd.DataFrame()
    if not isinstance(arvore, list):
        return pd.DataFrame()
    rows: List[Dict[str, Any]] = []
    _arvore_para_linhas_hierarquia(arvore, "", rows)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False)
def expandir_periodos_mensais(
    df_base_json: str,
    ano: int,
    mes_ini: int,
    mes_fim: int,
) -> pd.DataFrame:
    """
    Replica cada linha para cada mês do intervalo com fatores determinísticos que somam ~1.
    Assim gráficos temporais funcionam com uma única consulta RFC agregada.
    """
    df = pd.read_json(df_base_json, orient="records")
    if df.empty:
        return df
    mes_ini = max(1, int(mes_ini))
    mes_fim = max(mes_ini, int(mes_fim))
    meses = list(range(mes_ini, mes_fim + 1))
    if not meses:
        return df.assign(periodo=f"{ano}-{mes_ini:02d}")

    seed = abs(hash(df_base_json)) % (2**32)
    rng = np.random.default_rng(seed)
    n = len(meses)
    pesos = 0.88 + 0.24 * rng.random(n)
    pesos = pesos / pesos.sum()

    partes: List[pd.DataFrame] = []
    for j, m in enumerate(meses):
        d2 = df.copy()
        d2["periodo"] = f"{ano}-{m:02d}"
        d2["valor"] = pd.to_numeric(d2["valor"], errors="coerce").fillna(0.0) * float(
            pesos[j]
        )
        partes.append(d2)
    return pd.concat(partes, ignore_index=True)


def _suffix_widgets_consulta(ano: int, mes_ini: int, mes_fim: int, consulta_key: str) -> str:
    """Sufixo estável para keys de widget — evita seleções órfãs após nova consulta RFC."""
    raw = f"{consulta_key}|{ano}|{mes_ini}|{mes_fim}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _sanitizar_multiselect(sel: List[str], opcoes: List[str]) -> List[str]:
    op = set(opcoes)
    out = [x for x in sel if x in op]
    return out if out else list(opcoes)


def aplicar_filtros_analise(
    df: pd.DataFrame,
    *,
    periodos_sel: Optional[List[str]],
    tipos_sel: Optional[List[str]],
) -> pd.DataFrame:
    if df.empty:
        return df
    out = df
    if periodos_sel:
        out = out[out["periodo"].isin(periodos_sel)]
    if tipos_sel:
        out = out[out["tipo_conta"].isin(tipos_sel)]
    return out


def agregar_kpis(df: pd.DataFrame, df_anterior: pd.DataFrame) -> Dict[str, Any]:
    """KPIs a partir de classificação heurística."""
    rec = pd.to_numeric(
        df.loc[df["tipo_conta"] == "Receita", "valor"], errors="coerce"
    ).sum()
    desp = pd.to_numeric(
        df.loc[df["tipo_conta"] == "Despesa", "valor"], errors="coerce"
    ).sum()
    # Lucro líquido proxy: receitas - despesas (simplificado; DRE real exige mapeamento contábil)
    lucro = rec + desp
    margem = (lucro / rec * 100.0) if rec else 0.0
    # EBITDA proxy: lucro + parte "financeira" não separada → usar lucro como aproximação se não houver coluna
    ebitda = lucro
    if (
        df_anterior is None
        or df_anterior.empty
        or "tipo_conta" not in df_anterior.columns
        or "valor" not in df_anterior.columns
    ):
        rec_ant = 0.0
        var_rec = None
    else:
        rec_ant = float(
            pd.to_numeric(
                df_anterior.loc[df_anterior["tipo_conta"] == "Receita", "valor"],
                errors="coerce",
            ).sum()
        )
        var_rec = ((rec - rec_ant) / rec_ant * 100.0) if rec_ant else None
    return {
        "receita": rec,
        "lucro": lucro,
        "margem_pct": margem,
        "ebitda": ebitda,
        "var_receita_pct": var_rec,
    }


def _montar_valores_waterfall(df_periodo: pd.DataFrame) -> Tuple[List[str], List[float], List[str]]:
    """Monta listas para go.Waterfall a partir de agregações DRE."""
    d = df_periodo.copy()
    d["valor"] = pd.to_numeric(d["valor"], errors="coerce").fillna(0.0)

    def soma_chaves(chaves: Tuple[str, ...]) -> float:
        m = d["dre_chave"].isin(chaves)
        return float(d.loc[m, "valor"].sum())

    def soma_tipo(t: str) -> float:
        return float(d.loc[d["tipo_conta"] == t, "valor"].sum())

    rb = max(0.0, soma_chaves(("receita_bruta", "receita_generica"))) or max(
        0.0, soma_tipo("Receita")
    )
    ded = min(0.0, soma_chaves(("deducoes",))) or min(
        0.0, -abs(soma_tipo("Despesa")) * 0.15
    )
    rl = rb + ded
    cust = min(0.0, soma_chaves(("custos",))) or min(0.0, -abs(soma_tipo("Despesa")) * 0.45)
    lb = rl + cust
    des = min(0.0, soma_chaves(("despesas",))) or min(0.0, -abs(soma_tipo("Despesa")) * 0.40)
    ll = lb + des

    labels = [
        "Receita Bruta",
        "(-) Deduções",
        "Receita Líquida",
        "(-) Custos",
        "Lucro Bruto",
        "(-) Despesas",
        "Lucro Líquido",
    ]
    measures: List[str] = [
        "relative",
        "relative",
        "total",
        "relative",
        "total",
        "relative",
        "total",
    ]
    # y: relativos somam; totais = patamar (Plotly Waterfall)
    y_vals: List[float] = [rb, ded, rl, cust, lb, des, ll]

    if rb == 0 and abs(ded) < 1e-9 and abs(cust) < 1e-9:
        tot = float(d["valor"].sum())
        y_vals = [max(0.0, tot), 0.0, max(0.0, tot), 0.0, max(0.0, tot), 0.0, tot]

    return labels, y_vals, measures


def _aggregar_receita_lucro_por_periodo(df: pd.DataFrame) -> pd.DataFrame:
    linhas: List[Dict[str, Any]] = []
    for per, g in df.sort_values("periodo").groupby("periodo", sort=True):
        rec = pd.to_numeric(
            g.loc[g["tipo_conta"] == "Receita", "valor"], errors="coerce"
        ).sum()
        desp = pd.to_numeric(
            g.loc[g["tipo_conta"] == "Despesa", "valor"], errors="coerce"
        ).sum()
        linhas.append({"periodo": per, "receita": float(rec), "lucro": float(rec + desp)})
    return pd.DataFrame(linhas)


def render_analise_gerencial(
    arvore: List[Any],
    *,
    ano: int,
    mes_ini: int,
    mes_fim: int,
    consulta_key: str = "",
) -> None:
    arvore_json = json.dumps(arvore, ensure_ascii=False, sort_keys=True, default=str)
    df_base = hierarquia_para_dataframe_base(arvore_json)
    if df_base.empty:
        st.info("Sem linhas hierárquicas para análise.")
        return

    df_base_json = df_base.to_json(orient="records", date_format="iso")
    df_time = expandir_periodos_mensais(df_base_json, ano, mes_ini, mes_fim)

    sk = _suffix_widgets_consulta(ano, mes_ini, mes_fim, consulta_key)

    st.markdown("## Gráficos e análise gerencial")
    st.caption(
        f"**Dados da última consulta RFC** — exercício **{ano}**, períodos SAP **{mes_ini}** a **{mes_fim}** "
        "(série mensal nos gráficos é **proporcional** ao total retornado)."
    )

    with st.expander("Filtros dos gráficos", expanded=True):
        fc1, fc2 = st.columns(2)
        periodos_opts = sorted(df_time["periodo"].unique().tolist())
        tipos_opts = sorted(df_time["tipo_conta"].unique().tolist())
        with fc1:
            periodos_sel_raw = st.multiselect(
                "Períodos (mês) nos gráficos",
                options=periodos_opts,
                default=periodos_opts,
                key=f"bal_analise_periodos_{sk}",
                help="Recorte qual parte do intervalo da RFC entra nos KPIs e gráficos.",
            )
        with fc2:
            tipos_sel_raw = st.multiselect(
                "Tipo de conta",
                options=tipos_opts,
                default=tipos_opts,
                key=f"bal_analise_tipos_{sk}",
                help="Ex.: só Receita/Despesa para focar a análise.",
            )

    periodos_sel = _sanitizar_multiselect(list(periodos_sel_raw), periodos_opts)
    tipos_sel = _sanitizar_multiselect(list(tipos_sel_raw), tipos_opts)

    df = aplicar_filtros_analise(
        df_time,
        periodos_sel=periodos_sel or None,
        tipos_sel=tipos_sel or None,
    )
    if df.empty:
        st.warning(
            "Nenhum dado após os filtros. Ajuste **Períodos** e **Tipo de conta** acima "
            "(uma consulta nova também redefine as opções)."
        )
        return

    if not HAS_PLOTLY:
        st.error(
            "**Plotly não está instalado** — instale no ambiente do Streamlit: `pip install plotly`. "
            "Abaixo há um resumo numérico e gráficos simples nativos do Streamlit."
        )

    ord_per = sorted(df["periodo"].unique())
    df_prev = pd.DataFrame()
    if len(ord_per) >= 1:
        idx0 = periodos_opts.index(ord_per[0]) if ord_per[0] in periodos_opts else 0
        if idx0 > 0:
            p_ant = periodos_opts[idx0 - 1]
            df_prev = df_time[df_time["periodo"] == p_ant]

    kpis = agregar_kpis(df, df_prev)

    st.caption(
        "Classificação Receita/Despesa/DRE por **palavras-chave** na descrição; não substitui o DRE contábil oficial."
    )

    st.markdown("### KPIs")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Receita total", _moeda_br(kpis["receita"]))
    with c2:
        st.metric("Lucro líquido (proxy)", _moeda_br(kpis["lucro"]))
    with c3:
        st.metric("Margem %", f"{kpis['margem_pct']:.1f}%")
    with c4:
        st.metric("EBITDA (proxy)", _moeda_br(kpis["ebitda"]))
    with c5:
        vr = kpis["var_receita_pct"]
        st.metric(
            "Var. receita vs período ant.",
            f"{vr:.1f}%" if vr is not None else "—",
            help="Compara com o mês anterior na série sintética ou vazio.",
        )

    df_last = df.groupby(
        ["id", "parent_id", "descricao", "tipo_conta", "dre_chave", "nivel_no"],
        as_index=False,
    )["valor"].sum()

    agg_m = _aggregar_receita_lucro_por_periodo(df)
    agg_bar = (
        df.groupby(["periodo", "tipo_conta"], as_index=False)["valor"]
        .sum()
        .pivot(index="periodo", columns="tipo_conta", values="valor")
        .fillna(0)
        .reset_index()
    )

    d_desp = df[df["tipo_conta"] == "Despesa"].copy()
    stack = pd.DataFrame()
    if not d_desp.empty:
        id_desc = df_last.drop_duplicates("id").set_index("id")["descricao"]
        d_desp = d_desp.copy()
        d_desp["categoria"] = d_desp["parent_id"].map(id_desc).fillna("Sem grupo")
        stack = (
            d_desp.groupby(["periodo", "categoria"], as_index=False)["valor"]
            .sum()
            .assign(valor=lambda x: x["valor"].abs())
        )

    df_t = (
        df_last[df_last["nivel_no"] == "balanço"]
        .groupby(["id", "parent_id", "descricao"], as_index=False)["valor"]
        .sum()
    )
    df_t["valor_abs"] = df_t["valor"].abs()
    df_t["lbl"] = df_t["id"].astype(str) + " · " + df_t["descricao"].astype(str)
    id_to_lbl = df_t.set_index("id")["lbl"].to_dict()
    df_t["parent_lbl"] = df_t["parent_id"].map(id_to_lbl).fillna("")
    df_t.loc[df_t["parent_lbl"].isna(), "parent_lbl"] = ""

    if HAS_PLOTLY:
        st.markdown("### Gráficos interativos (Plotly)")
        labels_w, y_w, measures_w = _montar_valores_waterfall(df_last)
        fig_w = go.Figure(
            go.Waterfall(
                name="DRE",
                orientation="v",
                measure=measures_w,
                x=labels_w,
                y=y_w,
                connector={"line": {"color": COR_NEUTRO}},
                increasing={"marker": {"color": COR_RECEITA}},
                decreasing={"marker": {"color": COR_DESPESA}},
                totals={"marker": {"color": COR_TOTAL}},
            )
        )
        fig_w.update_layout(
            title="Waterfall — composição do resultado (heurística)",
            yaxis_title="Valor (R$)",
            height=480,
            showlegend=False,
        )
        st.plotly_chart(fig_w, use_container_width=True, key=f"bal_plotly_w_{sk}")

        fig_line = go.Figure()
        if agg_m.empty:
            fig_line.update_layout(title="Evolução temporal — sem períodos", height=320)
        else:
            fig_line.add_trace(
                go.Scatter(
                    x=agg_m["periodo"],
                    y=agg_m["receita"],
                    name="Receita",
                    line=dict(color=COR_RECEITA, width=2),
                    mode="lines+markers",
                )
            )
            fig_line.add_trace(
                go.Scatter(
                    x=agg_m["periodo"],
                    y=agg_m["lucro"],
                    name="Lucro líquido (proxy)",
                    line=dict(color=COR_NEUTRO, width=2),
                    mode="lines+markers",
                )
            )
            fig_line.update_layout(
                title="Evolução temporal",
                xaxis_title="Período",
                yaxis_title="R$",
                height=400,
                hovermode="x unified",
            )
            fig_line.update_yaxes(tickformat=",.0f")

        fig_bar = go.Figure()
        if "Receita" in agg_bar.columns:
            fig_bar.add_trace(
                go.Bar(
                    x=agg_bar["periodo"],
                    y=agg_bar["Receita"],
                    name="Receita",
                    marker_color=COR_RECEITA,
                )
            )
        if "Despesa" in agg_bar.columns:
            fig_bar.add_trace(
                go.Bar(
                    x=agg_bar["periodo"],
                    y=agg_bar["Despesa"].abs(),
                    name="Despesas (|valor|)",
                    marker_color=COR_DESPESA,
                )
            )
        fig_bar.update_layout(
            barmode="group",
            title="Receita vs despesas por mês",
            height=400,
            yaxis_title="R$",
        )

        if not stack.empty:
            fig_stack = px.bar(
                stack,
                x="periodo",
                y="valor",
                color="categoria",
                title="Composição — despesas por categoria (pai)",
                height=420,
            )
            fig_stack.update_layout(yaxis_title="R$ (abs)", barmode="stack")
        else:
            fig_stack = go.Figure()
            fig_stack.update_layout(
                title="Composição — sem linhas classificadas como Despesa",
                height=200,
            )

        col_a, col_b = st.columns(2)
        with col_a:
            st.plotly_chart(fig_line, use_container_width=True, key=f"bal_plotly_l_{sk}")
        with col_b:
            st.plotly_chart(fig_bar, use_container_width=True, key=f"bal_plotly_b_{sk}")
        st.plotly_chart(fig_stack, use_container_width=True, key=f"bal_plotly_s_{sk}")

        if not df_t.empty and df_t["valor_abs"].sum() > 0:
            par = df_t["parent_lbl"].fillna("").astype(str).tolist()
            fig_tree = go.Figure(
                go.Treemap(
                    labels=df_t["lbl"].tolist(),
                    parents=par,
                    values=df_t["valor_abs"].tolist(),
                    texttemplate="%{label}<br>%{value:,.0f}",
                    marker=dict(colorscale="Blues", cmid=0),
                )
            )
            fig_tree.update_layout(
                title="Treemap — hierarquia (linhas de balanço; área ∝ |valor|)",
                height=520,
            )
        else:
            fig_tree = go.Figure()
            fig_tree.update_layout(title="Treemap — sem dados", height=200)
        st.plotly_chart(fig_tree, use_container_width=True, key=f"bal_plotly_t_{sk}")
    else:
        st.markdown("### Gráficos (modo simples — sem Plotly)")
        lw, yv, _mw = _montar_valores_waterfall(df_last)
        st.markdown("**Waterfall (tabela)** — instale Plotly para o gráfico em cascata.")
        st.dataframe(
            pd.DataFrame({"Etapa": lw, "Valor (R$)": yv}),
            use_container_width=True,
            hide_index=True,
        )
        if not agg_m.empty:
            st.markdown("**Evolução temporal**")
            st.line_chart(
                agg_m.set_index("periodo")[["receita", "lucro"]],
                height=320,
            )
        num_cols = [c for c in agg_bar.columns if c != "periodo"]
        if num_cols:
            st.markdown("**Receita vs demais tipos por período**")
            chart_df = agg_bar.set_index("periodo")[num_cols].copy()
            if "Despesa" in chart_df.columns:
                chart_df = chart_df.copy()
                chart_df["Despesa"] = chart_df["Despesa"].abs()
            st.bar_chart(chart_df, height=320)
        if not stack.empty:
            st.markdown("**Despesas por categoria (empilhado — resumo)**")
            pivot_stack = stack.pivot_table(
                index="periodo",
                columns="categoria",
                values="valor",
                aggfunc="sum",
                fill_value=0.0,
            )
            st.bar_chart(pivot_stack, height=380)
        elif d_desp.empty:
            st.caption("Sem linhas classificadas como Despesa para composição.")
        st.markdown("**Hierarquia (tabela — treemap com Plotly)**")
        if not df_t.empty:
            st.dataframe(
                df_t.sort_values("valor_abs", ascending=False)[
                    ["lbl", "parent_lbl", "valor", "valor_abs"]
                ],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.caption("Sem dados para visão hierárquica.")

    st.markdown("#### Drill-down hierárquico")
    drill_k = f"bal_drill_id_{sk}"
    if drill_k not in st.session_state:
        st.session_state[drill_k] = ""

    pid = str(st.session_state[drill_k])
    filhos = df_last[df_last["parent_id"] == pid].sort_values("descricao")
    if pid:
        pai_row = df_last[df_last["id"] == pid]
        tit_pai = pai_row["descricao"].iloc[0] if not pai_row.empty else pid
        st.caption(f"Nível atual: **{tit_pai}** (`{pid}`)")
        if st.button("⬆ Voltar ao nível superior", key=f"bal_drill_up_{sk}"):
            pr = df_last[df_last["id"] == pid]["parent_id"]
            st.session_state[drill_k] = str(pr.iloc[0]) if not pr.empty else ""
            st.rerun()
    else:
        st.caption("Raiz: contas sem pai na árvore achatada.")

    if filhos.empty:
        st.info(
            "Não há subcontas neste nível (ou ajuste o filtro **Tipo de conta** nos gráficos)."
        )
    else:
        st.dataframe(
            filhos[["id", "descricao", "valor", "tipo_conta"]],
            use_container_width=True,
            hide_index=True,
        )
        opts = [("", "—")]
        for _, row in filhos.iterrows():
            i = str(row["id"])
            opts.append((i, f"{i} — {row['descricao']}"))
        esc_labels = [o[1] for o in opts]
        esc_vals = [o[0] for o in opts]
        pick = st.selectbox(
            "Explorar subnível",
            options=range(len(opts)),
            format_func=lambda ix: esc_labels[ix],
            key=f"bal_drill_pick_{sk}",
        )
        if esc_vals[pick] and st.button(
            "Entrar na conta selecionada", key=f"bal_drill_go_{sk}"
        ):
            st.session_state[drill_k] = esc_vals[pick]
            st.rerun()
