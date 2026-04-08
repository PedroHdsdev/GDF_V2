#!/usr/bin/env bash
set -euo pipefail
# Worker Celery — carga automática XML/SPED e jobs em fila.
# Ajuste VENV_PATH e PROJECT_DIR ao layout do servidor (igual run_gunicorn.sh).

VENV_PATH="${VENV_PATH:-/var/www/gdf_v2/venv}"
PROJECT_DIR="${PROJECT_DIR:-/var/www/gdf_v2/GDF_PJT}"
CONCURRENCY="${CELERY_WORKER_CONCURRENCY:-2}"

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

exec celery -A GDF_PJT worker -l info --concurrency="$CONCURRENCY"
