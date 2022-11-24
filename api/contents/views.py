import json
from collections import OrderedDict

from django.db import transaction
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema, no_body

from django.utils.translation import gettext_lazy as _
from django.utils.translation.trans_null import gettext_lazy

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from django.db.models import Q


from api.contents.serializers import (
    BookCreateSerializer, DetailBookListSerializer,
    NoteSerializer, NoteSchemaSerializer, NoteCreateSerializer, NoteLikesRelationSerializer, PageSchemaSerializer,
    PageLikesRelationSerializer, PageAllSchemaSerializer, PageCommentSerializer, PageCommentSchemaSerializer,
    PageCommentCreateUpdateSerializer,
)
from api.contents.exceptions import NoteNotFound, PageNotFound
from api.contents.serializers import PageSerializer, PageDetailSerializer
from api.users.mixins import AuthorizingMixin
from apps.contents.models import BookObject, Note, NoteLikesRelation, Page, PageLikesRelation, PageComment
from utils.naver_api import NaverSearchAPI
from utils.swagger import (
    swagger_parameter,
    swagger_response,
    swagger_schema_with_properties,
    swagger_schema_with_description,
    swagger_schema_with_items,
    BookObjectFailCaseCollection as book_fail_case,
    NoteFailCaseCollection as note_fail_case,
    UserFailCaseCollection as user_fail_case,
    PageFailCaseCollection as page_fail_case,
    PageCommentFailCaseCollection as page_comment_fail_case,
    note_response_example,
    note_detail_response_example,
    page_response_example,
    page_all_response_example, page_comment_response_example,
)


