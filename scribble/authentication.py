from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from rest_framework.exceptions import NotAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken, AuthenticationFailed
from rest_framework_simplejwt.settings import api_settings


class CustomJWTAuthentication(JWTAuthentication):
    www_authenticate_realm = "api"
    media_type = "application/json"

    access_token, raw_token, validated_token = None, None, None
    user = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_header(self, request):
        header = request.META.get(api_settings.AUTH_HEADER_NAME)
        return header

    def get_raw_token(self, auth_header):
        try:
            header_type, header_content = auth_header.rsplit(" ", 1)
        except Exception:
            raise NotAuthenticated()
        else:
            if header_type not in api_settings.AUTH_HEADER_TYPES:
                return None
            return header_content

    def get_validated_token(self, raw_token):
        auth_token = api_settings.AUTH_TOKEN_CLASSES[0]
        try:
            return auth_token(raw_token)
        except TokenError:
            raise InvalidToken(detail=_(f"유효하지 않은 token type을 가진 {auth_token.token_type} token 입니다."))

    def get_user(self, validated_token):
        try:
            user_id = validated_token[api_settings.USER_ID_CLAIM]
        except TokenError:
            return InvalidToken(detail=_("유효하지 않은 token type을 가진 token 입니다."))

        try:
            user = self.user_model.objects.get(**{api_settings.USER_ID_FIELD: user_id})
        except self.user_model.DoesNotExist:
            raise AuthenticationFailed(detail=_("사용자를 찾을 수 없습니다"), code="user_not_found")
        else:
            if not user.is_active:
                raise AuthenticationFailed(detail=_("사용자가 활성화되어 있지 않습니다"), code="user_inactive")
        return user

    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token
