import multiprocessing
import os

# Gunicorn configuration file
# Adjust worker count as appropriate for your server
workers = int(os.environ.get('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
bind = os.environ.get('GUNICORN_BIND', '127.0.0.1:8500')
# Integração SAP (RFC em lote, ex. GDF_RFC_CONSULTA) pode exceder vários minutos.
# Se o worker for encerrado por timeout, o Nginx costuma devolver 502 com HTML.
timeout = int(os.environ.get('GUNICORN_TIMEOUT', 150))
keepalive = int(os.environ.get('GUNICORN_KEEPALIVE', 2))
worker_class = os.environ.get('GUNICORN_WORKER_CLASS', 'sync')

accesslog = os.environ.get('GUNICORN_ACCESS_LOG', '-')
errorlog = os.environ.get('GUNICORN_ERROR_LOG', '-')

loglevel = os.environ.get('GUNICORN_LOGLEVEL', 'info')
