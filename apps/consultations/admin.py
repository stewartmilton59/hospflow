"""Consultations Admin"""
from django.contrib import admin
from .models import ICD10Code, Consultation, Prescription


@admin.register(ICD10Code)
class ICD10CodeAdmin(admin.ModelAdmin):
    list_display = ["code", "description", "category", "is_sdh", "is_active"]
    list_filter = ["category", "is_sdh", "is_active"]
    search_fields = ["code", "description"]


class PrescriptionInline(admin.TabularInline):
    model = Prescription
    extra = 1


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ["id", "patient", "doctor", "visit_date", "status", "priority", "disposition"]
    list_filter = ["status", "priority", "visit_type", "disposition", "is_notifiable_disease"]
    search_fields = ["patient__patient_number", "patient__first_name", "chief_complaint"]
    inlines = [PrescriptionInline]
    date_hierarchy = "visit_date"

    fieldsets = (
        ("Visit Info", {"fields": ("patient", "doctor", "facility", "visit_date", "status", "priority", "visit_type")}),
        ("Vitals", {"fields": (
            ("vital_temperature", "vital_blood_pressure_sys", "vital_blood_pressure_dia"),
            ("vital_heart_rate", "vital_respiratory_rate", "vital_oxygen_saturation"),
            ("vital_weight_kg", "vital_height_cm", "vital_bmi"),
        )}),
        ("Clinical", {"fields": ("chief_complaint", "history_of_present_illness", "physical_examination", "assessment_and_plan")}),
        ("Diagnosis", {"fields": ("primary_diagnosis", "secondary_diagnoses", "sdoh_codes")}),
        ("Outcome", {"fields": ("disposition", "referral_facility")}),
        ("Billing", {"fields": ("consultation_fee", "is_nhif_claimable")}),
        ("Reporting", {"fields": ("is_notifiable_disease",)}),
    )


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ["consultation", "medication", "dosage", "quantity_prescribed", "dispensed"]
    list_filter = ["dispensed"]
