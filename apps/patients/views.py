"""Patient API Views"""
from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from .models import Patient, ConsentLog
from .serializers import (
    PatientListSerializer, PatientDetailSerializer, 
    PatientCreateSerializer, ConsentLogSerializer
)
from apps.accounts.permissions import IsClinicalStaff, IsReceptionist, IsAdmin


class PatientListCreateView(generics.ListCreateAPIView):
    queryset = Patient.objects.filter(is_active=True)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["gender", "facility", "region", "district", "consent_status"]
    search_fields = ["patient_number", "nida_nin", "first_name", "last_name", "phone_number"]
    ordering_fields = ["created_at", "last_name", "date_of_birth"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PatientCreateSerializer
        return PatientListSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsReceptionist()]
        return [IsClinicalStaff()]

    def perform_create(self, serializer):
        serializer.save(registered_by=self.request.user)


class PatientDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Patient.objects.all()
    serializer_class = PatientDetailSerializer
    permission_classes = [IsClinicalStaff]
    lookup_field = "unique_id"


class PatientSearchView(generics.ListAPIView):
    """Advanced patient search across multiple fields"""
    serializer_class = PatientListSerializer
    permission_classes = [IsClinicalStaff]

    def get_queryset(self):
        queryset = Patient.objects.filter(is_active=True)
        q = self.request.query_params.get("q", "")
        if q:
            queryset = queryset.filter(
                Q(patient_number__icontains=q) |
                Q(nida_nin__icontains=q) |
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q) |
                Q(phone_number__icontains=q)
            )
        return queryset


@api_view(["POST"])
@permission_classes([IsClinicalStaff])
def record_consent(request, unique_id):
    """Record patient consent per PDPA 2022"""
    try:
        patient = Patient.objects.get(unique_id=unique_id)
    except Patient.DoesNotExist:
        return Response({"error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)

    method = request.data.get("method", "digital")
    patient.record_consent(method=method, user=request.user)
    return Response({"message": "Consent recorded successfully", "consent_date": patient.consent_date})


@api_view(["POST"])
@permission_classes([IsClinicalStaff])
def withdraw_consent(request, unique_id):
    """Handle consent withdrawal"""
    try:
        patient = Patient.objects.get(unique_id=unique_id)
    except Patient.DoesNotExist:
        return Response({"error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)

    patient.withdraw_consent(user=request.user)
    return Response({"message": "Consent withdrawn successfully"})
