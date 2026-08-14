FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        g++ \
        libpq-dev \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt

COPY gdf /app/gdf
COPY nwrfcsdk /app/nwrfcsdk

WORKDIR /app/gdf

ENV DJANGO_SETTINGS_MODULE=config.settings
ENV LD_LIBRARY_PATH=/app/nwrfcsdk/lib

RUN DB_ENGINE=django.db.backends.postgresql \
    DB_NAME=build \
    DB_USER=build \
    DB_PASSWORD=build \
    DB_HOST=127.0.0.1 \
    DB_PORT=5432 \
    SECRET_KEY=build-only-secret \
    CERT_PASSWORD_FERNET_KEY=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA= \
    FORCE_SCRIPT_NAME=/gdf \
    python manage.py collectstatic --noinput

RUN mkdir -p /app/gdf/logs
RUN mkdir -p /var/lib/gdf

EXPOSE 8500
EXPOSE 8600

CMD ["gunicorn", "-c", "/app/gdf/etc/gunicorn_config.py", "config.wsgi:application"]