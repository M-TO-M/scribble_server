from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.contents.models import BookObject, Note, NoteLikesRelation, Page, PageLikesRelation
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

    def validate_isbn(self, value):
        try:
            self.Meta.model.objects.get(isbn__exact=value)
            raise ValidationError(detail=_("exist_book"))
        except self.Meta.model.DoesNotExist:
            return value


class BookCreateSerializer(serializers.ModelSerializer):
    isbn = serializers.SerializerMethodField()

    class Meta:
        model = BookObject
        fields = ['title', 'author', 'publisher', 'category', 'thumbnail']

    def get_isbn(self, value):
        try:
            ISBNValidator(value)
        except ValidationError:
            raise ValidationError(detail=_("invalid_isbn"))

        self.isbn = value
        return self.isbn

    def create(self, validated_data):
        self.get_isbn(validated_data.pop('isbn'))

        try:
            book = BookObject.objects.get(isbn__exact=self.isbn)
        except BookObject.DoesNotExist:
            book_object_data = NaverSearchAPI()(self.isbn)[0]
            book = BookObject.objects.create(**book_object_data)
        return book


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = '__all__'

    # TODO: like 구체화, isinstance로 구체화
    def to_representation(self, instance: Note):
        return {
            'id': instance.id,
            'note_author': UserSerializer(instance=instance.user).data,
            'book': BookObjectSerializer(instance=instance.book).data,
            'likes_count': instance.note_likes_relation.count(),
            'hit': instance.hit,
            'pages': PageSerializer(instance=instance.page.all(), many=True).data
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


class PageBulkCreateUpdateSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        page_data = [Page(**item) for item in validated_data]
        return Page.objects.bulk_create(page_data)

    def update(self, instance, validated_data):
        instance.transcript = validated_data.pop('transcript', instance.transcript)
        instance.phrase = validated_data.pop('phrase', instance.phrase)
        instance.note_index = validated_data.pop('category', instance.note_index)
        instance.save()

        return instance


class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = '__all__'
        list_serializer_class = PageBulkCreateUpdateSerializer

    def to_representation(self, instance: Page):
        return {
            'id': instance.id,
            'note_index': instance.note_index,
            'transcript': instance.transcript,
            'phrase': instance.phrase,
            'hit': instance.hit,
            'note_id': instance.note.id
        }


class PageLikesRelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageLikesRelation
        fields = '__all__'

    def create(self, validated_data):
        page_relation = PageLikesRelation.objects.create(**validated_data)
        return page_relation.page, page_relation
