from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from django.db.models import Q

from rest_framework import generics, mixins

from api.main.serializers import MainSchemaSerializer, UserMainSchemaSerializer
from api.contents.note.serializers import NoteSerializer
from api.contents.page.serializers import PageSerializer

from apps.contents.models import Note, Page, BookObject
from apps.users.models import User
from core.exceptions import UserNotFound
from core.views import TemplateMainView

from utils.swagger import swagger_response, swagger_parameter, main_response_example, user_main_response_example, \
    UserFailCaseCollection as user_fail_case


class MainView(TemplateMainView):
    queryset = Page.objects.all()
    serializer_class = PageSerializer

    def __init__(self):
        super(MainView, self).__init__()
        self.pagination_class.data_key = 'pages'

    @swagger_auto_schema(
        operation_id='main',
        operation_description='메인 화면에 나열할 데이터를 return합니다.',
        manual_parameters=[
            swagger_parameter('mode', openapi.IN_QUERY, '정렬기준 (조회수, 좋아요수, 댓글수)', openapi.TYPE_STRING,
                              pattern=['hit / likes / reviews']),
            swagger_parameter('sorting', openapi.IN_QUERY, '오름차순/내림차순', openapi.TYPE_STRING,
                              pattern=['ascending / descending']),
            swagger_parameter('limit', openapi.IN_QUERY, '한 번에 조회할 데이터의 수 (default=4, max=count)',
                              openapi.TYPE_INTEGER),
            swagger_parameter('offset', openapi.IN_QUERY, '조회할 데이터의 offset (default=0)', openapi.TYPE_INTEGER)
        ],
        responses={
            200: swagger_response(
                description='MAIN_200',
                schema=MainSchemaSerializer,
                examples=main_response_example
            )
        },
        security=[]
    )
    def get(self, request, *args, **kwargs):
        data = self.get_paginated_data(self.get_queryset())
        return self.get_paginated_response(data)


class UserMainView(TemplateMainView):
    queryset = Note.objects.all().select_related('user')
    serializer_class = NoteSerializer

    def __init__(self):
        super(UserMainView, self).__init__()
        self.pagination_class.data_key = 'notes'

    @swagger_auto_schema(
        operation_id='user_main',
        operation_description='사용자가 작성한 노트와 페이지 데이터를 return 합니다.',
        manual_parameters=[
            swagger_parameter('mode', openapi.IN_QUERY, '정렬기준 (조회수, 좋아요수, 댓글수)', openapi.TYPE_STRING,
                              pattern=['hit / likes / reviews']),
            swagger_parameter('sorting', openapi.IN_QUERY, '오름차순/내림차순', openapi.TYPE_STRING,
                              pattern=['ascending / descending']),
            swagger_parameter('limit', openapi.IN_QUERY, '한 번에 조회할 데이터의 수 (default=4, max=count)',
                              openapi.TYPE_INTEGER),
            swagger_parameter('offset', openapi.IN_QUERY, '조회할 데이터의 offset (default=0)', openapi.TYPE_INTEGER)
        ],
        responses={
            200: swagger_response(
                description='USER_MAIN_200',
                schema=UserMainSchemaSerializer,
                examples=user_main_response_example
            ),
            404: user_fail_case.USER_404_DOES_NOT_EXIST.as_md()
        }
    )
    def get(self, request, *args, **kwargs):
        user_id = self.kwargs[self.lookup_field]
        try:
            user = User.objects.get(id=user_id)
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
