import altair           as alt
import streamlit        as st
import pandas           as pd
import tp_lists_Compras as tl
import numpy            as np
import calendar


# -------------------------------------------------------------------
# BASE
# -------------------------------------------------------------------
class GraficoBase:
    def __init__(self, df):
        self.df = df.copy()

    def ordenar(self, texto, key):
        ordem = st.selectbox(
            texto,
            ["Maior para Menor", "Menor para Maior"],
            key=key
        )
        return ordem == "Menor para Maior"
    
    def converter_data(self, coluna):
        if coluna not in self.df.columns:
            st.error(f"Coluna '{coluna}' não encontrada no DataFrame.")
            return self.df

        self.df[coluna] = pd.to_datetime(self.df[coluna], errors='coerce')
        return self.df.dropna(subset=[coluna])

    # Ajuste de escala por métrica
    def format_valor(self, row):
        if row['Métrica'] in tl.Metrica_valores_k:
            row['Valor_plot'] = row['Valor'] / 1_000  
            row['label'] = f"{row['Valor_plot']:.1f}k"
        
        elif row['Métrica'] in tl.Metrica_valores_p:
            row['Valor_plot'] = row['Valor']  
            row['label'] = f"{row['Valor_plot']:.1f}%"
        
        else:
            row['Valor_plot'] = row['Valor']
            row['label'] = f"{row['Valor_plot']:.2f}"
    
        return row

    def definir_cor(self, coluna):
        coluna_lower = coluna.lower()
        if "quantidade" in coluna_lower:
            return "#f39c12"
        if "imposto" in coluna_lower:
            return "#fa5ca6"
        if "líquido" in coluna_lower or "liquido" in coluna_lower:
            return "#8cc7ee"  
        return "#3498db"     

# -------------------------------------------------------------------
# Graficos Dashboard 1
# -------------------------------------------------------------------
class Grafico_pizza(GraficoBase):
    def G_pizza(self, valor_x, valor_y, titulo=None):
        # Validar colunas
        if valor_x not in self.df.columns:
            st.error(f"Coluna '{valor_x}' não existe no DataFrame.")
            return
        if valor_y not in self.df.columns:
            st.error(f"Métrica '{valor_y}' não existe no DataFrame.")
            return

        # Preparar DataFrame
        df_valid = self.df[[valor_x, valor_y]].copy()
        df_valid = df_valid.dropna(subset=[valor_x, valor_y])
        df_valid[valor_y] = pd.to_numeric(df_valid[valor_y], errors="coerce")
        df_valid = df_valid.dropna(subset=[valor_y])

        if df_valid.empty:
            st.warning("Não há dados válidos para plotar.")
            return

        #Agrupa e soma
        df_agg = df_valid.groupby(valor_x, as_index=False)[valor_y].sum()
        df_agg = df_agg.sort_values(by=valor_y, ascending=False).head(10)
        df_agg['percent'] = df_agg[valor_y] / df_agg[valor_y].sum()

        if titulo is None:
            titulo = f"{valor_y} por {valor_x}"

        #st.write("Dados agregados:", df_agg)

        chart = alt.Chart(df_agg).mark_arc(innerRadius=50).encode(
            theta=alt.Theta(field='percent', type='quantitative'),
            color=alt.Color(field=valor_x, type='nominal'),
            tooltip=[
                alt.Tooltip(valor_x, title=valor_x),
                alt.Tooltip(valor_y, title=valor_y, format=',.2f'),
                alt.Tooltip('percent:Q', title='Percentual', format='.2%')
            ]
        ).properties(title=titulo, height=400)

        st.altair_chart(chart, use_container_width=True)

