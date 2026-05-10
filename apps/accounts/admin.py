"""Django Admin configuration for Accounts"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Department, Facility


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "get_full_name", "role", "department", "facility", "is_active", "is_verified"]
    list_filter = ["role", "is_active", "is_verified", "department", "facility", "date_joined"]
    search_fields = ["email", "first_name", "last_name", "nida_nin", "professional_reg_no"]
    ordering = ["-date_joined"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal Info"), {"fields": ("first_name", "last_name", "nida_nin", "phone_number")}),
        (_("Professional"), {"fields": ("role", "department", "facility", "professional_reg_no")}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "is_verified", "groups", "user_permissions")}),
        (_("Security"), {"fields": ("last_login_ip", "failed_login_attempts", "locked_until", "mfa_enabled")}),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "role", "password1", "password2"),
        }),
    )


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "head", "is_active"]
    search_fields = ["name", "code"]


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ["name", "facility_type", "region", "district", "nhif_facility_code", "is_active"]
    list_filter = ["facility_type", "region", "is_active"]
    search_fields = ["name", "registration_number", "nhif_facility_code", "tra_tin"]
