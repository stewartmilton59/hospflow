"""Billing, VFD Fiscal Compliance, and NHIF Insurance"""
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings

from apps.common.models import TimestampedModel


class Invoice(TimestampedModel):
    """Patient Invoice with TRA VFD Compliance"""
    PAYMENT_METHODS = [
        ("cash", _("Cash")),
        ("nhif", _("NHIF")),
        ("insurance", _("Other Insurance")),
        ("card", _("Card Payment")),
        ("mobile_money", _("Mobile Money")),
        ("mixed", _("Mixed Payment")),
    ]

    STATUS_CHOICES = [
        ("pending", _("Pending")),
        ("paid", _("Paid")),
        ("partial", _("Partially Paid")),
        ("cancelled", _("Cancelled")),
        ("refunded", _("Refunded")),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_number = models.CharField(max_length=20, unique=True, db_index=True)
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.CASCADE,
        related_name="invoices"
    )
    facility = models.ForeignKey(
        "accounts.Facility",
        on_delete=models.CASCADE,
        related_name="invoices"
    )
    consultation = models.ForeignKey(
        "consultations.Consultation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoice"
    )

    # Financial Summary
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_due = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default="cash")

    # VFD Fields (TRA Compliance)
    vfd_registered = models.BooleanField(default=False)
    vfd_gc = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_("VFD Global Counter")
    )
    vfd_rctnum = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_("VFD Receipt Number")
    )
    vfd_znum = models.CharField(
        max_length=8, blank=True,
        verbose_name=_("VFD Z-Report Number")
    )
    vfd_signature = models.TextField(blank=True)
    vfd_qr_code = models.TextField(blank=True)
    vfd_registered_at = models.DateTimeField(null=True, blank=True)

    # NHIF Fields
    nhif_claim = models.ForeignKey(
        "NHIFClaim",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="invoices"
    )
    nhif_authorized = models.BooleanField(default=False)
    nhif_authorization_id = models.CharField(max_length=50, blank=True)

    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="issued_invoices"
    )

    class Meta:
        db_table = "billing_invoice"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["patient", "status"]),
            models.Index(fields=["facility", "created_at"]),
            models.Index(fields=["vfd_registered", "vfd_gc"]),
        ]

    def __str__(self):
        return f"INV-{self.invoice_number} - {self.patient} - TZS {self.total_amount}"

    def save(self, *args, **kwargs):
        # Calculate totals
        self.balance_due = self.total_amount - self.amount_paid - self.discount
        if self.balance_due <= 0:
            self.status = "paid"
        elif self.amount_paid > 0:
            self.status = "partial"

        if not self.invoice_number:
            today = timezone.now()
            count = Invoice.objects.filter(
                facility=self.facility,
                created_at__date=today.date()
            ).count() + 1
            self.invoice_number = f"INV-{today.strftime('%Y%m%d')}-{count:04d}"

        super().save(*args, **kwargs)


class InvoiceItem(models.Model):
    """Individual line items on an invoice"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")
    description = models.CharField(max_length=255)
    item_code = models.CharField(max_length=20, blank=True, help_text=_("NHIF/MSD item code"))
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    # Categorization for reporting
    category = models.CharField(
        max_length=20,
        choices=[
            ("consultation", _("Consultation")),
            ("procedure", _("Procedure")),
            ("medication", _("Medication")),
            ("laboratory", _("Laboratory")),
            ("radiology", _("Radiology")),
            ("ward", _("Ward Charges")),
            ("other", _("Other")),
        ]
    )

    class Meta:
        db_table = "billing_invoice_item"

    def save(self, *args, **kwargs):
        self.total_price = (self.quantity * self.unit_price) * (1 + self.tax_rate / 100)
        super().save(*args, **kwargs)


class NHIFClaim(TimestampedModel):
    """NHIF Insurance Claims"""
    STATUS_CHOICES = [
        ("draft", _("Draft")),
        ("submitted", _("Submitted")),
        ("acknowledged", _("Acknowledged")),
        ("approved", _("Approved")),
        ("rejected", _("Rejected")),
        ("paid", _("Paid")),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    claim_number = models.CharField(max_length=30, unique=True, db_index=True)
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.CASCADE,
        related_name="nhif_claims"
    )
    facility = models.ForeignKey(
        "accounts.Facility",
        on_delete=models.CASCADE,
        related_name="nhif_claims"
    )

    # NHIF API Fields
    member_card_number = models.CharField(max_length=20)
    authorization_id = models.CharField(max_length=50, blank=True)
    scheme_code = models.CharField(max_length=20, blank=True)

    # Claim Details
    claim_date = models.DateTimeField(default=timezone.now)
    admission_date = models.DateField(null=True, blank=True)
    discharge_date = models.DateField(null=True, blank=True)
    diagnosis_codes = models.JSONField(default=list, help_text=_("ICD-10 codes for claim"))

    # Financial
    claim_amount = models.DecimalField(max_digits=12, decimal_places=2)
    approved_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    rejection_reason = models.TextField(blank=True)

    # API Tracking
    nhif_reference = models.CharField(max_length=100, blank=True, db_index=True)
    submission_payload = models.JSONField(default=dict)
    api_response = models.JSONField(default=dict)

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="submitted_nhif_claims"
    )

    class Meta:
        db_table = "billing_nhif_claim"
        ordering = ["-claim_date"]

    def save(self, *args, **kwargs):
        if not self.claim_number:
            today = timezone.now()
            count = NHIFClaim.objects.filter(
                facility=self.facility,
                claim_date__date=today.date()
            ).count() + 1
            self.claim_number = f"NHIF-{today.strftime('%Y%m%d')}-{count:04d}"
        super().save(*args, **kwargs)


class VFDCounter(models.Model):
    """TRA VFD Counter Management - Singleton per facility"""
    facility = models.OneToOneField(
        "accounts.Facility",
        on_delete=models.CASCADE,
        related_name="vfd_counter"
    )
    global_counter = models.PositiveIntegerField(default=0, help_text=_("GC: Never resets"))
    daily_counter = models.PositiveIntegerField(default=0, help_text=_("DC: Resets at midnight"))
    z_report_number = models.CharField(max_length=8, blank=True)
    last_z_report_date = models.DateField(null=True, blank=True)
    last_receipt_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "billing_vfd_counter"

    def __str__(self):
        return f"VFD Counters for {self.facility.name}"
