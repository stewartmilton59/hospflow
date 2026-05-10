from django.urls import path
from .views import (
    WardListView, BedListView, AdmissionListCreateView,
    AdmissionDetailView, discharge_patient,
    NursingNoteListCreateView, MARListCreateView, administer_medication
)

urlpatterns = [
    path("wards/", WardListView.as_view(), name="ward-list"),
    path("beds/", BedListView.as_view(), name="bed-list"),
    path("admissions/", AdmissionListCreateView.as_view(), name="admission-list"),
    path("admissions/<uuid:id>/", AdmissionDetailView.as_view(), name="admission-detail"),
    path("admissions/<uuid:admission_id>/discharge/", discharge_patient, name="discharge"),
    path("nursing-notes/", NursingNoteListCreateView.as_view(), name="nursing-notes"),
    path("mar/", MARListCreateView.as_view(), name="mar-list"),
    path("mar/<uuid:mar_id>/administer/", administer_medication, name="administer-medication"),
]