class BookViewSet(viewsets.ModelViewSet):
    search_class = NaverSearchAPI()
    serializer_class = BookCreateSerializer
    queryset = BookObject.objects.all()
    authentication_classes = []

    @swagger_auto_schema(
        operation_id='book_new',
        operation_description='노트 생성을 위한 도서정보를 생성합니다.',
        request_body=swagger_schema_with_properties(
            openapi.TYPE_OBJECT,
            {
                'isbn': swagger_schema_with_description(openapi.TYPE_STRING, '도서 isbn 문자열'),
                'title': swagger_schema_with_description(openapi.TYPE_STRING, '제목'),
                'author': swagger_schema_with_description(openapi.TYPE_STRING, '작가'),
                'publisher': swagger_schema_with_description(openapi.TYPE_STRING, '출판사'),
                'thumbnail': swagger_schema_with_description(openapi.FORMAT_URI, '도서 이미지')
            }
        ),
        responses={
            201: swagger_response(
                description='BOOK_201_NEW',
                schema=serializer_class,
                examples={
                    "id": 1,
                    "isbn": "9788949114118",
                    "created_at": "2022-06-01T03:36:31.725317Z",
                    "updated_at": "2022-06-01T03:36:31.725358Z",
                    "title": "여름이 온다",
                    "author": "이수지",
                    "publisher": "비룡소",
                    "category": {},
                    "thumbnail": "https://bookthumb-phinf.pstatic.net/cover/208/162/20816223.jpg"
                }
            ),
            400:
                book_fail_case.BOOK_400_INVALID_ISBN_NOT_STRING.as_md() +
                book_fail_case.BOOK_400_INVALID_ISBN_WRONG_LENGTH.as_md() +
                book_fail_case.BOOK_400_INVALID_ISBN_FAILED_CHECKSUM.as_md() +
                book_fail_case.BOOK_400_INVALID_ISBN.as_md()
        },
        security=[]
    )
    @action(detail=False, methods=["post"])
    def new(self, request, *args, **kwargs):
        return self.create(request)

    @swagger_auto_schema(
        operation_id='navbar_book_search',
        operation_description='네브바에서 모든 도서에 대한 검색을 수행합니다.'
                              '필사된 노트가 많은 책 순으로 정렬한 결과를 리턴합니다.\n\n'
                              'parameter로는 검색어 또는 isbn 문자열 중 하나의 값만 전달할 수 있습니다.\n\n'
                              '두 개의 값을 모두 전달할 경우, 검색어가 우선 적용됩니다.',
        manual_parameters=[
            swagger_parameter('query', openapi.IN_QUERY, '검색어', openapi.TYPE_STRING, required=True),
            swagger_parameter('isbn', openapi.IN_QUERY, 'isbn 문자열', openapi.TYPE_STRING, required=True),
            swagger_parameter('display', openapi.IN_QUERY, '검색결과 수', openapi.TYPE_INTEGER),
        ],
        responses={}
    )
    @action(
        detail=False,
        methods=["get"],
        serializer_class=DetailBookListSerializer,
        url_path=r"search/navbar",
        name="navbar_book_search"
    )
    def navbar_book_search(self, request, *args, **kwargs):
        q = request.GET.get("query") or request.GET.get("isbn")
        display = request.GET.get("display")
        db_search_result = self.queryset.filter(
            Q(title__contains=q) |
            Q(author__contains=q) |
            Q(publisher__contains=q) |
            Q(isbn__exact=q)
        )
        api_search_type, api_search_result = self.search_class(q, display)
        results = self.serializer_class(instance=db_search_result, many=True).data
        db_search_isbn_keys = [re['isbn'] for re in results]
        for api_re in api_search_result:
            if api_re['isbn'] not in db_search_isbn_keys:
                results.append(api_re)
        if results is None:
            return Response(None, status=status.HTTP_204_NO_CONTENT)

        for result in results:
            p_count = Note.objects.filter(book__isbn=result['isbn']).exclude(page=None).values_list('page',
                                                                                                    flat=True).count()
            result.update({'count': p_count})
        results.sort(key=lambda x: x['count'], reverse=True)
        response = {"type": api_search_type, "results": results}
        return Response(response, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id='tagging_book_search',
        operation_description='페이지 생성시 등록할 도서에 대한 검색을 수행합니다.\n\n'
                              'parameter로는 검색어 또는 isbn 문자열 중 하나의 값만 전달할 수 있습니다.\n\n'
                              '두 개의 값을 모두 전달할 경우, 검색어가 우선 적용됩니다.',
        manual_parameters=[
            swagger_parameter('query', openapi.IN_QUERY, '검색어', openapi.TYPE_STRING, required=True),
            swagger_parameter('isbn', openapi.IN_QUERY, 'isbn 문자열', openapi.TYPE_STRING, required=True),
            swagger_parameter('display', openapi.IN_QUERY, '검색결과 수', openapi.TYPE_INTEGER),
        ],
        responses={
            200: swagger_response(
                description='BOOK_200_TAGGING_SEARCH',
                schema=serializer_class,
                examples={
                    "0": {
                        'isbn': '9788949114118',
                        'title': '여름이 온다',
                        'author': '이수지',
                        'publisher': '비룡소',
                        'thumbnail': 'https://bookthumb-phinf.pstatic.net/cover/208/162/20816223.jpg'
                    }
                }
            ),
            204: swagger_response(description='BOOK_204_TAGGING_SEARCH_NO_RESULT')
        },
        security=[]
    )
    @action(
        detail=False,
        methods=["get"],
        serializer_class=DetailBookListSerializer,
        url_path=r"search/tagging",
        name="tagging_book_search"
    )
    def tagging_book_search(self, request, *args, **kwargs):
        q = request.GET.get("query") or request.GET.get("isbn")
        display = request.GET.get("display")

        result = self.search_class(q, display)
        if result is None:
            return Response(None, status=status.HTTP_204_NO_CONTENT)
        return Response(result, status=status.HTTP_200_OK)


