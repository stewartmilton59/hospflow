from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WardsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.wards"
    verbose_name = _("Ward Management")
