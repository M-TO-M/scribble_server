from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from rest_framework.exceptions import NotAuthenticated
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken, AuthenticationFailed
from rest_framework_simplejwt.settings import api_settings


class CustomJWTAuthentication:
    www_authenticate_realm = "api"
    media_type = "application/json"

    access_token, raw_token, validated_token = None, None, None
    user = None

    def __init__(self):
        self.user_model = get_user_model()

    def get_auth_header(self, request):
        header = request.META.get(api_settings.AUTH_HEADER_NAME)
        return header

    def get_raw_token(self, auth_header):
        try:
            header_type, header_content = auth_header.rsplit(" ", 1)
        except Exception:
            raise NotAuthenticated()
        else:
            if header_type not in api_settings.AUTH_HEADER_NAME:
                return None
            return header_content

    def get_validated_token(self, raw_token):
        auth_token = api_settings.AUTH_TOKEN_CLASSES[0]
        try:
            return auth_token(raw_token)
        except TokenError:
            message = {
                'token_classes': auth_token.__name__,
                'token_type': auth_token.type,
                'error_message': TokenError.args[0]
            }
            raise InvalidToken({
                "detail": _("유효하지 않은 token type을 가진 token 입니다."),
                "messages": message,
                })

    def get_user(self, validated_token):
        try:
            user_id = validated_token[api_settings.USER_ID_CLAIM]
        except KeyError:
            return InvalidToken({"detail": _("유효하지 않은 token type을 가진 token 입니다.")})

        try:
            user = self.user_model.objects.get(**{api_settings.USER_ID_FIELD: user_id})
        except self.user_model.DoesNotExist:
            raise AuthenticationFailed(detail=_("사용자를 찾을 수 없습니다"), code="user_not_found")
        else:
            if not user.is_active:
                raise AuthenticationFailed(detail=_("사용자가 활성화되어 있지 않습니다"), code="user_inactive")

    @classmethod
    def authenticate(cls, request):
        auth = cls()
        header = auth.get_auth_header(request)
        if header is None:
            return None

        raw_token = auth.get_raw_token(header)
        if raw_token is None:
            return None

        validated_token = auth.get_validated_token(raw_token)
        return auth.get_user(validated_token), validated_token
