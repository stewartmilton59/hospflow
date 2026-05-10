"""Base test configuration"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.accounts.models import Facility, Department

User = get_user_model()


class BaseHospFlowTest(TestCase):
    def setUp(self):
        self.facility = Facility.objects.create(
            name="Test Regional Hospital",
            facility_type="regional_referral",
            registration_number="REG-001",
            region="Dar es Salaam",
            district="Ilala",
            phone="+255712345678",
            email="test@hospflow.go.tz",
            nhif_facility_code="TEST001",
            tra_tin="123-456-789",
            vfd_serial_number="TRA-VFD-TEST-001"
        )

        self.department = Department.objects.create(
            name="General Medicine",
            code="GMED",
            description="General medical department"
        )

        self.admin_user = User.objects.create_superuser(
            email="admin@test.com",
            first_name="Admin",
            last_name="User",
            role="admin",
            password="adminpass123"
        )
        self.admin_user.facility = self.facility
        self.admin_user.save()
