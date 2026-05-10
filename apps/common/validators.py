"""Common validators for HospFlow"""
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_phone_number_tz(value):
    """Validate Tanzanian phone number format"""
    pattern = r"^(0|\+255|255)[67][123456789][0-9]{7}$"
    if not re.match(pattern, value):
        raise ValidationError(
            _("%(value)s is not a valid Tanzanian phone number."),
            params={"value": value},
        )


def validate_tz_currency(value):
    """Validate positive decimal for TZS"""
    if value < 0:
        raise ValidationError(_("Amount cannot be negative."))
