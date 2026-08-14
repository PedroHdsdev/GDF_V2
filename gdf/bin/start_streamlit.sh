#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${GDF_PROJECT_DIR:-/app/gdf}"
PORT="${STREAMLIT_PORT:-8600}"
MAIN_APP="${PROJECT_DIR}/streamlit/main.py"

if [ ! -f "$MAIN_APP" ]; then
    echo "Erro: aplicação Streamlit não encontrada: $MAIN_APP" >&2
    exit 1
fi

cd "$PROJECT_DIR"

echo "Inicializando o Streamlit..."
echo "Aplicação: $MAIN_APP"
echo "Porta: $PORT"

exec streamlit run "$MAIN_APP" \
    --server.address=0.0.0.0 \
    --server.port="$PORT" \
    --server.headless=true \
    --browser.gatherUsageStats=false