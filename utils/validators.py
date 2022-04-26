from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError


domain_allowlist = ["naver.com", "daum.com", "gmail.com", "icloud.com"]


class SpecificEmailDomainValidator(EmailValidator):
    def validate_domain_part(self, domain_part):
        if self.domain_regex.match(domain_part) is None:
            return False

        if domain_part not in self.domain_allowlist:
            raise ValidationError("사용할 수 없는 이메일 도메인입니다")

        return True
