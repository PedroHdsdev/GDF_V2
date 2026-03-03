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

# Ensure logs directory exists
sudo mkdir -p /var/log/gunicorn
sudo chown $(whoami):$(whoami) /var/log/gunicorn

# Run gunicorn with config
exec gunicorn -c gunicorn_config.py GDF_PJT.wsgi:application
