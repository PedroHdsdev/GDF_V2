"""Tema customizado alinhado ao layout Django (GDF)."""
import streamlit as st


def apply_theme():
    """Aplica tema e estilos customizados para alinhar com o Django."""
    # Injeta na sidebar (menos visível) com wrapper oculto
    st.sidebar.markdown("""
        <div id="gdf-theme-injector" style="display:none!important;height:0;overflow:hidden;">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
        /* === Fonte e tipografia (Django) === */
        html, body, [data-testid="stAppViewContainer"], .stApp {
            font-family: 'Poppins', -apple-system, BlinkMacSystemFont, sans-serif !important;
        }

        /* === Background gradient (Django layout-page) === */
        [data-testid="stAppViewContainer"] {
            background: radial-gradient(circle at 12% 12%, rgba(14, 165, 233, 0.12), transparent 45%),
                radial-gradient(circle at 88% 12%, rgba(249, 115, 22, 0.1), transparent 45%),
                radial-gradient(circle at 85% 85%, rgba(16, 185, 129, 0.08), transparent 50%),
                linear-gradient(135deg, #0f172a 0%, #111827 50%, #1f2937 100%) !important;
        }

        /* === Cores de acento (Django: #0ea5e9 sky, #f97316 sun) === */
        [data-baseweb="tag"] {
            background-color: #0ea5e9 !important;
            color: white !important;
        }
        .stSelectbox [data-baseweb="select"] input:focus {
            border-color: #0ea5e9 !important;
            box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.25) !important;
        }
        [role="radio"] { accent-color: #0ea5e9 !important; }
        [role="checkbox"] { accent-color: #0ea5e9 !important; }
        .stSlider input[type="range"] { accent-color: #0ea5e9 !important; }

        /* === Sidebar (Django: white, #f8f9fa) === */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%) !important;
            font-family: 'Poppins', sans-serif !important;
        }
        [data-testid="stSidebar"] .stMarkdown { margin-top: 0.5rem; }
        [data-testid="stSidebar"] .stCaptionContainer { margin-top: 0.25rem; }

        /* === Título principal (hero estilo Django) === */
        [data-testid="stSidebar"] h1 {
            font-size: 1.5rem !important;
            font-weight: 700 !important;
        }
        .stMarkdown h1 {
            font-size: clamp(1.5rem, 2vw, 2rem) !important;
            font-weight: 700 !important;
            color: #f8fafc !important;
        }

        /* === Cards/seções (Django layout-card) === */
        [data-testid="stVerticalBlock"] > div {
            border-radius: 16px;
        }
        .stExpander {
            background: rgba(30, 41, 59, 0.6) !important;
            border: 1px solid rgba(148, 163, 184, 0.2) !important;
            border-radius: 16px !important;
        }

        /* === Tabs (Django) === */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 12px;
            background: rgba(30, 41, 59, 0.5);
        }
        .stTabs [aria-selected="true"] {
            background: rgba(14, 165, 233, 0.2) !important;
            border-color: #0ea5e9 !important;
        }

        /* === Métricas e dados === */
        [data-testid="stMetricValue"] {
            font-weight: 700 !important;
        }

        /* === Footer === */
        .stCaption {
            color: rgba(248, 250, 252, 0.7) !important;
            font-size: 0.85rem !important;
        }

        /* === Padding do conteúdo (Django layout-page) === */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 3rem !important;
            max-width: 100% !important;
        }

        /* === Divisores === */
        hr {
            border-color: rgba(148, 163, 184, 0.2) !important;
        }
        #gdf-theme-injector{display:none!important;height:0!important;overflow:hidden!important;}
        </style>
        </div>
    """, unsafe_allow_html=True)
