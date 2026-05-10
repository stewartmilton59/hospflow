"""HospFlow Accounts - RBAC & Identity Management"""
import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, Group
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User Model with RBAC for Tanzanian Healthcare"""

    ROLE_CHOICES = [
        ("admin", _("Administrator")),
        ("doctor", _("Doctor")),
        ("nurse", _("Nurse")),
        ("pharmacist", _("Pharmacist")),
        ("receptionist", _("Receptionist")),
        ("lab_tech", _("Laboratory Technician")),
        ("accountant", _("Accountant")),
        ("ward_clerk", _("Ward Clerk")),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_("email address"), unique=True)
    nida_nin = models.CharField(
        _("NIDA NIN"), 
        max_length=20, 
        blank=True, 
        null=True,
        db_index=True,
        help_text=_("20-digit National Identification Number")
    )
    first_name = models.CharField(_("first name"), max_length=150)
    last_name = models.CharField(_("last name"), max_length=150)
    phone_number = models.CharField(_("phone number"), max_length=15, blank=True)
    role = models.CharField(_("role"), max_length=20, choices=ROLE_CHOICES, default="receptionist")
    department = models.ForeignKey(
        "Department", 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="staff"
    )
    facility = models.ForeignKey(
        "Facility",
        on_delete=models.CASCADE,
        related_name="staff",
        null=True,
    )

    # Professional Registration (for doctors/nurses)
    professional_reg_no = models.CharField(
        _("professional registration number"),
        max_length=50,
        blank=True,
        help_text=_("Medical Council or Nursing Council registration number")
    )

    # Status Fields
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    failed_login_attempts = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    # MFA
    mfa_enabled = models.BooleanField(default=False)
    mfa_secret = models.CharField(max_length=255, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "role"]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        db_table = "accounts_user"
        indexes = [
            models.Index(fields=["role", "is_active"]),
            models.Index(fields=["facility", "department"]),
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name

    def is_account_locked(self):
        if self.locked_until and self.locked_until > timezone.now():
            return True
        return False

    def save(self, *args, **kwargs):
        # Auto-assign to Django Group based on role
        super().save(*args, **kwargs)
        if self.role:
            group, _ = Group.objects.get_or_create(name=self.role.upper())
            self.groups.add(group)


class Department(models.Model):
    """Hospital Departments"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    head = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="headed_department",
        limit_choices_to={"role": "doctor"}
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "accounts_department"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Facility(models.Model):
    """Healthcare Facility (Hospital/Clinic)"""
    FACILITY_TYPES = [
        ("national_referral", _("National Referral Hospital")),
        ("regional_referral", _("Regional Referral Hospital")),
        ("district_hospital", _("District Hospital")),
        ("health_center", _("Health Center")),
        ("dispensary", _("Dispensary")),
        ("clinic", _("Clinic")),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    facility_type = models.CharField(max_length=20, choices=FACILITY_TYPES)
    registration_number = models.CharField(max_length=50, unique=True)

    # Location
    region = models.CharField(max_length=50)
    district = models.CharField(max_length=50)
    ward = models.CharField(max_length=50)
    street = models.CharField(max_length=100, blank=True)

    # Contact
    phone = models.CharField(max_length=15)
    email = models.EmailField()

    # NHIF & Regulatory
    nhif_facility_code = models.CharField(max_length=20, blank=True, db_index=True)
    tra_tin = models.CharField(max_length=20, blank=True, verbose_name=_("TRA TIN"))
    vfd_serial_number = models.CharField(max_length=50, blank=True)

    # DHIS2
    dhis2_org_unit_id = models.CharField(max_length=50, blank=True, db_index=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "facilities"
        db_table = "accounts_facility"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.get_facility_type_display()})"
