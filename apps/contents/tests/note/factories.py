import factory
from factory import fuzzy

from apps.contents.models import Note, NoteLikesRelation
from apps.contents.tests.book_object.factories import BookObjectFactory
from apps.users.tests.user.factories import UserFactory


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
