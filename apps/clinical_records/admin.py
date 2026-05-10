from django.contrib import admin
from .models import ClinicalRecord, LabResult, RadiologyReport


class LabResultInline(admin.TabularInline):
    model = LabResult
    extra = 0


class RadiologyReportInline(admin.TabularInline):
    model = RadiologyReport
    extra = 0


@admin.register(ClinicalRecord)
class ClinicalRecordAdmin(admin.ModelAdmin):
    list_display = ["id", "patient", "record_date", "record_type", "recorded_by"]
    list_filter = ["record_type", "record_date"]
    search_fields = ["patient__first_name", "patient__last_name", "patient__patient_number"]
    inlines = [LabResultInline, RadiologyReportInline]
    readonly_fields = ["id", "record_date", "created_at"]


@admin.register(LabResult)
class LabResultAdmin(admin.ModelAdmin):
    list_display = ["clinical_record", "test_name", "loinc_code", "is_abnormal", "created_at"]
    list_filter = ["is_abnormal", "created_at"]


@admin.register(RadiologyReport)
class RadiologyReportAdmin(admin.ModelAdmin):
    list_display = ["clinical_record", "study_type", "body_part", "radiologist", "created_at"]
