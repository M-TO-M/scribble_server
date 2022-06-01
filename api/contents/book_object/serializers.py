from drf_yasg.utils import swagger_serializer_method

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from django.utils.translation import gettext_lazy as _

from apps.contents.models import BookObject
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
        fields = ['isbn', 'title', 'author', 'publisher', 'category', 'thumbnail']

    @swagger_serializer_method(serializer_or_field=serializers.CharField(help_text='isbn'))
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
