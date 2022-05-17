import json

from django.utils.translation import gettext_lazy as _
from django.utils.translation.trans_null import gettext_lazy

from rest_framework import generics, mixins, status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response

from api.contents.serializers import *
from apps.contents.models import Note, NoteLikesRelation, Page
from core.exceptions import NoteNotFound, PageNotFound


class BookView(generics.CreateAPIView):
    serializer_class = BookCreateSerializer

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        book_create_serializer = self.serializer_class()
        book = book_create_serializer.create(validated_data=data)

        response = {
            "book": BookObjectSerializer(instance=book).data
        }
        return Response(response, status=status.HTTP_201_CREATED)


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


class PageView(generics.GenericAPIView,
               mixins.RetrieveModelMixin,
               mixins.CreateModelMixin,
               mixins.UpdateModelMixin,
               mixins.DestroyModelMixin):

    queryset = Page.objects.all().select_related('note__user', 'note__book')
    serializer_class = PageSerializer

    def get(self, request, *args, **kwargs):
        try:
            page = self.get_object()
        except Exception:
            raise PageNotFound()

        if request.user and request.user.id != page.note.user.id:
            page.update_page_hit()
            page.save()

        page_data = self.serializer_class(instance=page).data
        response = {"page": page_data}

        return Response(response, status.HTTP_200_OK)

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

        page_data = data["pages"]
        for k, v in page_data.items():
            page_data[k]['note'] = note.id
        page_data_list = list(page_data.values())

        page_serializer = self.serializer_class(data=page_data_list, many=True)
        page_serializer.is_valid(raise_exception=True)
        pages = page_serializer.create(page_serializer.validated_data)

        response = {
            "pages": self.serializer_class(instance=pages, many=True).data
        }
        return Response(response, status.HTTP_201_CREATED)

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

        response = {
            "page": self.serializer_class(instance=update_page).data
        }
        return Response(response, status=status.HTTP_201_CREATED)

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
