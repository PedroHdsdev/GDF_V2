"""Gráficos para Dashboard de Vendas – dinâmicos e alinhados ao tema GDF."""
import altair as alt
import streamlit as st
import pandas as pd
import numpy as np

from .base import GraficoBase
from . import lists_vendas as tl

try:
    from config.constants import CHART_PALETTE, CHART_COLORS
except ImportError:
    CHART_PALETTE = ["#0ea5e9", "#f97316", "#8b5cf6", "#ec4899", "#14b8a6"]
    CHART_COLORS = {"primary": "#0ea5e9", "secondary": "#f97316"}


class Grafico_pizza(GraficoBase):
    def __init__(self, df):
        super().__init__(df, tl)

    def G_pizza(self, valor_x, valor_y, titulo=None):
        if valor_x not in self.df.columns:
            st.error(f"Coluna '{valor_x}' não existe no DataFrame.")
            return
        if valor_y not in self.df.columns:
            st.error(f"Métrica '{valor_y}' não existe no DataFrame.")
            return

        df_valid = self.df[[valor_x, valor_y]].copy()
        df_valid = df_valid.dropna(subset=[valor_x, valor_y])
        df_valid[valor_y] = pd.to_numeric(df_valid[valor_y], errors="coerce")
        df_valid = df_valid.dropna(subset=[valor_y])

        if df_valid.empty:
            st.warning("Não há dados válidos para plotar.")
            return

        df_agg = df_valid.groupby(valor_x, as_index=False)[valor_y].sum()
        df_agg = df_agg.sort_values(by=valor_y, ascending=False).head(10)
        df_agg['percent'] = df_agg[valor_y] / df_agg[valor_y].sum()

        if titulo is None:
            titulo = f"{valor_y} por {valor_x}"

        selection = alt.selection_single(on="click", empty="none", fields=[valor_x])
        chart = alt.Chart(df_agg).mark_arc(innerRadius=55, strokeWidth=2).encode(
            theta=alt.Theta(field='percent', type='quantitative'),
            color=alt.condition(
                selection,
                alt.Color(field=valor_x, type='nominal', scale=alt.Scale(range=CHART_PALETTE), legend=alt.Legend(title=valor_x)),
                alt.value("lightgray"),
            ),
            tooltip=[
                alt.Tooltip(valor_x, title=valor_x),
                alt.Tooltip(valor_y, title=valor_y, format=',.2f'),
                alt.Tooltip('percent:Q', title='Percentual', format='.2%')
            ]
        ).properties(title=titulo, height=400).add_selection(selection).interactive()
        st.altair_chart(chart, use_container_width=True)


class Grafico_barra(GraficoBase):
    def __init__(self, df):
        super().__init__(df, tl)

    def G_barra(self, valor_x, valor_y, ordenacao, titulo=None):
        if valor_x not in self.df.columns:
            st.error(f"Coluna '{valor_x}' não existe no DataFrame.")
            return
        if valor_y not in self.df.columns:
            st.error(f"Métrica '{valor_y}' não existe no DataFrame.")
            return

        df_valid = self.df[[valor_x, valor_y]].copy()
        df_valid = df_valid.dropna(subset=[valor_x, valor_y])
        df_valid[valor_y] = pd.to_numeric(df_valid[valor_y], errors="coerce")
        df_valid = df_valid.dropna(subset=[valor_y])

        if df_valid.empty:
            st.warning("Não há dados válidos para plotar.")
            return

        df_agg = df_valid.groupby(valor_x, as_index=False)[valor_y].sum()

        if ordenacao == "Do maior para o menor":
            df_rank = df_agg.sort_values(by=valor_y, ascending=False).head(10)
        else:
            df_rank = df_agg.sort_values(by=valor_y, ascending=True).head(10)

        if titulo is None:
            titulo = f"{valor_y} por {valor_x}"

        total_val = df_rank[valor_y].sum()
        df_rank = df_rank.copy()
        df_rank['pct'] = (df_rank[valor_y] / total_val * 100).round(1) if total_val else 0
        fmt = ',.0f' if 'Quantidade' in valor_y else ',.2f'
        selection = alt.selection_single(on="click", empty="none", fields=[valor_x])
        chart = (
            alt.Chart(df_rank)
            .mark_bar(cornerRadius=6, strokeWidth=2)
            .encode(
                x=alt.X(valor_y, type='quantitative', title=valor_y),
                y=alt.Y(
                    valor_x,
                    type='nominal',
                    title=valor_x,
                    sort=df_rank[valor_x].tolist()
                ),
                color=alt.condition(
                    selection,
                    alt.value(CHART_COLORS.get("secondary", "#f97316")),
                    alt.Color(valor_x, type='nominal', scale=alt.Scale(range=CHART_PALETTE), legend=None),
                ),
                opacity=alt.condition(selection, alt.value(1), alt.value(0.85)),
                tooltip=[
                    alt.Tooltip(valor_x, title=valor_x),
                    alt.Tooltip(valor_y, title=valor_y, format=fmt),
                    alt.Tooltip('pct:Q', title='% do total', format='.1f'),
                ],
            )
            .properties(title=titulo, height=600)
            .add_selection(selection)
            .interactive()
        )
        st.altair_chart(chart, use_container_width=True)


