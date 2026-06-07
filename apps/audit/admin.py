from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import AuditLog, DataExportLog


@admin.register(AuditLog)
class AuditLogAdmin(ModelAdmin):
    list_display = ["created_at", "user", "action", "resource_type", "severity", "ip_address"]
    list_filter = ["action", "severity", "resource_type", "created_at"]
    search_fields = ["user__email", "resource_id", "resource_repr"]
    readonly_fields = ["id", "created_at", "user", "action", "resource_type", "resource_id", 
                       "ip_address", "user_agent", "previous_state", "new_state"]
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(DataExportLog)
class DataExportLogAdmin(ModelAdmin):
    list_display = ["created_at", "user", "export_type", "record_count", "file_format"]
