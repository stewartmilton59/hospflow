"""Celery configuration for HospFlow."""
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hospflow.settings")

app = Celery("hospflow")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
