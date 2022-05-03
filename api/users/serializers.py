from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.users.models import User


class SignUpSerializer(serializers.ModelSerializer):
    nickname = serializers.CharField(error_messages={'unique': _('exist_nickname')})

    class Meta:
        model = User
        fields = ("id", "email", "password", "nickname", "category", "profile_image", "created_at", "updated_at")

    def validate_email(self, value):
        try:
            self.Meta.model.objects.get(email__exact=value)
            raise ValidationError(detail=_("exist_email"))
        except self.Meta.model.DoesNotExist:
            return value

    def validate_nickname(self, value):
        try:
            self.Meta.model.objects.get(nickname=value)
            raise ValidationError(detail=_("exist_nickname"))
        except self.Meta.model.DoesNotExist:
            return value

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user
