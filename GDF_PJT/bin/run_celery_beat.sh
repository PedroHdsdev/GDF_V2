#!/usr/bin/env bash
set -euo pipefail
# Celery Beat — agenda scan_carga_automatica (CELERY_BEAT_SCHEDULE em settings).
# Arquivo de estado do beat persiste entre reinícios (evita tarefas duplicadas).

VENV_PATH="${VENV_PATH:-/var/www/gdf_v2/venv}"
PROJECT_DIR="${PROJECT_DIR:-/var/www/gdf_v2/GDF_PJT}"
SCHEDULE_FILE="${CELERY_BEAT_SCHEDULE_FILE:-/var/lib/gdf/celerybeat-schedule}"

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

mkdir -p "$(dirname "$SCHEDULE_FILE")"

exec celery -A GDF_PJT beat -l info --schedule="$SCHEDULE_FILE"
