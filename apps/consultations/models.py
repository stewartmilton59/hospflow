"""Clinical Workflows with ICD-10-CM and SDoH Z-Codes"""
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from apps.common.models import TimestampedModel


class ICD10Code(models.Model):
    """ICD-10-CM Code Repository - National MIT Aligned"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=10, unique=True, db_index=True)
    description = models.TextField()
    category = models.CharField(max_length=10, db_index=True)
    subcategory = models.CharField(max_length=50, blank=True)
    is_sdh = models.BooleanField(
        default=False,
        help_text=_("Social Determinants of Health Z-code (Z55-Z65)")
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "consultations_icd10_code"
        ordering = ["code"]
        verbose_name = "ICD-10-CM Code"
        verbose_name_plural = "ICD-10-CM Codes"

    def __str__(self):
        return f"{self.code} - {self.description[:50]}"


class Consultation(TimestampedModel):
    """Clinical Encounter / OPD Visit"""
    STATUS_CHOICES = [
        ("scheduled", _("Scheduled")),
        ("checked_in", _("Checked In")),
        ("in_progress", _("In Progress")),
        ("completed", _("Completed")),
        ("cancelled", _("Cancelled")),
        ("no_show", _("No Show")),
    ]

    PRIORITY_CHOICES = [
        ("routine", _("Routine")),
        ("urgent", _("Urgent")),
        ("emergency", _("Emergency")),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.CASCADE,
        related_name="consultations"
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="consultations",
        limit_choices_to={"role": "doctor"}
    )
    facility = models.ForeignKey(
        "accounts.Facility",
        on_delete=models.CASCADE,
        related_name="consultations"
    )

    # Visit Details
    visit_date = models.DateTimeField(db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="scheduled")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="routine")
    visit_type = models.CharField(
        max_length=20,
        choices=[
            ("new", _("New Case")),
            ("follow_up", _("Follow Up")),
            ("referral", _("Referral")),
            ("emergency", _("Emergency")),
        ],
        default="new"
    )

    # Vitals (captured by nurse)
    vital_temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    vital_blood_pressure_sys = models.PositiveSmallIntegerField(null=True, blank=True)
    vital_blood_pressure_dia = models.PositiveSmallIntegerField(null=True, blank=True)
    vital_heart_rate = models.PositiveSmallIntegerField(null=True, blank=True)
    vital_respiratory_rate = models.PositiveSmallIntegerField(null=True, blank=True)
    vital_oxygen_saturation = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    vital_weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    vital_height_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    vital_bmi = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)

    # Clinical Notes
    chief_complaint = models.TextField()
    history_of_present_illness = models.TextField(blank=True)
    physical_examination = models.TextField(blank=True)
    assessment_and_plan = models.TextField(blank=True)

    # ICD-10 Coding
    primary_diagnosis = models.ForeignKey(
        ICD10Code,
        on_delete=models.PROTECT,
        related_name="primary_consultations",
        null=True,
        blank=True
    )
    secondary_diagnoses = models.ManyToManyField(
        ICD10Code,
        related_name="secondary_consultations",
        blank=True
    )
    sdoh_codes = models.ManyToManyField(
        ICD10Code,
        related_name="sdoh_consultations",
        blank=True,
        limit_choices_to={"is_sdh": True},
        help_text=_("Social Determinants of Health Z-codes (Z55-Z65)")
    )

    # Outcome
    disposition = models.CharField(
        max_length=20,
        choices=[
            ("discharged", _("Discharged")),
            ("admitted", _("Admitted")),
            ("referred", _("Referred")),
            ("died", _("Died")),
            ("absconded", _("Absconded")),
        ],
        blank=True
    )
    referral_facility = models.CharField(max_length=255, blank=True)

    # Billing
    consultation_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_nhif_claimable = models.BooleanField(default=False)

    # Reporting Flags
    is_notifiable_disease = models.BooleanField(
        default=False,
        help_text=_("Flag for e-IDSR / DHIS2 outbreak reporting")
    )

    class Meta:
        db_table = "consultations_consultation"
        ordering = ["-visit_date"]
        indexes = [
            models.Index(fields=["patient", "visit_date"]),
            models.Index(fields=["doctor", "visit_date"]),
            models.Index(fields=["facility", "visit_date", "status"]),
            models.Index(fields=["is_notifiable_disease", "visit_date"]),
        ]

    def __str__(self):
        return f"Consultation {self.id} - {self.patient} on {self.visit_date.date()}"

    def save(self, *args, **kwargs):
        # Auto-calculate BMI
        if self.vital_weight_kg and self.vital_height_cm:
            height_m = float(self.vital_height_cm) / 100
            self.vital_bmi = round(float(self.vital_weight_kg) / (height_m ** 2), 2)

        # Check for notifiable diseases (simplified logic)
        if self.primary_diagnosis and self.primary_diagnosis.category in ["A00", "A20", "B20"]:
            self.is_notifiable_disease = True

        super().save(*args, **kwargs)


class Prescription(TimestampedModel):
    """Medication Prescription"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    consultation = models.ForeignKey(
        Consultation,
        on_delete=models.CASCADE,
        related_name="prescriptions"
    )
    medication = models.ForeignKey(
        "inventory.InventoryItem",
        on_delete=models.PROTECT,
        related_name="prescriptions"
    )
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=50)
    duration_days = models.PositiveSmallIntegerField()
    quantity_prescribed = models.PositiveIntegerField()
    instructions = models.TextField(blank=True)

    # Dispensing
    dispensed = models.BooleanField(default=False)
    dispensed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={"role": "pharmacist"}
    )
    dispensed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "consultations_prescription"
        ordering = ["-created_at"]
