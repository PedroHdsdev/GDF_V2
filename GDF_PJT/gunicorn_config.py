import multiprocessing
import os

# Gunicorn configuration file
# Adjust worker count as appropriate for your server
workers = int(os.environ.get('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
bind = os.environ.get('GUNICORN_BIND', '127.0.0.1:8500')
timeout = int(os.environ.get('GUNICORN_TIMEOUT', 120))
keepalive = int(os.environ.get('GUNICORN_KEEPALIVE', 2))
worker_class = os.environ.get('GUNICORN_WORKER_CLASS', 'sync')
accesslog = os.environ.get('GUNICORN_ACCESS_LOG', '/var/log/gunicorn/access.log')
errorlog = os.environ.get('GUNICORN_ERROR_LOG', '/var/log/gunicorn/error.log')
loglevel = os.environ.get('GUNICORN_LOGLEVEL', 'info')
