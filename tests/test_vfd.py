"""Tests for TRA VFD Integration"""
from django.test import TestCase
from unittest.mock import patch, MagicMock
from apps.billing.models import Invoice, VFDCounter
from apps.billing.vfd_service import VFDService
from apps.accounts.models import Facility
from apps.patients.models import Patient
from django.utils import timezone


class VFDTests(TestCase):
    def setUp(self):
        self.facility = Facility.objects.create(
            name="Test Hospital",
            facility_type="district_hospital",
            registration_number="REG-001",
            region="Dar es Salaam",
            district="Ilala",
            phone="+255712345678",
            email="test@test.com",
            vfd_serial_number="TRA-VFD-TEST-001"
        )

        self.patient = Patient.objects.create(
            first_name="Test",
            last_name="Patient",
            date_of_birth=timezone.now().date().replace(year=1990),
            gender="male",
            phone_number="+255712345678",
            region="Dar es Salaam",
            district="Ilala",
            ward="Test",
            facility=self.facility
        )

    @patch("apps.billing.vfd_service.requests.post")
    def test_vfd_receipt_registration(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"status": "success", "receipt_id": "RCP-001"}
        )

        invoice = Invoice.objects.create(
            patient=self.patient,
            facility=self.facility,
            total_amount=50000,
            status="pending"
        )

        vfd_service = VFDService(self.facility)
        result = vfd_service.register_receipt(invoice)

        self.assertTrue(result["success"])
        self.assertIsNotNone(invoice.vfd_gc)
        self.assertIsNotNone(invoice.vfd_signature)

    def test_vfd_counter_increment(self):
        counter, _ = VFDCounter.objects.get_or_create(facility=self.facility)
        initial_gc = counter.global_counter
        initial_dc = counter.daily_counter

        counter.global_counter += 1
        counter.daily_counter += 1
        counter.save()

        counter.refresh_from_db()
        self.assertEqual(counter.global_counter, initial_gc + 1)
        self.assertEqual(counter.daily_counter, initial_dc + 1)

    def test_znum_format(self):
        znum = timezone.now().strftime("%Y%m%d")
        self.assertEqual(len(znum), 8)
        self.assertTrue(znum.isdigit())