class Grafico_barra(GraficoBase):
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

        # ------------------------
        # Ordenação correta
        # ------------------------
        if ordenacao == "Do maior para o menor":
            df_rank = df_agg.sort_values(by=valor_y, ascending=False).head(10)
        else:
            df_rank = df_agg.sort_values(by=valor_y, ascending=True).head(10)

        # ------------------------
        # Título automático
        # ------------------------
        if titulo is None:
            titulo = f"{valor_y} por {valor_x}"

        # ------------------------
        # Gráfico SEM riscos e com ordenação real
        # ------------------------
        chart = (
            alt.Chart(df_rank)
            .mark_bar()
            .encode(
                x=alt.X(valor_y, type='quantitative', title=valor_y),
                y=alt.Y(
                    valor_x,
                    type='nominal',
                    title=valor_x,
                    sort=df_rank[valor_x].tolist()  # ordenação final correta
                ),
                tooltip=[
                    alt.Tooltip(valor_x, title=valor_x),
                    alt.Tooltip(valor_y, title=valor_y, format=',.2f'),
                ],
            )
            .properties(title=titulo, height=600)
        )

        st.altair_chart(chart, use_container_width=True)
    
        # -------------------------------------------
    def G_barra_multicolunas(self, valor_x, list_y, ordenacao, titulo=None):

        if isinstance(list_y, str):
            list_y = [list_y]

        # Filtrar e limpar
        df_valid = self.df[[valor_x] + list_y].copy()
        df_valid = df_valid.dropna(subset=[valor_x] + list_y)

        for col in list_y:
            df_valid[col] = pd.to_numeric(df_valid[col], errors="coerce")

        df_valid = df_valid.dropna(subset=list_y)

        # Somar valores por categoria
        df_rank = df_valid.groupby(valor_x, as_index=False)[list_y].sum()

        # Ordenar pelo primeiro item de list_y
        if ordenacao == "Do maior para o menor" and list_y[0] == "Valor Líquido":
            df_rank = df_rank.sort_values(list_y[1], ascending=False).head(10)

        if ordenacao == "Do menor para o maior" and list_y[0] == "Valor Líquido":
            df_rank = df_rank.sort_values(list_y[1], ascending=False).head(10)

        elif ordenacao == "Do maior para o menor":
            df_rank = df_rank.sort_values(list_y[0], ascending=False).head(10)

        else:
            df_rank = df_rank.sort_values(list_y[0], ascending=True).head(10)

        # Cores fixas
        paleta = {
            "Valor Líquido": "#4FA3F7",
            "Total de Impostos": "#FF4FA0",
            "Faturamento": "#3498db",
            "Quantidade de Produto": "#f39c12"
        }

        # Criar ranges da barra
        if list_y == ["Valor Líquido", "Total de Impostos"]:

            df_rank["start_liquido"] = 0
            df_rank["end_liquido"] = df_rank["Valor Líquido"]

            df_rank["start_imposto"] = df_rank["Valor Líquido"]
            df_rank["end_imposto"] = df_rank["Valor Líquido"] + df_rank["Total de Impostos"]

            barra_liquido = (
                alt.Chart(df_rank)
                .mark_bar(color=paleta["Valor Líquido"])
                .encode(
                    x=alt.X("start_liquido:Q"),
                    x2="end_liquido:Q",
                    y=alt.Y(f"{valor_x}:N", sort=df_rank[valor_x].tolist()),
                    tooltip=[valor_x, "Valor Líquido"]
                )
            )

            barra_imposto = (
                alt.Chart(df_rank)
                .mark_bar(color=paleta["Total de Impostos"])
                .encode(
                    x=alt.X("start_imposto:Q"),
                    x2="end_imposto:Q",
                    y=alt.Y(f"{valor_x}:N"),
                    tooltip=[valor_x, "Total de Impostos"]
                )
            )

            chart = (barra_liquido + barra_imposto).properties(
                title=titulo or f"Total por {valor_x}",
                height=600
            )

            st.altair_chart(chart, use_container_width=True)
            return

        # Caso seja apenas 1 métrica → barra simples
        chart = (
            alt.Chart(df_rank)
            .mark_bar(color=paleta.get(list_y[0], "#7f8c8d"))
            .encode(
                x=alt.X(f"{list_y[0]}:Q", title="Total"),
                y=alt.Y(f"{valor_x}:N", sort=df_rank[valor_x].tolist()),
                tooltip=[valor_x, list_y[0]]
            )
            .properties(title=titulo or f"Total por {valor_x}", height=600)
        )

        st.altair_chart(chart, use_container_width=True)

    def G_multiplas_metricas(self, coluna_data='mes_nome', coluna_ano='ano',
                         metricas=None, filtro_anos=None, filtro_meses=None,
                         periodo="Mensal", titulo=None):
        
        df_valid = self.df.copy()
        # Filtra anos
        if filtro_anos:
            df_valid = df_valid[df_valid[coluna_ano].isin(filtro_anos)]

        # Filtra meses apenas se for Mensal
        if periodo == "Mensal" and filtro_meses:
            mes_ini, mes_fim = filtro_meses
            df_valid = df_valid[(df_valid['mes'] >= mes_ini) & (df_valid['mes'] <= mes_fim)]
        else:
            mes_ini, mes_fim = 1, 12  # pega todos os meses

        # Define métricas
        if metricas is None:
            metricas = [c for c in df_valid.columns if c not in [coluna_data, coluna_ano, 'mes']]

        # Agrupa os dados
        if periodo == "Mensal":
            df_grouped = df_valid.groupby([coluna_ano, 'mes', coluna_data], as_index=False)[metricas].sum()
            df_long = df_grouped.melt(
                id_vars=[coluna_ano, 'mes', coluna_data],
                value_vars=metricas,
                var_name='Métrica',
                value_name='Valor'
            )
            # Ordena meses
            meses_ordenados = [calendar.month_name[m].capitalize() for m in range(mes_ini, mes_fim+1)]
            x_sort = meses_ordenados
        else:  # Anual
            df_grouped = df_valid.groupby([coluna_ano], as_index=False)[metricas].sum()
            df_grouped[coluna_data] = df_grouped[coluna_ano].astype(str)
            df_long = df_grouped.melt(
                id_vars=[coluna_data, coluna_ano],
                value_vars=metricas,
                var_name='Métrica',
                value_name='Valor'
            )
            x_sort = None

        df_long = df_long.apply(self.format_valor, axis=1)

        # Cria gráfico de linha
        chart = (
            alt.Chart(df_long)
            .mark_line(point=alt.OverlayMarkDef(size=100), strokeWidth=4) 
            .encode(
                x=alt.X(f'{coluna_data}:N', title='Mês' if periodo=="Mensal" else 'Ano', sort=x_sort),
                y=alt.Y('Valor_plot:Q', title='Valor'),
                color=alt.Color('Métrica:N', legend=alt.Legend(title='Métrica')),
                strokeDash=alt.StrokeDash(f'{coluna_ano}:N', legend=alt.Legend(title='Ano')),
                tooltip=[
                    alt.Tooltip(f'{coluna_ano}:N', title='Ano'),
                    alt.Tooltip(f'{coluna_data}:N', title='Mês' if periodo=="Mensal" else 'Ano'),
                    alt.Tooltip('Métrica:N', title='Métrica'),
                    alt.Tooltip('Valor_plot:Q', format=',.2f')
                ]
            )
            .properties(height=400, title=titulo)
        )

        # Rótulos com valores
        labels = chart.mark_text(
            align='center',
            baseline='bottom',
            dy=-5,  # desloca acima do ponto
            fontSize=12
        ).encode(
            text=alt.Text('label:N')
        )

        final_chart = (chart + labels).properties(height=400, title=titulo)
        st.altair_chart(final_chart, use_container_width=True)

