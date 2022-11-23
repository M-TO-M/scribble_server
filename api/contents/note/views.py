import json

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema, no_body

from django.utils.translation import gettext_lazy as _
from django.utils.translation.trans_null import gettext_lazy

from rest_framework import generics, mixins, status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response

from api.contents.note.serializers import *
from api.contents.page.serializers import PageSerializer
from apps.contents.models import Note, NoteLikesRelation
from api.contents.exceptions import NoteNotFound
from utils.swagger import swagger_response, note_response_example, \
    swagger_schema_with_properties, swagger_schema_with_description, \
    NoteFailCaseCollection as note_fail_case, UserFailCaseCollection as user_fail_case, note_detail_response_example


class NoteView(generics.GenericAPIView, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin):
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
    def get(self, request, *args, **kwargs):
        try:
            note = self.get_object()
        except Exception:
            raise NoteNotFound()

        if request.user and request.user.id != note.user.id:
            note.update_note_hit()
            note.save()

        note_data = self.serializer_class(instance=note).data

        pages = self.serializer_class.get_note_pages(instance=note)
        pages_data = PageSerializer(instance=pages, many=True).data

        note_data['pages'] = pages_data
        response = {"note": note_data}

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
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except Exception:
            raise ValidationError(detail=_("no_book_in_req_body"))
        else:
            if 'book_isbn' not in data:
                raise ValidationError(detail=_("no_book_in_req_body"))

            data = {"user": request.user, "isbn": data['book_isbn']}
            note_create_serializer = NoteCreateSerializer()
            note = note_create_serializer.create(validated_data=data)

            response = {
                "note": self.serializer_class(instance=note).data
            }
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
    def delete(self, request, *args, **kwargs):
        try:
            note = self.get_object()
        except Exception:
            raise NoteNotFound()

        if request.user and note.user.id != request.user.id:
            raise AuthenticationFailed(detail=_("unauthorized_user"))

        self.perform_destroy(note)
        return Response(None, status=status.HTTP_204_NO_CONTENT)


class NoteLikeView(generics.GenericAPIView, mixins.CreateModelMixin, mixins.DestroyModelMixin):
    queryset = Note.objects.all()
    serializer_class = NoteLikesRelationSerializer

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
    def post(self, request, *args, **kwargs):
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

        response = {
            "note": NoteSerializer(note).data
        }

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
    def delete(self, request, *args, **kwargs):
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