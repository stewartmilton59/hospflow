from django.contrib import admin
from .models import InventoryItem, InventoryBatch, DispensingLog, StockAdjustment


class InventoryBatchInline(admin.TabularInline):
    model = InventoryBatch
    extra = 0


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ["name", "msd_code", "category", "ven_classification", "total_stock", "is_low_stock", "is_active"]
    list_filter = ["category", "ven_classification", "requires_prescription", "is_active"]
    search_fields = ["name", "generic_name", "msd_code"]
    inlines = [InventoryBatchInline]


@admin.register(InventoryBatch)
class InventoryBatchAdmin(admin.ModelAdmin):
    list_display = ["item", "batch_number", "expiry_date", "quantity_remaining", "facility"]
    list_filter = ["facility", "expiry_date"]
    search_fields = ["item__name", "batch_number"]
    date_hierarchy = "expiry_date"


@admin.register(DispensingLog)
class DispensingLogAdmin(admin.ModelAdmin):
    list_display = ["patient", "batch", "quantity_dispensed", "dispensed_by", "created_at"]
    list_filter = ["dispensed_by", "created_at"]


@admin.register(StockAdjustment)
class StockAdjustmentAdmin(admin.ModelAdmin):
    list_display = ["batch", "adjustment_type", "quantity_adjusted", "performed_by", "created_at"]
    list_filter = ["adjustment_type", "created_at"]
