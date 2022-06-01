from random import randint
from typing import Union

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenBlacklistSerializer

from apps.users.models import User, category_choices
from core.validators import SpecificEmailDomainValidator, domain_allowlist, CategoryDictValidator
from scribble.authentication import CustomJWTAuthentication


class UserValidationBaseSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        error_messages={'unique': _('exist_email')},
        validators=[SpecificEmailDomainValidator(allowlist=domain_allowlist)]
    )
    nickname = serializers.CharField(error_messages={'unique': _('exist_nickname')})
    category = serializers.JSONField(
        validators=[CategoryDictValidator(limit_value=category_choices)]
    )

    class Meta:
        model = User
        fields = '__all__'

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

    def validate_category(self, value):
        ret = {}
        for val in value:
            if val not in category_choices:
                raise ValidationError(detail={"detail": "invalid_category", "category_list": category_choices})
            ret[category_choices.index(val)] = val
        return ret


class SignUpSerializer(UserValidationBaseSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "password", "nickname", "category", "profile_image", "created_at", "updated_at")

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class SignOutSerializer(TokenBlacklistSerializer):
    user_id = serializers.IntegerField()
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField()

    def validate(self, attrs):
        self.refresh = self.token_class(attrs['refresh'])
        access = str(self.refresh.access_token)

        auth = CustomJWTAuthentication()
        validated_token = auth.get_validated_token(access)
        user = auth.get_user(validated_token)

        if attrs['user_id'] != user.id:
            raise ValidationError(detail=_("unauthorized_user"))

        return attrs

    def save(self):
        try:
            self.refresh.blacklist()
        except TokenError:
            raise ValidationError(detail=_("invalid_refresh_token"))
        return {}


class VerifySerializer(serializers.ModelSerializer):
    email = serializers.SerializerMethodField()
    nickname = serializers.SerializerMethodField()

    @staticmethod
    def get_email(email: str) -> str:
        try:
            User.objects.get(email__exact=email)
            raise ValidationError(detail=_("exist_email"))
        except User.DoesNotExist:
            domain = email.rsplit("@", 1)[1]
            if domain not in domain_allowlist:
                raise ValidationError(detail={"detail": "invalid_domain", "domain_allowlist": domain_allowlist})
            return domain

    @staticmethod
    def get_nickname(nickname: str) -> None:
        try:
            User.objects.get(nickname__exact=nickname)
            recommend = nickname + str(randint(1, 100))
            raise ValidationError(detail={"detail": "exist_nickname", "recommend": recommend})
        except User.DoesNotExist:
            return None


class UserSerializer(UserValidationBaseSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "password", "nickname", "category", "profile_image", "created_at", "updated_at")

    def update(self, instance, validated_data):
        instance.nickname = validated_data.pop('nickname', instance.nickname)
        instance.profile_image = validated_data.pop('profile_image', instance.profile_image)
        instance.category = validated_data.pop('category', instance.category)
        instance.save()

        return instance


class CategoryFieldSerializer(serializers.Serializer):
    follow = serializers.SerializerMethodField()
    unfollow = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()

    @staticmethod
    def get_follow(user: User, req_data: list) -> list:
        valid_data = []
        user_category_values = list(user.category.values())
        for value in req_data:
            if value in user_category_values:
                raise ValidationError(detail=_(f"exist_follow_{value}"))
            valid_data.append(value)

        return valid_data

    @staticmethod
    def get_unfollow(user: User, req_data: list) -> list:
        valid_data = list(user.category.values())
        for value in req_data:
            if value not in valid_data:
                raise ValidationError(detail=_(f"no_exist_unfollow_{value}"))
            valid_data.remove(value)
        return valid_data

    @staticmethod
    def get_category(value: Union[list, dict]):
        if isinstance(value, dict):
            return value
        if isinstance(value, list):
            ret = {}
            for val in value:
                if val not in category_choices:
                    raise ValidationError(detail={"detail": "invalid_category", "category_list": category_choices})
                ret[category_choices.index(val)] = val
            return ret
