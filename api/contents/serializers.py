from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.contents.models import BookObject
from core.validators import ISBNValidator


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

    def create(self, validated_data):
        book = BookObject.objects.create(**validated_data)
        return book
