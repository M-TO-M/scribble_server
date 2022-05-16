from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.contents.models import BookObject, Note, NoteLikesRelation
from api.users.serializers import UserSerializer
from core.validators import ISBNValidator
from utils.naver_api import NaverSearchAPI


class BookObjectSerializer(serializers.ModelSerializer):
    isbn = serializers.CharField(
        error_messages={'unique': _('exist_book')},
        validators=[ISBNValidator]
    )

    class Meta:
        model = BookObject
        fields = '__all__'

    @staticmethod
    def get_or_create_book_by_given_isbn(isbn):
        try:
            ISBNValidator(isbn)
        except ValidationError:
            raise ValidationError(detail=_("invalid_isbn"))

        try:
            book = BookObject.objects.get(isbn__exact=isbn)
        except BookObject.DoesNotExist:
            data = NaverSearchAPI()(isbn)
            book_serializer = BookObjectSerializer(data=data[0])
            book_serializer.is_valid(raise_exception=True)
            book = book_serializer.create(validated_data=book_serializer.validated_data)

        return book

    def validate_isbn(self, value):
        try:
            self.Meta.model.objects.get(isbn__exact=value)
            raise ValidationError(detail=_("exist_book"))
        except self.Meta.model.DoesNotExist:
            return value

    def create(self, validated_data):
        book = BookObject.objects.create(**validated_data)
        return book


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = '__all__'

    # TODO: like 구체화
    def to_representation(self, instance):
        return {
            'id': instance.id,
            'note_author': UserSerializer(instance=instance.user).data,
            'book': BookObjectSerializer(instance=instance.book).data,
            'likes': instance.note_likes_relation.count(),
            'hit': instance.hit
        }

    def create(self, validated_data):
        note = Note.objects.create(**validated_data)
        return note


class NoteLikesRelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoteLikesRelation
        fields = '__all__'

    def create(self, validated_data):
        note_relation = NoteLikesRelation.objects.create(**validated_data)
        return note_relation.note, note_relation
