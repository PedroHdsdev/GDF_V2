"""Gráficos para Dashboard de Compras – dinâmicos e alinhados ao tema GDF."""
import altair as alt
import streamlit as st
import pandas as pd
import numpy as np

from .base import GraficoBase
from . import lists_compras as tl

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
    def __init__(self, df, lists_module=None):
        super().__init__(df, lists_module if lists_module is not None else tl)

    def G_multiplas_metricas(self, coluna_data='mes_nome', coluna_ano='ano',
                             metricas=None, filtro_anos=None, filtro_meses=None,
                             periodo="Mensal", titulo=None):

        df_valid = self.df.copy()
        if filtro_anos:
            df_valid = df_valid[df_valid[coluna_ano].isin(filtro_anos)]

        meses_para_sort = None
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
                if m in self.tl.Metrica_valores_p:
                    agg_dict[m] = 'sum'
                else:
                    agg_dict[m] = 'sum'

            df_grouped = df_valid.groupby(
                [coluna_ano, 'mes', coluna_data],
                as_index=False
            ).agg(agg_dict)

            if 'Faturamento' in df_grouped.columns:
                fat = pd.to_numeric(df_grouped['Faturamento'], errors='coerce').fillna(0)
                for _col_m in getattr(self.tl, 'METRICAS_MARGEM_PCT', ()):
                    if _col_m in df_grouped.columns:
                        mg = pd.to_numeric(df_grouped[_col_m], errors='coerce').fillna(0)
                        df_grouped[_col_m] = np.where(fat != 0, (mg / fat) * 100, 0)

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
                if m in self.tl.Metrica_valores_p:
                    agg_dict[m] = 'sum'
                else:
                    agg_dict[m] = 'sum'

            df_grouped = df_valid.groupby([coluna_ano], as_index=False).agg(agg_dict)

            if 'Faturamento' in df_grouped.columns:
                fat = pd.to_numeric(df_grouped['Faturamento'], errors='coerce').fillna(0)
                for _col_m in getattr(self.tl, 'METRICAS_MARGEM_PCT', ()):
                    if _col_m in df_grouped.columns:
                        mg = pd.to_numeric(df_grouped[_col_m], errors='coerce').fillna(0)
                        df_grouped[_col_m] = np.where(fat != 0, (mg / fat) * 100, 0)

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
    def __init__(self, df, lists_module=None):
        super().__init__(df, lists_module if lists_module is not None else tl)

    def G_comparacao_unificado(self, metrica="Faturamento", anos_select=None, mes_select=None):
        """Comparativo: eixo X = meses escolhidos; uma linha por ano (cor). Um único mês → barras por ano."""
        df = self.df.copy()
        if metrica not in df.columns:
            st.error(f"Métrica '{metrica}' não existe.")
            return
        df[metrica] = pd.to_numeric(df[metrica], errors='coerce').fillna(0)

        anos_select = list(anos_select or [])
        mes_select = list(mes_select or [])
        if not anos_select or not mes_select:
            st.warning("Selecione pelo menos 1 ano e 1 mês.")
            return

        df_comp = df[(df['ano'].isin(anos_select)) & (df['mes'].isin(mes_select))].copy()
        if df_comp.empty:
            st.warning("Nenhum dado encontrado para a combinação selecionada.")
            return

        margem_como_pct = metrica in getattr(self.tl, 'METRICAS_MARGEM_PCT', ())
        if margem_como_pct and 'Faturamento' in df_comp.columns:
            df_comp['Faturamento'] = pd.to_numeric(df_comp['Faturamento'], errors='coerce').fillna(0)
            df_comp[metrica] = pd.to_numeric(df_comp[metrica], errors='coerce').fillna(0)
            g = df_comp.groupby(['ano', 'mes'], as_index=False).agg(
                {metrica: 'sum', 'Faturamento': 'sum'}
            )
            fat = g['Faturamento'].to_numpy(dtype=float)
            mg = pd.to_numeric(g[metrica], errors='coerce').fillna(0).to_numpy(dtype=float)
            g[metrica] = np.where(fat != 0, (mg / fat) * 100, 0.0)
            df_agg = g[['ano', 'mes', metrica]]
            y_title = f"{metrica} (% s/ faturamento)"
            fmt_tooltip = ',.2f'
            fmt_text = '.1f'
        else:
            df_agg = df_comp.groupby(['ano', 'mes'], as_index=False)[metrica].sum()
            y_title = metrica
            fmt_tooltip = ',.0f' if metrica == "Quantidade Total" else ',.2f'
            fmt_text = ',.0f' if metrica == "Quantidade Total" else ',.2f'
            if margem_como_pct:
                st.caption("Margem como soma em R$ (sem coluna Faturamento para calcular %).")

        def _mes_label(m):
            try:
                mi = int(m)
                if 1 <= mi <= 12:
                    return _MESES_PT[mi - 1]
            except (TypeError, ValueError):
                pass
            return ''

        df_agg['mes_nome'] = df_agg['mes'].map(_mes_label)
        df_agg['ano_str'] = df_agg['ano'].astype(str)
        meses_ord = sorted(int(m) for m in mes_select)
        x_sort = [_MESES_PT[m - 1] for m in meses_ord]

        anos_ord = sorted(int(a) for a in anos_select)
        ano_domain = [str(a) for a in anos_ord]
        pal = list(CHART_PALETTE)
        while len(pal) < len(ano_domain):
            pal.extend(CHART_PALETTE)
        pal = pal[: len(ano_domain)]
        color_scale = alt.Color(
            'ano_str:N',
            title='Ano',
            scale=alt.Scale(domain=ano_domain, range=pal),
            legend=alt.Legend(orient='top', direction='horizontal'),
        )

        _pt_line = alt.OverlayMarkDef(size=72, filled=True)
        _ln = dict(point=_pt_line, strokeWidth=2.5)

        if len(meses_ord) >= 2:
            df_plot = df_agg[df_agg['mes'].isin(meses_ord)].copy()
            titulo = f"Comparativo por mês — {y_title}"
            media_val = df_plot[metrica].mean()
            chart = (
                alt.Chart(df_plot)
                .mark_line(**_ln)
                .encode(
                    x=alt.X('mes_nome:N', title='Mês', sort=x_sort),
                    y=alt.Y(f'{metrica}:Q', title=y_title),
                    color=color_scale,
                    tooltip=[
                        alt.Tooltip('ano_str:N', title='Ano'),
                        alt.Tooltip('mes_nome:N', title='Mês'),
                        alt.Tooltip(f'{metrica}:Q', title=metrica, format=fmt_tooltip),
                    ],
                )
                .properties(height=420, title=titulo)
            )
            rule = (
                alt.Chart(pd.DataFrame({'y': [media_val]}))
                .mark_rule(color=CHART_COLORS.get('secondary', '#f97316'), strokeDash=[4, 2])
                .encode(y='y:Q')
            )
            text = chart.mark_text(align='center', baseline='bottom', dy=-6, fontSize=10).encode(
                text=alt.Text(f'{metrica}:Q', format=fmt_text)
            )
            st.altair_chart((chart + rule + text).interactive(), use_container_width=True)
            return

        m = meses_ord[0]
        df_one = df_agg[df_agg['mes'] == m].copy()
        if df_one.empty:
            st.warning("Nenhum dado para o mês selecionado.")
            return
        df_one = df_one.sort_values('ano')
        titulo = f"{_MESES_PT[m - 1]} — por ano — {y_title}"
        chart = (
            alt.Chart(df_one)
            .mark_bar(cornerRadius=6, size=40)
            .encode(
                x=alt.X('ano_str:N', title='Ano', sort=ano_domain),
                y=alt.Y(f'{metrica}:Q', title=y_title),
                color=color_scale,
                tooltip=[
                    alt.Tooltip('ano_str:N', title='Ano'),
                    alt.Tooltip(f'{metrica}:Q', title=metrica, format=fmt_tooltip),
                ],
            )
            .properties(height=420, title=titulo)
        )
        text = chart.mark_text(align='center', baseline='bottom', dy=-4, fontSize=10).encode(
            text=alt.Text(f'{metrica}:Q', format=fmt_text)
        )
        st.altair_chart((chart + text).interactive(), use_container_width=True)

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
