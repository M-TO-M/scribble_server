from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from django.utils.translation import gettext_lazy as _

from api.contents.book_object.serializers import BookObjectSerializer, BookCreateSerializer
from api.users.serializers import UserSerializer
from apps.contents.models import Note, BookObject, NoteLikesRelation, Page
from core.serializers import StringListField
from core.validators import ISBNValidator


class NoteSchemaSerializer(serializers.Serializer):
    id = serializers.IntegerField(help_text='노트 id', read_only=True)
    note_author = UserSerializer(help_text='작성자', read_only=True)
    book = BookObjectSerializer(help_text='도서명', read_only=True)
    like_count = serializers.IntegerField(help_text='좋아요 수', read_only=True)
    like_user = StringListField(help_text='좋아요를 누른 사용자 list', read_only=True)
    hit = serializers.IntegerField(help_text='조회수', read_only=True)
    pages_count = serializers.IntegerField(help_text='노트에 저장된 페이지 수', read_only=True)


class NoteSerializer(serializers.ModelSerializer):
    like_user = serializers.SerializerMethodField()

    class Meta:
        model = Note
        fields = '__all__'

    @staticmethod
    def get_like_user(instance):
        like_user = []
        relation = instance.note_likes_relation.all()
        for r in relation:
            like_user.append(UserSerializer(instance=r.like_user).data)
        return like_user

    @staticmethod
    def get_note_pages(instance: Note):
        pages = Page.objects.filter(note_id=instance.id)
        return pages

    def to_representation(self, instance: Note):
        return {
            'id': instance.id,
            'note_author': UserSerializer(instance=instance.user).data,
            'book': BookObjectSerializer(instance=instance.book).data,
            'like_count': instance.note_likes_relation.count(),
            'like_user': self.get_like_user(instance),
            'hit': instance.hit,
            'pages_count': self.get_note_pages(instance).count()
        }


class NoteCreateSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    isbn = serializers.SerializerMethodField()
    book = serializers.SerializerMethodField()

    class Meta:
        model = Note
        fields = ['user']

    def get_isbn(self, value):
        try:
            ISBNValidator(value)
        except ValidationError:
            raise ValidationError(detail=_("invalid_isbn"))

        self.isbn = value
        return self.isbn

    def get_book(self) -> BookObject:
        data = {"isbn": self.isbn}

        book_create_serializer = BookCreateSerializer()
        self.book = book_create_serializer.create(validated_data=data)

        return self.book

    def create(self, validated_data):
        user = validated_data.pop('user')
        self.get_isbn(validated_data.pop('isbn'))
        self.get_book()

        return Note.objects.create(user=user, book=self.book)


class NoteLikesRelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoteLikesRelation
        fields = '__all__'

    def create(self, validated_data):
        note_relation = NoteLikesRelation.objects.create(**validated_data)
        return note_relation.note, note_relation
