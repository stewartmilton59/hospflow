from django.urls import path
from .views import (
    InvoiceListCreateView, InvoiceDetailView,
    register_vfd_receipt, submit_z_report,
    NHIFClaimListCreateView, verify_nhif_member, submit_nhif_claim
)

urlpatterns = [
    path("invoices/", InvoiceListCreateView.as_view(), name="invoice-list"),
    path("invoices/<uuid:id>/", InvoiceDetailView.as_view(), name="invoice-detail"),
    path("invoices/<uuid:invoice_id>/vfd/", register_vfd_receipt, name="vfd-register"),
    path("z-report/<uuid:facility_id>/", submit_z_report, name="z-report"),
    path("nhif/claims/", NHIFClaimListCreateView.as_view(), name="nhif-claim-list"),
    path("nhif/verify/", verify_nhif_member, name="nhif-verify"),
    path("nhif/claims/<uuid:claim_id>/submit/", submit_nhif_claim, name="nhif-submit"),
]
