import json
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema, no_body

from django.db.models import Q, F
from django.core.serializers.json import DjangoJSONEncoder

from rest_framework import generics, mixins, status
from rest_framework.response import Response

from api.contents.book_object.serializers import SimpleBookListSerializer
from api.main.serializers import MainSchemaSerializer, UserMainSchemaSerializer, MainBookListSchemaSerializer
from api.contents.note.serializers import NoteSerializer
from api.contents.page.serializers import PageSerializer, PageDetailSerializer
from api.users.serializers import UserSerializer

from apps.contents.models import Note, Page, BookObject
from apps.users.models import User
from core.exceptions import UserNotFound
from core.views import TemplateMainView

from utils.swagger import swagger_response, swagger_parameter, main_response_example, user_main_response_example, \
    UserFailCaseCollection as user_fail_case, main_book_list_response_example


class MainView(TemplateMainView):
    queryset = Page.objects.all().select_related('note', 'note__book')
    serializer_class = PageDetailSerializer

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
        data = self.get_paginated_data(self.get_queryset().order_by('-created_at'))
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

        return self.paginator.get_paginated_response(data=data, user=UserSerializer(instance=user).data)


class SearchView(generics.GenericAPIView, mixins.RetrieveModelMixin):
    def get(self, request, *args, **kwargs):
        params = self.request.query_params.get('q')
        from_book = BookObject.objects.filter(
            Q(title__icontains=params) &
            Q(author__icontains=params) &
            Q(publisher__icontains=params)
        )

        return None


class BookListView(generics.RetrieveAPIView):
    queryset = Note.objects.all().select_related('book__isbn')
    serializer_class = SimpleBookListSerializer

    @swagger_auto_schema(
        operation_id='main_book_list',
        operation_description='사용자가 등록한 책 정보(isbn, 등록일)를 조회합니다.',
        request_body=no_body,
        manual_parameters=[swagger_parameter('id', openapi.IN_PATH, '사용자 id', openapi.TYPE_INTEGER)],
        responses={
            200: swagger_response(
                description='MAIN_BOOK_LIST_200',
                schema=MainBookListSchemaSerializer,
                examples=main_book_list_response_example
            )
        }
    )
    def get(self, request, *args, **kwargs):
        user_id = self.kwargs[self.lookup_field]
        try:
            user = User.objects.get(id=user_id)
        except Exception:
            raise UserNotFound()

        queryset = self.get_queryset().filter(user=user)\
            .annotate(note_id=F('id'), isbn=F('book__isbn'), datetime=F('created_at'))\
            .values('note_id', 'isbn', 'datetime').order_by('-datetime')
        book_list = json.dumps(list(queryset), cls=DjangoJSONEncoder)

        return Response(json.loads(book_list), status=status.HTTP_200_OK)
