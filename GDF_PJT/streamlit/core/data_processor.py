"""
Processador de dados NFe para Dashboards.
Centraliza a construção de DataFrames e queries.
"""
import pandas as pd

from config.constants import (
    CUSTO_DASHBOARD_DETAIL_LIMIT,
    descricao_tipo_pagamento,
    RELATORIO_CUSTO_CFOP_LIST,
)


class DashboardData:
    """Container imutável com os dados processados do dashboard."""

    __slots__ = (
        "df_merged", "df_produtos", "df_parcelas", "df_pagamento",
        "tipo_relatorio", "g_q_nfe", "df_custo_linhas",
        "df_custo_rank_cliente", "df_custo_rank_cidade",
        "custo_detail_limit", "custo_detail_truncated",
    )

    def __init__(
        self,
        df_merged,
        df_produtos,
        df_parcelas,
        df_pagamento,
        tipo_relatorio,
        g_q_nfe,
        df_custo_linhas=None,
        df_custo_rank_cliente=None,
        df_custo_rank_cidade=None,
        custo_detail_limit: int = 0,
        custo_detail_truncated: bool = False,
    ):
        self.df_merged = df_merged
        self.df_produtos = df_produtos
        self.df_parcelas = df_parcelas
        self.df_pagamento = df_pagamento
        self.tipo_relatorio = tipo_relatorio
        self.g_q_nfe = g_q_nfe
        self.df_custo_linhas = df_custo_linhas if df_custo_linhas is not None else pd.DataFrame()
        self.df_custo_rank_cliente = (
            df_custo_rank_cliente if df_custo_rank_cliente is not None else pd.DataFrame()
        )
        self.df_custo_rank_cidade = (
            df_custo_rank_cidade if df_custo_rank_cidade is not None else pd.DataFrame()
        )
        self.custo_detail_limit = custo_detail_limit
        self.custo_detail_truncated = custo_detail_truncated

    @property
    def is_vendas(self):
        return self.tipo_relatorio == "Vendas"

    @property
    def is_compras(self):
        return self.tipo_relatorio == "Compras"

    @property
    def is_custo(self):
        return self.tipo_relatorio == "Custo"


