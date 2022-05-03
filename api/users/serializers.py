from random import randint

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


class VerifySerializer(serializers.ModelSerializer):
    email = serializers.SerializerMethodField()
    nickname = serializers.SerializerMethodField()

    @staticmethod
    def get_email(email: str) -> str:
        try:
            User.objects.get(email__exact=email)
            raise ValidationError(detail=_("exist_email"))
        except User.DoesNotExist:
            return email.rsplit("@", 1)[1]

    @staticmethod
    def get_nickname(nickname: str) -> None:
        try:
            User.objects.get(nickname__exact=nickname)
            recommend = nickname + str(randint(1, 100))
            raise ValidationError(detail={"fail_case": "exist_nickname", "recommend": recommend})
        except User.DoesNotExist:
            return None
