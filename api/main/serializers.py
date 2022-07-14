from rest_framework import serializers

from api.contents.note.serializers import NoteSchemaSerializer
from api.contents.page.serializers import PageSchemaSerializer
from api.users.serializers import UserSerializer


class MainSchemaSerializer(serializers.Serializer):
    count = serializers.IntegerField(help_text='전체 게시물(페이지) 수', read_only=True)
    previous_offset = serializers.IntegerField(help_text='조회 가능한 이전 start offset', read_only=True)
    next_offset = serializers.IntegerField(help_text='조회 가능한 다음 offset', read_only=True)
    pages = PageSchemaSerializer(many=True, help_text='페이지', read_only=True)


class UserMainSchemaSerializer(serializers.Serializer):
    count = serializers.IntegerField(help_text='전체 게시물(페이지) 수', read_only=True)
    previous_offset = serializers.IntegerField(help_text='조회 가능한 이전 start offset', read_only=True)
    next_offset = serializers.IntegerField(help_text='조회 가능한 다음 offset', read_only=True)
    notes = NoteSchemaSerializer(many=True, help_text='노트', read_only=True)
    user = UserSerializer(help_text='사용자', read_only=True)

