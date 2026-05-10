"""Ward Management, Bed Occupancy, and MAR"""
import uuid
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings

from apps.common.models import TimestampedModel


class Ward(models.Model):
    """Hospital Ward"""
    WARD_TYPES = [
        ("general_male", _("General Male")),
        ("general_female", _("General Female")),
        ("maternity", _("Maternity")),
        ("pediatric", _("Pediatric")),
        ("surgical", _("Surgical")),
        ("icu", _("Intensive Care")),
        ("nicu", _("Neonatal ICU")),
        ("isolation", _("Isolation")),
        ("private", _("Private")),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    ward_type = models.CharField(max_length=20, choices=WARD_TYPES)
    facility = models.ForeignKey(
        "accounts.Facility",
        on_delete=models.CASCADE,
        related_name="wards"
    )
    floor = models.CharField(max_length=20, blank=True)
    capacity = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "wards_ward"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.get_ward_type_display()})"

    @property
    def available_beds(self):
        return self.beds.filter(status="available").count()

    @property
    def occupancy_rate(self):
        total = self.beds.filter(is_active=True).count()
        occupied = self.beds.filter(status="occupied").count()
        return (occupied / total * 100) if total > 0 else 0


class Bed(models.Model):
    """Individual Bed Tracking"""
    STATUS_CHOICES = [
        ("available", _("Available")),
        ("occupied", _("Occupied")),
        ("reserved", _("Reserved")),
        ("maintenance", _("Maintenance")),
        ("cleaning", _("Cleaning")),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE, related_name="beds")
    bed_number = models.CharField(max_length=10)
    bed_type = models.CharField(
        max_length=20,
        choices=[
            ("standard", _("Standard")),
            ("electric", _("Electric")),
            ("cot", _("Cot")),
            ("bassinet", _("Bassinet")),
            ("isolation", _("Isolation")),
        ],
        default="standard"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="available")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "wards_bed"
        unique_together = ["ward", "bed_number"]
        indexes = [
            models.Index(fields=["ward", "status"]),
            models.Index(fields=["status", "is_active"]),
        ]

    def __str__(self):
        return f"Bed {self.bed_number} - {self.ward.name}"


class Admission(TimestampedModel):
    """Inpatient Admission Record"""
    STATUS_CHOICES = [
        ("admitted", _("Admitted")),
        ("discharged", _("Discharged")),
        ("transferred", _("Transferred")),
        ("absconded", _("Absconded")),
        ("deceased", _("Deceased")),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.CASCADE,
        related_name="admissions"
    )
    bed = models.ForeignKey(
        Bed,
        on_delete=models.PROTECT,
        related_name="admissions"
    )
    ward = models.ForeignKey(
        Ward,
        on_delete=models.PROTECT,
        related_name="admissions"
    )
    facility = models.ForeignKey(
        "accounts.Facility",
        on_delete=models.CASCADE,
        related_name="admissions"
    )

    # Admission Details
    admission_date = models.DateTimeField(default=timezone.now)
    discharge_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="admitted")

    # Clinical
    admitting_diagnosis = models.TextField()
    discharge_diagnosis = models.TextField(blank=True)
    discharge_summary = models.TextField(blank=True)
    discharge_disposition = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ("home", _("Home")),
            ("transfer", _("Transfer")),
            ("referral", _("Referral")),
            ("died", _("Died")),
            ("ama", _("Against Medical Advice")),
        ]
    )

    # Billing
    daily_rate = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_bill = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Review Flags
    review_due = models.DateTimeField(null=True, blank=True)
    review_overdue = models.BooleanField(default=False)

    admitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="admitted_patients"
    )
    discharged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="discharged_patients"
    )

    class Meta:
        db_table = "wards_admission"
        ordering = ["-admission_date"]
        indexes = [
            models.Index(fields=["patient", "status"]),
            models.Index(fields=["ward", "status"]),
            models.Index(fields=["admission_date", "discharge_date"]),
            models.Index(fields=["review_due", "review_overdue"]),
        ]

    def __str__(self):
        return f"Admission {self.id} - {self.patient} in {self.bed}"

    def save(self, *args, **kwargs):
        if self.status == "admitted" and not self.review_due:
            # Set review flag for 48 hours if no clinical note
            self.review_due = timezone.now() + timezone.timedelta(hours=48)
        super().save(*args, **kwargs)

    @transaction.atomic
    def discharge(self, user, summary="", disposition="home"):
        """Atomic discharge operation"""
        self.status = "discharged"
        self.discharge_date = timezone.now()
        self.discharge_summary = summary
        self.discharge_disposition = disposition
        self.discharged_by = user

        # Calculate ward charges
        days = (self.discharge_date - self.admission_date).days or 1
        self.total_bill = days * self.daily_rate

        self.save()

        # Free the bed atomically
        Bed.objects.filter(pk=self.bed.pk).update(status="cleaning")

        # Create final invoice
        from apps.billing.models import Invoice
        Invoice.objects.create(
            patient=self.patient,
            facility=self.facility,
            total_amount=self.total_bill,
            status="pending",
            issued_by=user
        )


class NursingNote(TimestampedModel):
    """Nursing documentation"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    admission = models.ForeignKey(
        Admission,
        on_delete=models.CASCADE,
        related_name="nursing_notes"
    )
    note = models.TextField()
    vital_temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    vital_blood_pressure = models.CharField(max_length=20, blank=True)
    vital_pulse = models.PositiveSmallIntegerField(null=True, blank=True)
    vital_respiration = models.PositiveSmallIntegerField(null=True, blank=True)
    vital_spo2 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="nursing_notes",
        limit_choices_to={"role": "nurse"}
    )

    class Meta:
        db_table = "wards_nursing_note"
        ordering = ["-created_at"]


class MedicationAdministrationRecord(TimestampedModel):
    """MAR - Track medication given to inpatients"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    admission = models.ForeignKey(
        Admission,
        on_delete=models.CASCADE,
        related_name="mar_entries"
    )
    prescription = models.ForeignKey(
        "consultations.Prescription",
        on_delete=models.CASCADE,
        related_name="mar_entries"
    )
    scheduled_time = models.DateTimeField()
    administered_time = models.DateTimeField(null=True, blank=True)
    dose_given = models.CharField(max_length=50)
    route = models.CharField(max_length=50)
    administered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="administered_medications",
        limit_choices_to={"role__in": ["nurse", "doctor"]}
    )
    notes = models.TextField(blank=True)
    missed = models.BooleanField(default=False)
    missed_reason = models.TextField(blank=True)

    class Meta:
        db_table = "wards_mar"
        verbose_name = "Medication Administration Record"
        verbose_name_plural = "Medication Administration Records"
        ordering = ["scheduled_time"]
