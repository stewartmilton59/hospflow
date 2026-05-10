from rest_framework import generics
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import ClinicalRecord, LabResult, RadiologyReport
from .serializers import ClinicalRecordSerializer, LabResultSerializer, RadiologyReportSerializer
from apps.accounts.permissions import IsClinicalStaff


class ClinicalRecordListCreateView(generics.ListCreateAPIView):
    queryset = ClinicalRecord.objects.all()
    serializer_class = ClinicalRecordSerializer
    permission_classes = [IsClinicalStaff]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["patient", "record_type", "record_date"]
    search_fields = ["patient__first_name", "patient__last_name"]


class ClinicalRecordDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ClinicalRecord.objects.all()
    serializer_class = ClinicalRecordSerializer
    permission_classes = [IsClinicalStaff]
    lookup_field = "id"


class LabResultListCreateView(generics.ListCreateAPIView):
    queryset = LabResult.objects.all()
    serializer_class = LabResultSerializer
    permission_classes = [IsClinicalStaff]


class RadiologyReportListCreateView(generics.ListCreateAPIView):
    queryset = RadiologyReport.objects.all()
    serializer_class = RadiologyReportSerializer
    permission_classes = [IsClinicalStaff]