def apply_compras_filters(data: DashboardData, filter_values: dict) -> DashboardData:
    """
    Aplica filtros em memória ao DashboardData de Compras.
    filter_values pode conter: fornecedores, produtos, ncms, ufs, filiais (listas de valores selecionados).
    Retorna novo DashboardData com df_merged e df_produtos filtrados.
    """
    if not data.is_compras:
        return data
    df_m = data.df_merged
    df_p = data.df_produtos

    ids_keep = None

    if filter_values.get("fornecedores"):
        sel = [str(x).strip() for x in filter_values["fornecedores"] if x]
        if sel:
            mask = df_m["cnpj_fornecedor"].astype(str).isin(sel)
            if ids_keep is not None:
                ids_keep = ids_keep & mask
            else:
                ids_keep = mask

    if filter_values.get("ufs"):
        sel = [str(x).strip().upper() for x in filter_values["ufs"] if x]
        if sel:
            uf_col = df_m.get("uf_fornecedor")
            if uf_col is not None:
                mask = uf_col.fillna("").astype(str).str.upper().isin(sel)
                if ids_keep is not None:
                    ids_keep = ids_keep & mask
                else:
                    ids_keep = mask

    if filter_values.get("filiais"):
        sel = [str(x).strip() for x in filter_values["filiais"] if x]
        if sel:
            cod = df_m.get("cod_filial")
            if cod is not None:
                mask = cod.fillna("").astype(str).isin(sel)
                if ids_keep is not None:
                    ids_keep = ids_keep & mask
                else:
                    ids_keep = mask

    if filter_values.get("produtos") or filter_values.get("ncms"):
        ids_from_produtos = None
        if filter_values.get("produtos"):
            sel = [str(x).strip() for x in filter_values["produtos"] if x]
            if sel and not df_p.empty and "descricao" in df_p.columns:
                mask_p = df_p["descricao"].astype(str).str.strip().isin(sel)
                ids_from_produtos = set(df_p.loc[mask_p, "id_identificacao"].dropna().unique())
        if filter_values.get("ncms"):
            sel = [str(x).strip() for x in filter_values["ncms"] if x]
            if sel and not df_p.empty and "ncm" in df_p.columns:
                df_p_ncm = df_p.copy()
                df_p_ncm["ncm"] = df_p_ncm["ncm"].fillna("").astype(str).str.strip()
                mask_ncm = df_p_ncm["ncm"].isin(sel)
                ids_ncm = set(df_p.loc[mask_ncm, "id_identificacao"].dropna().unique())
                ids_from_produtos = ids_ncm if ids_from_produtos is None else ids_from_produtos & ids_ncm
        if ids_from_produtos is not None:
            mask = df_m["id_identificacao"].isin(ids_from_produtos)
            if ids_keep is not None:
                ids_keep = ids_keep & mask
            else:
                ids_keep = mask

    if ids_keep is not None:
        id_list = df_m.loc[ids_keep, "id_identificacao"].dropna().unique()
        df_m = df_m[df_m["id_identificacao"].isin(id_list)].copy()
        if not df_p.empty:
            df_p = df_p[df_p["id_identificacao"].isin(id_list)].copy()

    id_list_final = df_m["id_identificacao"].dropna().unique()
    df_parcelas = data.df_parcelas
    df_pagamento = data.df_pagamento
    if not data.df_parcelas.empty and "id_identificacao" in data.df_parcelas.columns:
        df_parcelas = data.df_parcelas[data.df_parcelas["id_identificacao"].isin(id_list_final)].copy()
    if not data.df_pagamento.empty and "id_identificacao" in data.df_pagamento.columns:
        df_pagamento = data.df_pagamento[data.df_pagamento["id_identificacao"].isin(id_list_final)].copy()

    return DashboardData(
        df_merged=df_m,
        df_produtos=df_p,
        df_parcelas=df_parcelas,
        df_pagamento=df_pagamento,
        tipo_relatorio=data.tipo_relatorio,
        g_q_nfe=data.g_q_nfe,
        df_custo_linhas=data.df_custo_linhas,
        df_custo_rank_cliente=data.df_custo_rank_cliente,
        df_custo_rank_cidade=data.df_custo_rank_cidade,
        custo_detail_limit=data.custo_detail_limit,
        custo_detail_truncated=data.custo_detail_truncated,
    )


