import os
import sys
import streamlit       as st
import pandas          as pd
import tp_lists      as tl 
import tp_graficos   as tg
from datetime          import date
from django.core.cache import cache

# ============================================================
# Configuração inicial Streamlit
# ============================================================
st.set_page_config(page_title="Dashboard ProjectCusto", layout="wide")

# ============================================================
# Inicializa o ambiente Django
# ============================================================
@st.cache_resource
def init_django():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # ProjectCusto/ProjectCusto
    if BASE_DIR not in sys.path:
        sys.path.append(BASE_DIR)

    import django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ProjectCusto.settings")
    django.setup()

init_django()

# Imports Django depois do setup
from django.contrib.auth.models import User
from GDF_PJT.app.db_GDF.Public.models import RelatorioCusto, Bukrs, SapLog
from django.db.models import Q
import jwt
from django.conf import settings

# ============================================================
# Autenticação
# ============================================================
token = st.query_params.get("token")

if not token:
    st.error("Acesso negado")
    st.stop()

try:
    #payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    #username = payload["username"]
    username = "test"
except jwt.ExpiredSignatureError:
    st.error("Sessão expirada")
    st.stop()
    st.markdown(
        "<script>window.top.location.href='/login/'</script>",
        unsafe_allow_html=True
    )
    
except jwt.InvalidTokenError:
    st.error("Sessão expirada")
    st.stop()
    st.markdown(
        "<script>window.top.location.href='/login/'</script>",
        unsafe_allow_html=True
    )


try:
    user_obj = User.objects.get(username=username)
    bukrs_list = list(user_obj.user_bukrs.values_list("bukrs", flat=True))

    if not bukrs_list:
        st.error("Usuário sem empresa vinculada (bukrs).")
        st.stop()

except User.DoesNotExist:
    st.error("Usuário inválido.")
    st.stop()
    st.markdown(
        "<script>window.top.location.href='/login/'</script>",
        unsafe_allow_html=True
    )

# ============================================================
# Filtros – Sidebar
# ============================================================
st.sidebar.header("Filtros")
bukrs_options = list(Bukrs.objects.filter(bukrs__in=bukrs_list))
bukrs_display = ["Todas"] + [f"{b.bukrs} - {b.butxt}" for b in bukrs_options]

selected_bukrs = st.sidebar.selectbox("Empresa (Bukrs):", options=bukrs_display)
filial_input = st.sidebar.text_input("Filial (Werks)", placeholder="Ex: 1001")

st.sidebar.header("Periodo:")
usar_periodo = st.sidebar.checkbox("Usar período", value=True)
col_dt1, col_dt2 = st.sidebar.columns(2)
data_inicio = col_dt1.date_input(
    "De",
    value= date.today().replace(day=1),
    format="DD/MM/YYYY"
)
data_fim = col_dt2.date_input(
    "Até",
    value=date.today(),
    format="DD/MM/YYYY"
)

# ============================================================
# Aplicação dos Filtros
# ============================================================
q_filtros = Q()
q_filtros &= Q(bukrs_id__in=bukrs_list)

if selected_bukrs != "Todas":
    bukrs_codigo = selected_bukrs.split(" - ")[0]
    q_filtros &= Q(bukrs__bukrs=bukrs_codigo)


if filial_input:
    q_filtros &= Q(werks=filial_input)

if data_inicio and data_fim:
    if data_inicio > data_fim:
        st.warning("Data inicial maior que a final.")
    elif data_inicio < data_fim and usar_periodo:
        q_filtros &= Q(pstdat__range=(data_inicio, data_fim))

# ============================================================
# QuerySet base (Sqlpostgres) select
# ============================================================
q_filtros &= Q(cfop__in=tl.cfop_list)
queryset = RelatorioCusto.objects.filter(q_filtros).values(*tl.campos)
            
# ============================================================
# DataFrame
# ============================================================
if queryset.exists():
    df = pd.DataFrame.from_records(queryset)
    df.rename(columns=tl.colunas_amigaveis, inplace=True)
else:
    st.warning("Nenhum dado encontrado.")
    df = pd.DataFrame()

if df.empty:
    st.stop()

# ============================================================
# Notificação de log
# ============================================================
@st.cache_data(ttl=60)
def tem_notificacao(bukrs_list):
    return SapLog.objects.filter( 
        bukrs_id__in=bukrs_list,
        mgstype="E" 
        ).exists()

def render_log(log):
    if log.mgstype == "E":
        st.error(
            f"""
            **Empresa:** {log.bukrs}  
            **Mensagem:** {log.mensagem}  
            **Data:** {log.datahora:%d/%m/%Y %H:%M}
            """
        )
    elif log.mgstype == "S":
        st.success(
            f"""
            **Empresa:** {log.bukrs}  
            **Mensagem:** {log.mensagem}  
            **Data:** {log.datahora:%d/%m/%Y %H:%M}
            """
        )
