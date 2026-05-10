"""Notification & Communication Module"""
import uuid
from django.db import models
from django.conf import settings

from apps.common.models import TimestampedModel


class NotificationLog(TimestampedModel):
    """Log of all notifications sent"""
    CHANNEL_CHOICES = [
        ("sms", "SMS"),
        ("email", "Email"),
        ("push", "Push Notification"),
        ("whatsapp", "WhatsApp"),
    ]

    TYPE_CHOICES = [
        ("appointment_reminder", "Appointment Reminder"),
        ("lab_result", "Lab Result Ready"),
        ("otp", "One-Time Password"),
        ("receipt", "E-Receipt"),
        ("alert", "General Alert"),
        ("campaign", "Health Campaign"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True
    )
    recipient_number = models.CharField(max_length=15)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    message = models.TextField()

    # Delivery tracking
    message_id = models.CharField(max_length=100, blank=True, db_index=True)
    provider = models.CharField(max_length=30, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("sent", "Sent"),
            ("delivered", "Delivered"),
            ("failed", "Failed"),
            ("read", "Read"),
        ],
        default="pending"
    )
    delivered_at = models.DateTimeField(null=True, blank=True)
    failed_reason = models.TextField(blank=True)

    # Cost tracking
    cost_tzs = models.DecimalField(max_digits=10, decimal_places=4, default=0)

    class Meta:
        db_table = "notifications_log"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "notification_type", "status"]),
            models.Index(fields=["message_id", "provider"]),
        ]


class AppointmentReminder(TimestampedModel):
    """Scheduled appointment reminders"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    consultation = models.ForeignKey(
        "consultations.Consultation",
        on_delete=models.CASCADE,
        related_name="reminders"
    )
    scheduled_time = models.DateTimeField()
    sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "notifications_appointment_reminder"
        ordering = ["scheduled_time"]
