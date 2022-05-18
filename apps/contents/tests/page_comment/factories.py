import factory
from factory import fuzzy

from apps.contents.models import PageComment
from apps.contents.tests.page.factories import PageFactory


class PageCommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PageComment

    page = factory.SubFactory(PageFactory)
    depth = fuzzy.FuzzyInteger(low=0)
    parent = fuzzy.FuzzyInteger(low=0)
    content = fuzzy.FuzzyText()
