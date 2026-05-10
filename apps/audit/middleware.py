"""Audit Log Middleware - Captures all PHI access"""
import json
from django.utils import timezone
from django.conf import settings
from .models import AuditLog


class AuditLogMiddleware:
    SENSITIVE_RESOURCES = [
        "patients", "consultations", "clinical_records", 
        "admissions", "prescriptions", "invoices", "nhif_claims"
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if not hasattr(request, "user") or not request.user.is_authenticated:
            return response
        if not request.path.startswith("/api/"):
            return response

        resource_type = self._extract_resource_type(request.path)
        if not resource_type:
            return response

        action = self._determine_action(request.method)
        severity = self._determine_severity(action, resource_type)

        try:
            AuditLog.objects.create(
                user=request.user,
                action=action,
                severity=severity,
                resource_type=resource_type,
                resource_id=self._extract_resource_id(request.path),
                resource_repr=self._build_resource_repr(request, response),
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:512],
                session_id=request.session.session_key or "",
                change_summary=f"{action} {resource_type} via {request.method} {request.path}",
                retention_until=timezone.now() + timezone.timedelta(days=365 * settings.MEDICAL_RECORD_RETENTION_YEARS)
            )
        except Exception:
            pass

        return response

    def _extract_resource_type(self, path):
        parts = path.strip("/").split("/")
        if len(parts) >= 2 and parts[0] == "api":
            return parts[1] if parts[1] in self.SENSITIVE_RESOURCES else None
        return None

    def _extract_resource_id(self, path):
        parts = path.strip("/").split("/")
        if len(parts) >= 3:
            return parts[2]
        return ""

    def _determine_action(self, method):
        mapping = {"GET": "READ", "POST": "CREATE", "PUT": "UPDATE", "PATCH": "UPDATE", "DELETE": "DELETE"}
        return mapping.get(method, "READ")

    def _determine_severity(self, action, resource_type):
        if action == "DELETE":
            return "critical"
        if resource_type in ["patients", "clinical_records"]:
            return "high"
        return "medium"

    def _build_resource_repr(self, request, response):
        return f"{request.method} {request.path} - Status {response.status_code}"

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")
