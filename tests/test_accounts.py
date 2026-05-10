"""Tests for Accounts module"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.accounts.models import Facility

User = get_user_model()


class AccountsTests(TestCase):
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

    def test_user_creation(self):
        user = User.objects.create_user(
            email="doctor@test.com",
            first_name="John",
            last_name="Doe",
            role="doctor",
            password="testpass123",
            facility=self.facility
        )
        self.assertEqual(user.email, "doctor@test.com")
        self.assertEqual(user.role, "doctor")
        self.assertTrue(user.check_password("testpass123"))

    def test_superuser_creation(self):
        admin = User.objects.create_superuser(
            email="admin@test.com",
            first_name="Admin",
            last_name="User",
            role="admin",
            password="adminpass123"
        )
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)

    def test_nin_validation(self):
        from apps.patients.validators import validate_nida_nin
        # Valid NIN
        self.assertIsNone(validate_nida_nin("12345678901234567890"))
        # Invalid length
        with self.assertRaises(Exception):
            validate_nida_nin("1234567890")
        # Invalid characters
        with self.assertRaises(Exception):
            validate_nida_nin("1234567890123456789A")

    def test_account_lockout(self):
        user = User.objects.create_user(
            email="nurse@test.com",
            first_name="Jane",
            last_name="Smith",
            role="nurse",
            password="testpass123"
        )
        user.failed_login_attempts = 5
        from django.utils import timezone
        user.locked_until = timezone.now() + timezone.timedelta(minutes=30)
        user.save()

        self.assertTrue(user.is_account_locked())