_MESES_NOMES_CUSTO = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']


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
        if self.tipo_relatorio == "Custo":
            return self._process_custo(
                empresas_queryset=empresas_queryset,
                empresa_selecionada=empresa_selecionada,
                usar_periodo=usar_periodo,
                data_inicio=data_inicio,
                data_fim=data_fim,
            )

        from app.db_GDF.Public.models import Empresa
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
                'nfe_serie_id', 'descricao', 'quantidade', 'valor_total', 'valor_unitario', 'ncm', 'cfop'
            )
        )
        if not df_produtos.empty:
            df_produtos.rename(columns={'nfe_serie_id': 'id_identificacao'}, inplace=True)
            df_produtos['valor_unitario'] = pd.to_numeric(df_produtos['valor_unitario'], errors='coerce').fillna(0)
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

        if self.tipo_relatorio == "Compras":
            df_filial = self._build_filial(g_q_nfe)
            if not df_filial.empty:
                df_merged = df_merged.merge(df_filial, on='id_identificacao', how='left')
            if 'cod_filial' not in df_merged.columns:
                df_merged['cod_filial'] = None
            if 'nome_filial' not in df_merged.columns:
                df_merged['nome_filial'] = None

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
            df_custo_linhas=pd.DataFrame(),
            df_custo_rank_cliente=pd.DataFrame(),
            df_custo_rank_cidade=pd.DataFrame(),
            custo_detail_limit=0,
            custo_detail_truncated=False,
        )

    def _process_custo(
        self,
        empresas_queryset,
        empresa_selecionada: str,
        usar_periodo: bool,
        data_inicio,
        data_fim,
    ) -> DashboardData | None:
        """
        Relatório de custo: agregações no PostgreSQL (sem carregar milhões de linhas).
        CFOP já normalizado (strip) na carga; índice parcial (migration 0069) alinha com o filtro.
        """
        from decimal import Decimal

        from django.db.models import DecimalField, Sum, Value
        from django.db.models.functions import Coalesce, ExtractMonth, ExtractYear

        from app.db_GDF.Sap.models import RelatorioCusto

        lsl_cod_empresa = list(empresas_queryset.values_list('cod_empresa', flat=True))
        if empresa_selecionada and empresa_selecionada not in ("Todas", "Todas as empresas"):
            cod_empresa = empresa_selecionada.split(" - ")[0].strip()
            lsl_cod_empresa = [cod_empresa]

        q = (
            RelatorioCusto.objects.filter(
                empresa__cod_empresa__in=lsl_cod_empresa,
                cfop__in=RELATORIO_CUSTO_CFOP_LIST,
            )
            .select_related('empresa')
        )
        if usar_periodo and data_inicio and data_fim:
            q = q.filter(pstdat__range=(data_inicio, data_fim))

        z18 = Value(Decimal('0'), output_field=DecimalField(max_digits=18, decimal_places=2))
        z16 = Value(Decimal('0'), output_field=DecimalField(max_digits=16, decimal_places=3))
        z10 = Value(Decimal('0'), output_field=DecimalField(max_digits=10, decimal_places=2))

        qd = q.exclude(pstdat__isnull=True)

        def _sum18(field):
            return Coalesce(Sum(field), z18)

        def _sum16(field):
            return Coalesce(Sum(field), z16)

        def _sum10(field):
            return Coalesce(Sum(field), z10)

        # --- Série mensal por empresa (para gráficos) ---
        mrows = list(
            qd.annotate(ano=ExtractYear('pstdat'), mes=ExtractMonth('pstdat'))
            .values('empresa__cod_empresa', 'empresa__fantasia', 'empresa__razao', 'ano', 'mes')
            .annotate(
                vlr_tot_doc=_sum18('vlr_tot_doc'),
                total_impostos=_sum10('total_impostos'),
                margem_contrib_ger=_sum18('margem_contrib_ger'),
                cmv_gerencial=_sum18('cmv_gerencial'),
                qtd_prod=_sum16('qtd_prod'),
                vlr_liquido=_sum18('vlr_liquido'),
            )
        )
        if not mrows:
            return None

        df_merged = pd.DataFrame.from_records(mrows)
        df_merged['empresa'] = (
            df_merged['empresa__fantasia']
            .fillna(df_merged['empresa__razao'])
            .fillna(df_merged['empresa__cod_empresa'])
            .astype(str)
            .str.strip()
        )
        bad_empresa = df_merged['empresa'].isin(('', 'nan'))
        if bad_empresa.any():
            df_merged.loc[bad_empresa, 'empresa'] = df_merged.loc[bad_empresa, 'empresa__cod_empresa'].astype(str)
        df_merged = df_merged.rename(columns={
            'vlr_tot_doc': 'Faturamento',
            'total_impostos': 'Total Impostos',
            'margem_contrib_ger': 'Margem Contrib. Gerencial',
            'cmv_gerencial': 'CMV Gerencial',
            'qtd_prod': 'Quantidade Total',
            'vlr_liquido': 'Valor Líquido',
        })
        for col in (
            'Faturamento', 'Total Impostos', 'Margem Contrib. Gerencial',
            'CMV Gerencial', 'Quantidade Total', 'Valor Líquido',
        ):
            if col in df_merged.columns:
                df_merged[col] = pd.to_numeric(df_merged[col], errors='coerce').fillna(0)
        df_merged['mes_nome'] = df_merged['mes'].map(
            lambda m: _MESES_NOMES_CUSTO[int(m) - 1] if m and 1 <= int(m) <= 12 else ''
        )

        # --- Grupo de mercadorias (agregado no banco) ---
        grows = list(
            qd.values('wgbez', 'matkl').annotate(
                valor_total=_sum18('vlr_tot_doc'),
                quantidade=_sum16('qtd_prod'),
                total_impostos=_sum10('total_impostos'),
                cmv_ger=_sum18('cmv_gerencial'),
                margem_ger=_sum18('margem_contrib_ger'),
            )
        )
        df_gr = pd.DataFrame.from_records(grows) if grows else pd.DataFrame()
        if not df_gr.empty:
            wg = df_gr['wgbez'].fillna('').astype(str).str.strip()
            mk = df_gr['matkl'].fillna('').astype(str).str.strip()
            df_gr['descricao'] = wg.where(wg != '', mk)
            df_gr['descricao'] = df_gr['descricao'].mask(df_gr['descricao'] == '', 'Sem grupo')
            df_produtos = pd.DataFrame({
                'descricao': df_gr['descricao'],
                'valor_total': pd.to_numeric(df_gr['valor_total'], errors='coerce').fillna(0),
                'quantidade': pd.to_numeric(df_gr['quantidade'], errors='coerce').fillna(0),
                'total_impostos': pd.to_numeric(df_gr['total_impostos'], errors='coerce').fillna(0),
                'CMV Gerencial': pd.to_numeric(df_gr['cmv_ger'], errors='coerce').fillna(0),
                'Margem Contrib. Gerencial': pd.to_numeric(df_gr['margem_ger'], errors='coerce').fillna(0),
            })
        else:
            df_produtos = pd.DataFrame()

        # --- Ranking: um registro por cliente / por cidade (pré-agregado) ---
        crows = list(
            qd.exclude(stcd1__isnull=True)
            .exclude(stcd1='')
            .values('stcd1', 'name1')
            .annotate(
                Faturamento=_sum18('vlr_tot_doc'),
                sum_qtd=_sum16('qtd_prod'),
                sum_imp=_sum10('total_impostos'),
                sum_vlr_liq=_sum18('vlr_liquido'),
                sum_margem=_sum18('margem_contrib_ger'),
                sum_cmv=_sum18('cmv_gerencial'),
            )
        )
        df_rc = pd.DataFrame.from_records(crows) if crows else pd.DataFrame()
        if not df_rc.empty:
            df_rc = df_rc.rename(columns={
                'stcd1': 'cnpj_cliente',
                'name1': 'nome_cliente',
                'sum_qtd': 'Quantidade Total',
                'sum_imp': 'Total Impostos',
                'sum_vlr_liq': 'Valor Líquido',
                'sum_margem': 'Margem Contrib. Gerencial',
                'sum_cmv': 'CMV Gerencial',
            })
            for col in (
                'Faturamento', 'Quantidade Total', 'Total Impostos', 'Valor Líquido',
                'Margem Contrib. Gerencial', 'CMV Gerencial',
            ):
                if col in df_rc.columns:
                    df_rc[col] = pd.to_numeric(df_rc[col], errors='coerce').fillna(0)

        city_rows = list(
            qd.exclude(ort01__isnull=True)
            .exclude(ort01='')
            .values('ort01')
            .annotate(
                Faturamento=_sum18('vlr_tot_doc'),
                sum_qtd=_sum16('qtd_prod'),
                sum_imp=_sum10('total_impostos'),
                sum_vlr_liq=_sum18('vlr_liquido'),
                sum_margem=_sum18('margem_contrib_ger'),
                sum_cmv=_sum18('cmv_gerencial'),
            )
        )
        df_rct = pd.DataFrame.from_records(city_rows) if city_rows else pd.DataFrame()
        if not df_rct.empty:
            df_rct = df_rct.rename(columns={
                'ort01': 'cidade',
                'sum_qtd': 'Quantidade Total',
                'sum_imp': 'Total Impostos',
                'sum_vlr_liq': 'Valor Líquido',
                'sum_margem': 'Margem Contrib. Gerencial',
                'sum_cmv': 'CMV Gerencial',
            })
            for col in (
                'Faturamento', 'Quantidade Total', 'Total Impostos', 'Valor Líquido',
                'Margem Contrib. Gerencial', 'CMV Gerencial',
            ):
                if col in df_rct.columns:
                    df_rct[col] = pd.to_numeric(df_rct[col], errors='coerce').fillna(0)

        # --- Amostra da tabela detalhada (LIMIT) ---
        limit = CUSTO_DASHBOARD_DETAIL_LIMIT
        detail_cols = (
            'pstdat', 'docnum', 'matnr', 'maktx', 'matkl', 'wgbez', 'cfop',
            'stcd1', 'name1', 'ort01',
            'vlr_tot_doc', 'total_impostos', 'margem_contrib_ger',
            'cmv_gerencial', 'qtd_prod', 'vlr_liquido',
            'empresa__cod_empresa', 'empresa__fantasia', 'empresa__razao',
        )
        detail_qs = qd.order_by('-pstdat', 'docnum', 'matnr')[:limit]
        dlines = list(detail_qs.values(*detail_cols))
        truncated = len(dlines) >= limit

        df_custo = pd.DataFrame.from_records(dlines) if dlines else pd.DataFrame()
        if not df_custo.empty:
            df_custo['pstdat'] = pd.to_datetime(df_custo['pstdat'], errors='coerce')
            df_custo['empresa'] = (
                df_custo['empresa__fantasia']
                .fillna(df_custo['empresa__razao'])
                .fillna(df_custo['empresa__cod_empresa'])
                .astype(str)
                .str.strip()
            )
            bad = df_custo['empresa'].isin(('', 'nan'))
            if bad.any():
                df_custo.loc[bad, 'empresa'] = df_custo.loc[bad, 'empresa__cod_empresa'].astype(str)
            for col in (
                'vlr_tot_doc', 'total_impostos', 'margem_contrib_ger', 'cmv_gerencial',
                'qtd_prod', 'vlr_liquido',
            ):
                df_custo[col] = pd.to_numeric(df_custo[col], errors='coerce').fillna(0)
            df_custo['cnpj_cliente'] = df_custo['stcd1'].fillna('').astype(str).str.strip()
            df_custo['nome_cliente'] = df_custo['name1'].fillna('').astype(str).str.strip()
            df_custo['cidade'] = df_custo['ort01'].fillna('').astype(str).str.strip()
            df_custo['Faturamento'] = df_custo['vlr_tot_doc']
            df_custo['Quantidade Total'] = df_custo['qtd_prod']
            df_custo['Total Impostos'] = df_custo['total_impostos']
            df_custo['Valor Líquido'] = df_custo['vlr_liquido']
            df_custo['Margem Contrib. Gerencial'] = df_custo['margem_contrib_ger']
            df_custo['CMV Gerencial'] = df_custo['cmv_gerencial']

        return DashboardData(
            df_merged=df_merged,
            df_produtos=df_produtos,
            df_parcelas=pd.DataFrame(),
            df_pagamento=pd.DataFrame(),
            tipo_relatorio='Custo',
            g_q_nfe=RelatorioCusto.objects.none(),
            df_custo_linhas=df_custo,
            df_custo_rank_cliente=df_rc,
            df_custo_rank_cidade=df_rct,
            custo_detail_limit=limit,
            custo_detail_truncated=truncated,
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
                    'emitente__endereco__uf',
                )
            )
            if not df.empty:
                df.rename(columns={
                    'identificacao_id': 'id_identificacao',
                    'emitente__cnpj': 'cnpj_fornecedor',
                    'emitente__razao_social': 'nome_fornecedor',
                    'emitente__nome_fantasia': 'nome_fantasia_fornecedor',
                    'emitente__endereco__uf': 'uf_fornecedor',
                }, inplace=True)
                df['nome_cliente'] = df['nome_fornecedor'].fillna(df['nome_fantasia_fornecedor'])
                df['cnpj_cliente'] = df['cnpj_fornecedor']
                if 'uf_fornecedor' not in df.columns:
                    df['uf_fornecedor'] = None
            else:
                df = pd.DataFrame(columns=['id_identificacao', 'cnpj_fornecedor', 'nome_fornecedor', 'nome_cliente', 'cnpj_cliente', 'uf_fornecedor'])
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
            if 'uf_fornecedor' not in df_merged.columns:
                df_merged['uf_fornecedor'] = None

    def _build_filial(self, g_q_nfe):
        """Para Compras: retorna id_identificacao, cod_filial, nome_filial."""
        from app.db_GDF.NFe.models import NFe

        df = pd.DataFrame.from_records(
            NFe.objects.filter(identificacao__in=g_q_nfe).values(
                'identificacao_id',
                'filial__cod_filial',
                'filial__nome',
            )
        )
        if not df.empty:
            df.rename(columns={
                'identificacao_id': 'id_identificacao',
                'filial__cod_filial': 'cod_filial',
                'filial__nome': 'nome_filial',
            }, inplace=True)
        return df

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
