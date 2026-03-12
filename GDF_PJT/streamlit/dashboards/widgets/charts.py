"""Widgets de gráficos reutilizáveis."""
import streamlit as st
import pandas as pd
import altair as alt

try:
    from config.constants import CHART_PALETTE, CHART_COLORS
except ImportError:
    CHART_PALETTE = ["#0ea5e9", "#f97316", "#8b5cf6", "#ec4899", "#14b8a6"]
    CHART_COLORS = {"primary": "#0ea5e9", "secondary": "#f97316", "success": "#10b981"}

_MESES_NOMES = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']


def render_evolucao_temporal(df_merged, grafico_mod, tipo_relatorio: str):
    """Tab: Evolução temporal - Como as métricas evoluem ao longo do tempo."""
    metricas_opcoes = [
        ("Faturamento", "Valor total das NF-e"),
        ("Total Impostos", "Soma de impostos (ICMS, PIS, COFINS, IPI)"),
        ("Valor Líquido", "Faturamento menos impostos"),
        ("Quantidade Total", "Quantidade de itens"),
    ]
    if tipo_relatorio == "Compras":
        metricas_opcoes.append(("Credito_Tributario_Total", "Créditos tributários (ICMS, PIS, COFINS)"))

    st.markdown("**O que você quer analisar?**")
    st.caption("Evolução mês a mês ou total anual. Use zoom (arrastar no gráfico) e passe o mouse para ver valores. Ideal para tendências e sazonalidade.")

    col_filtro1, col_filtro2, col_filtro3 = st.columns([2, 2, 2])

    metricas_labels = [m[0] for m in metricas_opcoes]

    with col_filtro1:
        metricas_selecionadas = st.multiselect(
            "Métricas a acompanhar",
            options=metricas_labels,
            default=["Faturamento"],
            key="tab1_metricas",
            help="Selecione uma ou mais. Cada métrica aparece como uma linha no gráfico.",
        )

    with col_filtro2:
        anos_disponiveis = sorted(df_merged['ano'].unique())
        default_anos = anos_disponiveis[-2:] if len(anos_disponiveis) >= 2 else anos_disponiveis
        anos_selecionados = st.multiselect(
            "Anos",
            options=anos_disponiveis,
            default=default_anos,
            key="tab1_anos",
            help="Compare a evolução em um ou mais anos. Múltiplos anos = uma linha por ano.",
        )

    with col_filtro3:
        periodo_value = st.radio(
            "Visão",
            options=["Mensal", "Anual"],
            format_func=lambda x: "Mês a mês" if x == "Mensal" else "Total por ano",
            horizontal=True,
            key="tab1_periodo",
            help="Mensal: linha do tempo. Anual: barras com total de cada ano.",
        )

    filtro_meses = None
    if periodo_value == "Mensal" and anos_selecionados:
        meses_no_df = sorted(df_merged[df_merged['ano'].isin(anos_selecionados)]['mes'].unique())
        if meses_no_df:
            meses_sel = st.multiselect(
                "Filtrar meses (opcional)",
                options=meses_no_df,
                default=meses_no_df,
                format_func=lambda x: _MESES_NOMES[x - 1],
                key="tab1_meses",
                help="Deixe todos para ver o ano completo, ou escolha meses específicos.",
            )
            if meses_sel:
                filtro_meses = sorted(meses_sel)

    if metricas_selecionadas and anos_selecionados:
        try:
            g_linha = grafico_mod.Grafico_linha(df_merged)
            g_linha.G_multiplas_metricas(
                coluna_data='mes_nome',
                coluna_ano='ano',
                metricas=metricas_selecionadas,
                filtro_anos=anos_selecionados,
                filtro_meses=filtro_meses,
                periodo=periodo_value,
                titulo=f"Evolução {periodo_value} - {', '.join(metricas_selecionadas)}"
            )
        except Exception as err_graph:
            st.error(f"❌ Erro ao gerar gráfico: {str(err_graph)}")
    else:
        st.info("👆 Selecione pelo menos uma métrica e um ano para ver o gráfico.")


