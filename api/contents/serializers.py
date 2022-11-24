from collections import OrderedDict

from django.db import transaction
from django.db.models import Count
from drf_yasg.utils import swagger_serializer_method

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from django.utils.translation import gettext_lazy as _

from api.contents.exceptions import PageCommentNotFound, PageNotFound
from api.contents.validators import ISBNValidator
from api.users.serializers import UserSerializer
from apps.contents.models import Note, BookObject, NoteLikesRelation, Page, PageLikesRelation, PageComment
from utils.naver_api import NaverSearchAPI


class StringListField(serializers.ListField):
    child = serializers.CharField()


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
    class Meta:
        model = BookObject
        fields = ['isbn', 'title', 'author', 'publisher', 'category', 'thumbnail']

    @swagger_serializer_method(serializer_or_field=serializers.CharField(help_text='isbn'))
    def validate_isbn(self, value):
        try:
            ISBNValidator(value)
        except ValidationError:
            raise ValidationError(detail=_("invalid_isbn"))
        return value

    def create(self, validated_data):
        isbn = self.validate_isbn(validated_data.pop('isbn'))
        try:
            book = BookObject.objects.get(isbn__exact=isbn)
        except BookObject.DoesNotExist:
            _, value = NaverSearchAPI()(isbn)
            book = BookObject.objects.create(**value[0])
        return book


class SimpleBookListSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookObject
        fields = ['isbn']


class DetailBookListSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookObject
        fields = ['isbn', 'title', 'author', 'publisher', 'thumbnail']

    def to_representation(self, instance):
        return dict(super(DetailBookListSerializer, self).to_representation(instance))


class NoteWithoutBookSchemaSerializer(serializers.Serializer):
    id = serializers.IntegerField(help_text='노트 id', read_only=True)
    note_author = UserSerializer(help_text='작성자', read_only=True)
    like_count = serializers.IntegerField(help_text='좋아요 수', read_only=True)
    like_user = StringListField(help_text='좋아요를 누른 사용자 list', read_only=True)
    hit = serializers.IntegerField(help_text='조회수', read_only=True)
    pages_count = serializers.IntegerField(help_text='노트에 저장된 페이지 수', read_only=True)


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
        ordering = ['created_at']

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

    @staticmethod
    def get_or_create_book(isbn) -> BookObject:
        book_create_serializer = BookCreateSerializer()
        book = book_create_serializer.create(validated_data={"isbn": isbn})
        return book

    def create(self, validated_data):
        isbn = validated_data.pop('isbn')
        if not isbn:
            raise ValidationError(detail=_("no_book_isbn"))

        note, created = Note.objects.get_or_create(
            user=validated_data.pop('user'),
            book=self.get_or_create_book(isbn=isbn)
        )
        return note


class NoteLikesRelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoteLikesRelation
        fields = '__all__'

    def create(self, validated_data):
        note_relation = NoteLikesRelation.objects.create(**validated_data)
        return note_relation.note, note_relation


class PageDetailSchemaSerialzer(serializers.Serializer):
    id = serializers.IntegerField(help_text='페이지 id', read_only=True)
    note_index = serializers.IntegerField(help_text='페이지의 노트 index', read_only=True)
    transcript = serializers.URLField(help_text='필사 이미지 URL', read_only=True)
    phrase = serializers.CharField(help_text='필사 구절', read_only=True)
    hit = serializers.IntegerField(help_text='조회수', read_only=True)
    book_page = serializers.IntegerField(help_text='도서의 페이지(쪽)', read_only=True)
    like_count = serializers.IntegerField(help_text='좋아요 수', read_only=True)
    like_user = StringListField(help_text='좋아요를 누른 사용자 list', read_only=True)
    reviews_count = serializers.IntegerField(help_text='리뷰 수', read_only=True)


