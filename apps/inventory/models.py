"""Inventory & Pharmacy with FEFO and Batch Tracking"""
import uuid
from django.db import models, transaction
from django.db.models import F
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.conf import settings

from apps.common.models import TimestampedModel


class InventoryItem(TimestampedModel):
    """Medicine / Medical Supply Master Data"""
    CATEGORY_CHOICES = [
        ("medicine", _("Medicine")),
        ("medical_supply", _("Medical Supply")),
        ("laboratory", _("Laboratory Reagent")),
        ("radiology", _("Radiology Consumable")),
        ("surgical", _("Surgical Instrument")),
    ]

    VEN_CHOICES = [
        ("vital", _("Vital")),
        ("essential", _("Essential")),
        ("non_essential", _("Non-Essential")),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    msd_code = models.CharField(
        max_length=20,
        blank=True,
        db_index=True,
        help_text=_("Medical Stores Department catalogue code")
    )
    name = models.CharField(max_length=255)
    generic_name = models.CharField(max_length=255, blank=True)
    brand_name = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    ven_classification = models.CharField(max_length=15, choices=VEN_CHOICES, blank=True)

    # MSD Pricing
    msd_unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Stock Control
    reorder_level = models.PositiveIntegerField(default=10)
    reorder_quantity = models.PositiveIntegerField(default=50)

    # Regulatory
    requires_prescription = models.BooleanField(default=False)
    controlled_substance = models.BooleanField(default=False)
    storage_conditions = models.CharField(max_length=50, blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "inventory_item"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["category", "ven_classification"]),
            models.Index(fields=["msd_code", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.msd_code or 'N/A'})"

    @property
    def total_stock(self):
        return self.batches.aggregate(total=models.Sum("quantity_remaining"))["total"] or 0

    @property
    def is_low_stock(self):
        return self.total_stock <= self.reorder_level


class InventoryBatch(TimestampedModel):
    """Batch-level tracking for FEFO (First-Expiry-First-Out)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item = models.ForeignKey(
        InventoryItem,
        on_delete=models.CASCADE,
        related_name="batches"
    )
    facility = models.ForeignKey(
        "accounts.Facility",
        on_delete=models.CASCADE,
        related_name="inventory_batches"
    )

    batch_number = models.CharField(max_length=50, db_index=True)
    expiry_date = models.DateField(db_index=True)
    quantity_received = models.PositiveIntegerField()
    quantity_remaining = models.PositiveIntegerField()

    # Procurement
    supplier = models.CharField(max_length=100, blank=True)
    invoice_reference = models.CharField(max_length=50, blank=True)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)

    # Location
    storage_location = models.CharField(max_length=50, blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "inventory_batch"
        ordering = ["expiry_date", "created_at"]
        indexes = [
            models.Index(fields=["item", "expiry_date", "quantity_remaining"]),
            models.Index(fields=["facility", "expiry_date"]),
            models.Index(fields=["batch_number", "item"]),
        ]
        unique_together = ["item", "batch_number", "facility"]

    def __str__(self):
        return f"{self.item.name} - Batch {self.batch_number} (Exp: {self.expiry_date})"

    def clean(self):
        if self.expiry_date < timezone.now().date():
            raise ValidationError(_("Cannot receive expired stock."))
        if self.quantity_remaining > self.quantity_received:
            raise ValidationError(_("Remaining quantity cannot exceed received quantity."))


class DispensingLog(TimestampedModel):
    """Track every dispensing event for audit and stock control"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prescription = models.ForeignKey(
        "consultations.Prescription",
        on_delete=models.CASCADE,
        related_name="dispensing_logs",
        null=True,
        blank=True
    )
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.CASCADE,
        related_name="dispensing_logs"
    )
    batch = models.ForeignKey(
        InventoryBatch,
        on_delete=models.PROTECT,
        related_name="dispensing_logs"
    )
    quantity_dispensed = models.PositiveIntegerField()
    dispensed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="dispensed_items",
        limit_choices_to={"role": "pharmacist"}
    )

    class Meta:
        db_table = "inventory_dispensing_log"
        ordering = ["-created_at"]


class StockAdjustment(TimestampedModel):
    """Record stock adjustments (damage, expiry, recount)"""
    ADJUSTMENT_TYPES = [
        ("expired", _("Expired")),
        ("damaged", _("Damaged")),
        ("recount", _("Recount")),
        ("returned", _("Returned to Supplier")),
        ("theft", _("Theft/Loss")),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(
        InventoryBatch,
        on_delete=models.CASCADE,
        related_name="adjustments"
    )
    adjustment_type = models.CharField(max_length=20, choices=ADJUSTMENT_TYPES)
    quantity_adjusted = models.IntegerField(help_text=_("Negative for reduction"))
    reason = models.TextField()
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    class Meta:
        db_table = "inventory_stock_adjustment"
