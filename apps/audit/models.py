"""Audit & Compliance Logging - PDPA 2022 / HIPAA"""
import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from apps.common.models import TimestampedModel


class AuditLog(TimestampedModel):
    """Comprehensive audit trail for all PHI access"""

    ACTION_CHOICES = [
        ("CREATE", _("Create")),
        ("READ", _("Read")),
        ("UPDATE", _("Update")),
        ("DELETE", _("Delete")),
        ("EXPORT", _("Export")),
        ("LOGIN", _("Login")),
        ("LOGOUT", _("Logout")),
        ("FAILED_LOGIN", _("Failed Login")),
        ("CONSENT_GRANTED", _("Consent Granted")),
        ("CONSENT_WITHDRAWN", _("Consent Withdrawn")),
        ("PRESCRIPTION_DISPENSED", _("Prescription Dispensed")),
        ("CLAIM_SUBMITTED", _("Claim Submitted")),
        ("VFD_RECEIPT", _("VFD Receipt Generated")),
    ]

    SEVERITY_CHOICES = [
        ("low", _("Low")),
        ("medium", _("Medium")),
        ("high", _("High")),
        ("critical", _("Critical")),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs"
    )
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default="low")

    resource_type = models.CharField(max_length=50, help_text=_("e.g., Patient, Consultation, Invoice"))
    resource_id = models.CharField(max_length=100, blank=True)
    resource_repr = models.CharField(max_length=255, blank=True, help_text=_("Human-readable identifier"))

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_id = models.CharField(max_length=100, blank=True)

    previous_state = models.JSONField(default=dict, blank=True)
    new_state = models.JSONField(default=dict, blank=True)
    change_summary = models.TextField(blank=True)

    pdpa_compliant = models.BooleanField(default=True)
    consent_verified = models.BooleanField(default=False)
    retention_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "audit_log"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "action", "created_at"]),
            models.Index(fields=["resource_type", "resource_id"]),
            models.Index(fields=["severity", "created_at"]),
            models.Index(fields=["ip_address", "created_at"]),
            models.Index(fields=["pdpa_compliant", "created_at"]),
        ]


class DataExportLog(TimestampedModel):
    """Log all data exports for PDPA compliance"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    export_type = models.CharField(max_length=50)
    filters_applied = models.JSONField(default=dict)
    record_count = models.PositiveIntegerField()
    file_format = models.CharField(max_length=20)
    file_hash = models.CharField(max_length=64, blank=True)
    download_url = models.URLField(blank=True)
    expiry_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "audit_export_log"
        ordering = ["-created_at"]
