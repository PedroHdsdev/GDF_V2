import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GDF_PJT.settings')

app = Celery('GDF_PJT')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
