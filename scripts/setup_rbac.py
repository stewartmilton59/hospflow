"""Setup script for RBAC groups and permissions"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hospflow.settings")
django.setup()

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


def create_role_groups():
    """Create Django groups for each hospital role"""
    roles = ["ADMIN", "DOCTOR", "NURSE", "PHARMACIST", "RECEPTIONIST", "LAB_TECH", "ACCOUNTANT", "WARD_CLERK"]

    for role in roles:
        group, created = Group.objects.get_or_create(name=role)
        if created:
            print(f"Created group: {role}")
        else:
            print(f"Group already exists: {role}")

    print("\nRBAC setup complete.")


if __name__ == "__main__":
    create_role_groups()
