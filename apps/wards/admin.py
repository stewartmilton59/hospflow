from django.contrib import admin
from .models import Ward, Bed, Admission, NursingNote, MedicationAdministrationRecord


class BedInline(admin.TabularInline):
    model = Bed
    extra = 1


@admin.register(Ward)
class WardAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "ward_type", "floor", "capacity", "available_beds", "occupancy_rate", "is_active"]
    list_filter = ["ward_type", "is_active"]
    inlines = [BedInline]


@admin.register(Bed)
class BedAdmin(admin.ModelAdmin):
    list_display = ["bed_number", "ward", "bed_type", "status"]
    list_filter = ["status", "bed_type", "ward"]


@admin.register(Admission)
class AdmissionAdmin(admin.ModelAdmin):
    list_display = ["id", "patient", "bed", "ward", "admission_date", "status", "review_overdue"]
    list_filter = ["status", "ward", "admission_date"]
    date_hierarchy = "admission_date"


@admin.register(NursingNote)
class NursingNoteAdmin(admin.ModelAdmin):
    list_display = ["admission", "recorded_by", "created_at"]


@admin.register(MedicationAdministrationRecord)
class MARAdmin(admin.ModelAdmin):
    list_display = ["admission", "prescription", "scheduled_time", "administered_time", "missed"]
    list_filter = ["missed", "scheduled_time"]
