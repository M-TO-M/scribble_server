import json
from collections import OrderedDict

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema, no_body

from django.utils.translation import gettext_lazy as _
from django.utils.translation.trans_null import gettext_lazy

from rest_framework import generics, mixins, status
from rest_framework.exceptions import ValidationError, AuthenticationFailed
from rest_framework.response import Response

from api.contents.note.serializers import NoteCreateSerializer, NoteSerializer
from api.contents.page.serializers import PageSerializer, PageLikesRelationSerializer, PageSchemaSerializer
from apps.contents.models import Note, Page, PageLikesRelation
from core.exceptions import PageNotFound
from utils.swagger import swagger_response, swagger_schema_with_description, swagger_schema_with_properties, \
    page_response_example, PageFailCaseCollection as page_fail_case, UserFailCaseCollection as user_fail_case, \
    swagger_schema_with_items


class PageView(generics.GenericAPIView,
               mixins.RetrieveModelMixin,
               mixins.CreateModelMixin,
               mixins.UpdateModelMixin,
               mixins.DestroyModelMixin):
    queryset = Page.objects.all().select_related('note', 'note__user', 'note__book')
    serializer_class = PageSerializer

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
    def get(self, request, *args, **kwargs):
        try:
            page = self.get_object()
        except Exception:
            raise PageNotFound()

        if request.user and request.user.id != page.note.user.id:
            page.update_page_hit()
            page.save()

        note_data = NoteSerializer(instance=page.note).data
        book_data = note_data.pop('book')
        page_data = self.serializer_class(instance=page).data
        response = {
            "note": note_data,
            "book": book_data,
            "page_detail": page_data
        }

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
                page_fail_case.PAGE_400_NO_BOOK_ISBN_IN_REQUEST_BODY.as_md()
        }
    )
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except Exception:
            raise ValidationError(detail=_("no_data_in_req_body"))

        note_exists = data['note']
        if note_exists:
            if "note_pk" not in data:
                raise ValidationError(detail=_("no_note_pk_in_req_body"))
            note = Note.objects.get(id=data['note_pk'])
        else:
            if "book_isbn" not in data:
                raise ValidationError(detail=_("no_book_in_req_body"))

            note_data = {"user": request.user, "isbn": data["book_isbn"]}
            note_create_serializer = NoteCreateSerializer()
            note = note_create_serializer.create(validated_data=note_data)
        # todo: page의 note_index 갱신하면 생성
        page_data = data["pages"]
        for page in page_data:
            page.update({'note': note.id})

        page_serializer = self.serializer_class(data=page_data, many=True)
        page_serializer.is_valid(raise_exception=True)
        pages = page_serializer.create(page_serializer.validated_data)

        response = {
            "pages": self.serializer_class(instance=pages, many=True).data
        }
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
    def patch(self, request, *args, **kwargs):
        try:
            page = self.get_object()
        except Exception:
            raise PageNotFound()

        if request.user and request.user.id != page.note.user.id:
            raise AuthenticationFailed(detail=_("unauthorized_user"))

        data = json.loads(request.body)
        page_serializer = self.serializer_class(data=data)
        page_serializer.is_valid(raise_exception=True)
        update_page = page_serializer.update(instance=page, validated_data=data)

        note_data = NoteSerializer(instance=page.note).data
        book_data = note_data.pop('book')
        response = {
            "note": note_data,
            "book": book_data,
            "page": self.serializer_class(instance=update_page).data
        }

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
    def delete(self, request, *args, **kwargs):
        try:
            page = self.get_object()
        except Exception:
            raise PageNotFound()

        if request.user and request.user.id != page.note.user.id:
            raise AuthenticationFailed(detail=_("unauthorized_user"))

        self.perform_destroy(page)
        return Response(None, status=status.HTTP_204_NO_CONTENT)


class PageLikeView(generics.GenericAPIView, mixins.CreateModelMixin, mixins.DestroyModelMixin):
    queryset = Page.objects.all()
    serializer_class = PageLikesRelationSerializer

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
    def post(self, request, *args, **kwargs):
        try:
            page = self.get_object()
        except Page.DoesNotExist:
            raise PageNotFound()

        try:
            PageLikesRelation.objects.get(like_user=request.user, page=page)
            raise ValidationError(detail=gettext_lazy('exist_like'))
        except PageLikesRelation.DoesNotExist:
            pass

        data = {"like_user": request.user.pk, "page": page.pk}
        page_relation_serializer = self.serializer_class(data=data)
        page_relation_serializer.is_valid(raise_exception=True)
        page, _ = page_relation_serializer.create(page_relation_serializer.validated_data)

        response = {
            "page": PageSerializer(page).data
        }

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
    def delete(self, request, *args, **kwargs):
        try:
            page = self.get_object()
        except Page.DoesNotExist:
            raise PageNotFound()

        try:
            relation = PageLikesRelation.objects.get(like_user=request.user, page=page)
        except PageLikesRelation.DoesNotExist:
            raise ValidationError(detail=_('no_exist_like'))

        self.perform_destroy(relation)
        return Response(None, status=status.HTTP_204_NO_CONTENT)
