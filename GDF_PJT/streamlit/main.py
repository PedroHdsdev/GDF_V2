"""
Streamlit GDF – Apps de análise por solução
Entry point único: qual dashboard rodar vem do token (tipo_relatorio) ou do query param ?dashboard=.
Cada solução pode ter um ou mais dashboards (ex.: solução Dashboard → Vendas/Compras; outras soluções no futuro).
"""
import os
import sys
import streamlit as st

# ============================================================
# Configuração inicial Streamlit
# ============================================================
st.set_page_config(page_title="Dashboard GDF", layout="wide")

# ============================================================
# Inicializa o ambiente Django (antes de qualquer import Django)
# Usar django.apps.apps.ready para nunca chamar setup() duas vezes
# (evita RuntimeError("populate() isn't reentrant") em reruns do Streamlit).
# ============================================================


def init_django():
    # __file__ = .../GDF_PJT/streamlit/main.py
    streamlit_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(streamlit_dir)  # projeto (onde está manage.py, app/, GDF_PJT/)

    # Django precisa do diretório do projeto em sys.path para import GDF_PJT.settings
    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)
    # Streamlit precisa do dir streamlit/ para import config.* e core.*
    if streamlit_dir not in sys.path:
        sys.path.insert(0, streamlit_dir)

    # Working directory no projeto evita erros de path ao carregar apps
    os.chdir(base_dir)

    import django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "GDF_PJT.settings")
    # Evita "populate() isn't reentrant": em reruns o Django já pode estar populado
    try:
        already_ready = getattr(
            getattr(django.apps, "apps", None), "ready", False
        )
    except Exception:
        already_ready = False
    if not already_ready:
        try:
            django.setup()
        except RuntimeError as e:
            if "isn't reentrant" not in str(e):
                raise


init_django()

# ============================================================
# Imports após Django init
# ============================================================
from django.conf import settings
from config.theme import apply_theme
from core.auth import authenticate
from core.factory import create_dashboard

# ============================================================
# Autenticação
# ============================================================
token = st.query_params.get("token")
auth = authenticate(token, settings.SECRET_KEY)

if auth is None:
    st.stop()

# ============================================================
# Qual dashboard executar: vem do token (tipo_relatorio). Opcionalmente ?dashboard= sobrescreve.
# ============================================================
dashboard_key = st.query_params.get("dashboard") or auth.tipo_relatorio
dashboard = create_dashboard(auth, dashboard_key=dashboard_key)
if not dashboard.run():
    st.stop()

# Aplica tema ao final (evita bloco visível no início)
apply_theme()