"""""
class Grafico_Composto(GraficoBase):
    def G_barra_linha(self, valor_x, valor_y, titulo=None, i_metrica=None):
        if not isinstance(valor_x, list) or not isinstance(valor_y, list):
            st.error("Os parâmetros valor_x e valor_y devem ser listas de colunas.")
            return

        # Seleção dinâmica dentro do método
        #col1, col2 = st.columns(2)
        #with col1:
        #    coluna_dim = st.selectbox(
        #        "Escolha a dimensão (categoria):",
        #        options=valor_x,
        #        key=f"top10_dim_{id(self)}"
        #    )
        #with col2:
        #    if i_metrica is None:
        #        coluna_met = st.selectbox(
        #            "Escolha a métrica:",
        #            options=valor_y,
        #            key=f"top10_met_{id(self)}"
        #        )

        # Agrupa e agrega
        #aggregated = self.df.groupby(coluna_dim, as_index=False).agg({
        #    "Faturamento": "sum",
        #    "V.CMV": "sum",
        #    "M. Contribuição": "mean"
        #})

        # Ajustes de escala
        aggregated["Faturamento"] /= 1_000_000
        aggregated["V.CMV"] /= 1_000_000
        aggregated["M. Contribuição"] = pd.to_numeric(aggregated["M. Contribuição"], errors="coerce")
        if aggregated["M. Contribuição"].max() > 1:
            aggregated["M. Contribuição"] /= 100

        # Ordena e limita top 10
        ascending = self.ordenar(f"Ordenar ({coluna_dim}):", key=f"ordem_mix_{id(self)}")
        aggregated = aggregated.sort_values("Faturamento", ascending=ascending).head(10)

        # Codificação Altair
        x_encode = alt.X(f"{coluna_dim}:O", title=coluna_dim)

        bars = alt.Chart(aggregated).mark_bar(opacity=0.85, color="#5400bb").encode(
            x=x_encode,
            y=alt.Y("Faturamento:Q", title="Faturamento (M)"),
            tooltip=[alt.Tooltip("Faturamento:Q", format=",.2f")]
        )

        line_cmv = alt.Chart(aggregated).mark_line(point=True, color="#13EEFD").encode(
            x=x_encode,
            y=alt.Y("V.CMV:Q", title="V.CMV (M)"),
            tooltip=[alt.Tooltip("V.CMV:Q", format=",.2f")]
        )

        line_mc = alt.Chart(aggregated).mark_line(point=True, color="#048cb6").encode(
            x=x_encode,
            y=alt.Y("M. Contribuição:Q",
                    axis=alt.Axis(format=".0%", title="% M. Contribuição")),
            tooltip=[alt.Tooltip("M. Contribuição:Q", format=".0%", title="% M. Contribuição")]
        )

        final = alt.layer(bars, line_cmv, line_mc).resolve_scale(y='independent').properties(
            height=500, title=titulo or f"Top 10 por {coluna_dim}"
        )

        st.altair_chart(final, use_container_width=True)
"""
class Grafico_linha(GraficoBase):
    def G_multiplas_metricas(self, coluna_data='mes_nome', coluna_ano='ano',
                         metricas=None, filtro_anos=None, filtro_meses=None,
                         periodo="Mensal", titulo=None):
        
        df_valid = self.df.copy()
        # Filtra anos
        if filtro_anos:
            df_valid = df_valid[df_valid[coluna_ano].isin(filtro_anos)]

        # Filtra meses apenas se for Mensal
        if periodo == "Mensal" and filtro_meses:
            mes_ini, mes_fim = filtro_meses
            df_valid = df_valid[(df_valid['mes'] >= mes_ini) & (df_valid['mes'] <= mes_fim)]
        else:
            mes_ini, mes_fim = 1, 12  # pega todos os meses

        # Define métricas
        if metricas is None:
            metricas = [c for c in df_valid.columns if c not in [coluna_data, coluna_ano, 'mes']]

        # Agrupa os dados
        if periodo == "Mensal":
            agg_dict = {}
            for m in metricas:
                if m in tl.Metrica_valores_p:
                    agg_dict[m] = 'sum'  # porcentagem = média correta
                else:
                    agg_dict[m] = 'sum'  # valores absolutos = soma

            df_grouped = df_valid.groupby(
            [coluna_ano, 'mes', coluna_data],
            as_index=False
            ).agg(agg_dict)
            
            # Calcula porcentagem separadamente (M. Contribuição) 
            #df_grouped['M. Contribuição'] = (df_grouped['M. Contribuição'] /df_grouped['Faturamento']) * 100
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
            
            # Ordena meses
            meses_ordenados = [calendar.month_name[m].capitalize() for m in range(mes_ini, mes_fim+1)]
            x_sort = meses_ordenados

        else:  # Anual
            #df_grouped = df_valid.groupby([coluna_ano], as_index=False)[metricas].sum()
            agg_dict = {}
            for m in metricas:
                if m in tl.Metrica_valores_p:
                    agg_dict[m] = 'sum'  # porcentagem = média correta
                else:
                    agg_dict[m] = 'sum'  # valores absolutos = soma
    
            df_grouped = df_valid.groupby(
            [coluna_ano],
            as_index=False
            ).agg(agg_dict)

            st.write("Dados agrupados anuais:", df_grouped)
            
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
        
        # Cria gráfico de linha
        if periodo == "Mensal":
            chart = (
                alt.Chart(df_long)
                .mark_line(point=alt.OverlayMarkDef(size=100), strokeWidth=4) 
                .encode(
                    x=alt.X(f'{coluna_data}:N', title='Mês' if periodo=="Mensal" else 'Ano', sort=x_sort),
                    y=alt.Y('label:N', title='Valor'),
                    color=alt.Color('Métrica:N', legend=alt.Legend(title='Métrica')),
                    strokeDash=alt.StrokeDash(f'{coluna_ano}:N', legend=alt.Legend(title='Ano')),
                    tooltip=[
                        alt.Tooltip(f'{coluna_ano}:N', title='Ano'),
                        alt.Tooltip(f'{coluna_data}:N', title='Mês' if periodo=="Mensal" else 'Ano'),
                        alt.Tooltip('Métrica:N', title='Métrica'),
                        alt.Tooltip('label:N', title='Valor')
                    ]
                )
                .properties(height=400, title=titulo)
            )
        else:
            chart = (
                alt.Chart(df_long)
                .mark_bar(point=alt.OverlayMarkDef(size=100), strokeWidth=4) 
                .encode(
                    x=alt.X(f'{coluna_data}:N', title='Mês' if periodo=="Mensal" else 'Ano', sort=x_sort),
                    y=alt.Y('label:N', title='Valor'),
                    color=alt.Color('Métrica:N', legend=alt.Legend(title='Métrica')),
                    strokeDash=alt.StrokeDash(f'{coluna_ano}:N', legend=alt.Legend(title='Ano')),
                    tooltip=[
                        alt.Tooltip(f'{coluna_ano}:N', title='Ano'),
                        alt.Tooltip(f'{coluna_data}:N', title='Mês' if periodo=="Mensal" else 'Ano'),
                        alt.Tooltip('Métrica:N', title='Métrica'),
                        alt.Tooltip('label:N', title='Valor')
                    ]
                )
                .properties(height=400, title=titulo)
            )

        # Rótulos com valores
        labels = chart.mark_text(
            align='center',
            baseline='bottom',
            dy=-5,  # desloca acima do ponto
            fontSize=12
        ).encode(
            text=alt.Text('label:N')
        )

        final_chart = (chart + labels).properties(height=400, title=titulo)
        st.altair_chart(final_chart, use_container_width=True)

    def G_multiplas_metricas_barra_invertido(
            self,
            coluna_data='mes_nome',
            coluna_ano='ano',
            metricas=None,
            filtro_anos=None,
            filtro_meses=None,
            periodo="Mensal",
            titulo=None
        ):

            df_valid = self.df.copy()

            # -------------------------------
            # Filtros
            # -------------------------------
            if filtro_anos:
                df_valid = df_valid[df_valid[coluna_ano].isin(filtro_anos)]

            if periodo == "Mensal" and filtro_meses:
                mes_ini, mes_fim = filtro_meses
                df_valid = df_valid[
                    (df_valid['mes'] >= mes_ini) &
                    (df_valid['mes'] <= mes_fim)
                ]
            else:
                mes_ini, mes_fim = 1, 12

            # -------------------------------
            # Métricas
            # -------------------------------
            if metricas is None:
                metricas = [
                    c for c in df_valid.columns
                    if c not in [coluna_data, coluna_ano, 'mes']
                ]

            # -------------------------------
            # Agrupamento
            # -------------------------------
            agg_dict = {m: 'sum' for m in metricas}

            if periodo == "Mensal":
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

                meses_ordenados = [
                    calendar.month_name[m].capitalize()
                    for m in range(mes_ini, mes_fim + 1)
                ]
                y_sort = meses_ordenados

                df_long = df_grouped.melt(
                    id_vars=[coluna_ano, 'mes', coluna_data],
                    value_vars=metricas,
                    var_name='Métrica',
                    value_name='Valor'
                )

            else:  # Anual
                df_grouped = df_valid.groupby(
                    [coluna_ano],
                    as_index=False
                ).agg(agg_dict)

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

                y_sort = None

            # -------------------------------
            # Formatação
            # -------------------------------
            df_long = df_long.apply(self.format_valor, axis=1)

            # -------------------------------
            # Gráfico – BARRA + EIXOS INVERTIDOS
            # -------------------------------

            chart = (
                alt.Chart(df_long)
                .mark_line(strokeWidth=2)
                .encode(
                    y=alt.Y(
                        f'{coluna_data}:N',
                        title='Mês' if periodo == "Mensal" else 'Ano',
                        sort=y_sort
                    ),
                    x=alt.X(
                        'Valor:Q',
                        title='Valor'
                    ),
                    color=alt.Color(
                        'Métrica:N',
                        legend=alt.Legend(title='Métrica')
                    ),
                    tooltip=[
                        alt.Tooltip(f'{coluna_ano}:N', title='Ano'),
                        alt.Tooltip(f'{coluna_data}:N', title='Mês' if periodo == "Mensal" else 'Ano'),
                        alt.Tooltip('Métrica:N', title='Métrica'),
                        alt.Tooltip('label:N', title='Valor')
                    ]
                )
                .properties(height=400, title=titulo)
            )

            # -------------------------------
            # Rótulos
            # -------------------------------
            labels = chart.mark_text(
                align='left',
                baseline='middle',
                dx=5,
                fontSize=12
            ).encode(
                text=alt.Text('label:N')
            )

            final_chart = (chart + labels).properties(height=400, title=titulo)
            st.altair_chart(final_chart, use_container_width=True)


