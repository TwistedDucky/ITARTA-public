# backend/celery.py
import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
# This tells Celery where to find your Django project's configuration.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# Create the Celery app instance
app = Celery('backend')

# Load task modules from all registered Django app configs.
# The namespace='CELERY' means all celery-related configuration keys 
# in settings.py must begin with 'CELERY_'
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps (like rides/tasks.py)
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')