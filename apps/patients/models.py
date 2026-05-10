"""HospFlow Patients - Master Patient Index (MPI)"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings

from apps.common.models import TimestampedModel
from apps.common.encryption import get_encryption
from .validators import validate_nida_nin, validate_no_future_date


class Patient(TimestampedModel):
    """Master Patient Index compliant with Tanzania PDPA 2022 and NIDA"""

    GENDER_CHOICES = [
        ("male", _("Male")),
        ("female", _("Female")),
        ("other", _("Other")),
        ("unknown", _("Unknown")),
    ]

    MARITAL_STATUS = [
        ("single", _("Single")),
        ("married", _("Married")),
        ("divorced", _("Divorced")),
        ("widowed", _("Widowed")),
        ("separated", _("Separated")),
    ]

    # Internal UUID Primary Key (prevents ID scraping)
    # unique_id = models.UUIDField(
    #    primary_key=True,
    #    default=uuid.uuid4,
    #    editable=False,
    #    db_index=True
    # )

    # NIDA Integration - 20-digit NIN
    nida_nin = models.CharField(
        _("NIDA NIN"),
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        validators=[validate_nida_nin],
        db_index=True,
        help_text=_("20-digit National Identification Number from NIDA"),
    )

    # Biometric Hooks for NIDA CIG Integration
    biometric_verified = models.BooleanField(default=False)
    biometric_reference = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("Reference ID from NIDA biometric system"),
    )

    # Demographics
    first_name = models.CharField(_("first name"), max_length=100)
    middle_name = models.CharField(_("middle name"), max_length=100, blank=True)
    last_name = models.CharField(_("last name"), max_length=100)
    date_of_birth = models.DateField(
        validators=[validate_no_future_date],
        help_text=_("Validated against NIDA records"),
    )
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        help_text=_("Required for HIE and MTUHA reporting"),
    )
    marital_status = models.CharField(max_length=10, choices=MARITAL_STATUS, blank=True)

    # Contact
    phone_number = models.CharField(_("phone number"), max_length=15)
    email = models.EmailField(blank=True)
    emergency_contact_name = models.CharField(max_length=150, blank=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True)

    # Address
    region = models.CharField(max_length=50)
    district = models.CharField(max_length=50)
    ward = models.CharField(max_length=50)
    village_street = models.CharField(max_length=100, blank=True)

    # Insurance
    nhif_card_number = models.CharField(
        max_length=20,
        blank=True,
        db_index=True,
        help_text=_("NHIF membership card number"),
    )
    insurance_scheme = models.CharField(max_length=50, blank=True)
    insurance_expiry = models.DateField(null=True, blank=True)

    # Occupation & SDoH (Social Determinants of Health)
    occupation = models.CharField(max_length=100, blank=True)
    education_level = models.CharField(max_length=50, blank=True)

    # Consent Management - PDPA 2022 Compliance
    consent_status = models.BooleanField(
        default=False,
        help_text=_(
            "Explicit consent for processing sensitive health data per PDPA 2022 Section 5"
        ),
    )
    consent_date = models.DateTimeField(null=True, blank=True)
    consent_method = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ("written", _("Written Signature")),
            ("digital", _("Digital Consent")),
            ("verbal", _("Verbal (Witnessed)")),
            ("guardian", _("Guardian Consent")),
        ],
    )
    consent_withdrawn = models.BooleanField(default=False)
    consent_withdrawn_date = models.DateTimeField(null=True, blank=True)

    # Administrative
    facility = models.ForeignKey(
        "accounts.Facility", on_delete=models.CASCADE, related_name="patients"
    )
    patient_number = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text=_("Internal facility patient number (MRN)"),
    )
    is_active = models.BooleanField(default=True)
    deceased = models.BooleanField(default=False)
    deceased_date = models.DateField(null=True, blank=True)

    # Audit
    registered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="registered_patients",
    )

    class Meta:
        db_table = "patients_patient"
        verbose_name = _("patient")
        verbose_name_plural = _("patients")
        indexes = [
            models.Index(fields=["nida_nin", "is_active"]),
            models.Index(fields=["patient_number", "facility"]),
            models.Index(fields=["nhif_card_number", "insurance_expiry"]),
            models.Index(fields=["last_name", "first_name", "date_of_birth"]),
            models.Index(fields=["region", "district", "ward"]),
        ]
        permissions = [
            ("export_patient_data", "Can export patient data for reporting"),
            ("view_phi", "Can view protected health information"),
        ]

    def __str__(self):
        return f"{self.patient_number} - {self.get_full_name()}"

    def get_full_name(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"

    def get_age(self):
        today = timezone.now().date()
        born = self.date_of_birth
        age = (
            today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        )
        return age

    def can_process_data(self):
        """Check if patient consent allows data processing per PDPA"""
        if not self.consent_status:
            return False
        if self.consent_withdrawn:
            return False
        return True

    def record_consent(self, method="digital", user=None):
        """Record informed consent with timestamp"""
        self.consent_status = True
        self.consent_date = timezone.now()
        self.consent_method = method
        self.consent_withdrawn = False
        self.save()

        ConsentLog.objects.create(
            patient=self,
            action="granted",
            method=method,
            performed_by=user,
            timestamp=self.consent_date,
        )

    def withdraw_consent(self, user=None):
        """Handle consent withdrawal per PDPA right to erasure"""
        self.consent_withdrawn = True
        self.consent_withdrawn_date = timezone.now()
        self.save()

        ConsentLog.objects.create(
            patient=self,
            action="withdrawn",
            method="patient_request",
            performed_by=user,
            timestamp=self.consent_withdrawn_date,
        )

    def save(self, *args, **kwargs):
        if not self.patient_number:
            # Generate MRN: FAC-CODE-YYYY-NNNN
            year = timezone.now().year
            count = (
                Patient.objects.filter(
                    facility=self.facility, created_at__year=year
                ).count()
                + 1
            )
            self.patient_number = f"{self.facility.code}-{year}-{count:04d}"
        super().save(*args, **kwargs)


class ConsentLog(models.Model):
    """Audit trail for consent management - PDPA 2022 compliance"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="consent_logs"
    )
    action = models.CharField(
        max_length=20,
        choices=[
            ("granted", _("Consent Granted")),
            ("withdrawn", _("Consent Withdrawn")),
            ("updated", _("Consent Updated")),
        ],
    )
    method = models.CharField(max_length=20)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        db_table = "patients_consent_log"
        ordering = ["-timestamp"]


class NextOfKin(models.Model):
    """Emergency contacts and next of kin"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="next_of_kin"
    )
    full_name = models.CharField(max_length=150)
    relationship = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        db_table = "patients_next_of_kin"
        verbose_name_plural = "next of kin"
