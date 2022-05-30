from django.db.models import Q

from rest_framework import generics, mixins

from api.contents.note.serializers import NoteSerializer
from api.contents.page.serializers import PageSerializer

from apps.contents.models import Note, Page, BookObject
from core.exceptions import UserNotFound
from core.views import TemplateMainView


class MainView(TemplateMainView):
    queryset = Page.objects.all()
    serializer_class = PageSerializer

    def __init__(self):
        super(MainView, self).__init__()
        self.pagination_class.data_key = 'pages'

    def get(self, request, *args, **kwargs):
        data = self.get_paginated_data(self.get_queryset())
        return self.get_paginated_response(data)


class UserMainView(TemplateMainView):
    queryset = Note.objects.all().select_related('user')
    serializer_class = NoteSerializer

    def __init__(self):
        super(UserMainView, self).__init__()
        self.pagination_class.data_key = 'notes'

    def get(self, request, *args, **kwargs):
        try:
            user = self.get_object()
        except Exception:
            raise UserNotFound()

        notes = self.get_queryset().filter(user_id=user.id)
        data = self.get_paginated_data(notes)
        return self.get_paginated_response(data)


class SearchView(generics.GenericAPIView, mixins.RetrieveModelMixin):
    def get(self, request, *args, **kwargs):
        params = self.request.query_params.get('q')
        from_book = BookObject.objects.filter(
            Q(title__icontains=params) &
            Q(author__icontains=params) &
            Q(publisher__icontains=params)
        )

        return None
