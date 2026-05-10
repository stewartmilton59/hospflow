from django.contrib import admin
from .models import DHIS2DataElement, DHIS2Report, MTUHAIndicator


@admin.register(DHIS2DataElement)
class DHIS2DataElementAdmin(admin.ModelAdmin):
    list_display = ["dhis2_uid", "name", "mtuha_book", "mtuha_indicator"]
    search_fields = ["name", "dhis2_uid"]


@admin.register(DHIS2Report)
class DHIS2ReportAdmin(admin.ModelAdmin):
    list_display = ["report_period", "facility", "report_type", "status", "created_at"]
    list_filter = ["status", "report_type", "created_at"]


@admin.register(MTUHAIndicator)
class MTUHAIndicatorAdmin(admin.ModelAdmin):
    list_display = ["indicator_code", "name", "book", "aggregation_method"]