class Grafico_linha(GraficoBase):
    def __init__(self, df):
        super().__init__(df, tl)

    def G_multiplas_metricas(self, coluna_data='mes_nome', coluna_ano='ano',
                             metricas=None, filtro_anos=None, filtro_meses=None,
                             periodo="Mensal", titulo=None):

        df_valid = self.df.copy()
        if filtro_anos:
            df_valid = df_valid[df_valid[coluna_ano].isin(filtro_anos)]

        meses_para_sort = None  # lista de meses para ordenar o eixo X
        if periodo == "Mensal" and filtro_meses:
            if isinstance(filtro_meses, (list, tuple)):
                meses_list = [int(m) for m in filtro_meses]
                df_valid = df_valid[df_valid['mes'].isin(meses_list)]
                meses_para_sort = sorted(meses_list)
            else:
                mes_ini, mes_fim = 1, 12
        else:
            mes_ini, mes_fim = 1, 12

        if metricas is None:
            metricas = [c for c in df_valid.columns if c not in [coluna_data, coluna_ano, 'mes']]

        if periodo == "Mensal":
            agg_dict = {}
            for m in metricas:
                if m in tl.Metrica_valores_p:
                    agg_dict[m] = 'sum'
                else:
                    agg_dict[m] = 'sum'

            df_grouped = df_valid.groupby(
                [coluna_ano, 'mes', coluna_data],
                as_index=False
            ).agg(agg_dict)

            if 'M. Contribuição' in df_grouped.columns:
                df_grouped['M. Contribuição'] = np.where(
                    df_grouped['Faturamento'] != 0,
                    (df_grouped['M. Contribuição'] / df_grouped['Faturamento']) * 100,
                    0
                )

            df_long = df_grouped.melt(
                id_vars=[coluna_ano, 'mes', coluna_data],
                value_vars=metricas,
                var_name='Métrica',
                value_name='Valor'
            )

            _meses_pt = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
                         7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
            meses_seq = meses_para_sort if meses_para_sort else list(range(mes_ini, mes_fim + 1))
            x_sort = [_meses_pt[m] for m in meses_seq]

        else:
            agg_dict = {}
            for m in metricas:
                if m in tl.Metrica_valores_p:
                    agg_dict[m] = 'sum'
                else:
                    agg_dict[m] = 'sum'

            df_grouped = df_valid.groupby([coluna_ano], as_index=False).agg(agg_dict)

            if 'M. Contribuição' in df_grouped.columns:
                df_grouped['M. Contribuição'] = np.where(
                    df_grouped['Faturamento'] != 0,
                    (df_grouped['M. Contribuição'] / df_grouped['Faturamento']) * 100,
                    0
                )

            df_grouped[coluna_data] = df_grouped[coluna_ano].astype(str)
            df_long = df_grouped.melt(
                id_vars=[coluna_data, coluna_ano],
                value_vars=metricas,
                var_name='Métrica',
                value_name='Valor'
            )
            x_sort = None

        df_long = df_long.apply(self.format_valor, axis=1)

        if periodo == "Mensal":
            chart = (
                alt.Chart(df_long)
                .mark_line(point=alt.OverlayMarkDef(size=90, filled=True), strokeWidth=2.5)
                .encode(
                    x=alt.X(f'{coluna_data}:N', title='Mês', sort=x_sort),
                    y=alt.Y('Valor_plot:Q', title='Valor', scale=alt.Scale(padding=0.1)),
                    color=alt.Color('Métrica:N', legend=alt.Legend(title='Métrica'), scale=alt.Scale(range=CHART_PALETTE)),
                    strokeDash=alt.StrokeDash(f'{coluna_ano}:N', legend=alt.Legend(title='Ano')),
                    tooltip=[
                        alt.Tooltip(f'{coluna_ano}:N', title='Ano'),
                        alt.Tooltip(f'{coluna_data}:N', title='Mês'),
                        alt.Tooltip('Métrica:N', title='Métrica'),
                        alt.Tooltip('Valor:Q', title='Valor', format=',.2f'),
                        alt.Tooltip('label:N', title='Exibição')
                    ]
                )
                .properties(height=420, title=titulo)
            )
            labels = chart.mark_text(align='center', baseline='bottom', dy=-5, fontSize=10).encode(
                text=alt.Text('label:N')
            )
            final_chart = (chart + labels).properties(height=420, title=titulo).interactive()
        else:
            chart = (
                alt.Chart(df_long)
                .mark_bar(cornerRadius=6, size=50)
                .encode(
                    x=alt.X(f'{coluna_data}:N', title='Ano'),
                    y=alt.Y('Valor_plot:Q', title='Valor', scale=alt.Scale(padding=0.1)),
                    color=alt.Color('Métrica:N', legend=alt.Legend(title='Métrica'), scale=alt.Scale(range=CHART_PALETTE)),
                    tooltip=[
                        alt.Tooltip(f'{coluna_ano}:N', title='Ano'),
                        alt.Tooltip('Métrica:N', title='Métrica'),
                        alt.Tooltip('Valor:Q', title='Valor', format=',.2f'),
                        alt.Tooltip('label:N', title='Exibição')
                    ]
                )
                .properties(height=400, title=titulo)
            )
            labels = chart.mark_text(align='center', baseline='bottom', dy=-3, fontSize=10).encode(
                text=alt.Text('label:N')
            )
            final_chart = (chart + labels).properties(height=400, title=titulo).interactive()
        st.altair_chart(final_chart, use_container_width=True)