class PageSchemaSerializer(serializers.Serializer):
    note = NoteWithoutBookSchemaSerializer(help_text='페이지가 등록된 노트', read_only=True)
    book = BookObjectSerializer(help_text='도서 정보', read_only=True)
    page_detail = PageDetailSchemaSerialzer(help_text='페이지 세부정보', read_only=True)


class PageAllSchemaSerializer(serializers.Serializer):
    book = BookObjectSerializer(help_text='도서 정보', read_only=True)
    page_count = serializers.IntegerField(help_text='페이지 수', read_only=True)
    pages = PageDetailSchemaSerialzer(help_text='페이지 정보', read_only=True)


class PageBulkSerializer(serializers.ListSerializer):
    note = serializers.SerializerMethodField('set_note')

    def set_note(self):
        self.note = self.context.get('note')

    def create(self, validated_data):
        self.set_note()
        with transaction.atomic():
            for data in validated_data:
                data.update({'note': self.note})
            obj_data = [Page(**item) for item in validated_data]
            pages = Page.objects.bulk_create(obj_data)
            note_index = Page.objects.values('note_id')\
                .annotate(count=Count('note_id'))\
                .filter(note=self.note)[0]
            note_index['count'] -= len(obj_data)
            for p in pages:
                p.note_index = note_index['count'] + 1
                note_index['count'] += 1
            Page.objects.bulk_update(pages, ['note_index'])
            return pages

    def update(self, instance, validated_data):
        instance.transcript = validated_data.pop('transcript', instance.transcript)
        instance.phrase = validated_data.pop('phrase', instance.phrase)
        instance.note_index = validated_data.pop('note_index', instance.note_index)
        instance.book_page = validated_data.pop('book_page', instance.book_page)
        instance.save()

        return instance


class PageSerializer(serializers.ModelSerializer):
    like_user = serializers.SerializerMethodField()

    class Meta:
        model = Page
        fields = '__all__'
        list_serializer_class = PageBulkSerializer

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
            'note_index': instance.note_index,
            'transcript': instance.transcript,
            'phrase': instance.phrase,
            'book_page': instance.book_page,
            'hit': instance.hit,
            'like_count': instance.page_likes_relation.count(),
            'like_user': self.get_like_user(instance)
        }


class PageDetailSerializer(PageSerializer):
    @staticmethod
    def get_note_author_from_book(instance: Page):
        return UserSerializer(instance=instance.note.user).data

    @staticmethod
    def get_book_from_page(instance: Page):
        return DetailBookListSerializer(instance=instance.note.book).data

    @staticmethod
    def get_comments_from_page(instance: Page):
        return PageCommentSerializer(instance=instance.page_comment.all(), many=True).data

    def to_representation(self, instance: Page):
        page_author = self.get_note_author_from_book(instance)
        book = self.get_book_from_page(instance)
        page_comments = self.get_comments_from_page(instance)
        page_detail = super(PageDetailSerializer, self).to_representation(instance)

        return OrderedDict([
            ('book', book),
            ('page_author', page_author),
            ('page_detail', page_detail),
            ('page_comments', page_comments)
        ])


class PageLikesRelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageLikesRelation
        fields = '__all__'

    def create(self, validated_data):
        page_relation = PageLikesRelation.objects.create(**validated_data)
        return page_relation.page, page_relation


class PageCommentSchemaSerializer(serializers.Serializer):
    id = serializers.IntegerField(help_text='페이지 코멘트 id', read_only=True)
    page_id = serializers.IntegerField(help_text='페이지 id', read_only=True)
    comment_user = serializers.IntegerField(help_text='코멘트 작성자 id', read_only=True)
    depth = serializers.IntegerField(help_text='코멘트 depth (0 ~)', read_only=True)
    parent = serializers.IntegerField(help_text='상위 코멘트 id (default=0)', read_only=True)
    content = serializers.CharField(help_text='코멘트 내용', read_only=True)


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
            'comment_user': {
                'id': instance.comment_user.id,
                'nickname': instance.comment_user.nickname
            },
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
                raise PageCommentNotFound(detail=_("no_exist_parent_comment"))
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
