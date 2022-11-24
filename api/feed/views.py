import json
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema, no_body

from django.db.models import F
from django.core.serializers.json import DjangoJSONEncoder

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from api.feed.serializers import MainSchemaSerializer, UserMainSchemaSerializer, MainNoteListSchemaSerializer
from api.contents.serializers import SimpleBookListSerializer, PageDetailSerializer
from apps.contents.models import Note, Page

from api.users.serializers import UserSerializer
from api.users.pagination import MainViewPagination
from api.users.exceptions import UserNotFound
from apps.users.models import User

from utils.swagger import (
    swagger_response,
    swagger_parameter,
    main_response_example,
    user_main_response_example,
    UserFailCaseCollection as user_fail_case,
    main_note_list_response_example
)


class MainFeedViewSet(viewsets.ModelViewSet):
    queryset = Page.objects.all().select_related('note', 'note__book')
    serializer_class = PageDetailSerializer
    authentication_classes = []
    pagination_class = MainViewPagination

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pagination_class.data_key = 'pages'

    def get_paginated_data(self, queryset):
        pagination = self.paginate_queryset(queryset)
        serializer = self.serializer_class(instance=pagination or queryset, many=True)
        return serializer.data

    def get_filtered_data(self, request, data):
        key = self.request.query_params.get('key')
        if key not in ['hit', 'like', 'pages']:
            return data
        if key in ['like', 'pages']:
            key += '_count'
        sorting = self.request.query_params.get('sorting')
        data.sort(key=lambda x: x[key], reverse=True) if sorting == 'descending' else data.sort(key=lambda x: x[key])
        return data

    @swagger_auto_schema(
        operation_id='main_feed',
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
    @action(detail=False, methods=["get"], url_path=r"main", name="feed_main")
    def feed_main(self, request, *args, **kwargs):
        data = self.get_paginated_data(self.get_queryset().order_by('-created_at'))
        return self.get_paginated_response(data)

    @swagger_auto_schema(
        operation_id='main_user',
        operation_description='사용자가 작성한 노트와 페이지 데이터를 return 합니다.',
        manual_parameters=[
            swagger_parameter('key', openapi.IN_QUERY, '정렬기준 (조회수, 좋아요수, 댓글수)', openapi.TYPE_STRING,
                              pattern=['hit, like, pages']),
            swagger_parameter('sorting', openapi.IN_QUERY, '오름차순/내림차순', openapi.TYPE_STRING,
                              pattern=['ascending, descending']),
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
    @action(
        detail=True, methods=["get"], url_path=r"all", name="user_main",
        queryset=Note.objects.all().exclude(page__isnull=True).select_related('user')
    )
    def user_main(self, request, *args, **kwargs):
        try:
            user = User.objects.get(id=self.kwargs[self.lookup_field])
        except Exception:
            raise UserNotFound()

        queryset = self.get_queryset().filter(user_id=user.id)
        serializer = self.serializer_class(instance=queryset, many=True)
        notes = self.get_filtered_data(self.request, serializer.data)

        response = {"notes": notes, "user": UserSerializer(instance=user).data}
        return Response(response, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id='main_note_list',
        operation_description='사용자가 필사한 책 정보(isbn, 등록일)를 조회합니다.',
        request_body=no_body,
        manual_parameters=[swagger_parameter('id', openapi.IN_PATH, '사용자 id', openapi.TYPE_INTEGER)],
        responses={
            200: swagger_response(
                description='MAIN_NOTE_LIST_200',
                schema=MainNoteListSchemaSerializer,
                examples=main_note_list_response_example
            )
        }
    )
    @action(
        detail=True, methods=["get"], url_path=r"notes", name="note_list_main",
        queryset=Note.objects.all().select_related('book__isbn'),
        serializer_class=SimpleBookListSerializer
    )
    def note_list_main(self, request, *args, **kwargs):
        try:
            user = User.objects.get(id=self.kwargs[self.lookup_field])
        except Exception:
            raise UserNotFound()

        queryset = self.get_queryset().filter(user=user)\
            .annotate(note_id=F('id'), isbn=F('book__isbn'), datetime=F('created_at'))\
            .values('note_id', 'isbn', 'datetime').order_by('-datetime')
        book_list = json.dumps(list(queryset), cls=DjangoJSONEncoder)
        return Response(json.loads(book_list), status=status.HTTP_200_OK)
