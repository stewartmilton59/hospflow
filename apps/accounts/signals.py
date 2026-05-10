"""Signals for Accounts"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from apps.patients.models import Patient
from apps.consultations.models import Consultation
from apps.clinical_records.models import ClinicalRecord
from apps.inventory.models import InventoryItem, DispensingLog

User = get_user_model()


@receiver(post_save, sender=User)
def assign_role_permissions(sender, instance, created, **kwargs):
    """Assign granular permissions based on role"""
    if not created:
        return

    role_perms = {
        "doctor": [
            "view_patient", "change_patient", "add_consultation", "change_consultation",
            "view_clinicalrecord", "add_clinicalrecord", "change_clinicalrecord",
            "view_inventoryitem", "view_dispensinglog",
        ],
        "nurse": [
            "view_patient", "change_patient", "view_consultation",
            "view_clinicalrecord", "add_clinicalrecord",
            "view_inventoryitem", "add_dispensinglog",
        ],
        "pharmacist": [
            "view_patient", "view_consultation", "view_clinicalrecord",
            "view_inventoryitem", "change_inventoryitem", "add_dispensinglog",
        ],
        "receptionist": [
            "add_patient", "change_patient", "view_patient",
            "add_consultation", "view_consultation",
        ],
        "lab_tech": [
            "view_patient", "view_consultation", "view_clinicalrecord",
            "add_clinicalrecord", "change_clinicalrecord",
        ],
    }

    if instance.role in role_perms:
        perms = role_perms[instance.role]
        for perm_codename in perms:
            try:
                perm = Permission.objects.get(codename=perm_codename)
                instance.user_permissions.add(perm)
            except Permission.DoesNotExist:
                pass
