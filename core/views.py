import json

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenViewBase
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from core.serializers import ScribbleTokenObtainPairSerializer
from scribble import settings


class ScribbleTokenObtainView(generics.CreateAPIView):
    serializer_class = ScribbleTokenObtainPairSerializer

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.user = None

    def finalize_response(self, request, response, *args, **kwargs):
        super(ScribbleTokenObtainView, self).finalize_response(request, response, *args, **kwargs)
        if response.status_code >= 400:
            return response

        token = self.serializer_class.get_token(self.user)

        # access token을 browser의 private 변수로 사용하도록 응답 데이터로 전달
        response.data['access'] = str(token.access_token)

        # refresh token을 cookie에 저장
        response.set_cookie(
            key=settings.SIMPLE_JWT["AUTH_COOKIE"],
            value=str(token),
            expires=settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"],
            secure=settings.SIMPLE_JWT["AUTH_COOKIE_SECURE"],
            httponly=settings.SIMPLE_JWT["AUTH_COOKIE_HTTP_ONLY"]
        )

        # TODO: cache db에 refresh token을 key로, request ip_addr/user_agent를 value로 저장
        # TODO: access token 발급 시, 검증
        return response


class ScribbleTokenRefreshView(TokenViewBase):
    serializer_class = TokenRefreshSerializer

    def post(self, request, *args, **kwargs):
        data = {'refresh': request.COOKIES[settings.SIMPLE_JWT["AUTH_COOKIE"]]}
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.validated_data, status=status.HTTP_201_CREATED)

    def finalize_response(self, request, response, *args, **kwargs):
        super(ScribbleTokenRefreshView, self).finalize_response(request, response, *args, **kwargs)

        refresh = response.data.pop('refresh')
        response.set_cookie(
            key=settings.SIMPLE_JWT["AUTH_COOKIE"],
            value=str(refresh),
            expires=settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"],
            secure=settings.SIMPLE_JWT["AUTH_COOKIE_SECURE"],
            httponly=settings.SIMPLE_JWT["AUTH_COOKIE_HTTP_ONLY"]
        )

        return response