_MESES_PT = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']


class Grafico_comparacao(GraficoBase):
    def __init__(self, df):
        super().__init__(df, tl)

    def G_comparacao_unificado(self, metrica="Faturamento", anos_select=None, mes_select=None):
        """Comparativo unificado: vários meses+1 ano OU 1 mês+vários anos OU vários de ambos."""
        df = self.df.copy()
        if metrica not in df.columns:
            st.error(f"Métrica '{metrica}' não existe.")
            return
        df[metrica] = pd.to_numeric(df[metrica], errors='coerce').fillna(0)

        fmt_tooltip = ',.0f' if metrica == "Quantidade Total" else ',.2f'
        fmt_text = ',.0f' if metrica == "Quantidade Total" else ',.2f'

        n_anos = len(anos_select or [])
        n_meses = len(mes_select or [])

        if n_anos < 1 or n_meses < 1:
            st.warning("Selecione pelo menos 1 ano e 1 mês.")
            return

        df_comp = df[(df['ano'].isin(anos_select)) & (df['mes'].isin(mes_select))].copy()
        if df_comp.empty:
            st.warning("Nenhum dado encontrado para a combinação selecionada.")
            return

        # Modo 1: 1 ano + vários meses → barras por mês
        if n_anos == 1 and n_meses >= 2:
            df_agg = df_comp.groupby('mes', as_index=False)[metrica].sum()
            df_agg = df_agg.sort_values('mes')
            df_agg['label'] = df_agg['mes'].apply(lambda x: _MESES_PT[x - 1])
            x_sort = df_agg['label'].tolist()
            titulo = f"Comparativo de meses ({anos_select[0]}) - {metrica}"
            media_val = df_agg[metrica].mean()
            df_agg['media'] = media_val
            chart = (
                alt.Chart(df_agg)
                .mark_bar(cornerRadius=8)
                .encode(
                    x=alt.X('label:N', title='Mês', sort=x_sort),
                    y=alt.Y(f'{metrica}:Q', title=metrica),
                    color=alt.Color('label:N', scale=alt.Scale(range=CHART_PALETTE), legend=None),
                    tooltip=[
                        alt.Tooltip('label:N', title='Mês'),
                        alt.Tooltip(f'{metrica}:Q', title=metrica, format=fmt_tooltip),
                        alt.Tooltip('media:Q', title='Média período', format=fmt_tooltip),
                    ]
                )
                .properties(height=400, title=titulo)
            )
            rule = alt.Chart(pd.DataFrame({'y': [media_val]})).mark_rule(color=CHART_COLORS.get('secondary', '#f97316'), strokeDash=[4, 2]).encode(y='y:Q')
            text = chart.mark_text(align='center', baseline='bottom', dy=-5).encode(text=alt.Text(f'{metrica}:Q', format=fmt_text))
            st.altair_chart((chart + rule + text), use_container_width=True)
            return

        # Modo 2: vários anos + 1 mês → barras por ano
        if n_anos >= 2 and n_meses == 1:
            mes_nome = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'][mes_select[0] - 1]
            df_agg = df_comp.groupby('ano', as_index=False)[metrica].sum()
            df_agg = df_agg.sort_values('ano')
            df_agg['label'] = df_agg['ano'].astype(str)
            anos_sort = df_agg['label'].tolist()
            titulo = f"{mes_nome} - Comparação entre anos - {metrica}"
            media_val = df_agg[metrica].mean()
            df_agg['media'] = media_val
            chart = (
                alt.Chart(df_agg)
                .mark_bar(cornerRadius=8)
                .encode(
                    x=alt.X('label:N', title='Ano', sort=anos_sort),
                    y=alt.Y(f'{metrica}:Q', title=metrica),
                    color=alt.Color('label:N', scale=alt.Scale(range=CHART_PALETTE), legend=None),
                    tooltip=[
                        alt.Tooltip('label:N', title='Ano'),
                        alt.Tooltip(f'{metrica}:Q', title=metrica, format=fmt_tooltip),
                        alt.Tooltip('media:Q', title='Média', format=fmt_tooltip),
                    ]
                )
                .properties(height=400, title=titulo)
            )
            rule = alt.Chart(pd.DataFrame({'y': [media_val]})).mark_rule(color=CHART_COLORS.get('secondary', '#f97316'), strokeDash=[4, 2]).encode(y='y:Q')
            text = chart.mark_text(align='center', baseline='bottom', dy=-5).encode(text=alt.Text(f'{metrica}:Q', format=fmt_text))
            st.altair_chart((chart + rule + text), use_container_width=True)
            return

        # Modo 3: vários anos + vários meses → barras por (mês, ano), mesmos meses lado a lado
        df_agg = df_comp.groupby(['ano', 'mes'], as_index=False)[metrica].sum()
        df_agg['mes_nome'] = df_agg['mes'].apply(lambda x: _MESES_PT[x - 1])
        df_agg['label'] = df_agg['mes_nome'] + '/' + df_agg['ano'].astype(str)
        df_agg = df_agg.sort_values(['mes', 'ano'])  # Jan/21, Jan/22, Fev/21, Fev/22...
        x_sort = df_agg['label'].tolist()
        titulo = f"Comparativo - {metrica}"
        media_val = df_agg[metrica].mean()
        df_agg['media'] = media_val
        chart = (
            alt.Chart(df_agg)
            .mark_bar(cornerRadius=8)
            .encode(
                x=alt.X('label:N', title='Período', sort=x_sort),
                y=alt.Y(f'{metrica}:Q', title=metrica),
                color=alt.Color('label:N', scale=alt.Scale(range=CHART_PALETTE), legend=None),
                tooltip=[
                    alt.Tooltip('label:N', title='Período'),
                    alt.Tooltip(f'{metrica}:Q', title=metrica, format=fmt_tooltip),
                    alt.Tooltip('media:Q', title='Média', format=fmt_tooltip),
                ]
            )
            .properties(height=400, title=titulo)
        )
        rule = alt.Chart(pd.DataFrame({'y': [media_val]})).mark_rule(color=CHART_COLORS.get('secondary', '#f97316'), strokeDash=[4, 2]).encode(y='y:Q')
        text = chart.mark_text(align='center', baseline='bottom', dy=-5).encode(text=alt.Text(f'{metrica}:Q', format=fmt_text))
        st.altair_chart((chart + rule + text), use_container_width=True)

    def G_comparacao_anos_meses(self, tipo_comparacao="Mês vs Mês", metrica="Faturamento",
                                anos_select=None, mes_select=None, titulo=None):

        df = self.df.copy()

        if metrica not in df.columns:
            st.error(f"Métrica '{metrica}' não existe.")
            return

        df[metrica] = pd.to_numeric(df[metrica], errors='coerce').fillna(0)

        if titulo is None:
            titulo = f"{tipo_comparacao} - {metrica}"

        fmt_tooltip = ',.0f' if metrica == "Quantidade Total" else ',.2f'
        fmt_text = ',.0f' if metrica == "Quantidade Total" else ',.2f'

        if tipo_comparacao == "Mês vs Mês":
            if not mes_select or len(mes_select) < 2:
                st.warning("Selecione 2 ou mais meses.")
                return

            df_comp = df[df['mes'].isin(mes_select)].copy()
            if anos_select:
                df_comp = df_comp[df_comp['ano'].isin(anos_select)]
            if df_comp.empty:
                st.warning("Nenhum dado encontrado para os meses e ano selecionados.")
                return
            df_agg = df_comp.groupby('mes', as_index=False)[metrica].sum()
            df_agg = df_agg.sort_values('mes')
            df_agg['mes_nome'] = df_agg['mes'].apply(lambda x: _MESES_PT[x - 1])
            x_sort = df_agg['mes_nome'].tolist()

            chart = (
                alt.Chart(df_agg)
                .mark_bar(cornerRadius=8)
                .encode(
                    x=alt.X('mes_nome:N', title='Mês', sort=x_sort),
                    y=alt.Y(f'{metrica}:Q', title=metrica),
                    color=alt.Color('mes_nome:N', scale=alt.Scale(scheme='blues'), legend=None),
                    tooltip=[
                        alt.Tooltip('mes_nome:N', title='Mês'),
                        alt.Tooltip(f'{metrica}:Q', title=metrica, format=fmt_tooltip)
                    ]
                )
                .properties(height=400, title=titulo)
            )

            text = chart.mark_text(align='center', baseline='bottom', dy=-5).encode(
                text=alt.Text(f'{metrica}:Q', format=fmt_text)
            )

            st.altair_chart((chart + text), use_container_width=True)

        elif tipo_comparacao == "Ano vs Ano":
            if not anos_select or len(anos_select) < 2:
                st.warning("Selecione 2 ou mais anos.")
                return

            df_comp = df[df['ano'].isin(anos_select)].copy()
            df_agg = df_comp.groupby('ano', as_index=False)[metrica].sum()
            df_agg = df_agg.sort_values('ano')
            anos_sort = df_agg['ano'].astype(str).tolist()

            chart = (
                alt.Chart(df_agg)
                .mark_bar(cornerRadius=8)
                .encode(
                    x=alt.X('ano:N', title='Ano', sort=anos_sort),
                    y=alt.Y(f'{metrica}:Q', title=metrica),
                    color=alt.Color('ano:N', scale=alt.Scale(scheme='blues'), legend=None),
                    tooltip=[
                        alt.Tooltip('ano:N', title='Ano'),
                        alt.Tooltip(f'{metrica}:Q', title=metrica, format=fmt_tooltip)
                    ]
                )
                .properties(height=400, title=titulo)
            )

            text = chart.mark_text(align='center', baseline='bottom', dy=-5).encode(
                text=alt.Text(f'{metrica}:Q', format=fmt_text)
            )

            st.altair_chart((chart + text), use_container_width=True)

        elif tipo_comparacao == "Mês em Anos Diferentes":
            if not mes_select or len(mes_select) != 1:
                st.warning("Selecione exatamente 1 mês.")
                return

            if not anos_select or len(anos_select) < 2:
                st.warning("Selecione 2 ou mais anos.")
                return

            l_v_mes = mes_select[0]
            df_comp = df[(df['mes'] == l_v_mes) & (df['ano'].isin(anos_select))].copy()
            df_agg = df_comp.groupby('ano', as_index=False)[metrica].sum()
            df_agg = df_agg.sort_values('ano')

            l_v_mes_nome = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'][l_v_mes - 1]
            l_v_titulo = f"{l_v_mes_nome} - Comparação Anual: {metrica}"

            chart = (
                alt.Chart(df_agg)
                .mark_bar(cornerRadius=8)
                .encode(
                    x=alt.X('ano:N', title='Ano', sort=df_agg['ano'].astype(str).tolist()),
                    y=alt.Y(f'{metrica}:Q', title=metrica),
                    color=alt.Color('ano:N', scale=alt.Scale(scheme='blues'), legend=None),
                    tooltip=[
                        alt.Tooltip('ano:N', title='Ano'),
                        alt.Tooltip(f'{metrica}:Q', title=metrica, format=fmt_tooltip)
                    ]
                )
                .properties(height=400, title=l_v_titulo)
            )

            text = chart.mark_text(align='center', baseline='bottom', dy=-5).encode(
                text=alt.Text(f'{metrica}:Q', format=fmt_text)
            )

            st.altair_chart((chart + text), use_container_width=True)
