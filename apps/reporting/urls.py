from django.urls import path
from .views import (
    DHIS2ReportListView, DHIS2DataElementListView,
    generate_mtuha_report, submit_dhis2_report, check_notifiable_disease
)

urlpatterns = [
    path("dhis2/reports/", DHIS2ReportListView.as_view(), name="dhis2-reports"),
    path("dhis2/elements/", DHIS2DataElementListView.as_view(), name="dhis2-elements"),
    path("mtuha/generate/", generate_mtuha_report, name="generate-mtuha"),
    path("dhis2/submit/", submit_dhis2_report, name="submit-dhis2"),
    path("eidsr/check/<str:icd10_code>/", check_notifiable_disease, name="check-notifiable"),
]
