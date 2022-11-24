import json

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema, no_body

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenViewBase
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

import scribble.settings.base as settings
from utils.cache import get_or_set_token_cache

from api.users.exceptions import UserNotFound
from api.users.mixins import AuthorizingMixin, SignInLoggingMixin
from api.users.serializers import *
from utils.swagger import (
    swagger_response,
    swagger_parameter,
    swagger_schema_with_properties,
    swagger_schema_with_description, swagger_schema_with_items,
    UserFailCaseCollection as user_fail_case,
    user_response_example,
    user_response_example_with_access
)


class ScribbleTokenRefreshView(TokenViewBase):
    serializer_class = TokenRefreshSerializer

    @swagger_auto_schema(
        operation_id='token_refresh',
        operation_description='토큰을 재발급합니다.\n 요청시, cookie에 blacklist에 등록할 refresh_token을 담아야 합니다.',
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

        # addr = request.META.get('REMOTE_ADDR')
        # cached, msg = get_or_set_token_cache(remote_addr=addr, user=user)
        # if cached is False:
        #     response.status_code = 401
        #     return response

        refresh = response.data.pop('refresh')
        response.set_cookie(
            key=settings.SIMPLE_JWT["AUTH_COOKIE"],
            value=str(refresh),
            expires=settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"],
            secure=settings.SIMPLE_JWT["AUTH_COOKIE_SECURE"],
            httponly=settings.SIMPLE_JWT["AUTH_COOKIE_HTTP_ONLY"]
        )
        return response


class BaseModelViewSet(viewsets.ModelViewSet):
    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        assert lookup_url_kwarg in self.kwargs
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        try:
            obj = queryset.get(**filter_kwargs)
        except queryset.model.DoesNotExist:
            raise UserNotFound()

        self.check_object_permissions(self.request, obj)
        return obj


class TokenObtainViewSet(BaseModelViewSet):
    def set_logging_cache(self, request):
        if settings.RUN_ENV == "prod":
            addr = request.META.get('REMOTE_ADDR')
            cached, msg = get_or_set_token_cache(remote_addr=addr, user=request.user)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super(TokenObtainViewSet, self).finalize_response(request, response, *args, **kwargs)
        if response.status_code >= 400:
            return response

        if self.action == "signin":
            self.set_logging_cache(request=request)
            token = ScribbleTokenObtainPairSerializer().get_token(request.user)
            response.data["access"] = str(token.access_token)
            response.data["refresh"] = str(token)
            response.set_cookie(
                key=settings.SIMPLE_JWT["AUTH_COOKIE"],
                value=str(token),
                expires=settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"],
                secure=settings.SIMPLE_JWT["AUTH_COOKIE_SECURE"],
                httponly=settings.SIMPLE_JWT["AUTH_COOKIE_HTTP_ONLY"]
            )
        elif self.action == "signout":
            response.delete_cookie(settings.SIMPLE_JWT["AUTH_COOKIE"])
        return response


# todo: custom exception 이전에 설정된 default exception을 호출하는 문제 해결하기
class UserViewSet(TokenObtainViewSet, SignInLoggingMixin, AuthorizingMixin):
    serializer_class = UserSerializer
    queryset = User.objects.all()

    @swagger_auto_schema(
        operation_id='sign_up',
        operation_description='회원가입을 수행합니다.',
        request_body=swagger_schema_with_properties(
            openapi.TYPE_OBJECT,
            {
                "email": swagger_schema_with_description(openapi.FORMAT_EMAIL, "이메일"),
                "password": swagger_schema_with_description(openapi.FORMAT_PASSWORD, "비밀번호"),
                "nickname": swagger_schema_with_description(openapi.TYPE_STRING, "닉네임"),
                "category": swagger_schema_with_items(openapi.TYPE_ARRAY, openapi.TYPE_STRING, "추가/삭제할 카테고리 list"),
                "profile_image": swagger_schema_with_description(openapi.FORMAT_URI, "프로필 사진")
            }
        ),
        responses={
            201: swagger_response(
                description='USER_201_SIGN_UP',
                schema=serializer_class,
                examples=user_response_example,
            ),
            400:
                user_fail_case.USER_400_VERIFY_EXIST_EMAIL.as_md() +
                user_fail_case.USER_400_VERIFY_EXIST_NICKNAME.as_md() +
                user_fail_case.USER_400_VERIFY_INVALID_DOMAIN.as_md() +
                user_fail_case.USER_400_INVALID_CATEGORY.as_md()
        },
        security=[]
    )
    @action(detail=False, methods=["post"], serializer_class=SignUpSerializer, name="new")
    def new(self, request, *args, **kwargs):
        return self.create(request)

    @swagger_auto_schema(
        operation_id='sign_in',
        operation_description='로그인을 수행합니다.',
        request_body=swagger_schema_with_properties(
            openapi.TYPE_OBJECT,
            {
                'email': swagger_schema_with_description(openapi.FORMAT_EMAIL, description='이메일'),
                'password': swagger_schema_with_description(openapi.FORMAT_PASSWORD, description='비밀번호')
            }
        ),
        responses={
            200: swagger_response(
                description='USER_201_SIGN_IN',
                schema=SignUpSerializer,
                examples=user_response_example_with_access
            ),
            400:
                user_fail_case.USER_400_SIGN_IN_NO_EXIST_EMAIL.as_md() +
                user_fail_case.USER_400_SIGN_IN_INVALID_PASSWORD.as_md()
        },
        security=[]
    )
    @action(detail=False, methods=["post"], serializer_class=SignInSerializer, name="signin")
    def signin(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        headers = self.get_success_headers(serializer.data)
        request.user = serializer.instance
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @swagger_auto_schema(
        operation_id='sign_out',
        operation_description='로그아웃을 수행합니다.\n 요청시, cookie에 blacklist에 등록할 refresh_token을 담아야 합니다.',
        request_body=no_body,
        responses={
            204: swagger_response(description='USER_204_SIGN_OUT'),
            400: user_fail_case.USER_400_SIGN_OUT_INVALID_REFRESH_TOKEN.as_md(),
            401: user_fail_case.USER_401_UNAUTHORIZED.as_md(),
            404: user_fail_case.USER_404_DOES_NOT_EXIST.as_md()
        }
    )
    @action(detail=False, methods=["post"], serializer_class=SignOutSerializer, name="signout")
    def signout(self, request, *args, **kwargs):
        data = {
            'refresh': request.COOKIES[settings.SIMPLE_JWT["AUTH_COOKIE"]],
            'user_id': request.user.id
        }

        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(None, status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        operation_id='user_delete',
        operation_description='사용자 탈퇴 기능을 수행합니다.',
        responses={
            204: swagger_response(description='USER_204_DELETE'),
            401: user_fail_case.USER_401_UNAUTHORIZED.as_md(),
            404: user_fail_case.USER_404_DOES_NOT_EXIST.as_md()
        }
    )
    @action(detail=True, methods=["delete"], name="delete")
    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        self.authorize_request_user(request, user)
        self.perform_destroy(request.user)
        return Response(None, status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        operation_id='user_edit',
        operation_description='사용자 정보를 수정합니다.',
        responses={
            201: swagger_response(
                description='USER_201_EDIT',
                schema=serializer_class,
                examples=user_response_example,
            ),
            400: user_fail_case.USER_400_EDIT_VALIDATION_ERROR.as_md(),
            401: user_fail_case.USER_401_UNAUTHORIZED.as_md(),
            404: user_fail_case.USER_404_DOES_NOT_EXIST.as_md()
        }
    )
    @action(detail=True, methods=["patch"], name="edit")
    def edit(self, request, *args, **kwargs):
        user = self.get_object()
        self.authorize_request_user(request, user)
        return self.partial_update(request)

    @swagger_auto_schema(
        operation_id='user_info',
        operation_description='token값으로 사용자 정보를 조회합니다.',
        responses={
            200: swagger_response(
                description='USER_200_INFO_BY_TOKEN',
                schema=UserSerializer,
                examples=user_response_example
            ),
            404: user_fail_case.USER_404_DOES_NOT_EXIST.as_md()
        }
    )
    @action(detail=False, methods=["get"], name="myinfo")
    def myinfo(self, request, *args, **kwargs):
        user = request.user
        if not user:
            raise UserNotFound()
        return Response({"user": UserSerializer(user).data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id='verify',
        operation_description='중복 검사(이메일, 닉네임)를 수행합니다.',
        manual_parameters=[
            swagger_parameter('nickname', openapi.IN_QUERY, '닉네임', openapi.TYPE_STRING),
            swagger_parameter('email', openapi.IN_QUERY, '이메일', openapi.FORMAT_EMAIL),
        ],
        responses={
            200: swagger_response(description='USER_200_VERIFY',
                                  examples={"status": "success", "provider": "naver.com"}),
            204: swagger_response(description='USER_204_VERIFY_NO_PARAMS'),
            400:
                user_fail_case.USER_400_VERIFY_EXIST_EMAIL.as_md() +
                user_fail_case.USER_400_VERIFY_EXIST_NICKNAME.as_md() +
                user_fail_case.USER_400_VERIFY_INVALID_DOMAIN.as_md()
        },
        security=[]
    )
    @action(detail=False, methods=["get"], serializer_class=VerifySerializer, name="verify")
    def verify(self, request, *args, **kwargs):
        params = request.GET
        if not params:
            return Response(None, status=status.HTTP_204_NO_CONTENT)

        email = params.get('email', '')
        if email:
            response = {"provider": self.serializer_class.get_email(email)}
            return Response(response, status=status.HTTP_200_OK)

        nickname = params.get('nickname', '')
        if nickname:
            response = {"nickname": self.serializer_class.get_nickname(nickname)}
            return Response(response, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id='user_category',
        operation_description='사용자가 선택한 관심분야/카테고리 정보를 조회합니다.',
        responses={
            200: swagger_response(description='USER_200_CATEGORY_VIEW', examples={"category": {'9': '과학'}}),
            404: user_fail_case.USER_404_DOES_NOT_EXIST.as_md()
        }
    )
    @action(detail=True, methods=["get"], serializer_class=CategoryFieldSerializer, name="category")
    def category(self, request, *args, **kwargs):
        user = self.get_object()
        response = {"category": user.category}
        return Response(response, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id='category_follow_unfollow',
        operation_description='관심분야/카테고리 정보를 수정합니다.',
        request_body=swagger_schema_with_properties(
            openapi.TYPE_OBJECT,
            {'category': swagger_schema_with_items(openapi.TYPE_ARRAY, openapi.TYPE_STRING, "추가/삭제할 카테고리 list")}
        ),
        manual_parameters=[
            swagger_parameter('user_id', openapi.IN_QUERY, '사용자 id', openapi.TYPE_INTEGER),
            swagger_parameter('event', openapi.IN_QUERY, '추가/삭제', openapi.TYPE_STRING, pattern=['follow / unfollow']),
        ],
        responses={
            201: swagger_response(
                description='USER_201_CATEGORY_FOLLOW_UNFOLLOW',
                schema=UserSerializer,
                examples=user_response_example
            ),
            204: swagger_response(description='USER_204_CATEGORY_PARAMS_NO_EXIST_OR_INVALID'),
            400:
                user_fail_case.USER_400_INVALID_CATEGORY.as_md() +
                user_fail_case.USER_400_FOLLOW_EXIST_CATEGORY.as_md() +
                user_fail_case.USER_400_FOLLOW_CANCEL_NO_EXIST_CATEGORY.as_md(),
            401: user_fail_case.USER_401_UNAUTHORIZED.as_md(),
            404: user_fail_case.USER_404_DOES_NOT_EXIST.as_md()
        }
    )
    @action(detail=False, methods=["patch"], serializer_class=CategoryFieldSerializer, name="category_update")
    def category_update(self, request, *args, **kwargs):
        user_id = request.GET.get("user_id")
        event = request.GET.get("event")
        if user_id is None or event is None:
            return Response(None, status=status.HTTP_204_NO_CONTENT)

        try:
            user = self.queryset.get(id=user_id)
        except User.DoesNotExist:
            raise UserNotFound()
        self.authorize_request_user(request, user)

        data = json.loads(request.body)
        raw_data = data.get('category', '')
        if raw_data is None:
            return Response(None, status=status.HTTP_204_NO_CONTENT)
        req_data = raw_data if isinstance(raw_data, list) else list(raw_data.values())

        if event == 'follow':
            valid_data = self.serializer_class.get_follow(user=user, req_data=req_data)
            valid_data.extend(list(user.category.values()))
        elif event == 'unfollow':
            valid_data = self.serializer_class.get_unfollow(user=user, req_data=req_data)
        else:
            return Response(None, status=status.HTTP_204_NO_CONTENT)
        valid_data = self.serializer_class.get_category(valid_data)
        user_serializer = UserSerializer(data=valid_data, partial=True)
        user_serializer.is_valid(raise_exception=True)
        update_user = user_serializer.update(instance=user, validated_data={'category': valid_data})

        response = {"user": UserSerializer(instance=update_user).data}
        return Response(response, status=status.HTTP_201_CREATED)


class PasswordViewSet(BaseModelViewSet, AuthorizingMixin):
    queryset = User.objects.all()
    serializer_class = PasswordChangeSerializer

    @swagger_auto_schema(
        operation_id='passwd_change',
        operation_description='비밀번호를 변경합니다.',
        request_body=swagger_schema_with_properties(
            openapi.TYPE_OBJECT,
            {
                'old_passwd': swagger_schema_with_description(openapi.TYPE_STRING, description='기존 비밀번호'),
                'new_passwd': swagger_schema_with_description(openapi.TYPE_STRING, description='변경할 비밀번호')
            }
        ),
        responses={
            201: swagger_response(
                description='USER_201_PASSWD_CHANGE',
                schema=UserSerializer,
                examples=user_response_example
            ),
            401: user_fail_case.USER_401_UNAUTHORIZED.as_md(),
            404: user_fail_case.USER_404_DOES_NOT_EXIST.as_md()
        }
    )
    @action(detail=True, methods=["put"], name="change")  # todo: throttling
    def change(self, request, *args, **kwargs):
        user = self.get_object()
        self.authorize_request_user(request, user)

        data = json.loads(request.body)
        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        user = serializer.check_passwd(obj=user)
        response = {"user": UserSerializer(instance=user).data}
        return Response(response, status=status.HTTP_201_CREATED)
