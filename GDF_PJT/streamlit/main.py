"""
Dashboard GDF - Streamlit
Entry point principal. Usa estrutura OOP para fácil manutenção e extensão.
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
# ============================================================
@st.cache_resource
def init_django():
    """Configura paths e inicializa Django."""
    # __file__ = streamlit/main.py
    streamlit_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(streamlit_dir)

    if base_dir not in sys.path:
        sys.path.append(base_dir)

    gdf_pjt_dir = os.path.join(base_dir, 'GDF_PJT')
    if gdf_pjt_dir not in sys.path:
        sys.path.insert(0, gdf_pjt_dir)

    if streamlit_dir not in sys.path:
        sys.path.insert(0, streamlit_dir)

    import django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "GDF_PJT.settings")
    django.setup()


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
# Executa o Dashboard
# ============================================================
dashboard = create_dashboard(auth)
if not dashboard.run():
    st.stop()

# Aplica tema ao final (evita bloco visível no início)
apply_theme()
