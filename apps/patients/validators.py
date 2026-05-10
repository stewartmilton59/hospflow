"""Patient-specific validators"""
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_nida_nin(value):
    """
    Validate 20-digit Tanzanian National Identification Number (NIN).
    The NIN is exactly 20 digits with no alphabetic characters.
    """
    if not value:
        return

    if not re.match(r"^\d{20}$", value):
        raise ValidationError(
            _("NIN must be exactly 20 digits. Received: %(value)s"),
            params={"value": value},
        )

    # Check for sequential or repeated digits (common fake patterns)
    if value in ["0" * 20, "1" * 20, "12345678901234567890"]:
        raise ValidationError(_("NIN appears to be invalid (sequential/repeated digits)."))


def validate_no_future_date(value):
    """Ensure date is not in the future"""
    from django.utils import timezone
    if value and value > timezone.now().date():
        raise ValidationError(_("Date cannot be in the future."))
