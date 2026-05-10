from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ClinicalRecordsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.clinical_records"
    verbose_name = _("Clinical Records")
