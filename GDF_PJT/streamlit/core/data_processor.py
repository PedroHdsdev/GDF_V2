"""
Processador de dados NFe para Dashboards.
Centraliza a construção de DataFrames e queries.
"""
import pandas as pd

from config.constants import descricao_tipo_pagamento


class DashboardData:
    """Container imutável com os dados processados do dashboard."""

    __slots__ = (
        "df_merged", "df_produtos", "df_parcelas", "df_pagamento",
        "tipo_relatorio", "g_q_nfe"
    )

    def __init__(self, df_merged, df_produtos, df_parcelas, df_pagamento, tipo_relatorio, g_q_nfe):
        self.df_merged = df_merged
        self.df_produtos = df_produtos
        self.df_parcelas = df_parcelas
        self.df_pagamento = df_pagamento
        self.tipo_relatorio = tipo_relatorio
        self.g_q_nfe = g_q_nfe

    @property
    def is_vendas(self):
        return self.tipo_relatorio == "Vendas"

    @property
    def is_compras(self):
        return self.tipo_relatorio == "Compras"


class DataProcessor:
    """Processa dados NFe e gera DataFrames para os dashboards."""

    def __init__(self, tipo_relatorio: str):
        self.tipo_relatorio = tipo_relatorio
        self.tipo_operacao = '1' if tipo_relatorio == "Vendas" else '0'

    def process(
        self,
        empresas_queryset,
        empresa_selecionada: str,
        usar_periodo: bool,
        data_inicio,
        data_fim,
    ) -> DashboardData | None:
        """
        Processa os dados conforme filtros e retorna DashboardData.
        Retorna None se não houver dados.
        """
        from app.db_GDF.Public.models import Empresas
        from app.db_GDF.NFe.models import (
            NFe_Identificacao, NFe_Total, NFe_Produto, NFe_Destinatario, NFe,
            NFe_Cobranca, NFe_Parcela, NFe_Pagamento,
        )

        lsl_cod_empresa = list(empresas_queryset.values_list('cod_empresa', flat=True))
        if empresa_selecionada and empresa_selecionada not in ("Todas", "Todas as empresas"):
            cod_empresa = empresa_selecionada.split(" - ")[0]
            lsl_cod_empresa = [cod_empresa]

        q_identificacoes = NFe_Identificacao.objects.filter(tipo_operacao=self.tipo_operacao)

        if usar_periodo and data_inicio and data_fim:
            q_identificacoes = q_identificacoes.filter(
                emissao__date__range=(data_inicio, data_fim)
            )

        g_q_nfe = q_identificacoes.filter(
            nfe__empresa__cod_empresa__in=lsl_cod_empresa
        ).distinct()

        if not g_q_nfe.exists():
            return None

        df_header = pd.DataFrame.from_records(
            g_q_nfe.values('id_identificacao', 'numero', 'serie', 'emissao', 'tipo_operacao')
        )

        df_totais = pd.DataFrame.from_records(
            NFe_Total.objects.filter(nfe_identificacao__in=g_q_nfe).values(
                'nfe_identificacao__id_identificacao',
                'valor_total_nfe', 'valor_base_icms', 'valor_icms', 'valor_ipi', 'valor_pis', 'valor_cofins'
            )
        )
        if not df_totais.empty:
            df_totais.rename(columns={'nfe_identificacao__id_identificacao': 'id_identificacao'}, inplace=True)
        else:
            df_totais = pd.DataFrame()

        df_produtos = pd.DataFrame.from_records(
            NFe_Produto.objects.filter(nfe_serie__in=g_q_nfe).values(
                'nfe_serie_id', 'descricao', 'quantidade', 'valor_total', 'ncm', 'cfop'
            )
        )
        if not df_produtos.empty:
            df_produtos.rename(columns={'nfe_serie_id': 'id_identificacao'}, inplace=True)
        else:
            df_produtos = pd.DataFrame()

        df_contraparte = self._build_contraparte(g_q_nfe)

        df_parcelas = self._build_parcelas(g_q_nfe)

        df_pagamento = self._build_pagamento(g_q_nfe)

        df_merged = df_header.merge(df_totais, on='id_identificacao', how='left')

        if not df_contraparte.empty:
            cols_merge = [c for c in df_contraparte.columns if c != 'id_identificacao']
            df_merged = df_merged.merge(
                df_contraparte[['id_identificacao'] + cols_merge], on='id_identificacao', how='left'
            )

        self._ensure_contraparte_columns(df_merged)

        if not df_produtos.empty:
            df_prod_agg = df_produtos.groupby('id_identificacao').agg({
                'quantidade': 'sum',
                'valor_total': 'sum',
                'descricao': 'count'
            }).rename(columns={'descricao': 'total_itens'})
            df_merged = df_merged.merge(df_prod_agg, on='id_identificacao', how='left')
        else:
            df_merged['total_itens'] = 0
            df_merged['quantidade'] = 0

        df_merged = self._add_metric_columns(df_merged)

        return DashboardData(
            df_merged=df_merged,
            df_produtos=df_produtos,
            df_parcelas=df_parcelas,
            df_pagamento=df_pagamento,
            tipo_relatorio=self.tipo_relatorio,
            g_q_nfe=g_q_nfe,
        )

    def _build_contraparte(self, g_q_nfe):
        from app.db_GDF.NFe.models import NFe

        if self.tipo_relatorio == "Compras":
            df = pd.DataFrame.from_records(
                NFe.objects.filter(identificacao__in=g_q_nfe).values(
                    'identificacao_id',
                    'emitente__cnpj',
                    'emitente__razao_social',
                    'emitente__nome_fantasia',
                )
            )
            if not df.empty:
                df.rename(columns={
                    'identificacao_id': 'id_identificacao',
                    'emitente__cnpj': 'cnpj_fornecedor',
                    'emitente__razao_social': 'nome_fornecedor',
                    'emitente__nome_fantasia': 'nome_fantasia_fornecedor',
                }, inplace=True)
                df['nome_cliente'] = df['nome_fornecedor'].fillna(df['nome_fantasia_fornecedor'])
                df['cnpj_cliente'] = df['cnpj_fornecedor']
            else:
                df = pd.DataFrame(columns=['id_identificacao', 'cnpj_fornecedor', 'nome_fornecedor', 'nome_cliente', 'cnpj_cliente'])
        else:
            df = pd.DataFrame.from_records(
                NFe.objects.filter(identificacao__in=g_q_nfe).values(
                    'identificacao_id',
                    'destinatario__documento',
                    'destinatario__razao_social',
                    'destinatario__endereco__nome_municipio',
                    'destinatario__endereco__uf',
                )
            )
            if not df.empty:
                df.rename(columns={
                    'identificacao_id': 'id_identificacao',
                    'destinatario__documento': 'cnpj_cliente',
                    'destinatario__razao_social': 'nome_cliente',
                    'destinatario__endereco__nome_municipio': 'cidade',
                    'destinatario__endereco__uf': 'estado',
                }, inplace=True)
            else:
                df = pd.DataFrame(columns=['id_identificacao', 'cnpj_cliente', 'nome_cliente', 'cidade', 'estado'])

        return df

    def _build_parcelas(self, g_q_nfe):
        from app.db_GDF.NFe.models import NFe_Parcela

        df = pd.DataFrame.from_records(
            NFe_Parcela.objects.filter(
                nfe_cobranca__nfe_identificacao__in=g_q_nfe
            ).values(
                'nfe_cobranca__nfe_identificacao_id',
                'data_vencimento', 'valor_parcela', 'numero_parcela'
            )
        )
        if not df.empty:
            df.rename(columns={'nfe_cobranca__nfe_identificacao_id': 'id_identificacao'}, inplace=True)
            df['data_vencimento'] = pd.to_datetime(df['data_vencimento'])
            df['valor_parcela'] = pd.to_numeric(df['valor_parcela'], errors='coerce').fillna(0)
        return df

    def _build_pagamento(self, g_q_nfe):
        from app.db_GDF.NFe.models import NFe_Pagamento

        df = pd.DataFrame.from_records(
            NFe_Pagamento.objects.filter(nfe_identificacao__in=g_q_nfe).values(
                "nfe_identificacao_id", "meio_pagamento", "valor_pago"
            )
        )
        if not df.empty:
            df.rename(columns={"nfe_identificacao_id": "id_identificacao"}, inplace=True)
            df["valor_pago"] = pd.to_numeric(df["valor_pago"], errors="coerce").fillna(0)
            df["tipo_pagamento_desc"] = df["meio_pagamento"].map(descricao_tipo_pagamento)
        else:
            df = pd.DataFrame(columns=["id_identificacao", "meio_pagamento", "valor_pago", "tipo_pagamento_desc"])
        return df

    def _ensure_contraparte_columns(self, df_merged):
        if self.tipo_relatorio != "Compras":
            if 'cidade' not in df_merged.columns:
                df_merged['cidade'] = None
            if 'estado' not in df_merged.columns:
                df_merged['estado'] = None
        else:
            if 'nome_fornecedor' not in df_merged.columns:
                df_merged['nome_fornecedor'] = None
            if 'cnpj_fornecedor' not in df_merged.columns:
                df_merged['cnpj_fornecedor'] = None

    def _add_metric_columns(self, df_merged):
        df_merged['emissao'] = pd.to_datetime(df_merged['emissao'])
        df_merged['ano'] = df_merged['emissao'].dt.year
        df_merged['mes'] = df_merged['emissao'].dt.month
        # Meses em português para consistência nos gráficos
        _meses_pt = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
                     7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
        df_merged['mes_nome'] = df_merged['mes'].map(_meses_pt)
        df_merged['Data Postagem'] = df_merged['emissao'].dt.date

        df_merged['Faturamento'] = df_merged['valor_total_nfe'].fillna(0)
        df_merged['Total Impostos'] = (
            df_merged['valor_icms'].fillna(0) +
            df_merged['valor_ipi'].fillna(0) +
            df_merged['valor_pis'].fillna(0) +
            df_merged['valor_cofins'].fillna(0)
        )
        df_merged['Valor Líquido'] = df_merged['Faturamento'] - df_merged['Total Impostos']
        df_merged['Quantidade Total'] = df_merged['quantidade'].fillna(0)

        df_merged['Credito_ICMS'] = df_merged['valor_icms'].fillna(0)
        df_merged['Credito_PIS'] = df_merged['valor_pis'].fillna(0)
        df_merged['Credito_COFINS'] = df_merged['valor_cofins'].fillna(0)
        df_merged['Credito_Tributario_Total'] = (
            df_merged['Credito_ICMS'] + df_merged['Credito_PIS'] + df_merged['Credito_COFINS']
        )

        return df_merged
