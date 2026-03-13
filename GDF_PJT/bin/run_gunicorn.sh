#!/usr/bin/env bash
set -euo pipefail

# Simple script to start gunicorn for GDF_PJT
# Adjust VENV_PATH and PROJECT_DIR to match your deployment layout
VENV_PATH="/var/www/gdf_v2/venv"
PROJECT_DIR="/var/www/gdf_v2/GDF_PJT"

if [ -d "$VENV_PATH" ]; then
  source "$VENV_PATH/bin/activate"
fi

cd "$PROJECT_DIR"

# SAP RFC SDK (PyRFC): nwrfcsdk na raiz do repositório (irmão de GDF_PJT)
NWRFC_LIB="${PROJECT_DIR%/GDF_PJT}/nwrfcsdk/lib"
if [ -d "$NWRFC_LIB" ]; then
  export LD_LIBRARY_PATH="${NWRFC_LIB}${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
fi

# Coletar estáticos para WhiteNoise servir CSS/JS (obrigatório com Gunicorn)
python manage.py collectstatic --noinput 2>/dev/null || true

# Ensure logs directory exists
sudo mkdir -p /var/log/gunicorn 2>/dev/null || true
sudo chown "$(whoami):$(whoami)" /var/log/gunicorn 2>/dev/null || true

# Run gunicorn with config (config em etc/)
CONFIG_FILE="etc/gunicorn_config.py"
if [ -f "$CONFIG_FILE" ]; then
  exec gunicorn -c "$CONFIG_FILE" GDF_PJT.wsgi:application
else
  exec gunicorn -c gunicorn_config.py GDF_PJT.wsgi:application
fi
