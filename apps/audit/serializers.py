from rest_framework import serializers
from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id", "created_at", "user", "user_email", "action", "severity",
            "resource_type", "resource_id", "resource_repr", "ip_address",
            "change_summary", "pdpa_compliant", "consent_verified"
        ]