def render_comparativo(df_merged, grafico_mod, tipo_relatorio: str = "Vendas"):
    """Tab: Comparativo - Compare períodos lado a lado."""
    metricas_base = ["Faturamento", "Total Impostos", "Valor Líquido", "Quantidade Total"]
    if tipo_relatorio == "Compras":
        metricas_base = metricas_base + ["Credito_Tributario_Total"]

    st.markdown("**O que você quer comparar?**")
    st.caption("Compare meses no mesmo ano ou o mesmo mês em anos diferentes. Clique na legenda (se houver) e use o tooltip para detalhes.")

    col_metrica, col_filtros = st.columns([1, 2])

    with col_metrica:
        metrica_comp = st.selectbox(
            "Métrica",
            options=metricas_base,
            key="metrica_comp",
            help="Valor a ser comparado.",
        )

    with col_filtros:
        anos_disponiveis = sorted(df_merged['ano'].unique())
        meses_disponiveis = sorted(df_merged['mes'].unique())

        anos_select = st.multiselect(
            "Anos",
            options=anos_disponiveis,
            default=anos_disponiveis[-1:] if anos_disponiveis else [],
            key="comp_anos",
            help="1 ano ou vários anos.",
        )
        mes_select = st.multiselect(
            "Meses",
            options=meses_disponiveis,
            default=meses_disponiveis[:3] if len(meses_disponiveis) >= 3 else meses_disponiveis,
            format_func=lambda x: _MESES_NOMES[x - 1],
            key="comp_meses",
            help="1 mês ou vários meses.",
        )

    if metrica_comp:
        try:
            g_comp = grafico_mod.Grafico_comparacao(df_merged)
            g_comp.G_comparacao_unificado(
                metrica=metrica_comp,
                anos_select=anos_select,
                mes_select=mes_select,
            )
        except Exception as err_comp:
            st.error(f"❌ Erro ao gerar comparativo: {str(err_comp)}")
    else:
        st.info("👆 Selecione uma métrica para ver o comparativo.")


