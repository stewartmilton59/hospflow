"""Patients URL Configuration"""
from django.urls import path
from .views import (
    PatientListCreateView, PatientDetailView, 
    PatientSearchView, record_consent, withdraw_consent
)

urlpatterns = [
    path("", PatientListCreateView.as_view(), name="patient-list"),
    path("search/", PatientSearchView.as_view(), name="patient-search"),
    path("<uuid:unique_id>/", PatientDetailView.as_view(), name="patient-detail"),
    path("<uuid:unique_id>/consent/", record_consent, name="record-consent"),
    path("<uuid:unique_id>/consent/withdraw/", withdraw_consent, name="withdraw-consent"),
]
