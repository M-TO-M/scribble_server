import re
from stdnum import isbn

from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError


def ISBNValidator(input_isbn):
    normalized = re.sub(" |-", "", input_isbn).upper()

    if not isinstance(normalized, str):
        raise ValidationError(_("invalid_isbn_not_string"))
    if len(normalized) != 10 and len(normalized) != 13:
        raise ValidationError(_("invalid_isbn_wrong_length"))
    if not isbn.is_valid(normalized):
        raise ValidationError(_("invalid_isbn_failed_checksum"))

    return True


