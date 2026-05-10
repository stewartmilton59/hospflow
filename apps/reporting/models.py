"""DHIS2 Integration and National Reporting"""
import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from apps.common.models import TimestampedModel


class DHIS2DataElement(models.Model):
    """Mapping of HospFlow data to DHIS2 data elements"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dhis2_uid = models.CharField(max_length=11, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, blank=True)
    category_combo = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)

    # MTUHA Mapping
    mtuha_book = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ("book_3", _("Book 3 - OPD")),
            ("book_5", _("Book 5 - RCH")),
            ("book_6", _("Book 6 - Immunization")),
            ("book_10", _("Book 10 - Hospital Report")),
        ]
    )
    mtuha_indicator = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "reporting_dhis2_data_element"
        ordering = ["name"]


class DHIS2Report(TimestampedModel):
    """Automated DHIS2 report submissions"""
    STATUS_CHOICES = [
        ("pending", _("Pending")),
        ("submitted", _("Submitted")),
        ("acknowledged", _("Acknowledged")),
        ("failed", _("Failed")),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_period = models.CharField(max_length=10, help_text=_("YYYYMM format"))
    facility = models.ForeignKey(
        "accounts.Facility",
        on_delete=models.CASCADE,
        related_name="dhis2_reports"
    )
    report_type = models.CharField(
        max_length=20,
        choices=[
            ("monthly", _("Monthly")),
            ("quarterly", _("Quarterly")),
            ("annual", _("Annual")),
        ]
    )

    # Aggregated Data
    data_values = models.JSONField(default=dict, help_text=_("DHIS2 data value set"))

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    dhis2_response = models.JSONField(default=dict)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    class Meta:
        db_table = "reporting_dhis2_report"
        ordering = ["-report_period"]
        unique_together = ["report_period", "facility", "report_type"]


class MTUHAIndicator(models.Model):
    """MTUHA Book 10 Indicators"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    indicator_code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    book = models.CharField(max_length=20)
    section = models.CharField(max_length=50)
    data_source = models.CharField(max_length=100, help_text=_("Django model.field reference"))
    aggregation_method = models.CharField(
        max_length=20,
        choices=[
            ("count", _("Count")),
            ("sum", _("Sum")),
            ("avg", _("Average")),
        ]
    )

    class Meta:
        db_table = "reporting_mtuha_indicator"
        ordering = ["indicator_code"]
