from django.urls import path
from .views import (
    ConsultationListCreateView, ConsultationDetailView,
    ICD10CodeListView, PrescriptionListCreateView, PrescriptionDispenseView
)

urlpatterns = [
    path("", ConsultationListCreateView.as_view(), name="consultation-list"),
    path("<uuid:id>/", ConsultationDetailView.as_view(), name="consultation-detail"),
    path("icd10/", ICD10CodeListView.as_view(), name="icd10-list"),
    path("prescriptions/", PrescriptionListCreateView.as_view(), name="prescription-list"),
    path("prescriptions/<uuid:id>/dispense/", PrescriptionDispenseView.as_view(), name="prescription-dispense"),
]
