from drf_yasg.utils import swagger_auto_schema, no_body

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenViewBase
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from core.pagination import MainViewPagination
from core.serializers import ScribbleTokenObtainPairSerializer
from utils.cache import get_or_set_token_cache
from utils.swagger import swagger_response, swagger_schema_with_properties, swagger_schema_with_description
import scribble.settings.base as settings


class TemplateMainView(generics.ListAPIView):
    pagination_class = MainViewPagination

    def filter_data(self, params: dict, data: list):
        mode = params.get('mode', '')
        if mode == "hit":
            sort_key = mode
        elif mode == "likes" or mode == "reviews":
            sort_key = mode + "_count"
        else:
            return data

        sorting = params.get('sorting', '')
        if sorting == 'descending':
            data.sort(key=lambda x: x[sort_key], reverse=True)
        else:
            data.sort(key=lambda x: x[sort_key])

        return data

    def get_paginated_data(self, queryset):
        pagination = self.paginate_queryset(queryset)
        serializer = self.serializer_class(instance=pagination or queryset, many=True)
        filtered_data = self.filter_data(self.request.query_params, serializer.data)

        return filtered_data


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

    @swagger_auto_schema(
        operation_id='token_refresh',
        operation_description='????????? ??????????????????.\n ?????????, cookie??? blacklist??? ????????? refresh_token??? ????????? ?????????.',
        request_body=no_body,
        responses={
            201: swagger_response(description='AUTH_201_TOKEN_REFRESH', schema=serializer_class)
        },
        security=[]
    )
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

