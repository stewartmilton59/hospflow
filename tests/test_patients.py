"""Tests for Patients module"""
from django.test import TestCase
from django.utils import timezone
from apps.patients.models import Patient, ConsentLog
from apps.accounts.models import Facility


class PatientTests(TestCase):
    def setUp(self):
        self.facility = Facility.objects.create(
            name="Test Hospital",
            facility_type="district_hospital",
            registration_number="REG-001",
            region="Dar es Salaam",
            district="Ilala",
            phone="+255712345678",
            email="test@test.com"
        )

    def test_patient_creation(self):
        patient = Patient.objects.create(
            first_name="Juma",
            last_name="Musa",
            date_of_birth=timezone.now().date().replace(year=1990),
            gender="male",
            phone_number="+255712345678",
            region="Dar es Salaam",
            district="Ilala",
            ward="Kariakoo",
            facility=self.facility,
            consent_status=True,
            consent_date=timezone.now(),
            consent_method="digital"
        )

        self.assertIsNotNone(patient.patient_number)
        self.assertTrue(patient.patient_number.startswith("TEST"))
        self.assertTrue(patient.can_process_data())

    def test_consent_withdrawal(self):
        patient = Patient.objects.create(
            first_name="Asha",
            last_name="Juma",
            date_of_birth=timezone.now().date().replace(year=1985),
            gender="female",
            phone_number="+255723456789",
            region="Dar es Salaam",
            district="Kinondoni",
            ward="Tandale",
            facility=self.facility,
            consent_status=True
        )

        patient.withdraw_consent()
        self.assertTrue(patient.consent_withdrawn)
        self.assertFalse(patient.can_process_data())

        # Check consent log created
        logs = ConsentLog.objects.filter(patient=patient, action="withdrawn")
        self.assertEqual(logs.count(), 1)

    def test_age_calculation(self):
        from datetime import date
        patient = Patient(
            first_name="Test",
            last_name="Patient",
            date_of_birth=date(1990, 1, 1),
            gender="male",
            phone_number="+255712345678",
            region="Dar es Salaam",
            district="Ilala",
            ward="Test",
            facility=self.facility
        )
        age = patient.get_age()
        self.assertGreater(age, 30)
