from rest_framework import serializers
from .models import NotificationLog


class NotificationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationLog
        fields = [
            "id", "recipient", "recipient_number", "channel", "notification_type",
            "message", "message_id", "provider", "status", "delivered_at",
            "failed_reason", "cost_tzs", "created_at"
        ]
