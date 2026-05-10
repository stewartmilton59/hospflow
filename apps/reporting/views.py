"""Reporting API Views"""
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from django.utils import timezone

from .service import DHIS2Service, eIDSRService
from .models import DHIS2Report, DHIS2DataElement
from .serializers import DHIS2ReportSerializer, DHIS2DataElementSerializer
from .tasks import submit_monthly_mtuha_report


class DHIS2ReportListView(generics.ListAPIView):
    queryset = DHIS2Report.objects.all()
    serializer_class = DHIS2ReportSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ["facility", "report_period", "status"]


class DHIS2DataElementListView(generics.ListAPIView):
    queryset = DHIS2DataElement.objects.all()
    serializer_class = DHIS2DataElementSerializer
    permission_classes = [IsAdminUser]


@api_view(["POST"])
@permission_classes([IsAdminUser])
def generate_mtuha_report(request):
    """Generate MTUHA Book 10 report"""
    facility_id = request.data.get("facility_id")
    year = request.data.get("year", timezone.now().year)
    quarter = request.data.get("quarter", 1)

    service = DHIS2Service()
    from apps.accounts.models import Facility
    facility = Facility.objects.get(id=facility_id)

    report = service.generate_mtuha_book_10(facility, year, quarter)
    return Response(report)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def submit_dhis2_report(request):
    """Queue DHIS2 report submission"""
    facility_id = request.data.get("facility_id")
    period = request.data.get("period")

    task = submit_monthly_mtuha_report.delay(facility_id, period)
    return Response({"task_id": task.id, "status": "queued"})


@api_view(["GET"])
@permission_classes([IsAdminUser])
def check_notifiable_disease(request, icd10_code):
    """Check if disease code is notifiable"""
    is_notifiable = eIDSRService.check_notifiable(icd10_code)
    return Response({"code": icd10_code, "notifiable": is_notifiable})
