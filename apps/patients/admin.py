"""Patient Admin Configuration"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline
from .models import Patient, ConsentLog, NextOfKin


class ConsentLogInline(TabularInline):
    model = ConsentLog
    extra = 0
    readonly_fields = ["action", "method", "performed_by", "timestamp", "ip_address"]
    can_delete = False


class NextOfKinInline(TabularInline):
    model = NextOfKin
    extra = 1


@admin.register(Patient)
class PatientAdmin(ModelAdmin):
    list_display = [
        "patient_number",
        "get_full_name",
        "nida_nin",
        "gender",
        "date_of_birth",
        "phone_number",
        "consent_status",
        "facility",
        "is_active",
    ]
    list_filter = [
        "gender",
        "consent_status",
        "facility",
        "region",
        "is_active",
        "deceased",
    ]
    search_fields = [
        "patient_number",
        "nida_nin",
        "first_name",
        "last_name",
        "phone_number",
        "nhif_card_number",
    ]
    readonly_fields = ["id", "patient_number", "created_at", "updated_at"]
    inlines = [ConsentLogInline, NextOfKinInline]

    fieldsets = (
        (
            _("Identifiers"),
            {
                "fields": (
                    "unique_id",
                    "patient_number",
                    "nida_nin",
                    "biometric_reference",
                )
            },
        ),
        (
            _("Personal Info"),
            {
                "fields": (
                    "first_name",
                    "middle_name",
                    "last_name",
                    "date_of_birth",
                    "gender",
                    "marital_status",
                )
            },
        ),
        (
            _("Contact"),
            {
                "fields": (
                    "phone_number",
                    "email",
                    "emergency_contact_name",
                    "emergency_contact_phone",
                )
            },
        ),
        (_("Address"), {"fields": ("region", "district", "ward", "village_street")}),
        (
            _("Insurance"),
            {"fields": ("nhif_card_number", "insurance_scheme", "insurance_expiry")},
        ),
        (
            _("Consent (PDPA 2022)"),
            {
                "fields": (
                    "consent_status",
                    "consent_date",
                    "consent_method",
                    "consent_withdrawn",
                    "consent_withdrawn_date",
                )
            },
        ),
        (
            _("Administrative"),
            {
                "fields": (
                    "facility",
                    "registered_by",
                    "is_active",
                    "deceased",
                    "deceased_date",
                )
            },
        ),
    )

    def get_full_name(self, obj):
        return obj.get_full_name()

    get_full_name.short_description = _("Name")


@admin.register(ConsentLog)
class ConsentLogAdmin(ModelAdmin):
    list_display = ["patient", "action", "method", "performed_by", "timestamp"]
    list_filter = ["action", "method", "timestamp"]
    search_fields = [
        "patient__patient_number",
        "patient__first_name",
        "patient__last_name",
    ]
    readonly_fields = [
        "patient",
        "action",
        "method",
        "performed_by",
        "timestamp",
        "ip_address",
    ]