col1, col2 = st.columns([11, 2])
with col2:
    if tem_notificacao(bukrs_list):
        label = "Status:🔴"   
    else:
        label = "Status:🟢"

    with st.popover(label, help="Notificações do sistema"):
        
        st.markdown("### 📋 Notificação (últimos 7 dias)")

        logs = SapLog.objects.filter(
            bukrs_id__in=bukrs_list,
            datahora__gte=pd.Timestamp.now() - pd.Timedelta(days=7),
        ).order_by("-datahora")[:50]

        if logs.exists():
            for log in logs:
                render_log(log)
        else:
            st.info("Nenhum log encontrado.")

# ============================================================
# Gráficos
# ============================================================

# ============================================================
# Evolução Comparativa (Grafico 1)
# ============================================================
st.subheader("Evolução do Faturamento")

# Pré-processamento
df["Data de Postagem"] = pd.to_datetime(df["Data de Postagem"], errors="coerce")
df = df.dropna(subset=["Data de Postagem"])
df['ano'] = df["Data de Postagem"].dt.year
df['mes'] = df["Data de Postagem"].dt.month
df['mes_nome'] = df["Data de Postagem"].dt.strftime('%B')

cx1, cx2 = st.columns(2)
with cx1:
    metricas_disponiveis = ["Faturamento", "V.CMV", "M. Contribuição", "Total de Impostos"]
    metricas_selecionadas = st.multiselect(
        "Métricas a exibir",
        options=metricas_disponiveis,
        default=metricas_disponiveis[:3]
    )

with cx2:
    anos_disponiveis = df['ano'].sort_values().unique()
    anos_selecionados = st.multiselect(
        "Escolha os anos para comparar",
        options=anos_disponiveis,
        default=anos_disponiveis[-2:]
    )

cx3, cx4 = st.columns(2)
periodo_value = cx3.selectbox(":", tl.periodo_list1, key="periodo")

if periodo_value == "Mensal":
    with cx4:
        mes_inicial, mes_final = st.select_slider(
            "Escolha o período (meses):",
            options=list(range(1, 13)),
            value=(1, 3)
        )

else:
    mes_inicial, mes_final = 1, 12  

# Criar objeto da classe e chamar método único
g = tg.Grafico_linha(df)
g.G_multiplas_metricas(
    coluna_data='mes_nome',
    coluna_ano='ano',
    metricas=metricas_selecionadas,
    filtro_anos=anos_selecionados,
    filtro_meses=(mes_inicial, mes_final),
    periodo=periodo_value,
    titulo="Faturamento Comparativo"
)


# ============================================================
# Ranks Vendas  (Grafico 2)
# ============================================================
st.subheader("🏆 Ranks de Vendas")

cx5, cx6 = st.columns(2)
valor_x = cx5.selectbox("Dimensão:", tl.Categoria_list1, key="ranks_x")
ordenacao = cx6.selectbox("Ordenar por:", tl.opcoes_ordenacao, key="ranks_ord")
valor_y = "Faturamento"

# Pizza
col1, col2 = st.columns(2)
with col1:
    g = tg.Grafico_pizza(df)
    g.G_pizza(valor_x=valor_x, valor_y=valor_y, titulo=f"{valor_y} por {valor_x}")

# Barra
with col2:
    g = tg.Grafico_barra(df)
    g.G_barra(valor_x=valor_x, valor_y=valor_y,ordenacao=ordenacao, titulo=f"{valor_y} por {valor_x}")

# ============================================================
# Grupo de Mercadorias (Grafico 3)
# ============================================================
st.subheader("Grupo de Mercadorias")

cx7,cx8 = st.columns(2)

valor_x = "Denominação do Grupo de Mercadorias"
Metrica_y = cx7.selectbox("Métrica:", tl.Metrica_grpmercadoria , key="gm_y")
ordenacao = cx8.selectbox("Ordenar por:", tl.opcoes_ordenacao, key="gm_ord")

if Metrica_y == "Total de Impostos":
    valor_y = ["Valor Líquido", "Total de Impostos"]
elif Metrica_y == "Faturamento":
    valor_y = ["Faturamento"]
elif Metrica_y == "Quantidade de Produto":
    valor_y = ["Quantidade de Produto"]

g=tg.Grafico_barra(df)
g.G_barra_multicolunas(
    valor_x=valor_x,
    list_y=valor_y,
    ordenacao=ordenacao,
    titulo=f"{valor_x}"
)

# ============================================================
# Dados (tabela completa)
# ============================================================
st.dataframe(df, use_container_width=True)

st.caption(f"PROCESSIT  {pd.Timestamp.now().strftime('%d/%m/%Y')}")
