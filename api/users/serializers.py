import logging
from typing import Union

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenBlacklistSerializer

from apps.users.choices import SocialAccountTypeEnum
from apps.users.models import User, category_choices
from core.fields import ChoiceTypeField
from core.validators import SpecificEmailDomainValidator, domain_allowlist, CategoryDictValidator
from scribble.authentication import CustomJWTAuthentication
from utils.logging_utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger("api.users.serializers"))


class UserBaseSerializer(serializers.ModelSerializer):
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
        fields = (
            "id",
            "social_type",
            "auth_id",
            "email",
            "password",
            "nickname",
            "category",
            "profile_image",
            "created_at",
            "updated_at"
        )

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


class SocialSignInSerializer(serializers.ModelSerializer):
    social_type = ChoiceTypeField(
        choices=SocialAccountTypeEnum.choices(),
        default=SocialAccountTypeEnum.DEFAULT.value,
        valid_choice={"social_type": SocialAccountTypeEnum.choices_list()}
    )
    auth_id = serializers.CharField(required=True, max_length=20)

    class Meta:
        model = User
        fields = (
            "id",
            "social_type",
            "auth_id",
            "nickname",
            "category",
            "profile_image",
            "created_at",
            "updated_at"
        )

    def validate_social_type(self, value):
        _default = self.get_fields().get("social_type").default
        if not value or value == _default:
            raise ValidationError("invalid_social_type")
        return value

    def validate(self, attrs):
        auth_id = attrs["auth_id"]
        if not auth_id:
            raise ValidationError("invalid_social_account")

        auth_id = f"{attrs['social_type'][0]}@{auth_id}"
        try:
            user = self.Meta.model.objects.get(social_type=attrs["social_type"], auth_id=auth_id)
            raise ValidationError(detail=_("exist_auth_id"))
        except self.Meta.model.DoesNotExist:
            return attrs

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        self.instance = user
        log.debug(f"{user.social_type} auth account created: {user.auth_id}")
        return user


class VerifySerializer(serializers.ModelSerializer):
    email = serializers.SerializerMethodField()
    nickname = serializers.SerializerMethodField()

    @staticmethod
    def get_email(email: str) -> tuple[bool, str]:
        try:
            User.objects.get(email=email)
            return False, "exist_email"
        except User.DoesNotExist:
            if email.rsplit("@", 1)[1] not in domain_allowlist:
                return False, "invalid_domain"
            return True, ""

    @staticmethod
    def get_nickname(nickname: str) -> tuple[bool, str]:
        try:
            User.objects.get(nickname__exact=nickname)
            return False, "exist_nickname"
        except User.DoesNotExist:
            return True, ""


class UserSerializer(UserBaseSerializer):
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        log.debug(f"drf account created: {user.id}")
        return user

    def update(self, instance, validated_data):
        instance.nickname = validated_data.pop('nickname', instance.nickname)
        instance.profile_image = validated_data.pop('profile_image', instance.profile_image)
        instance.category = validated_data.pop('category', instance.category)
        instance.save()
        return instance

    def to_representation(self, instance):
        data = super().to_representation(self.instance)
        data.pop('password')
        return data


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


class PasswordChangeSerializer(serializers.Serializer):
    old_passwd = serializers.CharField(required=True)
    new_passwd = serializers.CharField(required=True)

    def check_passwd(self, obj: User):
        if not obj.check_password(self.data.get('old_passwd')):
            raise ValidationError(detail=_(f"wrong_passwd"))
        new_passwd = self.data.get('new_passwd')
        if new_passwd:
            obj.set_password(new_passwd)
            obj.save()
            return obj
