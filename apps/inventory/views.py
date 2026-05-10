"""Inventory API Views with FEFO dispensing"""
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.db import transaction
from django.db.models import F, Sum
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.utils import timezone

from .models import InventoryItem, InventoryBatch, DispensingLog, StockAdjustment
from .serializers import (
    InventoryItemSerializer, InventoryBatchSerializer,
    DispensingLogSerializer, StockAdjustmentSerializer
)
from apps.accounts.permissions import IsPharmacist, IsClinicalStaff


class InventoryItemListView(generics.ListAPIView):
    queryset = InventoryItem.objects.filter(is_active=True)
    serializer_class = InventoryItemSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["category", "ven_classification", "requires_prescription"]
    search_fields = ["name", "generic_name", "msd_code"]
    permission_classes = [IsClinicalStaff]


class InventoryBatchListView(generics.ListAPIView):
    queryset = InventoryBatch.objects.filter(is_active=True, quantity_remaining__gt=0)
    serializer_class = InventoryBatchSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["item", "facility", "expiry_date"]
    permission_classes = [IsPharmacist]


@api_view(["POST"])
@permission_classes([IsPharmacist])
def dispense_medication(request):
    """
    Dispense medication using FEFO (First-Expiry-First-Out).
    Uses select_for_update() to prevent race conditions.
    """
    from apps.consultations.models import Prescription

    prescription_id = request.data.get("prescription_id")
    quantity = request.data.get("quantity")

    if not prescription_id or not quantity:
        return Response(
            {"error": "prescription_id and quantity are required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        prescription = Prescription.objects.get(id=prescription_id, dispensed=False)
    except Prescription.DoesNotExist:
        return Response(
            {"error": "Prescription not found or already dispensed"},
            status=status.HTTP_404_NOT_FOUND
        )

    item = prescription.medication

    with transaction.atomic():
        # Get batches ordered by expiry date (FEFO)
        batches = InventoryBatch.objects.select_for_update().filter(
            item=item,
            facility=request.user.facility,
            quantity_remaining__gt=0,
            expiry_date__gte=timezone.now().date()
        ).order_by("expiry_date")

        if not batches.exists():
            return Response(
                {"error": "No available stock for this medication"},
                status=status.HTTP_400_BAD_REQUEST
            )

        remaining_to_dispense = quantity
        dispensed_batches = []

        for batch in batches:
            if remaining_to_dispense <= 0:
                break

            dispense_qty = min(remaining_to_dispense, batch.quantity_remaining)

            # Use F() expression to prevent race condition
            InventoryBatch.objects.filter(pk=batch.pk).update(
                quantity_remaining=F("quantity_remaining") - dispense_qty
            )

            # Refresh to get updated value
            batch.refresh_from_db()

            # Create dispensing log
            log = DispensingLog.objects.create(
                prescription=prescription,
                patient=prescription.consultation.patient,
                batch=batch,
                quantity_dispensed=dispense_qty,
                dispensed_by=request.user
            )

            dispensed_batches.append({
                "batch": batch.batch_number,
                "quantity": dispense_qty,
                "expiry": batch.expiry_date
            })
            remaining_to_dispense -= dispense_qty

        if remaining_to_dispense > 0:
            transaction.set_rollback(True)
            return Response(
                {"error": f"Insufficient stock. Short by {remaining_to_dispense} units"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Mark prescription as dispensed
        prescription.dispensed = True
        prescription.dispensed_by = request.user
        prescription.dispensed_at = timezone.now()
        prescription.save()

    return Response({
        "message": "Medication dispensed successfully",
        "batches": dispensed_batches,
        "total_dispensed": quantity
    })


@api_view(["POST"])
@permission_classes([IsPharmacist])
def receive_stock(request):
    """Receive stock from MSD or supplier"""
    item_id = request.data.get("item_id")
    batch_number = request.data.get("batch_number")
    expiry_date = request.data.get("expiry_date")
    quantity = request.data.get("quantity")
    unit_cost = request.data.get("unit_cost", 0)

    try:
        item = InventoryItem.objects.get(id=item_id)
    except InventoryItem.DoesNotExist:
        return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)

    batch, created = InventoryBatch.objects.get_or_create(
        item=item,
        batch_number=batch_number,
        facility=request.user.facility,
        defaults={
            "expiry_date": expiry_date,
            "quantity_received": quantity,
            "quantity_remaining": quantity,
            "unit_cost": unit_cost,
            "supplier": request.data.get("supplier", "MSD")
        }
    )

    if not created:
        batch.quantity_received += quantity
        batch.quantity_remaining += quantity
        batch.save()

    return Response({
        "message": "Stock received successfully",
        "batch_id": str(batch.id),
        "total_quantity": batch.quantity_remaining
    })


class StockAdjustmentListCreateView(generics.ListCreateAPIView):
    queryset = StockAdjustment.objects.all()
    serializer_class = StockAdjustmentSerializer
    permission_classes = [IsPharmacist]

    def perform_create(self, serializer):
        adjustment = serializer.save(performed_by=self.request.user)
        # Update batch quantity
        batch = adjustment.batch
        batch.quantity_remaining += adjustment.quantity_adjusted
        if batch.quantity_remaining <= 0:
            batch.is_active = False
        batch.save()
