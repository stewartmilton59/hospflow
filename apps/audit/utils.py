"""Audit utilities for manual logging"""
from django.utils import timezone
from django.conf import settings
from .models import AuditLog


def log_phi_access(user, action, resource_type, resource_id, resource_repr="", 
                   previous_state=None, new_state=None, severity="medium"):
    return AuditLog.objects.create(
        user=user,
        action=action,
        severity=severity,
        resource_type=resource_type,
        resource_id=str(resource_id),
        resource_repr=resource_repr,
        previous_state=previous_state or {},
        new_state=new_state or {},
        retention_until=timezone.now() + timezone.timedelta(days=365 * settings.MEDICAL_RECORD_RETENTION_YEARS)
    )


def log_consent_event(patient, action, user=None):
    action_map = {"granted": "CONSENT_GRANTED", "withdrawn": "CONSENT_WITHDRAWN"}
    return AuditLog.objects.create(
        user=user,
        action=action_map.get(action, "CONSENT_GRANTED"),
        severity="high",
        resource_type="Patient",
        resource_id=str(patient.unique_id),
        resource_repr=f"Consent {action} for {patient.get_full_name()}",
        retention_until=timezone.now() + timezone.timedelta(days=365 * 25)
    )
