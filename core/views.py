import json

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenViewBase
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from core.serializers import ScribbleTokenObtainPairSerializer
from utils.cache import get_or_set_token_cache
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

        cached, msg = get_or_set_token_cache(request=request, user=self.user)

        token = self.serializer_class.get_token(self.user)
        response.data['access'] = str(token.access_token)
        response.set_cookie(
            key=settings.SIMPLE_JWT["AUTH_COOKIE"],
            value=str(token),
            expires=settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"],
            secure=settings.SIMPLE_JWT["AUTH_COOKIE_SECURE"],
            httponly=settings.SIMPLE_JWT["AUTH_COOKIE_HTTP_ONLY"]
        )

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

        cached, msg = get_or_set_token_cache(request=request, user=request.user)
        if cached is False:
            response.status_code = 401
            return response

        refresh = response.data.pop('refresh')
        response.set_cookie(
            key=settings.SIMPLE_JWT["AUTH_COOKIE"],
            value=str(refresh),
            expires=settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"],
            secure=settings.SIMPLE_JWT["AUTH_COOKIE_SECURE"],
            httponly=settings.SIMPLE_JWT["AUTH_COOKIE_HTTP_ONLY"]
        )

        return response

