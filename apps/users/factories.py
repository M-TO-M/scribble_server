import uuid
import random
import base64
import factory
from factory import fuzzy

from django.utils import timezone
from django.contrib.auth.hashers import make_password

from core.validators import domain_allowlist
from .models import User, category_choices


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ['nickname', 'email']

    nickname = fuzzy.FuzzyText(length=10)
    password = make_password('password')
    profile_image = factory.LazyAttribute(lambda n: base64.urlsafe_b64encode(uuid.uuid4().bytes))
    created_at = timezone.now()
    updated_at = timezone.now()
    is_staff = False
    is_superuser = False

    @factory.lazy_attribute_sequence
    def email(self, n):
        return f'{self.nickname}@{domain_allowlist[random.randrange(n + 1) % 4]}'

    @factory.lazy_attribute_sequence
    def category(self, n):
        value = {}
        category_dict = {i: value for i, value in enumerate(category_choices)}

        for i in range(1, (n + 1) % len(category_dict)):
            idx = random.randrange(i)
            value[idx] = category_dict[idx]
        return value
