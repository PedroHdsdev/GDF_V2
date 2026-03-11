#!/usr/bin/env bash
set -e

# Certificado SSL fica no NGINX; Streamlit roda em HTTP e só o proxy acessa.
PROJECT_DIR="${GDF_PROJECT_DIR:-/app/gdf_v2/GDF_PJT}"
PORT="${STREAMLIT_PORT:-8600}"
MAIN_APP="${PROJECT_DIR}/streamlit/main.py"

# Sempre usar o Python do venv (caminho absoluto) para funcionar com systemd e evitar
# conflito com a pasta streamlit/ do projeto. Rodar de /tmp para não carregar o pacote errado.
VENV_PYTHON="${PROJECT_DIR}/venv/bin/python"
if [ ! -x "$VENV_PYTHON" ]; then
  echo "Erro: venv não encontrado em ${PROJECT_DIR}/venv" >&2
  exit 1
fi

cd /tmp
echo Inicializando o Streamlit
exec "$VENV_PYTHON" -m streamlit run "$MAIN_APP" --server.port "$PORT" --server.address "127.0.0.1"