def render_ranking(df_merged, tipo_relatorio: str):
    """Tab: Ranking por Clientes, Cidades ou Fornecedores."""
    st.caption("Maiores por faturamento, quantidade ou impostos.")

    col_rank1, col_rank2, col_rank3 = st.columns([2, 2, 1])

    with col_rank1:
        if tipo_relatorio == "Compras":
            dimensao_rank = "Fornecedores"
        else:
            dimensao_rank = st.selectbox(
                "Dimensão",
                options=["Clientes", "Cidades"],
                key="rank_dimensao",
                help="Clientes: por CNPJ/razão social. Cidades: por município.",
            )

    with col_rank2:
        metrica_rank = st.selectbox(
            "Ordenar por",
            options=["Faturamento", "Quantidade Total", "Total Impostos", "Valor Líquido"],
            key="rank_metrica",
            help="Métrica para ordenar o ranking.",
        )

    with col_rank3:
        top_n = st.slider("Top N", min_value=5, max_value=30, value=10, key="rank_top")

    try:
        df_rank_src = df_merged.copy()
        df_rank_src['Faturamento'] = pd.to_numeric(df_rank_src['Faturamento'], errors='coerce').fillna(0)
        df_rank_src['Quantidade Total'] = pd.to_numeric(df_rank_src['Quantidade Total'], errors='coerce').fillna(0)
        df_rank_src['Total Impostos'] = pd.to_numeric(df_rank_src['Total Impostos'], errors='coerce').fillna(0)
        df_rank_src['Valor Líquido'] = df_rank_src['Faturamento'] - df_rank_src['Total Impostos']

        col_sort = metrica_rank

        if tipo_relatorio == "Compras" or dimensao_rank == "Fornecedores":
            key_cnpj = 'cnpj_fornecedor' if tipo_relatorio == "Compras" else 'cnpj_cliente'
            key_nome = 'nome_fornecedor' if tipo_relatorio == "Compras" else 'nome_cliente'
            df_rank = df_rank_src.dropna(subset=[key_cnpj]).groupby([key_cnpj, key_nome]).agg({
                'Faturamento': 'sum', 'Quantidade Total': 'sum', 'Total Impostos': 'sum', 'Valor Líquido': 'sum'
            }).reset_index()
            df_rank['label'] = df_rank[key_nome].fillna('S/N').str[:40] + ' (' + df_rank[key_cnpj].astype(str).str[-8:] + ')'
            df_rank = df_rank.nlargest(top_n, col_sort)
            total_geral = df_rank_src[col_sort].sum()
            df_rank['pct_total'] = (df_rank[col_sort] / total_geral * 100).round(1) if total_geral else 0

            titulo_eixo = "Fornecedor" if tipo_relatorio == "Compras" else "Cliente"
            titulo_chart = f"Top {top_n} {titulo_eixo}s por {col_sort}"

            chart_rank = alt.Chart(df_rank).mark_bar(cornerRadius=6).encode(
                y=alt.Y('label:N', title=titulo_eixo, sort=alt.EncodingSortField(field=col_sort, order='descending')),
                x=alt.X(f'{col_sort}:Q', title=col_sort),
                color=alt.Color('label:N', scale=alt.Scale(scheme='blues'), legend=None),
                tooltip=[
                    alt.Tooltip('label:N', title=titulo_eixo),
                    alt.Tooltip(f'{col_sort}:Q', title=col_sort, format=',.2f' if col_sort != 'Quantidade Total' else ',.0f'),
                    alt.Tooltip('pct_total:Q', title='% do total', format='.1f'),
                    alt.Tooltip('Faturamento:Q', title='Faturamento', format=',.2f'),
                    alt.Tooltip('Quantidade Total:Q', title='Quantidade', format=',.0f'),
                ]
            ).properties(height=max(300, len(df_rank) * 36), title=titulo_chart)
            st.altair_chart(chart_rank, use_container_width=True)

        elif dimensao_rank == "Cidades":
            df_rank = df_rank_src.dropna(subset=['cidade']).groupby('cidade').agg({
                'Faturamento': 'sum', 'Quantidade Total': 'sum', 'Total Impostos': 'sum'
            }).reset_index()
            df_rank['Valor Líquido'] = df_rank['Faturamento'] - df_rank['Total Impostos']
            df_rank = df_rank.nlargest(top_n, col_sort)
            total_geral = df_rank_src[col_sort].sum()
            df_rank['pct_total'] = (df_rank[col_sort] / total_geral * 100).round(1) if total_geral else 0

            chart_rank = alt.Chart(df_rank).mark_bar(cornerRadius=6).encode(
                y=alt.Y('cidade:N', title='Cidade', sort=alt.EncodingSortField(field=col_sort, order='descending')),
                x=alt.X(f'{col_sort}:Q', title=col_sort),
                color=alt.Color('cidade:N', scale=alt.Scale(scheme='blues'), legend=None),
                tooltip=[
                    alt.Tooltip('cidade:N', title='Cidade'),
                    alt.Tooltip(f'{col_sort}:Q', title=col_sort, format=',.2f' if col_sort != 'Quantidade Total' else ',.0f'),
                    alt.Tooltip('pct_total:Q', title='% do total', format='.1f'),
                    alt.Tooltip('Faturamento:Q', title='Faturamento', format=',.2f'),
                    alt.Tooltip('Quantidade Total:Q', title='Quantidade', format=',.0f'),
                ]
            ).properties(height=max(300, len(df_rank) * 36), title=f"Top {top_n} Cidades por {col_sort}")
            st.altair_chart(chart_rank, use_container_width=True)

    except Exception as err_rank:
        st.error(f"❌ Erro ao gerar ranking: {str(err_rank)}")


