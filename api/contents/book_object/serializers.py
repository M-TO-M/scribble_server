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
