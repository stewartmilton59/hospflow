"""Billing API Views"""
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import Invoice, NHIFClaim
from .serializers import InvoiceSerializer, InvoiceCreateSerializer, NHIFClaimSerializer
from .vfd_service import VFDService
from .nhif_service import NHIFService
from apps.accounts.permissions import IsBillingStaff, IsAdmin


class InvoiceListCreateView(generics.ListCreateAPIView):
    queryset = Invoice.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["status", "payment_method", "facility", "patient"]
    search_fields = ["invoice_number", "patient__first_name"]
    permission_classes = [IsBillingStaff]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return InvoiceCreateSerializer
        return InvoiceSerializer


class InvoiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsBillingStaff]
    lookup_field = "id"


@api_view(["POST"])
@permission_classes([IsBillingStaff])
def register_vfd_receipt(request, invoice_id):
    """Register invoice with TRA VFD system"""
    try:
        invoice = Invoice.objects.get(id=invoice_id)
    except Invoice.DoesNotExist:
        return Response({"error": "Invoice not found"}, status=status.HTTP_404_NOT_FOUND)

    if invoice.vfd_registered:
        return Response({"error": "Invoice already registered with VFD"}, status=status.HTTP_400_BAD_REQUEST)

    vfd_service = VFDService(invoice.facility)
    result = vfd_service.register_receipt(invoice)

    if result["success"]:
        return Response({"message": "VFD receipt registered", "gc": invoice.vfd_gc})
    return Response({"error": result.get("error")}, status=status.HTTP_502_BAD_GATEWAY)


@api_view(["POST"])
@permission_classes([IsAdmin])
def submit_z_report(request, facility_id):
    """Submit daily Z-report to TRA"""
    from apps.accounts.models import Facility
    try:
        facility = Facility.objects.get(id=facility_id)
    except Facility.DoesNotExist:
        return Response({"error": "Facility not found"}, status=status.HTTP_404_NOT_FOUND)

    vfd_service = VFDService(facility)
    result = vfd_service.submit_z_report()

    if result["success"]:
        return Response({"message": "Z-report submitted successfully"})
    return Response({"error": result.get("error")}, status=status.HTTP_502_BAD_GATEWAY)


# NHIF Views
class NHIFClaimListCreateView(generics.ListCreateAPIView):
    queryset = NHIFClaim.objects.all()
    serializer_class = NHIFClaimSerializer
    permission_classes = [IsBillingStaff]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status", "facility", "patient"]


@api_view(["POST"])
@permission_classes([IsBillingStaff])
def verify_nhif_member(request):
    """Verify NHIF member card at point of service"""
    card_number = request.data.get("card_number")
    if not card_number:
        return Response({"error": "Card number required"}, status=status.HTTP_400_BAD_REQUEST)

    service = NHIFService()
    result = service.verify_member(card_number)
    return Response(result)


@api_view(["POST"])
@permission_classes([IsBillingStaff])
def submit_nhif_claim(request, claim_id):
    """Submit NHIF claim electronically"""
    try:
        claim = NHIFClaim.objects.get(id=claim_id)
    except NHIFClaim.DoesNotExist:
        return Response({"error": "Claim not found"}, status=status.HTTP_404_NOT_FOUND)

    service = NHIFService()
    result = service.submit_claim(claim)
    return Response(result)
