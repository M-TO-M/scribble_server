import json

from django.utils.translation import gettext_lazy as _
from django.utils.translation.trans_null import gettext_lazy

from rest_framework import generics, mixins, status
from rest_framework.exceptions import ValidationError, AuthenticationFailed
from rest_framework.response import Response

from api.contents.note.serializers import NoteSerializer, NoteCreateSerializer, NoteLikesRelationSerializer
from apps.contents.models import Note, NoteLikesRelation
from core.exceptions import NoteNotFound


class NoteView(generics.GenericAPIView, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer

    def get(self, request, *args, **kwargs):
        try:
            note = self.get_object()
        except Exception:
            raise NoteNotFound()

        if request.user and request.user.id != note.user.id:
            note.update_note_hit()
            note.save()

        note_data = self.serializer_class(instance=note).data
        response = {"note": note_data}
        return Response(response, status.HTTP_200_OK)

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