# ============================================================
# NOVO MÉTODO: COMPARAÇÃO ANO vs ANO / MÊS vs MÊS
# ============================================================
class Grafico_comparacao(GraficoBase):
    """Gráfico de comparação para análises de Ano vs Ano, Mês vs Mês"""
    
    def G_comparacao_anos_meses(self, tipo_comparacao="Mês vs Mês", metrica="Faturamento", 
                                 anos_select=None, mes_select=None, titulo=None):
        """
        Gráfico de comparação flexível
        
        Args:
            tipo_comparacao: "Mês vs Mês", "Ano vs Ano", "Mês em Anos Diferentes"
            metrica: Nome da métrica para comparar
            anos_select: Lista de anos
            mes_select: Lista de meses
            titulo: Título customizado
        """
        
        df = self.df.copy()
        
        if metrica not in df.columns:
            st.error(f"Métrica '{metrica}' não existe.")
            return
        
        if titulo is None:
            titulo = f"{tipo_comparacao} - {metrica}"
        
        # ============================================================
        # COMPARAÇÃO: MÊS VS MÊS
        # ============================================================
        if tipo_comparacao == "Mês vs Mês":
            if not mes_select or len(mes_select) < 2:
                st.warning("Selecione 2+ meses.")
                return
            
            df_comp = df[df['mes'].isin(mes_select)].copy()
            df_agg = df_comp.groupby('mes', as_index=False)[metrica].sum()
            df_agg['mes_nome'] = df_agg['mes'].apply(
                lambda x: ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez'][x-1]
            )
            
            chart = (
                alt.Chart(df_agg)
                .mark_bar(cornerRadius=8)
                .encode(
                    x=alt.X('mes_nome:N', title='Mês', sort=df_agg['mes_nome'].tolist()),
                    y=alt.Y(f'{metrica}:Q', title=metrica),
                    color=alt.Color('mes_nome:N', scale=alt.Scale(scheme='blues'), legend=None),
                    tooltip=[
                        alt.Tooltip('mes_nome:N', title='Mês'),
                        alt.Tooltip(f'{metrica}:Q', title=metrica, format=',.0f')
                    ]
                )
                .properties(height=400, title=titulo)
            )
            
            text = chart.mark_text(align='center', baseline='bottom', dy=-5).encode(
                text=alt.Text(f'{metrica}:Q', format=',.0f')
            )
            
            st.altair_chart((chart + text), use_container_width=True)
        
        # ============================================================
        # COMPARAÇÃO: ANO VS ANO
        # ============================================================
        elif tipo_comparacao == "Ano vs Ano":
            if not anos_select or len(anos_select) < 2:
                st.warning("Selecione 2+ anos.")
                return
            
            df_comp = df[df['ano'].isin(anos_select)].copy()
            df_agg = df_comp.groupby('ano', as_index=False)[metrica].sum()
            
            chart = (
                alt.Chart(df_agg)
                .mark_bar(cornerRadius=8)
                .encode(
                    x=alt.X('ano:N', title='Ano'),
                    y=alt.Y(f'{metrica}:Q', title=metrica),
                    color=alt.Color('ano:N', scale=alt.Scale(scheme='blues'), legend=None),
                    tooltip=[
                        alt.Tooltip('ano:N', title='Ano'),
                        alt.Tooltip(f'{metrica}:Q', title=metrica, format=',.0f')
                    ]
                )
                .properties(height=400, title=titulo)
            )
            
            text = chart.mark_text(align='center', baseline='bottom', dy=-5).encode(
                text=alt.Text(f'{metrica}:Q', format=',.0f')
            )
            
            st.altair_chart((chart + text), use_container_width=True)
        
        # ============================================================
        # COMPARAÇÃO: MÊS EM ANOS DIFERENTES
        # ============================================================
        elif tipo_comparacao == "Mês em Anos Diferentes":
            if not mes_select or len(mes_select) != 1:
                st.warning("Selecione exatamente 1 mês.")
                return
            
            if not anos_select or len(anos_select) < 2:
                st.warning("Selecione 2+ anos.")
                return
            
            l_v_mes = mes_select[0]
            df_comp = df[(df['mes'] == l_v_mes) & (df['ano'].isin(anos_select))].copy()
            df_agg = df_comp.groupby('ano', as_index=False)[metrica].sum()
            
            l_v_mes_nome = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho',
                           'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro'][l_v_mes-1]
            l_v_titulo = f"{l_v_mes_nome} - Comparação Anual: {metrica}"
            
            chart = (
                alt.Chart(df_agg)
                .mark_bar(cornerRadius=8)
                .encode(
                    x=alt.X('ano:N', title='Ano'),
                    y=alt.Y(f'{metrica}:Q', title=metrica),
                    color=alt.Color('ano:N', scale=alt.Scale(scheme='blues'), legend=None),
                    tooltip=[
                        alt.Tooltip('ano:N', title='Ano'),
                        alt.Tooltip(f'{metrica}:Q', title=metrica, format=',.0f')
                    ]
                )
                .properties(height=400, title=l_v_titulo)
            )
            
            text = chart.mark_text(align='center', baseline='bottom', dy=-5).encode(
                text=alt.Text(f'{metrica}:Q', format=',.0f')
            )
            
            st.altair_chart((chart + text), use_container_width=True)