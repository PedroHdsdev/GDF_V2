"""Classe base compartilhada para gráficos."""
import streamlit as st
import pandas as pd


class GraficoBase:
    """Base para todos os gráficos do dashboard."""

    def __init__(self, df, lists_module):
        self.df = df.copy()
        self.tl = lists_module

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

    def format_valor(self, row):
        """Ajuste de escala por métrica (k=milhares, p=percentual)."""
        if row['Métrica'] in self.tl.Metrica_valores_k:
            row['Valor_plot'] = row['Valor'] / 1_000
            row['label'] = f"{row['Valor_plot']:.1f}k"

        elif row['Métrica'] in self.tl.Metrica_valores_p:
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
