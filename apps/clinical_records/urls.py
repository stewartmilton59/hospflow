from django.urls import path
from .views import (
    ClinicalRecordListCreateView, ClinicalRecordDetailView,
    LabResultListCreateView, RadiologyReportListCreateView
)

urlpatterns = [
    path("", ClinicalRecordListCreateView.as_view(), name="clinical-record-list"),
    path("<uuid:id>/", ClinicalRecordDetailView.as_view(), name="clinical-record-detail"),
    path("lab-results/", LabResultListCreateView.as_view(), name="lab-results"),
    path("radiology/", RadiologyReportListCreateView.as_view(), name="radiology-reports"),
]
