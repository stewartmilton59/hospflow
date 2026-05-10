"""Billing Serializers"""
from rest_framework import serializers
from .models import Invoice, InvoiceItem, NHIFClaim


class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = ["id", "description", "item_code", "quantity", "unit_price", "tax_rate", "total_price", "category"]


class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, read_only=True)
    patient_name = serializers.CharField(source="patient.get_full_name", read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id", "invoice_number", "patient", "patient_name", "facility",
            "subtotal", "tax_amount", "discount", "total_amount",
            "amount_paid", "balance_due", "status", "payment_method",
            "vfd_registered", "vfd_gc", "vfd_rctnum", "vfd_znum",
            "nhif_authorized", "nhif_authorization_id",
            "items", "created_at"
        ]


class InvoiceCreateSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True)

    class Meta:
        model = Invoice
        fields = ["patient", "facility", "consultation", "items", "payment_method", "discount"]

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        invoice = Invoice.objects.create(**validated_data)

        subtotal = 0
        for item_data in items_data:
            item = InvoiceItem.objects.create(invoice=invoice, **item_data)
            subtotal += item.total_price

        invoice.subtotal = subtotal
        invoice.tax_amount = subtotal * 0.18  # 18% VAT
        invoice.total_amount = invoice.subtotal + invoice.tax_amount - invoice.discount
        invoice.balance_due = invoice.total_amount
        invoice.save()

        return invoice


class NHIFClaimSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.get_full_name", read_only=True)

    class Meta:
        model = NHIFClaim
        fields = [
            "id", "claim_number", "patient", "patient_name", "facility",
            "member_card_number", "authorization_id", "scheme_code",
            "claim_date", "diagnosis_codes", "claim_amount",
            "approved_amount", "paid_amount", "status", "rejection_reason",
            "nhif_reference", "created_at"
        ]
        read_only_fields = ["claim_number", "status", "nhif_reference"]
