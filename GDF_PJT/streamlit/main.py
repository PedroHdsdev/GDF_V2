import os
import sys
import numpy                as np
import streamlit            as st
import pandas               as pd
import altair               as alt
import tp_graficos_Vendas   as tv 
import tp_graficos_Compras  as tc
import tp_lists_Vendas      as lv_v
import tp_lists_Compras     as lv_c
from datetime               import date
from django.core.cache      import cache

# ============================================================
# Configuração inicial Streamlit
# ============================================================
st.set_page_config(page_title="Dashboard GDF", layout="wide")

# ============================================================
# APLICAR TEMA CUSTOMIZADO (FILTROS AZUIS)
# ============================================================
st.markdown("""
    <style>
    /* Multiselect - Tags em Azul */
    [data-baseweb="tag"] {
        background-color: #1f77d4 !important;
        color: white !important;
    }
    
    /* Selectbox - Azul */
    .stSelectbox [data-baseweb="select"] input:focus {
        border-color: #1f77d4 !important;
        box-shadow: 0 0 0 3px rgba(31, 119, 212, 0.2) !important;
    }
    
    /* Radio Button - Azul */
    [role="radio"] {
        accent-color: #1f77d4 !important;
    }
    
    /* Checkbox - Azul */
    [role="checkbox"] {
        accent-color: #1f77d4 !important;
    }
    
    /* Slider - Azul */
    .stSlider input[type="range"] {
        accent-color: #1f77d4 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ============================================================
# Inicializa o ambiente Django
# ============================================================
@st.cache_resource
def init_django():
    g_v_base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if g_v_base_dir not in sys.path:
        sys.path.append(g_v_base_dir)
    
    g_v_gdf_pjt_dir = os.path.join(g_v_base_dir, 'GDF_PJT')
    if g_v_gdf_pjt_dir not in sys.path:
        sys.path.insert(0, g_v_gdf_pjt_dir)

    import django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "GDF_PJT.settings")
    django.setup()

init_django()

# Imports Django depois do setup
from django.contrib.auth.models import User, Group
from app.db_GDF.Public.models import Empresas
from app.db_GDF.NFe.models import (
    NFe_Identificacao, NFe_Total, NFe_Produto, NFe_Destinatario, NFe,
    NFe_Cobranca, NFe_Parcela,
)
from django.db.models import Q
from django.conf import settings

# ✅ JWT com fallback
try:
    from jwt import decode as jwt_decode
except ImportError:
    try:
        import jwt as jwt_module
        jwt_decode = jwt_module.decode
    except (ImportError, AttributeError):
        jwt_decode = None

# ============================================================
# Autenticação
# ============================================================
token = st.query_params.get("token")

if not token:
    st.error("Acesso negado")
    st.stop()

if jwt_decode is None:
    st.error("❌ JWT não disponível no servidor")
    st.stop()

try:
    g_v_payload = jwt_decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    l_v_username = g_v_payload["username"]
    l_v_user_id = g_v_payload["user_id"]
    l_v_tipo_relatorio = g_v_payload.get("tipo_relatorio", "Vendas")
    
    st.session_state["username"] = l_v_username
    st.session_state["user_id"] = l_v_user_id
    st.session_state["tipo_relatorio"] = l_v_tipo_relatorio
    
except Exception as err_token:
    st.error(f"❌ Erro de autenticação: {str(err_token)}")
    st.stop()

# ============================================================
# Verificação de usuário e empresas
# ============================================================
try:
    l_q_User = User.objects.get(username=l_v_username)
    g_q_Empresas = Empresas.objects.filter(
        userempresas__user=l_q_User
    ).distinct()
    
    if not g_q_Empresas:
        st.error("❌ Usuário sem empresa vinculada")
        st.stop()
        
except User.DoesNotExist:
    st.error("❌ Usuário inválido")
    st.stop()

# ============================================================
# Título e informações
# ============================================================
st.title(f"📊 Dashboard de {l_v_tipo_relatorio}")

if "username" in st.session_state:
    st.sidebar.markdown(f"👤 **Usuário:** {st.session_state['username']}")
    st.sidebar.markdown(f"📄 **Relatório:** {st.session_state['tipo_relatorio']}")
    st.sidebar.divider()

# ============================================================
# FILTROS SIDEBAR
# ============================================================
st.sidebar.markdown("### 🔍 Filtros")

# Empresa
g_q_Empresas_filtradas = g_q_Empresas.order_by('cod_empresa')
l_v_empresas_display = ["Todas"] + [f"{emp.cod_empresa} - {emp.razao}" for emp in g_q_Empresas_filtradas]
g_v_empresa_selecionada = st.sidebar.selectbox(
    "Empresa",
    options=l_v_empresas_display,
    label_visibility="collapsed",
    key="empresa_filter"
)

# Período
st.sidebar.markdown("**Período:**")
g_v_usar_periodo = st.sidebar.checkbox("Usar período", value=True, key="usar_periodo")

if g_v_usar_periodo:
    col_dt1, col_dt2 = st.sidebar.columns(2)
    data_inicio = col_dt1.date_input(
        "De",
        value=date.today().replace(day=1),
        format="DD/MM/YYYY",
        label_visibility="collapsed",
        key="data_inicio"
    )
    data_fim = col_dt2.date_input(
        "Até",
        value=date.today(),
        format="DD/MM/YYYY",
        label_visibility="collapsed",
        key="data_fim"
    )
else:
    data_inicio = None
    data_fim = None

st.sidebar.divider()

# ============================================================
# CONSTRUIR QUERIES
# ============================================================
tipo_relatorio = st.session_state.get("tipo_relatorio", "Vendas")
l_v_tipo_operacao = '1' if tipo_relatorio == "Vendas" else '0'

# Lista de empresas
lsl_g_cod_empresa = list(g_q_Empresas.values_list('cod_empresa', flat=True))
if g_v_empresa_selecionada != "Todas":
    l_v_cod_empresa = g_v_empresa_selecionada.split(" - ")[0]
    lsl_g_cod_empresa = [l_v_cod_empresa]

# Query base
g_q_identificacoes = NFe_Identificacao.objects.filter(
    tipo_operacao=l_v_tipo_operacao
)

# Filtro de período
if g_v_usar_periodo and data_inicio and data_fim:
    g_q_identificacoes = g_q_identificacoes.filter(
        emissao__date__range=(data_inicio, data_fim)
    )

# Filtro de empresa
g_q_nfe = g_q_identificacoes.filter(
    nfe__empresa__cod_empresa__in=lsl_g_cod_empresa
).distinct()

if not g_q_nfe.exists():
    st.warning("⚠️ Nenhum dado encontrado para os filtros selecionados")
    st.stop()

# ============================================================
# CONSTRUIR DATAFRAMES
# ============================================================

# ✅ DataFrame 1: Identificações
df_header = pd.DataFrame.from_records(
    g_q_nfe.values(
        'id_identificacao', 'numero', 'serie', 'emissao', 'tipo_operacao'
    )
)

# ✅ DataFrame 2: Totais (OneToOne com Identificacao)
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

# ✅ DataFrame 3: Produtos (ForeignKey nfe_serie para Identificacao)
df_produtos = pd.DataFrame.from_records(
    NFe_Produto.objects.filter(nfe_serie__in=g_q_nfe).values(
        'nfe_serie_id', 'descricao', 'quantidade', 'valor_total', 'ncm', 'cfop'
    )
)

if not df_produtos.empty:
    df_produtos.rename(columns={'nfe_serie_id': 'id_identificacao'}, inplace=True)
else:
    df_produtos = pd.DataFrame()

# ✅ DataFrame 4: Para Vendas = Destinatários (cliente); Para Compras = Emitente (fornecedor)
if tipo_relatorio == "Compras":
    df_contraparte = pd.DataFrame.from_records(
        NFe.objects.filter(identificacao__in=g_q_nfe).values(
            'identificacao_id',
            'emitente__cnpj',
            'emitente__razao_social',
            'emitente__nome_fantasia',
        )
    )
    if not df_contraparte.empty:
        df_contraparte.rename(columns={
            'identificacao_id': 'id_identificacao',
            'emitente__cnpj': 'cnpj_fornecedor',
            'emitente__razao_social': 'nome_fornecedor',
            'emitente__nome_fantasia': 'nome_fantasia_fornecedor',
        }, inplace=True)
        df_contraparte['nome_cliente'] = df_contraparte['nome_fornecedor'].fillna(df_contraparte['nome_fantasia_fornecedor'])
        df_contraparte['cnpj_cliente'] = df_contraparte['cnpj_fornecedor']
    else:
        df_contraparte = pd.DataFrame()
else:
    df_contraparte = pd.DataFrame.from_records(
        NFe.objects.filter(identificacao__in=g_q_nfe).values(
            'identificacao_id',
            'destinatario__documento',
            'destinatario__razao_social',
            'destinatario__endereco__nome_municipio',
            'destinatario__endereco__uf',
        )
    )
    if not df_contraparte.empty:
        df_contraparte.rename(columns={
            'identificacao_id': 'id_identificacao',
            'destinatario__documento': 'cnpj_cliente',
            'destinatario__razao_social': 'nome_cliente',
            'destinatario__endereco__nome_municipio': 'cidade',
            'destinatario__endereco__uf': 'estado',
        }, inplace=True)
    else:
        df_contraparte = pd.DataFrame()

if tipo_relatorio == "Compras" and df_contraparte.empty:
    df_contraparte = pd.DataFrame()
    df_contraparte['id_identificacao'] = []
    df_contraparte['cnpj_fornecedor'] = None
    df_contraparte['nome_fornecedor'] = None
    df_contraparte['nome_cliente'] = None
    df_contraparte['cnpj_cliente'] = None
elif tipo_relatorio != "Compras" and df_contraparte.empty:
    df_contraparte['cidade'] = None
    df_contraparte['estado'] = None

# ✅ DataFrame 4b (Compras): Parcelas para prazo de pagamento e fluxo de caixa
df_parcelas = pd.DataFrame()
if tipo_relatorio == "Compras":
    parcelas_raw = NFe_Parcela.objects.filter(
        nfe_cobranca__nfe_identificacao__in=g_q_nfe
    ).values(
        'nfe_cobranca__nfe_identificacao_id',
        'data_vencimento', 'valor_parcela', 'numero_parcela'
    )
    df_parcelas = pd.DataFrame.from_records(parcelas_raw)
    if not df_parcelas.empty:
        df_parcelas.rename(columns={'nfe_cobranca__nfe_identificacao_id': 'id_identificacao'}, inplace=True)
        df_parcelas['data_vencimento'] = pd.to_datetime(df_parcelas['data_vencimento'])
        df_parcelas['valor_parcela'] = pd.to_numeric(df_parcelas['valor_parcela'], errors='coerce').fillna(0)

# ✅ Merge 1: Header + Totais
df_merged = df_header.merge(df_totais, on='id_identificacao', how='left')

# ✅ Merge 1.5: Adicionar dados de contraparte (cliente ou fornecedor)
if not df_contraparte.empty:
    cols_merge = [c for c in df_contraparte.columns if c != 'id_identificacao']
    df_merged = df_merged.merge(df_contraparte[['id_identificacao'] + cols_merge], on='id_identificacao', how='left')
if tipo_relatorio != "Compras":
    if 'cidade' not in df_merged.columns:
        df_merged['cidade'] = None
    if 'estado' not in df_merged.columns:
        df_merged['estado'] = None
if tipo_relatorio == "Compras":
    if 'nome_fornecedor' not in df_merged.columns:
        df_merged['nome_fornecedor'] = None
    if 'cnpj_fornecedor' not in df_merged.columns:
        df_merged['cnpj_fornecedor'] = None

# ✅ Merge 2: Agregar produtos por NFe
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

# ✅ Converter datas e criar colunas de agregação
df_merged['emissao'] = pd.to_datetime(df_merged['emissao'])
df_merged['ano'] = df_merged['emissao'].dt.year
df_merged['mes'] = df_merged['emissao'].dt.month
df_merged['mes_nome'] = df_merged['emissao'].dt.strftime('%b')
df_merged['Data Postagem'] = df_merged['emissao'].dt.date

# ✅ Criar colunas de métricas
df_merged['Faturamento'] = df_merged['valor_total_nfe'].fillna(0)
df_merged['Total Impostos'] = (
    df_merged['valor_icms'].fillna(0) + 
    df_merged['valor_ipi'].fillna(0) + 
    df_merged['valor_pis'].fillna(0) + 
    df_merged['valor_cofins'].fillna(0)
)
df_merged['Valor Líquido'] = df_merged['Faturamento'] - df_merged['Total Impostos']
df_merged['Quantidade Total'] = df_merged['quantidade'].fillna(0)
# Compras: créditos tributários (ICMS, PIS, COFINS recuperáveis)
df_merged['Credito_ICMS'] = df_merged['valor_icms'].fillna(0)
df_merged['Credito_PIS'] = df_merged['valor_pis'].fillna(0)
df_merged['Credito_COFINS'] = df_merged['valor_cofins'].fillna(0)
df_merged['Credito_Tributario_Total'] = (
    df_merged['Credito_ICMS'] + df_merged['Credito_PIS'] + df_merged['Credito_COFINS']
)

if df_merged.empty:
    st.warning("⚠️ Nenhum dado disponível para gráficos")
    st.stop()

# ============================================================
# SEÇÃO DE GRÁFICOS
# ============================================================
st.markdown("---")
st.subheader("📈 Análise de Dados")

# Seleção de módulo de gráficos
grafico_mod = tv if tipo_relatorio == "Vendas" else tc
lv = lv_v if tipo_relatorio == "Vendas" else lv_c

# ============================================================
# TAB 1: EVOLUÇÃO TEMPORAL
# ============================================================
tab_evolucao, tab_comparacao = st.tabs(["📈 Evolução Temporal", "⚖️ Comparativo"])

with tab_evolucao:
    st.markdown("### Análise de Tendências ao Longo do Tempo")
    
    col_filtro1, col_filtro2, col_filtro3 = st.columns([2, 2, 2])
    
    with col_filtro1:
        metricas_disponiveis = ["Faturamento", "Total Impostos", "Valor Líquido"]
        if tipo_relatorio == "Compras":
            metricas_disponiveis = metricas_disponiveis + ["Credito_Tributario_Total"]
        metricas_selecionadas = st.multiselect(
            "Métricas",
            options=metricas_disponiveis,
            default=["Faturamento"],
            key="tab1_metricas"
        )
    
    with col_filtro2:
        anos_disponiveis = sorted(df_merged['ano'].unique())
        anos_selecionados = st.multiselect(
            "Anos",
            options=anos_disponiveis,
            default=anos_disponiveis[-1:] if anos_disponiveis else [],
            key="tab1_anos"
        )
    
    with col_filtro3:
        periodo_value = st.radio(
            "Período",
            options=["Mensal", "Anual"],
            horizontal=True,
            key="tab1_periodo"
        )
    
    if metricas_selecionadas and anos_selecionados:
        try:
            g_linha = grafico_mod.Grafico_linha(df_merged)
            g_linha.G_multiplas_metricas(
                coluna_data='mes_nome',
                coluna_ano='ano',
                metricas=metricas_selecionadas,
                filtro_anos=anos_selecionados,
                periodo=periodo_value,
                titulo=f"Evolução {periodo_value} - {', '.join(metricas_selecionadas)}"
            )
        except Exception as err_graph:
            st.error(f"❌ Erro ao gerar gráfico: {str(err_graph)}")
    else:
        st.info("ℹ️ Selecione métricas e anos para visualizar")

# ============================================================
# TAB 2: COMPARATIVO
# ============================================================
with tab_comparacao:
    st.markdown("### Análise Comparativa")
    
    col_comp1, col_comp2, col_comp3 = st.columns([2, 2, 2])
    
    with col_comp1:
        tipo_comparacao = st.radio(
            "Tipo de Comparação",
            options=["Mês vs Mês", "Ano vs Ano", "Mês em Anos Diferentes"],
            key="tipo_comp"
        )
    
    with col_comp2:
        metrica_comp = st.selectbox(
            "Métrica",
            options=["Faturamento", "Total Impostos", "Quantidade Total"],
            key="metrica_comp"
        )
    
    # Filtros dinâmicos por tipo de comparação
    if tipo_comparacao == "Mês vs Mês":
        meses_disponiveis = sorted(df_merged['mes'].unique())
        mes_select = st.multiselect(
            "Selecione 2+ meses",
            options=meses_disponiveis,
            key="mes_select_1"
        )
        anos_select = None
    
    elif tipo_comparacao == "Ano vs Ano":
        anos_disponiveis = sorted(df_merged['ano'].unique())
        anos_select = st.multiselect(
            "Selecione 2+ anos",
            options=anos_disponiveis,
            key="anos_select_1"
        )
        mes_select = None
    
    else:  # Mês em Anos Diferentes
        meses_disponiveis = sorted(df_merged['mes'].unique())
        mes_select = st.multiselect(
            "Selecione 1 mês",
            options=meses_disponiveis,
            max_selections=1,
            key="mes_select_2"
        )
        anos_disponiveis = sorted(df_merged['ano'].unique())
        anos_select = st.multiselect(
            "Selecione 2+ anos",
            options=anos_disponiveis,
            key="anos_select_2"
        )
    
    # Renderizar gráfico comparativo
    if metrica_comp:
        try:
            g_comp = grafico_mod.Grafico_comparacao(df_merged)
            g_comp.G_comparacao_anos_meses(
                tipo_comparacao=tipo_comparacao,
                metrica=metrica_comp,
                anos_select=anos_select,
                mes_select=mes_select
            )
        except Exception as err_comp:
            st.error(f"❌ Erro ao gerar comparativo: {str(err_comp)}")
    else:
        st.info("ℹ️ Selecione uma métrica")

# ============================================================
# TAB 3: RANKS (VENDAS = Clientes/Cidades; COMPRAS = Fornecedores)
# ============================================================
_tab_rank_title = "📊 Ranking de Fornecedores" if tipo_relatorio == "Compras" else "📊 Ranks de Vendas"
with st.tabs([_tab_rank_title])[0]:
    st.markdown("### 🏆 Ranking por valor (dependência de fornecedores / clientes)" if tipo_relatorio == "Compras" else "### 🏆 Ranking de Vendas (por Cliente e Localização)")
    
    col_rank1, col_rank2 = st.columns(2)
    
    with col_rank1:
        if tipo_relatorio == "Compras":
            dimensao_rank = "Fornecedores (CNPJ)"
        else:
            dimensao_rank = st.selectbox(
                "Dimensão para ranking",
                options=["Cidades", "Clientes (CNPJ)"],
                key="rank_dimensao"
            )
    
    with col_rank2:
        metrica_rank = st.selectbox(
            "Métrica",
            options=["Faturamento", "Quantidade Total", "Total Impostos"],
            key="rank_metrica"
        )
    
    try:
        df_rank_src = df_merged.copy()
        df_rank_src['Faturamento'] = pd.to_numeric(df_rank_src['Faturamento'], errors='coerce').fillna(0)
        df_rank_src['Quantidade Total'] = pd.to_numeric(df_rank_src['Quantidade Total'], errors='coerce').fillna(0)
        df_rank_src['Total Impostos'] = pd.to_numeric(df_rank_src['Total Impostos'], errors='coerce').fillna(0)
        col_sort = 'Faturamento' if metrica_rank == "Faturamento" else ('Quantidade Total' if metrica_rank == "Quantidade Total" else 'Total Impostos')
        
        if tipo_relatorio == "Compras" or dimensao_rank == "Fornecedores (CNPJ)":
            # Compras: agrupar por fornecedor (emitente)
            key_cnpj = 'cnpj_fornecedor' if tipo_relatorio == "Compras" else 'cnpj_cliente'
            key_nome = 'nome_fornecedor' if tipo_relatorio == "Compras" else 'nome_cliente'
            df_rank = df_rank_src.dropna(subset=[key_cnpj]).groupby([key_cnpj, key_nome]).agg({
                'Faturamento': 'sum', 'Quantidade Total': 'sum', 'Total Impostos': 'sum'
            }).reset_index()
            df_rank['cliente_label'] = df_rank[key_cnpj].astype(str) + ' - ' + df_rank[key_nome].fillna('S/N')
            df_rank = df_rank.nlargest(10, col_sort)
            chart_rank = alt.Chart(df_rank).mark_bar().encode(
                y=alt.Y('cliente_label:N', title='Fornecedor' if tipo_relatorio == "Compras" else 'Cliente', sort=alt.EncodingSortField(field=col_sort, order='descending')),
                x=alt.X(f'{col_sort}:Q', title=col_sort),
                color=alt.value('#1f77d4')
            ).properties(height=500, title=f"Top 10 Fornecedores por {col_sort}" if tipo_relatorio == "Compras" else f"Top 10 Clientes por {col_sort}")
            st.altair_chart(chart_rank, use_container_width=True)
        elif dimensao_rank == "Cidades":
            df_rank = df_rank_src.dropna(subset=['cidade']).groupby('cidade').agg({
                'Faturamento': 'sum', 'Quantidade Total': 'sum', 'Total Impostos': 'sum'
            }).reset_index()
            df_rank = df_rank.nlargest(10, col_sort)
            chart_rank = alt.Chart(df_rank).mark_bar().encode(
                y=alt.Y('cidade:N', title='Cidade', sort=alt.EncodingSortField(field=col_sort, order='descending')),
                x=alt.X(f'{col_sort}:Q', title=col_sort),
                color=alt.value('#1f77d4')
            ).properties(height=400, title=f"Top 10 Cidades por {col_sort}")
            st.altair_chart(chart_rank, use_container_width=True)
    except Exception as err_rank:
        st.error(f"❌ Erro ao gerar ranking: {str(err_rank)}")

# ============================================================
# TAB 4: GRUPO DE MERCADORIAS
# ============================================================
with st.tabs(["📦 Grupo de Mercadorias"])[0]:
    st.markdown("### 📦 Análise por Grupo de Mercadorias")
    
    col_grp1, col_grp2 = st.columns(2)
    
    with col_grp1:
        metrica_grp = st.selectbox(
            "Métrica",
            options=["Faturamento", "Quantidade Total", "Total Impostos"],
            key="grp_metrica"
        )
    
    with col_grp2:
        top_n = st.slider(
            "Top N produtos",
            min_value=5,
            max_value=50,
            value=10,
            key="grp_top"
        )
    
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
            color=alt.value('#1f77d4')
        ).properties(height=max(300, len(df_grp) * 25), title=f"Top {top_n} Produtos por {metrica_grp}")
        
        st.altair_chart(chart_grp, use_container_width=True)
    
    except Exception as err_grp:
        st.error(f"❌ Erro ao gerar grupo de mercadorias: {str(err_grp)}")

# ============================================================
# SEÇÃO COMPRAS: Análises financeiras, fiscais e estratégicas
# ============================================================
if tipo_relatorio == "Compras":
    st.markdown("---")
    st.subheader("📊 Análise de NF-e de Entrada (Compras)")
    tab_prazo, tab_parcelas, tab_cfop, tab_creditos, tab_abc = st.tabs([
        "⏱️ Prazo médio de pagamento",
        "📅 Parcelamento e fluxo de caixa",
        "📋 Distribuição por CFOP",
        "💰 Créditos tributários",
        "📈 Curva ABC (concentração)",
    ])
    
    with tab_prazo:
        st.markdown("### Prazo médio de pagamento (emissão → vencimento)")
        if not df_parcelas.empty and 'id_identificacao' in df_parcelas.columns:
            df_emissao = df_merged[['id_identificacao', 'emissao']].drop_duplicates()
            df_prazo = df_parcelas.merge(df_emissao, on='id_identificacao', how='left')
            df_prazo['emissao'] = pd.to_datetime(df_prazo['emissao'])
            df_prazo['dias_prazo'] = (pd.to_datetime(df_prazo['data_vencimento']) - df_prazo['emissao'].dt.normalize()).dt.days
            df_prazo['valor_parcela'] = pd.to_numeric(df_prazo['valor_parcela'], errors='coerce').fillna(0)
            total_valor = df_prazo['valor_parcela'].sum()
            if total_valor and total_valor > 0:
                prazo_medio = (df_prazo['dias_prazo'] * df_prazo['valor_parcela']).sum() / total_valor
                st.metric("Prazo médio ponderado (dias)", f"{prazo_medio:.0f} dias")
            else:
                prazo_medio = df_prazo['dias_prazo'].mean()
                st.metric("Prazo médio simples (dias)", f"{prazo_medio:.0f} dias")
            # Por fornecedor: prazo médio ponderado = sum(dias * valor) / sum(valor)
            df_prazo_f = df_prazo.merge(df_merged[['id_identificacao', 'nome_fornecedor', 'cnpj_fornecedor']].drop_duplicates(), on='id_identificacao', how='left')
            df_prazo_f['dias_x_valor'] = df_prazo_f['dias_prazo'] * df_prazo_f['valor_parcela']
            agg_f = df_prazo_f.groupby(['cnpj_fornecedor', 'nome_fornecedor']).agg(
                valor_total=('valor_parcela', 'sum'),
                soma_dias_valor=('dias_x_valor', 'sum')
            ).reset_index()
            agg_f['prazo_medio_dias'] = np.where(agg_f['valor_total'] > 0, agg_f['soma_dias_valor'] / agg_f['valor_total'], 0)
            agg_f = agg_f[agg_f['valor_total'] > 0].nlargest(10, 'valor_total')
            if not agg_f.empty:
                agg_f['label'] = agg_f['cnpj_fornecedor'].astype(str) + ' - ' + agg_f['nome_fornecedor'].fillna('S/N')
                chart_prazo = alt.Chart(agg_f).mark_bar().encode(
                    y=alt.Y('label:N', sort=alt.EncodingSortField(field='prazo_medio_dias', order='descending')),
                    x=alt.X('prazo_medio_dias:Q', title='Prazo médio (dias)'),
                    color=alt.value('#1f77d4')
                ).properties(height=400, title="Prazo médio por fornecedor (Top 10 por valor)")
                st.altair_chart(chart_prazo, use_container_width=True)
        else:
            st.info("ℹ️ Nenhuma parcela de pagamento cadastrada nas NF-e do período.")
    
    with tab_parcelas:
        st.markdown("### Impacto no fluxo de caixa (vencimentos por período)")
        if not df_parcelas.empty:
            df_parcelas['mes_venc'] = df_parcelas['data_vencimento'].dt.to_period('M').astype(str)
            fluxo = df_parcelas.groupby('mes_venc', as_index=False)['valor_parcela'].sum()
            chart_fluxo = alt.Chart(fluxo).mark_bar().encode(
                x=alt.X('mes_venc:N', title='Mês de vencimento'),
                y=alt.Y('valor_parcela:Q', title='Valor (R$)'),
                color=alt.value('#2ca02c')
            ).properties(height=350, title="Valor a pagar por mês de vencimento")
            st.altair_chart(chart_fluxo, use_container_width=True)
            with st.expander("Ver parcelas agregadas"):
                st.dataframe(fluxo, use_container_width=True)
        else:
            st.info("ℹ️ Nenhuma parcela cadastrada para exibir fluxo.")
    
    with tab_cfop:
        st.markdown("### Distribuição das compras por CFOP")
        if not df_produtos.empty and 'cfop' in df_produtos.columns:
            df_produtos['cfop'] = df_produtos['cfop'].fillna('Sem CFOP').astype(str)
            df_produtos['valor_total'] = pd.to_numeric(df_produtos['valor_total'], errors='coerce').fillna(0)
            cfop_agg = df_produtos.groupby('cfop', as_index=False)['valor_total'].sum()
            cfop_agg = cfop_agg.sort_values('valor_total', ascending=False).head(15)
            chart_cfop = alt.Chart(cfop_agg).mark_arc(innerRadius=50).encode(
                theta=alt.Theta('valor_total:Q'),
                color=alt.Color('cfop:N'),
                tooltip=[alt.Tooltip('cfop:N'), alt.Tooltip('valor_total:Q', format=',.2f')]
            ).properties(height=400, title="Compras por CFOP")
            st.altair_chart(chart_cfop, use_container_width=True)
            st.dataframe(cfop_agg, use_container_width=True, height=300)
        else:
            st.info("ℹ️ Nenhum CFOP nos itens das NF-e.")
    
    with tab_creditos:
        st.markdown("### Créditos tributários (ICMS, PIS, COFINS)")
        cred_icms = df_merged['Credito_ICMS'].sum()
        cred_pis = df_merged['Credito_PIS'].sum()
        cred_cof = df_merged['Credito_COFINS'].sum()
        cred_total = df_merged['Credito_Tributario_Total'].sum()
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Crédito ICMS", f"R$ {cred_icms:,.2f}")
        col2.metric("Crédito PIS", f"R$ {cred_pis:,.2f}")
        col3.metric("Crédito COFINS", f"R$ {cred_cof:,.2f}")
        col4.metric("Total créditos", f"R$ {cred_total:,.2f}")
        df_cred = pd.DataFrame({
            'Tributo': ['ICMS', 'PIS', 'COFINS'],
            'Valor': [cred_icms, cred_pis, cred_cof]
        })
        chart_cred = alt.Chart(df_cred).mark_bar().encode(
            x=alt.X('Tributo:N'),
            y=alt.Y('Valor:Q', title='Valor (R$)'),
            color=alt.Color('Tributo:N', scale=alt.Scale(range=['#1f77d4', '#ff7f0e', '#2ca02c']))
        ).properties(height=300)
        st.altair_chart(chart_cred, use_container_width=True)
    
    with tab_abc:
        st.markdown("### Curva ABC – Concentração de compras por fornecedor")
        df_abc = df_merged.dropna(subset=['cnpj_fornecedor']).groupby(['cnpj_fornecedor', 'nome_fornecedor']).agg(
            valor=('Faturamento', 'sum')
        ).reset_index()
        df_abc = df_abc[df_abc['valor'] > 0].sort_values('valor', ascending=False)
        if not df_abc.empty:
            total = df_abc['valor'].sum()
            df_abc['pct_acumulado'] = df_abc['valor'].cumsum() / total * 100
            df_abc['classe'] = pd.cut(df_abc['pct_acumulado'], bins=[0, 80, 95, 100], labels=['A', 'B', 'C'])
            df_abc['label'] = df_abc['cnpj_fornecedor'].astype(str) + ' - ' + df_abc['nome_fornecedor'].fillna('S/N')
            df_abc_plot = df_abc.head(25)
            chart_abc = alt.Chart(df_abc_plot).mark_bar().encode(
                y=alt.Y('label:N', sort=alt.EncodingSortField(field='valor', order='descending')),
                x=alt.X('valor:Q', title='Valor compras (R$)'),
                color=alt.Color('classe:N', scale=alt.Scale(domain=['A', 'B', 'C'], range=['#2ecc71', '#f39c12', '#e74c3c'])),
                tooltip=[alt.Tooltip('label:N'), alt.Tooltip('valor:Q', format=',.2f'), alt.Tooltip('pct_acumulado:Q', format='.1f', title='% Acumulado')]
            ).properties(height=max(350, len(df_abc_plot) * 22), title="Curva ABC – Classe A (até 80%), B (80–95%), C (restante)")
            st.altair_chart(chart_abc, use_container_width=True)
            st.caption("Classe A: até 80% do valor; B: 80–95%; C: acima de 95%.")
        else:
            st.info("ℹ️ Sem dados de fornecedor para Curva ABC.")

# ============================================================
# TABELA DE DADOS
# ============================================================
st.markdown("---")
with st.expander("📋 Ver dados completos"):
    st.dataframe(
        df_merged[['numero', 'serie', 'emissao', 'Faturamento', 'Total Impostos', 'Valor Líquido', 'Quantidade Total']],
        use_container_width=True,
        height=400
    )

st.caption(f"Dashboard GDF | Atualizado em {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}")
