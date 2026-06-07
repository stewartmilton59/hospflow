"""Billing Admin Configuration"""
from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import Invoice, InvoiceItem, NHIFClaim, VFDCounter


class InvoiceItemInline(TabularInline):
    model = InvoiceItem
    extra = 1


@admin.register(Invoice)
class InvoiceAdmin(ModelAdmin):
    list_display = [
        "invoice_number", "patient", "total_amount", "status", 
        "payment_method", "vfd_registered", "nhif_authorized"
    ]
    list_filter = ["status", "payment_method", "vfd_registered", "facility"]
    search_fields = ["invoice_number", "patient__first_name", "patient__last_name"]
    inlines = [InvoiceItemInline]
    readonly_fields = ["balance_due", "vfd_signature"]


@admin.register(NHIFClaim)
class NHIFClaimAdmin(ModelAdmin):
    list_display = ["claim_number", "patient", "claim_amount", "status", "claim_date"]
    list_filter = ["status", "claim_date"]
    search_fields = ["claim_number", "member_card_number", "patient__first_name"]


@admin.register(VFDCounter)
class VFDCounterAdmin(ModelAdmin):
    list_display = ["facility", "global_counter", "daily_counter", "z_report_number", "last_receipt_date"]
    readonly_fields = ["global_counter", "daily_counter"]
