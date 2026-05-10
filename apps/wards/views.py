"""Wards API Views"""
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db import transaction
from django.utils import timezone

from .models import Ward, Bed, Admission, NursingNote, MedicationAdministrationRecord
from .serializers import (
    WardSerializer, BedSerializer, AdmissionSerializer,
    NursingNoteSerializer, MARSerializer
)
from apps.accounts.permissions import IsClinicalStaff, IsNurse, IsDoctor


class WardListView(generics.ListAPIView):
    queryset = Ward.objects.filter(is_active=True)
    serializer_class = WardSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["facility", "ward_type"]
    permission_classes = [IsClinicalStaff]


class BedListView(generics.ListAPIView):
    queryset = Bed.objects.filter(is_active=True)
    serializer_class = BedSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["ward", "status", "bed_type"]
    permission_classes = [IsClinicalStaff]


class AdmissionListCreateView(generics.ListCreateAPIView):
    queryset = Admission.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["status", "ward", "facility"]
    search_fields = ["patient__first_name", "patient__last_name"]
    permission_classes = [IsDoctor]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AdmissionSerializer
        return AdmissionSerializer

    def perform_create(self, serializer):
        with transaction.atomic():
            admission = serializer.save(admitted_by=self.request.user)
            # Reserve bed
            Bed.objects.filter(pk=admission.bed.pk).update(status="occupied")


class AdmissionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Admission.objects.all()
    serializer_class = AdmissionSerializer
    permission_classes = [IsDoctor]
    lookup_field = "id"


@api_view(["POST"])
@permission_classes([IsDoctor])
def discharge_patient(request, admission_id):
    """Discharge patient and free bed atomically"""
    try:
        admission = Admission.objects.get(id=admission_id, status="admitted")
    except Admission.DoesNotExist:
        return Response({"error": "Admission not found"}, status=status.HTTP_404_NOT_FOUND)

    summary = request.data.get("discharge_summary", "")
    disposition = request.data.get("disposition", "home")

    admission.discharge(user=request.user, summary=summary, disposition=disposition)
    return Response({"message": "Patient discharged successfully"})


class NursingNoteListCreateView(generics.ListCreateAPIView):
    queryset = NursingNote.objects.all()
    serializer_class = NursingNoteSerializer
    permission_classes = [IsNurse]

    def perform_create(self, serializer):
        serializer.save(recorded_by=self.request.user)


class MARListCreateView(generics.ListCreateAPIView):
    queryset = MedicationAdministrationRecord.objects.all()
    serializer_class = MARSerializer
    permission_classes = [IsNurse]
    filterset_fields = ["admission", "scheduled_time"]


@api_view(["POST"])
@permission_classes([IsNurse])
def administer_medication(request, mar_id):
    """Record medication administration"""
    try:
        mar = MedicationAdministrationRecord.objects.get(id=mar_id)
    except MedicationAdministrationRecord.DoesNotExist:
        return Response({"error": "MAR entry not found"}, status=status.HTTP_404_NOT_FOUND)

    mar.administered_time = timezone.now()
    mar.administered_by = request.user
    mar.dose_given = request.data.get("dose_given", mar.prescription.dosage)
    mar.route = request.data.get("route", "oral")
    mar.notes = request.data.get("notes", "")
    mar.save()

    return Response({"message": "Medication administered recorded"})
