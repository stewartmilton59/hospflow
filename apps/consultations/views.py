"""Consultation API Views"""
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.utils import timezone

from .models import Consultation, ICD10Code, Prescription
from .serializers import (
    ConsultationListSerializer, ConsultationDetailSerializer,
    PrescriptionSerializer, ICD10CodeSerializer
)
from apps.accounts.permissions import IsClinicalStaff, IsDoctor, IsPharmacist


class ConsultationListCreateView(generics.ListCreateAPIView):
    queryset = Consultation.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "priority", "visit_type", "facility", "doctor"]
    search_fields = ["patient__first_name", "patient__last_name", "chief_complaint"]
    ordering_fields = ["visit_date", "priority"]
    permission_classes = [IsClinicalStaff]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ConsultationDetailSerializer
        return ConsultationListSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ConsultationDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Consultation.objects.all()
    serializer_class = ConsultationDetailSerializer
    permission_classes = [IsDoctor]
    lookup_field = "id"


class ICD10CodeListView(generics.ListAPIView):
    """Searchable ICD-10-CM code reference"""
    queryset = ICD10Code.objects.filter(is_active=True)
    serializer_class = ICD10CodeSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["code", "description", "category"]
    permission_classes = [IsClinicalStaff]


class PrescriptionListCreateView(generics.ListCreateAPIView):
    queryset = Prescription.objects.all()
    serializer_class = PrescriptionSerializer
    permission_classes = [IsDoctor]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class PrescriptionDispenseView(generics.UpdateAPIView):
    queryset = Prescription.objects.filter(dispensed=False)
    serializer_class = PrescriptionSerializer
    permission_classes = [IsPharmacist]
    lookup_field = "id"

    def perform_update(self, serializer):
        serializer.save(
            dispensed=True,
            dispensed_by=self.request.user,
            dispensed_at=timezone.now()
        )
