from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import DHIS2DataElement, DHIS2Report, MTUHAIndicator


@admin.register(DHIS2DataElement)
class DHIS2DataElementAdmin(ModelAdmin):
    list_display = ["dhis2_uid", "name", "mtuha_book", "mtuha_indicator"]
    search_fields = ["name", "dhis2_uid"]


@admin.register(DHIS2Report)
class DHIS2ReportAdmin(ModelAdmin):
    list_display = ["report_period", "facility", "report_type", "status", "created_at"]
    list_filter = ["status", "report_type", "created_at"]


@admin.register(MTUHAIndicator)
class MTUHAIndicatorAdmin(ModelAdmin):
    list_display = ["indicator_code", "name", "book", "aggregation_method"]
