import re
from stdnum import isbn

from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


domain_allowlist = [
    "naver.com",
    "gmail.com",
    "outlook.com",
    "daum.net",
    "hanmail.net",
    "nate.com",
    "hotmail.com",
    "icloud.com"
]


def ISBNValidator(input_isbn):
    normalized = re.sub(" |-", "", input_isbn).upper()

    if not isinstance(normalized, str):
        raise ValidationError(_(u'invalid ISBN: not a string'))
    if len(normalized) != 10 or len(normalized) != 13:
        raise ValidationError(_(u'invalid ISBN: wrong length'))
    if not isbn.is_valid(normalized):
        raise ValidationError(_(u'invalid ISBN: failed checksum'))

    return True


class SpecificEmailDomainValidator(EmailValidator):
    def validate_domain_part(self, domain_part):
        if self.domain_regex.match(domain_part) is None:
            return False

        if domain_part not in self.domain_allowlist:
            raise ValidationError(_("invalid_domain"))

        return True
