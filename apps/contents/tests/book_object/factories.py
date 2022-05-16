import random
import factory
from faker import Faker
from faker.providers.isbn import Provider

from apps.users.models import category_choices
from apps.contents.models import BookObject


class BookObjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BookObject
        django_get_or_create = ['isbn']

    isbn = factory.LazyAttribute(lambda n: Provider(generator=Faker()).isbn13(separator=''))
    title = factory.Sequence(lambda n: f'title_{n}')
    author = factory.Sequence(lambda n: f'author_{n}')
    publisher = factory.Sequence(lambda n: f'publisher_{n}')
    thumbnail = Faker().image_url()

    @factory.lazy_attribute_sequence
    def category(self, n):
        value = {}
        category_dict = {i: value for i, value in enumerate(category_choices)}

        for i in range(1, (n + 1) % len(category_dict)):
            idx = random.randrange(i)
            value[idx] = category_dict[idx]
        return value
