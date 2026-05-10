"""Tests for NHIF Integration"""
from django.test import TestCase
from unittest.mock import patch, MagicMock
from apps.billing.nhif_service import NHIFService
from apps.billing.models import NHIFClaim
from apps.accounts.models import Facility
from apps.patients.models import Patient
from django.utils import timezone


class NHIFTests(TestCase):
    def setUp(self):
        self.facility = Facility.objects.create(
            name="Test Hospital",
            facility_type="district_hospital",
            registration_number="REG-001",
            region="Dar es Salaam",
            district="Ilala",
            phone="+255712345678",
            email="test@test.com",
            nhif_facility_code="TEST001"
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
            facility=self.facility,
            nhif_card_number="NHIF123456"
        )

    @patch("apps.billing.nhif_service.requests.post")
    def test_member_verification(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "Status": "Active",
                "Scheme": "NHIF Tanzania",
                "AuthorizationID": "AUTH-001"
            }
        )

        service = NHIFService()
        result = service.verify_member("NHIF123456")

        self.assertTrue(result["valid"])
        self.assertEqual(result["status"], "Active")
        self.assertIsNotNone(result["authorization_id"])

    def test_claim_creation(self):
        claim = NHIFClaim.objects.create(
            patient=self.patient,
            facility=self.facility,
            member_card_number="NHIF123456",
            claim_amount=150000,
            diagnosis_codes=["A00.1", "B20.9"]
        )

        self.assertIsNotNone(claim.claim_number)
        self.assertTrue(claim.claim_number.startswith("NHIF-"))
        self.assertEqual(claim.status, "draft")

    @patch("apps.billing.nhif_service.requests.post")
    def test_claim_submission(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"ReferenceNo": "REF-001", "Status": "Received"}
        )

        claim = NHIFClaim.objects.create(
            patient=self.patient,
            facility=self.facility,
            member_card_number="NHIF123456",
            claim_amount=150000,
            diagnosis_codes=["A00.1"]
        )

        service = NHIFService()
        result = service.submit_claim(claim)

        self.assertTrue(result["success"])
        claim.refresh_from_db()
        self.assertEqual(claim.status, "submitted")