def render_grupo_mercadorias(df_produtos):
    """Tab: Grupo de mercadorias."""
    col_grp1, col_grp2 = st.columns(2)

    with col_grp1:
        metrica_grp = st.selectbox(
            "Métrica",
            options=["Faturamento", "Quantidade Total", "Total Impostos"],
            key="grp_metrica"
        )

    with col_grp2:
        top_n = st.slider("Top N produtos", min_value=5, max_value=50, value=10, key="grp_top")

    try:
        df_grp = df_produtos.copy()
        df_grp['valor_total'] = pd.to_numeric(df_grp['valor_total'], errors='coerce').fillna(0)
        df_grp['quantidade'] = pd.to_numeric(df_grp['quantidade'], errors='coerce').fillna(0)

        df_grp = df_grp.groupby('descricao').agg({
            'valor_total': 'sum',
            'quantidade': 'sum'
        }).reset_index()
        df_grp.columns = ['Descrição', 'Faturamento', 'Quantidade Total']
        df_grp['Total Impostos'] = df_grp['Faturamento'] * 0.15

        df_grp = df_grp.nlargest(top_n, metrica_grp)

        chart_grp = alt.Chart(df_grp).mark_bar().encode(
            y=alt.Y('Descrição:N', sort=alt.EncodingSortField(field=metrica_grp, order='descending')),
            x=alt.X(f'{metrica_grp}:Q', title=metrica_grp),
            color=alt.value('#1f77d4'),
            tooltip=[
                alt.Tooltip('Descrição:N', title='Produto'),
                alt.Tooltip(f'{metrica_grp}:Q', title=metrica_grp, format=',.2f' if metrica_grp != 'Quantidade Total' else ',.0f'),
            ]
        ).properties(height=max(300, len(df_grp) * 25), title=f"Top {top_n} Produtos por {metrica_grp}")
        st.altair_chart(chart_grp, use_container_width=True)
    except Exception as err_grp:
        st.error(f"❌ Erro ao gerar grupo de mercadorias: {str(err_grp)}")


def render_por_tipo_pagamento(df_pagamento):
    """Seção: Por tipo de pagamento."""
    st.caption("Tipos de pagamento conforme cadastro em json/Tipo_pagamento.json (código do XML → descrição).")
    if not df_pagamento.empty:
        agg_pag = df_pagamento.groupby("tipo_pagamento_desc").agg(
            quantidade_nfe=("id_identificacao", "nunique"),
            valor_total=("valor_pago", "sum"),
        ).reset_index()
        agg_pag = agg_pag.sort_values("valor_total", ascending=False)

        st.markdown("#### Por quantidade de NF-e")
        chart_pag_qtd = alt.Chart(agg_pag).mark_bar().encode(
            y=alt.Y("tipo_pagamento_desc:N", sort=alt.EncodingSortField(field="quantidade_nfe", order="descending")),
            x=alt.X("quantidade_nfe:Q", title="Quantidade de NF-e"),
            color=alt.value("#2ca02c"),
            tooltip=[
                alt.Tooltip("tipo_pagamento_desc:N", title="Tipo"),
                alt.Tooltip("quantidade_nfe:Q", title="Qtd. NF-e"),
                alt.Tooltip("valor_total:Q", title="Valor (R$)"),
            ],
        ).properties(height=max(300, len(agg_pag) * 32), title="NF-e por tipo de pagamento")
        st.altair_chart(chart_pag_qtd, use_container_width=True)
        with st.expander("Ver tabela por tipo de pagamento"):
            st.dataframe(
                agg_pag.rename(columns={
                    "tipo_pagamento_desc": "Tipo de pagamento",
                    "quantidade_nfe": "Qtd. NF-e",
                    "valor_total": "Valor total (R$)"
                }),
                use_container_width=True
            )
    else:
        st.info("ℹ️ Nenhum dado de pagamento cadastrado nas NF-e do período.")


def render_condicoes_pagamento(df_parcelas, df_merged):
    """Tab: Condições de pagamento mais usadas (Vendas)."""
    if not df_parcelas.empty and "id_identificacao" in df_parcelas.columns:
        df_emissao = df_merged[["id_identificacao", "emissao"]].drop_duplicates()
        df_cp = df_parcelas.merge(df_emissao, on="id_identificacao", how="left")
        emissao_dt = pd.to_datetime(df_cp["emissao"], utc=True).dt.normalize()
        venc_dt = pd.to_datetime(df_cp["data_vencimento"], utc=True).dt.normalize()
        df_cp["dias_prazo"] = (venc_dt - emissao_dt).dt.days
        df_cp["dias_prazo"] = df_cp["dias_prazo"].clip(lower=0)

        def montar_condicao(g):
            g = g.sort_values("numero_parcela")
            dias = g["dias_prazo"].astype(int).tolist()
            n = len(dias)
            if n == 1:
                return "1x à vista" if dias[0] <= 1 else f"1x em {dias[0]} dias"
            s = "/".join(str(d) for d in dias)
            return f"{n}x em {s} dias"

        cond_por_nfe = df_cp.groupby("id_identificacao").apply(montar_condicao).reset_index()
        cond_por_nfe.columns = ["id_identificacao", "condicao"]

        cond_counts = cond_por_nfe["condicao"].value_counts().reset_index()
        cond_counts.columns = ["Condição de pagamento", "Quantidade de NF-e"]
        cond_counts = cond_counts.sort_values("Quantidade de NF-e", ascending=False)

        top_n = st.slider("Top N condições a exibir", min_value=5, max_value=30, value=15, key="cond_pag_top")
        cond_plot = cond_counts.head(top_n)

        chart_cond = alt.Chart(cond_plot).mark_bar().encode(
            y=alt.Y("Condição de pagamento:N", sort=alt.EncodingSortField(field="Quantidade de NF-e", order="descending")),
            x=alt.X("Quantidade de NF-e:Q", title="Quantidade de NF-e"),
            color=alt.value("#1f77d4"),
            tooltip=[alt.Tooltip("Condição de pagamento:N"), alt.Tooltip("Quantidade de NF-e:Q")],
        ).properties(height=max(300, len(cond_plot) * 28), title="Condições de pagamento mais usadas (prazo por parcela)")
        st.altair_chart(chart_cond, use_container_width=True)
    else:
        st.info("ℹ️ Nenhuma parcela cadastrada para analisar condições de pagamento.")


