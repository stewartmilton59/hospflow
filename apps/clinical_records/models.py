"""Clinical Records with Encrypted PHI Fields"""

import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from apps.common.models import TimestampedModel
from apps.common.encryption import get_encryption


class ClinicalRecord(TimestampedModel):
    """Comprehensive clinical record with encrypted sensitive fields"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.CASCADE, related_name="clinical_records"
    )
    consultation = models.OneToOneField(
        "consultations.Consultation",
        on_delete=models.CASCADE,
        related_name="clinical_record",
        null=True,
        blank=True,
    )

    # Encrypted Fields (PHI)
    _diagnosis_encrypted = models.TextField(db_column="diagnosis", blank=True)
    _treatment_plan_encrypted = models.TextField(db_column="treatment_plan", blank=True)
    _notes_encrypted = models.TextField(db_column="notes", blank=True)
    _allergies_encrypted = models.TextField(db_column="allergies", blank=True)

    # Non-encrypted metadata
    record_date = models.DateTimeField(auto_now_add=True)
    record_type = models.CharField(
        max_length=20,
        choices=[
            ("opd", _("OPD Record")),
            ("ipd", _("IPD Record")),
            ("emergency", _("Emergency")),
            ("follow_up", _("Follow Up")),
        ],
        default="opd",
    )

    # Lab & Radiology References
    lab_tests = models.JSONField(default=list, blank=True)
    radiology_reports = models.JSONField(default=list, blank=True)

    # Attachments (secure storage)
    attachments = models.JSONField(default=list, blank=True)

    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="clinical_records",
    )

    class Meta:
        db_table = "clinical_records_clinicalrecord"
        ordering = ["-record_date"]
        indexes = [
            models.Index(fields=["patient", "record_date"]),
            models.Index(fields=["record_type", "record_date"]),
        ]

    @property
    def diagnosis(self):
        return get_encryption().decrypt(self._diagnosis_encrypted)

    @diagnosis.setter
    def diagnosis(self, value):
        self._diagnosis_encrypted = get_encryption().encrypt(value)

    @property
    def treatment_plan(self):
        return get_encryption().decrypt(self._treatment_plan_encrypted)

    @treatment_plan.setter
    def treatment_plan(self, value):
        self._treatment_plan_encrypted = get_encryption().encrypt(value)

    @property
    def notes(self):
        return get_encryption().decrypt(self._notes_encrypted)

    @notes.setter
    def notes(self, value):
        self._notes_encrypted = get_encryption().encrypt(value)

    @property
    def allergies(self):
        return get_encryption().decrypt(self._allergies_encrypted)

    @allergies.setter
    def allergies(self, value):
        self._allergies_encrypted = get_encryption().encrypt(value)


class LabResult(TimestampedModel):
    """Laboratory test results"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    clinical_record = models.ForeignKey(
        ClinicalRecord, on_delete=models.CASCADE, related_name="lab_results"
    )
    test_name = models.CharField(max_length=100)
    loinc_code = models.CharField(
        max_length=20, blank=True, help_text=_("LOINC code for interoperability")
    )
    result_value = models.CharField(max_length=255)
    reference_range = models.CharField(max_length=100, blank=True)
    unit = models.CharField(max_length=50, blank=True)
    is_abnormal = models.BooleanField(default=False)

    # File attachment (stored securely)
    result_file = models.FileField(
        upload_to="lab_results/%Y/%m/",
        blank=True,
        help_text=_("Scanned lab report or image"),
    )

    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="lab_results",
        limit_choices_to={"role": "lab_tech"},
    )

    class Meta:
        db_table = "clinical_records_labresult"
        ordering = ["-created_at"]


class RadiologyReport(TimestampedModel):
    """Radiology and imaging reports"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    clinical_record = models.ForeignKey(
        ClinicalRecord, on_delete=models.CASCADE, related_name="report_records"
    )
    study_type = models.CharField(max_length=50)
    body_part = models.CharField(max_length=50)
    findings = models.TextField()
    impression = models.TextField()

    # DICOM / Image storage
    images = models.JSONField(default=list, blank=True)
    dicom_study_uid = models.CharField(max_length=64, blank=True)

    radiologist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="radiology_reports",
        limit_choices_to={"role": "doctor"},
    )

    class Meta:
        db_table = "clinical_records_radiologyreport"
