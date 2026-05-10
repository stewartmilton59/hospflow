"""Celery tasks for inventory management"""
from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from .models import InventoryBatch, InventoryItem


@shared_task
def check_low_stock_and_expiry():
    """
    Nightly background task to check for low stock and expiry alerts.
    Sends notifications to procurement officers.
    """
    today = timezone.now().date()
    alert_threshold = today + timezone.timedelta(days=90)  # 3 months

    # Expiring batches
    expiring_batches = InventoryBatch.objects.filter(
        is_active=True,
        expiry_date__lte=alert_threshold,
        expiry_date__gte=today
    ).select_related("item", "facility")

    # Low stock items
    low_stock_items = []
    for item in InventoryItem.objects.filter(is_active=True):
        if item.is_low_stock:
            low_stock_items.append(item)

    # Send alerts (simplified - in production use SMS/email)
    alerts = []

    for batch in expiring_batches:
        days_left = (batch.expiry_date - today).days
        alerts.append(
            f"EXPIRY ALERT: {batch.item.name} (Batch {batch.batch_number}) "
            f"expires in {days_left} days at {batch.facility.name}"
        )

    for item in low_stock_items:
        alerts.append(
            f"LOW STOCK: {item.name} ({item.msd_code}) - "
            f"Current: {item.total_stock}, Reorder Level: {item.reorder_level}"
        )

    if alerts:
        # In production, send via SMS/Email to procurement
        print("\n".join(alerts))
        return f"Sent {len(alerts)} alerts"

    return "No alerts generated"
