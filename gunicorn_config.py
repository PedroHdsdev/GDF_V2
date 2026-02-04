"""
Gunicorn Configuration for GDF_V2
Configuração otimizada para 100+ usuários simultâneos
"""

import multiprocessing
import os

# Bind
bind = os.environ.get('GUNICORN_BIND', '127.0.0.1:8000')

# Workers
workers = int(os.environ.get('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = os.environ.get('GUNICORN_WORKER_CLASS', 'sync')
worker_connections = int(os.environ.get('GUNICORN_WORKER_CONNECTIONS', 1000))

# Request handling
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2

# Process naming
proc_name = 'gdf_v2'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (use nginx como reverse proxy em produção)
keyfile = None
certfile = None

# Logging
accesslog = os.environ.get('GUNICORN_ACCESS_LOG', '-')  # stdout
errorlog = os.environ.get('GUNICORN_ERROR_LOG', '-')   # stderr
loglevel = os.environ.get('GUNICORN_LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Server mechanics
reload = False
reload_extra_files = []

# Application
wsgi_app = 'GDF_PJT.wsgi:application'

# Post fork
def post_fork(server, worker):
    """Executado após fork do worker"""
    # Close database connections
    from django.db import connection
    connection.close()
    
    # Setup logging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Worker spawned (pid: {os.getpid()})")

# Pre fork
def pre_fork(server, worker):
    """Executado antes de fork do worker"""
    pass

# Worker int
def worker_int(worker):
    """Executado ao enviar SIGINT para worker"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Worker INT received (pid: {os.getpid()})")

# Worker abort
def worker_abort(worker):
    """Executado ao abortar worker"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Worker ABORT received (pid: {os.getpid()})")

# Pre exec
def pre_exec(server):
    """Executado antes de exec do novo master"""
    pass

# Post exec
def post_exec(server):
    """Executado após exec do novo master"""
    pass

# Pre load app
def pre_load_app(worker):
    """Executado antes de carregar a aplicação"""
    pass
