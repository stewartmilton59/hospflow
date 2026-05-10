"""Inventory Serializers"""
from rest_framework import serializers
from .models import InventoryItem, InventoryBatch, DispensingLog, StockAdjustment


class InventoryItemSerializer(serializers.ModelSerializer):
    total_stock = serializers.IntegerField(read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = InventoryItem
        fields = [
            "id", "msd_code", "name", "generic_name", "brand_name",
            "category", "ven_classification", "msd_unit_price", "selling_price",
            "reorder_level", "reorder_quantity", "requires_prescription",
            "controlled_substance", "total_stock", "is_low_stock", "is_active"
        ]


class InventoryBatchSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="item.name", read_only=True)
    item_msd_code = serializers.CharField(source="item.msd_code", read_only=True)
    days_until_expiry = serializers.SerializerMethodField()

    class Meta:
        model = InventoryBatch
        fields = [
            "id", "item", "item_name", "item_msd_code", "batch_number",
            "expiry_date", "days_until_expiry", "quantity_received",
            "quantity_remaining", "unit_cost", "supplier", "storage_location"
        ]

    def get_days_until_expiry(self, obj):
        from django.utils import timezone
        return (obj.expiry_date - timezone.now().date()).days


class DispensingLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DispensingLog
        fields = ["id", "prescription", "patient", "batch", "quantity_dispensed", "dispensed_by", "created_at"]


class StockAdjustmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockAdjustment
        fields = ["id", "batch", "adjustment_type", "quantity_adjusted", "reason", "performed_by", "created_at"]
