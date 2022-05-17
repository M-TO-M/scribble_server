import factory
from factory import fuzzy
from faker import Faker

from apps.contents.models import Page
from apps.contents.tests.note.factories import NoteFactory


class PageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Page

    note = factory.SubFactory(NoteFactory)
    note_index = fuzzy.FuzzyInteger(low=0)
    transcript = Faker().image_url()
    phrase = fuzzy.FuzzyText()
    hit = fuzzy.FuzzyInteger(low=0)
