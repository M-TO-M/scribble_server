from rest_framework import serializers

from api.contents.book_object.serializers import BookObjectSerializer
from api.contents.note.serializers import NoteWithoutBookSchemaSerializer
from api.users.serializers import UserSerializer
from apps.contents.models import Page, PageLikesRelation
from core.serializers import StringListField


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


class PageBulkCreateUpdateSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        page_data = [Page(**item) for item in validated_data]
        return Page.objects.bulk_create(page_data)

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
            'note_index': instance.note_index,
            'transcript': instance.transcript,
            'phrase': instance.phrase,
            'book_page': instance.book_page,
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
