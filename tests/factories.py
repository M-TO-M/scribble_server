import random
import factory
from factory import fuzzy
from faker import Faker

from django.utils import timezone
from django.contrib.auth.hashers import make_password
from faker.providers.isbn import Provider

from apps.users.models import User, category_choices, domain_allowlist
from apps.contents.models import BookObject, Note, NoteLikesRelation, Page, PageComment


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ['nickname', 'email']

    nickname = fuzzy.FuzzyText(length=10)
    password = make_password('password')
    profile_image = Faker().image_url()
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


class NoteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Note

    user = factory.SubFactory(UserFactory)
    book = factory.SubFactory(BookObjectFactory)
    hit = fuzzy.FuzzyInteger(low=0)


class NoteLikesRelationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NoteLikesRelation

    like_user = factory.SubFactory(UserFactory)
    note = factory.SubFactory(NoteFactory)


class PageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Page

    note = factory.SubFactory(NoteFactory)
    note_index = fuzzy.FuzzyInteger(low=0)
    transcript = Faker().image_url()
    phrase = fuzzy.FuzzyText()
    hit = fuzzy.FuzzyInteger(low=0)


class PageCommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PageComment
    comment_user = factory.SubFactory(UserFactory)
    page = factory.SubFactory(PageFactory)
    depth = fuzzy.FuzzyInteger(low=0)
    parent = fuzzy.FuzzyInteger(low=0)
    content = fuzzy.FuzzyText()
