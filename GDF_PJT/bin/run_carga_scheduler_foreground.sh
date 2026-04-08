#!/usr/bin/env bash
set -euo pipefail
# Agendador sem Redis/Celery — mesmo critério de app.api.carga_automatica.
# Uso: systemd (gdf-carga-scheduler.service) ou screen/tmux em servidor simples.

VENV_PATH="${VENV_PATH:-/var/www/gdf_v2/venv}"
PROJECT_DIR="${PROJECT_DIR:-/var/www/gdf_v2/GDF_PJT}"

if [ -d "$VENV_PATH" ]; then
  # shellcheck source=/dev/null
  source "$VENV_PATH/bin/activate"
fi

cd "$PROJECT_DIR"

NWRFC_LIB="${PROJECT_DIR%/GDF_PJT}/nwrfcsdk/lib"
if [ -d "$NWRFC_LIB" ]; then
  export LD_LIBRARY_PATH="${NWRFC_LIB}${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
fi

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-GDF_PJT.settings}"

exec python run_carga_scheduler.py
