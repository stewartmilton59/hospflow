"""TRA Virtual Fiscal Device (VFD) Integration Service"""
import base64
import hashlib
from datetime import datetime
from typing import Dict, Optional
import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import Invoice, VFDCounter


class VFDService:
    """
    TRA VFD Integration Service
    Handles digital signatures, counters, and Z-reports per TRA specifications.
    """

    def __init__(self, facility):
        self.facility = facility
        self.api_base = settings.VFD_API_BASE_URL
        self.tax_payer_id = settings.VFD_TAX_PAYER_ID
        self.serial_number = facility.vfd_serial_number or settings.VFD_SERIAL_NUMBER
        self.private_key_path = settings.VFD_PRIVATE_KEY_PATH

    def _load_private_key(self):
        """Load RSA private key for signing"""
        from cryptography.hazmat.primitives import serialization
        with open(self.private_key_path, "rb") as key_file:
            return serialization.load_pem_private_key(key_file.read(), password=None)

    def _generate_signature(self, payload: str) -> str:
        """Generate SHA-1 with RSA signature, Base64 encoded"""
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding

        private_key = self._load_private_key()
        signature = private_key.sign(
            payload.encode("utf-8"),
            padding.PKCS1v15(),
            hashes.SHA1()
        )
        return base64.b64encode(signature).decode("utf-8")

    def _get_or_create_counter(self) -> VFDCounter:
        counter, _ = VFDCounter.objects.get_or_create(facility=self.facility)
        return counter

    def _reset_daily_counter_if_needed(self, counter: VFDCounter):
        """Reset DC at midnight"""
        now = timezone.now()
        if counter.last_receipt_date and counter.last_receipt_date.date() != now.date():
            counter.daily_counter = 0
            counter.save()

    @transaction.atomic
    def register_receipt(self, invoice: Invoice) -> Dict:
        """
        Register receipt with TRA VFD system.
        Increments GC and DC, generates signature.
        """
        counter = self._get_or_create_counter()
        self._reset_daily_counter_if_needed(counter)

        # Lock row to prevent race conditions
        counter = VFDCounter.objects.select_for_update().get(pk=counter.pk)

        counter.global_counter += 1
        counter.daily_counter += 1
        counter.last_receipt_date = timezone.now()

        # ZNUM format: YYYYMMDD
        znum = timezone.now().strftime("%Y%m%d")
        counter.z_report_number = znum

        counter.save()

        # Build receipt payload
        receipt_data = {
            "TIN": self.tax_payer_id,
            "REGID": self.serial_number,
            "EFDSERIAL": self.serial_number,
            "CUSTIDTYPE": 1,  # TIN
            "CUSTID": invoice.patient.nida_nin or "",
            "CUSTNAME": invoice.patient.get_full_name(),
            "MOBILENUM": invoice.patient.phone_number or "",
            "RCTNUM": counter.global_counter,
            "DC": counter.daily_counter,
            "GC": counter.global_counter,
            "ZNUM": znum,
            "RCTVNUM": counter.global_counter,
            "DATE": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ITEMS": [
                {
                    "ID": str(item.id)[:8],
                    "DESC": item.description,
                    "QTY": float(item.quantity),
                    "TAXCODE": "1",  # Standard VAT
                    "AMT": float(item.total_price)
                }
                for item in invoice.items.all()
            ],
            "TOTAL": float(invoice.total_amount),
            "TAX": float(invoice.tax_amount),
        }

        # Generate signature
        payload_string = f"{receipt_data['TIN']}{receipt_data['RCTNUM']}{receipt_data['TOTAL']:.2f}"
        signature = self._generate_signature(payload_string)
        receipt_data["SIGNATURE"] = signature

        # Send to TRA
        try:
            response = requests.post(
                f"{self.api_base}/receipts",
                json=receipt_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
            result = response.json()

            # Update invoice with VFD data
            invoice.vfd_registered = True
            invoice.vfd_gc = counter.global_counter
            invoice.vfd_rctnum = counter.global_counter
            invoice.vfd_znum = znum
            invoice.vfd_signature = signature
            invoice.vfd_registered_at = timezone.now()
            invoice.save()

            return {"success": True, "vfd_data": receipt_data, "tra_response": result}

        except requests.RequestException as e:
            # Rollback counters on failure
            counter.global_counter -= 1
            counter.daily_counter -= 1
            counter.save()
            return {"success": False, "error": str(e)}

    def submit_z_report(self) -> Dict:
        """Submit daily Z-report to TRA before new business day"""
        counter = self._get_or_create_counter()

        znum = timezone.now().strftime("%Y%m%d")

        # Aggregate daily totals
        from django.db.models import Sum
        daily_invoices = Invoice.objects.filter(
            facility=self.facility,
            vfd_registered=True,
            vfd_znum=znum
        )

        totals = daily_invoices.aggregate(
            total_sales=Sum("total_amount"),
            total_tax=Sum("tax_amount"),
            receipt_count=models.Count("id")
        )

        z_report = {
            "TIN": self.tax_payer_id,
            "EFDSERIAL": self.serial_number,
            "ZNUM": znum,
            "DATE": timezone.now().strftime("%Y-%m-%d"),
            "TOTAL": float(totals.get("total_sales") or 0),
            "TAX": float(totals.get("total_tax") or 0),
            "NUMRCT": totals.get("receipt_count") or 0,
            "DC": counter.daily_counter,
        }

        try:
            response = requests.post(
                f"{self.api_base}/z-reports",
                json=z_report,
                timeout=30
            )
            response.raise_for_status()

            counter.last_z_report_date = timezone.now().date()
            counter.save()

            return {"success": True, "z_report": z_report}
        except requests.RequestException as e:
            return {"success": False, "error": str(e)}
