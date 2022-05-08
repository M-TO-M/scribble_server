import re
from stdnum import isbn

from django.core.validators import EmailValidator, BaseValidator
from django.utils.translation import gettext_lazy as _

from rest_framework.exceptions import ValidationError


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
            raise ValidationError({"detail": "invalid_domain", "domain_allowlist": self.domain_allowlist})

        return True


class CategoryDictValidator(BaseValidator):
    message = _("Ensure this value is contained in given data dict.")
    code = "limit_dict"

    def __init__(self, limit_value, message=None):
        super().__init__(limit_value, message)
        self.limit_value = limit_value
        if message:
            self.message = message

    def __call__(self, value):
        cleaned = self.clean(value) if isinstance(self.clean(value), list) else self.clean(value).values()
        limit_value = self.limit_value \
            if isinstance(self.limit_value, dict) else {i: val for i, val in enumerate(self.limit_value)}

        for value in cleaned:
            if self.compare(value, limit_value):
                raise ValidationError({"detail": "invalid_category", "category_list": self.limit_value})

    def compare(self, a, b):
        return a not in list(b.values())
