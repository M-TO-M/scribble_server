import logging
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.contents.models import Page, PageComment
from api.users.serializers import UserSerializer
from core.exceptions import PageNotFound, PageCommentNotFound
from utils.logging_utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger("api.contents.page_comment.views"))


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