def render_compras_analise(df_merged, df_produtos):
    """Tabs: CFOP, Créditos tributários, Curva ABC (Compras) – dinâmicos."""
    tab_cfop, tab_creditos, tab_abc = st.tabs([
        "📋 Distribuição por CFOP",
        "💰 Créditos tributários",
        "📈 Curva ABC (concentração)",
    ])

    with tab_cfop:
        st.markdown("### Distribuição das compras por CFOP")
        st.caption("Clique no gráfico para destacar; use o tooltip para valor e %.")
        if not df_produtos.empty and 'cfop' in df_produtos.columns:
            df_produtos_copy = df_produtos.copy()
            df_produtos_copy['cfop'] = df_produtos_copy['cfop'].fillna('Sem CFOP').astype(str)
            df_produtos_copy['valor_total'] = pd.to_numeric(df_produtos_copy['valor_total'], errors='coerce').fillna(0)
            cfop_agg = df_produtos_copy.groupby('cfop', as_index=False)['valor_total'].sum()
            cfop_agg = cfop_agg.sort_values('valor_total', ascending=False).head(15)
            total_cfop = cfop_agg['valor_total'].sum()
            cfop_agg['pct'] = (cfop_agg['valor_total'] / total_cfop * 100).round(1) if total_cfop else 0
            selection = alt.selection_single(on="click", empty="none", fields=["cfop"])
            chart_cfop = alt.Chart(cfop_agg).mark_arc(innerRadius=60, strokeWidth=2).encode(
                theta=alt.Theta('valor_total:Q'),
                color=alt.condition(
                    selection,
                    alt.Color('cfop:N', scale=alt.Scale(range=CHART_PALETTE), legend=alt.Legend(title="CFOP")),
                    alt.value("lightgray"),
                ),
                tooltip=[
                    alt.Tooltip('cfop:N', title='CFOP'),
                    alt.Tooltip('valor_total:Q', title='Valor (R$)', format=',.2f'),
                    alt.Tooltip('pct:Q', title='% do total', format='.1f'),
                ],
            ).properties(height=400, title="Compras por CFOP").add_selection(selection).interactive()
            st.altair_chart(chart_cfop, use_container_width=True)
            with st.expander("Ver tabela CFOP"):
                st.dataframe(cfop_agg, use_container_width=True, height=300)
        else:
            st.info("ℹ️ Nenhum CFOP nos itens das NF-e.")

    with tab_creditos:
        st.markdown("### Créditos tributários (ICMS, PIS, COFINS)")
        st.caption("Comparação entre tributos; passe o mouse para valor exato.")
        cred_icms = pd.to_numeric(df_merged['Credito_ICMS'], errors='coerce').fillna(0).sum()
        cred_pis = pd.to_numeric(df_merged['Credito_PIS'], errors='coerce').fillna(0).sum()
        cred_cof = pd.to_numeric(df_merged['Credito_COFINS'], errors='coerce').fillna(0).sum()
        cred_total = pd.to_numeric(df_merged['Credito_Tributario_Total'], errors='coerce').fillna(0).sum()
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Crédito ICMS", f"R$ {cred_icms:,.2f}")
        col2.metric("Crédito PIS", f"R$ {cred_pis:,.2f}")
        col3.metric("Crédito COFINS", f"R$ {cred_cof:,.2f}")
        col4.metric("Total créditos", f"R$ {cred_total:,.2f}")
        df_cred = pd.DataFrame({
            'Tributo': ['ICMS', 'PIS', 'COFINS'],
            'Valor': [cred_icms, cred_pis, cred_cof]
        })
        df_cred['pct'] = (df_cred['Valor'] / cred_total * 100).round(1) if cred_total else 0
        chart_cred = alt.Chart(df_cred).mark_bar(cornerRadius=6).encode(
            x=alt.X('Tributo:N', title='Tributo'),
            y=alt.Y('Valor:Q', title='Valor (R$)'),
            color=alt.Color('Tributo:N', scale=alt.Scale(range=CHART_PALETTE[:3]), legend=None),
            tooltip=[
                alt.Tooltip('Tributo:N', title='Tributo'),
                alt.Tooltip('Valor:Q', title='Valor (R$)', format=',.2f'),
                alt.Tooltip('pct:Q', title='% do total', format='.1f'),
            ],
        ).properties(height=300, title="Créditos por tributo").interactive()
        st.altair_chart(chart_cred, use_container_width=True)

    with tab_abc:
        st.markdown("### Curva ABC – Concentração de compras por fornecedor")
        st.caption("Classe A: até 80%; B: 80–95%; C: restante. Clique na barra para destacar.")
        df_abc = df_merged.dropna(subset=['cnpj_fornecedor']).groupby(['cnpj_fornecedor', 'nome_fornecedor']).agg(
            valor=('Faturamento', 'sum')
        ).reset_index()
        df_abc['valor'] = pd.to_numeric(df_abc['valor'], errors='coerce').fillna(0)
        df_abc = df_abc[df_abc['valor'] > 0].sort_values('valor', ascending=False)
        if not df_abc.empty:
            total = df_abc['valor'].sum()
            df_abc['pct_acumulado'] = df_abc['valor'].cumsum() / total * 100
            df_abc['classe'] = pd.cut(df_abc['pct_acumulado'], bins=[0, 80, 95, 100], labels=['A', 'B', 'C'])
            df_abc['label'] = df_abc['cnpj_fornecedor'].astype(str) + ' - ' + df_abc['nome_fornecedor'].fillna('S/N').str[:35]
            df_abc_plot = df_abc.head(25)
            abc_colors = [CHART_COLORS.get("success", "#10b981"), CHART_COLORS.get("secondary", "#f97316"), "#ef4444"]
            selection = alt.selection_single(on="click", empty="none", fields=["label"])
            chart_abc = alt.Chart(df_abc_plot).mark_bar(cornerRadius=4, strokeWidth=2).encode(
                y=alt.Y('label:N', sort=alt.EncodingSortField(field='valor', order='descending'), title='Fornecedor'),
                x=alt.X('valor:Q', title='Valor compras (R$)'),
                color=alt.condition(
                    selection,
                    alt.value(CHART_COLORS.get("secondary", "#f97316")),
                    alt.Color('classe:N', scale=alt.Scale(domain=['A', 'B', 'C'], range=abc_colors), legend=alt.Legend(title="Classe")),
                ),
                opacity=alt.condition(selection, alt.value(1), alt.value(0.9)),
                tooltip=[
                    alt.Tooltip('label:N', title='Fornecedor'),
                    alt.Tooltip('valor:Q', title='Valor (R$)', format=',.2f'),
                    alt.Tooltip('pct_acumulado:Q', title='% Acumulado', format='.1f'),
                    alt.Tooltip('classe:N', title='Classe ABC'),
                ]
            ).properties(height=max(350, len(df_abc_plot) * 24), title="Curva ABC – A (até 80%), B (80–95%), C (restante)").add_selection(selection).interactive()
            st.altair_chart(chart_abc, use_container_width=True)
            st.caption("Classe A: até 80% do valor; B: 80–95%; C: acima de 95%.")
        else:
            st.info("ℹ️ Sem dados de fornecedor para Curva ABC.")
