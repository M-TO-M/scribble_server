from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.contents.models import BookObject, Note, NoteLikesRelation, Page, PageLikesRelation, PageComment
from api.users.serializers import UserSerializer
from core.exceptions import PageNotFound
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

    def to_representation(self, instance: Note):
        return {
            'id': instance.id,
            'note_author': UserSerializer(instance=instance.user).data,
            'book': BookObjectSerializer(instance=instance.book).data,
            'like_count': instance.note_likes_relation.count(),
            'like_user': self.get_like_user(instance),
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
    like_user = serializers.SerializerMethodField()

    class Meta:
        model = Page
        fields = '__all__'
        list_serializer_class = PageBulkCreateUpdateSerializer

    @staticmethod
    def get_like_user(instance):
        like_user = []
        relation = instance.page_likes_relation.all()
        for r in relation:
            like_user.append(UserSerializer(instance=r.like_user).data)
        return like_user

    def to_representation(self, instance: Page):
        return {
            'id': instance.id,
            'note_id': instance.note.id,
            'note_index': instance.note_index,
            'transcript': instance.transcript,
            'phrase': instance.phrase,
            'hit': instance.hit,
            'like_count': instance.page_likes_relation.count(),
            'like_user': self.get_like_user(instance),
            'reviews_count': instance.page_comment.count()
        }


class PageLikesRelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageLikesRelation
        fields = '__all__'

    def create(self, validated_data):
        page_relation = PageLikesRelation.objects.create(**validated_data)
        return page_relation.page, page_relation


class PageCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageComment
        fields = '__all__'

    def to_representation(self, instance: PageComment):
        parent = instance.parent
        if parent == 0:
            rep_parent = parent
        else:
            parent_comment_instance = PageComment.objects.get(id=instance.parent)
            rep_parent = PageCommentSerializer(instance=parent_comment_instance).data
        return {
            'id': instance.id,
            'comment_user': instance.comment_user.id,
            'depth': instance.depth,
            'parent': rep_parent,
            'content': instance.content,
            'page_id': instance.page.id
        }


class PageCommentCreateUpdateSerializer(serializers.ModelSerializer):
    comment_user = UserSerializer()
    page = serializers.SerializerMethodField()
    parent = serializers.SerializerMethodField()
    depth = serializers.IntegerField(default=0)
    content = serializers.CharField()

    class Meta:
        model = PageComment
        fields = '__all__'

    def get_page(self, page_id):
        try:
            page = Page.objects.get(id=page_id)
        except Page.DoesNotExist:
            raise PageNotFound()

        self.page = page
        return self.page

    def get_parent(self, value):
        if value == 0:
            self.parent, self.depth = 0, 0
        else:
            try:
                parent_comment = PageComment.objects.get(id=value)
            except PageComment.DoesNotExist:
                raise ValidationError(detail=_("no_exist_parent_comment"))
            else:
                if parent_comment.page.id != self.page.id:
                    raise ValidationError(detail=_("invalid_parent_comment_pk"))
                self.parent, self.depth = parent_comment.id, parent_comment.depth + 1

        return self.parent

    def create(self, validated_data):
        comment_user = validated_data.pop('comment_user')
        page_id = validated_data.pop('page')
        parent_comment_id = validated_data.pop('parent')

        self.get_page(page_id)
        self.get_parent(parent_comment_id)

        data = {
            "comment_user": comment_user,
            "page": self.page,
            "depth": self.depth,
            "parent": self.parent,
            "content": validated_data.pop('content')
        }

        page_comment = PageComment.objects.create(**data)
        return page_comment

    def update(self, instance, validated_data):
        instance.content = validated_data.pop('content', instance.content)
        instance.save()

        return instance