class NoteViewSet(viewsets.ModelViewSet, AuthorizingMixin):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer

    @swagger_auto_schema(
        operation_id='note_detail',
        operation_description='노트를 조회합니다',
        responses={
            200: swagger_response(
                description='NOTE_200_DETAIL',
                schema=NoteSchemaSerializer,
                examples=note_detail_response_example
            ),
            404: note_fail_case.NOTE_404_DOES_NOT_EXIST.as_md()
        }
    )
    @action(detail=True, methods=["get"], url_path=r"", name="note_detail")
    def note_detail(self, request, *args, **kwargs):
        try:
            note = self.get_object()
        except Exception:
            raise NoteNotFound()
        if request.user and request.user.id != note.user.id:
            note.update_note_hit()
        note = self.serializer_class(instance=note).data
        pages = self.serializer_class.get_note_pages(instance=note)
        note['pages'] = PageSerializer(instance=pages, many=True).data

        response = {"note": note}
        return Response(response, status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id='note_new',
        operation_description='새로운 노트를 생성합니다.',
        request_body=swagger_schema_with_properties(
            openapi.TYPE_OBJECT,
            {"book_isbn": swagger_schema_with_description(openapi.TYPE_STRING, "도서 isbn 문자열")}
        ),
        responses={
            201: swagger_response(
                'NOTE_201_NEW',
                schema=NoteSchemaSerializer,
                examples=note_response_example
            ),
            400: note_fail_case.NOTE_400_NO_BOOK_INFO_IN_REQUEST_BODY.as_md()
        }
    )
    @action(detail=False, methods=["post"], name="new")
    def new(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except Exception:
            raise ValidationError(detail=_("no_book_in_req_body"))

        if 'book_isbn' not in data:
            raise ValidationError(detail=_("no_book_in_req_body"))
        data = {"user": request.user, "isbn": data['book_isbn']}
        note_create_serializer = NoteCreateSerializer()
        note = note_create_serializer.create(validated_data=data)

        response = {"note": self.serializer_class(instance=note).data}
        return Response(response, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_id='note_delete',
        operation_description='노트를 삭제합니다.',
        responses={
            204: swagger_response('NOTE_204_DELETE'),
            401: user_fail_case.USER_401_UNAUTHORIZED.as_md(),
            404: note_fail_case.NOTE_404_DOES_NOT_EXIST.as_md()
        }
    )
    @action(detail=True, methods=["delete"], name="delete")
    def delete(self, request, *args, **kwargs):
        try:
            note = self.get_object()
        except Exception:
            raise NoteNotFound()
        self.authorize_request_user(request=request, user=note.user)
        self.perform_destroy(note)
        return Response(None, status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        operation_id='note_like',
        operation_description='노트에 좋아요를 등록합니다.',
        request_body=no_body,
        responses={
            201: swagger_response(
                'NOTE_201_LIKE',
                schema=NoteSchemaSerializer,
                examples=note_response_example
            ),
            400: note_fail_case.NOTE_400_LIKE_EXIST_LIKE_RELATION.as_md(),
            404: note_fail_case.NOTE_404_DOES_NOT_EXIST.as_md()
        }
    )
    @action(
        detail=True,
        methods=["post"],
        serializer_class=NoteLikesRelationSerializer,
        name="note_like",
        url_path=r"<int:pk>/like"
    )
    def note_like(self, request, *args, **kwargs):
        try:
            note = self.get_object()
        except Note.DoesNotExist:
            raise NoteNotFound()

        try:
            NoteLikesRelation.objects.get(like_user=request.user, note=note)
            raise ValidationError(detail=gettext_lazy('exist_like'))
        except NoteLikesRelation.DoesNotExist:
            pass

        data = {"like_user": request.user.pk, "note": note.pk}
        note_relation_serializer = self.serializer_class(data=data)
        note_relation_serializer.is_valid(raise_exception=True)
        note, _ = note_relation_serializer.create(note_relation_serializer.validated_data)

        response = {"note": NoteSerializer(note).data}
        return Response(response, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_id='note_like_cancel',
        operation_description='노트의 좋아요를 취소합니다.',
        responses={
            204: swagger_response(description='NOTE_204_LIKE_CANCEL'),
            400: note_fail_case.NOTE_400_LIKE_CANCEL_NO_EXIST_LIKE_RELATION.as_md(),
            404: note_fail_case.NOTE_404_DOES_NOT_EXIST.as_md()
        }
    )
    @action(
        detail=True,
        methods=["delete"],
        serializer_class=NoteLikesRelationSerializer,
        name="note_like_cancel",
        url_path=r"<int:pk>/like/cancel"
    )
    def note_like_cancel(self, request, *args, **kwargs):
        try:
            note = self.get_object()
        except Note.DoesNotExist:
            raise NoteNotFound()

        try:
            relation = NoteLikesRelation.objects.get(like_user=request.user, note=note)
        except NoteLikesRelation.DoesNotExist:
            raise ValidationError(detail=_('no_exist_like'))
        self.perform_destroy(relation)
        return Response(None, status=status.HTTP_204_NO_CONTENT)


class PageViewSet(viewsets.ModelViewSet, AuthorizingMixin):
    queryset = Page.objects.all().select_related('note__user', 'note__book').prefetch_related('page_comment')
    serializer_class = PageDetailSerializer

    def get_object(self):
        try:
            obj = super(self).get_object()
        except Page.DoesNotExist:
            raise PageNotFound()
        return obj

    @swagger_auto_schema(
        operation_id='page_detail',
        operation_description='페이지를 조회합니다.',
        responses={
            200: swagger_response(
                description='PAGE_200_DETAIL',
                schema=PageSchemaSerializer,
                examples=page_response_example
            ),
            404: page_fail_case.PAGE_404_DOES_NOT_EXIST.as_md()
        }
    )
    @action(detail=True, methods=["get"], url_path=r"", name="detail")
    def detail(self, request, *args, **kwargs):
        page = self.get_object()
        if request.user and request.user.id != page.note.user.id:
            page.update_page_hit()
        response = self.serializer_class(instance=page).data
        return Response(response, status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id='page_new',
        operation_description='새로운 페이지를 등록합니다.',
        request_body=swagger_schema_with_properties(
            openapi.TYPE_OBJECT,
            {
                'note': swagger_schema_with_description(openapi.TYPE_BOOLEAN, '노트 등록여부'),
                'note_pk': swagger_schema_with_description(openapi.TYPE_INTEGER, '"note=True"인 경우 노트 객체의 id값'),
                'book_isbn': swagger_schema_with_description(openapi.TYPE_STRING, '"note=False"인 경우 전달해야 하는 도서 isbn값'),
                'pages': swagger_schema_with_items(
                    openapi.TYPE_ARRAY,
                    openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties=OrderedDict((
                            ('phrase', swagger_schema_with_description(openapi.TYPE_STRING, '필사 구절 text')),
                            ('transcript', swagger_schema_with_description(openapi.TYPE_STRING, '필사 이미지 url')),
                            ('book_page', swagger_schema_with_description(openapi.TYPE_INTEGER, '필사하려는 도서의 페이지 번호')),
                        )),
                    ),
                    description='등록할 페이지 정보 dict의 list'
                )
            }
        ),
        responses={
            201: swagger_response(
                description='PAGE_201_NEW',
                schema=PageSchemaSerializer,
                examples=page_response_example
            ),
            400:
                page_fail_case.PAGE_400_NO_NOTE_PK_IN_REQUEST_BODY.as_md() +
                page_fail_case.PAGE_400_NO_BOOK_ISBN_IN_REQUEST_BODY.as_md() +
                note_fail_case.NOTE_404_DOES_NOT_EXIST.as_md()
        }
    )
    @action(detail=False, methods=["post"], name="new", serializer_class=PageSerializer)
    def new(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except Exception:
            raise ValidationError(detail=_("no_data_in_req_body"))

        with transaction.atomic():
            note_exists = data["note"]
            if note_exists:
                try:
                    note_id = data["note_pk"]
                    note = Note.objects.get(id=note_id)
                except KeyError:
                    raise ValidationError(detail=_("no_note_pk"))
                except Note.DoesNotExist:
                    raise NoteNotFound()
            else:
                note_data = {"user": request.user, "isbn": data.get("book_isbn")}
                note_create_serializer = NoteCreateSerializer()
                note = note_create_serializer.create(validated_data=note_data)

            serializer = self.get_serializer(data=data["pages"], many=True, context={'note': note})
            serializer.is_valid(raise_exception=True)
            pages = serializer.create(serializer.validated_data)
            response = {"pages": self.serializer_class(instance=pages, many=True).data}
            return Response(response, status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_id='page_edit',
        operation_description='페이지를 수정합니다.',
        responses={
            201: swagger_response(
                description='PAGE_201_EDIT',
                schema=PageSchemaSerializer,
                examples=page_response_example
            ),
            400: page_fail_case.PAGE_400_EDIT_VALIDATION_ERROR.as_md(),
            401: user_fail_case.USER_401_UNAUTHORIZED.as_md(),
            404: page_fail_case.PAGE_404_DOES_NOT_EXIST.as_md()
        }
    )
    @action(detail=True, methods=["patch"], name="edit")
    def edit(self, request, *args, **kwargs):
        page = self.get_object()
        self.authorize_request_user(request=request, user=page.note.user)
        data = json.loads(request.body)
        page_serializer = self.serializer_class(data=data)
        page_serializer.is_valid(raise_exception=True)
        update_page = page_serializer.update(instance=page, validated_data=data)

        response = self.serializer_class(instance=update_page).data
        return Response(response, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_id='page_delete',
        operation_description='페이지를 삭제합니다.',
        responses={
            204: swagger_response(description='PAGE_204_DELETE'),
            401: user_fail_case.USER_401_UNAUTHORIZED.as_md(),
            404: page_fail_case.PAGE_404_DOES_NOT_EXIST.as_md()
        }
    )
    @action(detail=True, methods=["delete"], name="delete")
    def delete(self, request, *args, **kwargs):
        page = self.get_object()
        self.authorize_request_user(request=request, user=page.note.user)
        self.perform_destroy(page)
        return Response(None, status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        operation_id='page_like',
        operation_description='페이지에 좋아요를 표시합니다.',
        request_body=no_body,
        responses={
            201: swagger_response(
                'PAGE_201_LIKE',
                schema=PageSchemaSerializer,
                examples=page_response_example
            ),
            400: page_fail_case.PAGE_400_LIKE_EXIST_LIKE_RELATION.as_md(),
            404: page_fail_case.PAGE_404_DOES_NOT_EXIST.as_md()
        }
    )
    @action(
        detail=True,
        methods=["post"],
        name="like",
        serializer_class=PageLikesRelationSerializer
    )
    def like(self, request, *args, **kwargs):
        page = self.get_object()
        try:
            PageLikesRelation.objects.get(like_user=request.user, page=page)
            raise ValidationError(detail=gettext_lazy('exist_like'))
        except PageLikesRelation.DoesNotExist:
            pass

        data = {"like_user": request.user.pk, "page": page.pk}
        page_relation_serializer = self.serializer_class(data=data)
        page_relation_serializer.is_valid(raise_exception=True)
        page, _ = page_relation_serializer.create(page_relation_serializer.validated_data)

        response = {"page": PageSerializer(page).data}
        return Response(response, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_id='page_like_cancel',
        operation_description='페이지에 표시한 좋아요를 취소합니다.',
        responses={
            204: swagger_response(description='PAGE_204_LIKE_CANCEL'),
            400: page_fail_case.PAGE_400_LIKE_CANCEL_NO_EXIST_LIKE_RELATION.as_md(),
            404: page_fail_case.PAGE_404_DOES_NOT_EXIST.as_md()
        }
    )
    @action(
        detail=True,
        methods=["delete"],
        url_path=r"like/cancel",
        name="like_cancel",
        serializer_class=PageLikesRelationSerializer
    )
    def like_cancel(self, request, *args, **kwargs):
        page = self.get_object()
        try:
            relation = PageLikesRelation.objects.get(like_user=request.user, page=page)
        except PageLikesRelation.DoesNotExist:
            raise ValidationError(detail=_('no_exist_like'))

        self.perform_destroy(relation)
        return Response(None, status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        operation_id='page_all',
        operation_description='도서에 대하여 등록되어 있는 모든 페이지를 조회합니다.',
        responses={
            200: swagger_response(
                description='PAGE_ALL_200',
                schema=PageAllSchemaSerializer,
                examples=page_all_response_example
            ),
            204: swagger_response(description='PAGE_ALL_204')
        }
    )
    @action(
        detail=False,
        methods=["get"],
        url_path=r"all/<int:isbn>", name="all",
        serializer_class=PageSerializer,
        lookup_field="isbn"
    )
    def all(self, request, *args, **kwargs):
        try:
            book = BookObject.objects.get(isbn=self.kwargs[self.lookup_field])
        except BookObject.DoesNotExist:
            raise ValidationError(detail=_('no_exist_book'))

        pages = self.queryset.filter(note__book=book)
        if pages.count() == 0:
            return Response(None, status=status.HTTP_204_NO_CONTENT)
        response = {
            "book": DetailBookListSerializer(instance=book).data,
            "page_count": pages.count(),
            "pages": self.serializer_class(instance=pages, many=True).data
        }
        return Response(response, status=status.HTTP_200_OK)


class PageCommentViewSet(viewsets.ModelViewSet, AuthorizingMixin):
    queryset = PageComment.objects.all().select_related('page__note__user')
    serializer_class = PageCommentSerializer

    def get_object(self):
        try:
            obj = super(self).get_object()
        except Page.DoesNotExist:
            raise PageNotFound()
        return obj

    @swagger_auto_schema(
        operation_id='page_comment_detail',
        operation_description='페이지 코멘트를 조회합니다.',
        responses={
            200: swagger_response(
                description='PAGE_COMMENT_200_DETAIL',
                schema=PageCommentSchemaSerializer,
                examples=page_comment_response_example
            ),
            404: page_comment_fail_case.PAGE_COMMENT_404_DOES_NOT_EXIST.as_md()
        }
    )
    @action(detail=True, methods=["get"], url_path=r"", name="detail")
    def detail(self, request, *args, **kwargs):
        page_comment = self.get_object()
        page_comment_data = self.serializer_class(instance=page_comment).data
        response = {"page_comment": page_comment_data}
        return Response(response, status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id='page_comment_new',
        operation_description='페이지 코멘트를 등록합니다.',
        request_body=swagger_schema_with_properties(
            openapi.TYPE_OBJECT,
            {
                'page': swagger_schema_with_description(openapi.TYPE_INTEGER, '페이지 id'),
                'parent': swagger_schema_with_description(openapi.TYPE_INTEGER, '상위 댓글 id (default=0)'),
                'content': swagger_schema_with_description(openapi.TYPE_STRING, '댓글 내용'),
            }
        ),
        responses={
            201: swagger_response(
                description='PAGE_COMMENT_201_NEW',
                schema=PageCommentSchemaSerializer,
                examples=page_comment_response_example
            ),
            400:
                page_comment_fail_case.PAGE_COMMENT_400_NO_PAGE_PK_IN_REQUEST_BODY.as_md() +
                page_comment_fail_case.PAGE_COMMENT_400_INVALID_PARENT_COMMENT.as_md(),
            404:
                page_comment_fail_case.PAGE_COMMENT_404_DOES_NOT_EXIST.as_md() +
                page_comment_fail_case.PAGE_COMMENT_404_PARENT_COMMENT_DOES_NOT_EXIST.as_md()
        }
    )
    @action(detail=False, methods=["post"], name="new", serializer_class=PageCommentCreateUpdateSerializer)
    def new(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            if not data.get("page", None):
                raise ValidationError(detail=_("no_page_pk_in_body"))
        except Exception:
            raise ValidationError(detail=_("no_data_in_req_body"))

        page_comment_data = {
            "comment_user": self.request.user,
            "page": data["page"],
            "parent": data.pop('parent', 0),
            "content": data["content"]
        }
        serializer = self.get_serializer()
        page_comment = serializer.create(validated_data=page_comment_data)
        response = {"page_comment": self.serializer_class(instance=page_comment).data}
        return Response(response, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_id='page_comment_edit',
        operation_description='페이지 코멘트를 수정합니다.',
        responses={
            201: swagger_response(
                description='PAGE_COMMENT_201_EDIT',
                schema=PageCommentSchemaSerializer,
                examples=page_comment_response_example
            ),
            400: page_comment_fail_case.PAGE_COMMENT_400_EDIT_VALIDATION_ERROR.as_md(),
            401: user_fail_case.USER_401_UNAUTHORIZED.as_md(),
            404: page_comment_fail_case.PAGE_COMMENT_404_DOES_NOT_EXIST.as_md()
        }
    )
    @action(detail=True, methods=["patch"], name="edit")
    def edit(self, request, *args, **kwargs):
        page_comment = self.get_object()
        self.authorize_request_user(request=request, user=page_comment.comment_user)
        data = json.loads(request.body)
        page_comment_serializer = self.serializer_class(data=data)
        page_comment_serializer.is_valid(raise_exception=True)
        update_page_comment = page_comment_serializer.update(instance=page_comment, validated_data=data)

        response = {
            "page_comment": self.serializer_class(instance=update_page_comment).data
        }
        return Response(response, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_id='page_comment_delete',
        operation_description='페이지 코멘트를 삭제합니다.',
        responses={
            204: swagger_response(description='PAGE_COMMENT_204_DELETE'),
            401: user_fail_case.USER_401_UNAUTHORIZED.as_md(),
            404: page_comment_fail_case.PAGE_COMMENT_404_DOES_NOT_EXIST.as_md()
        }
    )
    @action(detail=True, methods=["delete"], name="delete")
    def delete(self, request, *args, **kwargs):
        page_comment = self.get_object()
        self.authorize_request_user(request=request, user=page_comment.comment_user)
        self.perform_destroy(page_comment)
        return Response(None, status=status.HTTP_204_NO_CONTENT)
