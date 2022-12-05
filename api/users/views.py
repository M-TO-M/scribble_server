import json
from typing import Union, Tuple

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema, no_body

from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.utils.translation import gettext_lazy as _

from rest_framework import generics, mixins, status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_tracking.mixins import LoggingMixin

from apps.users.models import UserLoginLog
from api.users.serializers import *

from core.views import ScribbleTokenObtainView
from core.exceptions import UserNotFound
from core.serializers import ScribbleTokenObtainPairSerializer
from utils.logging_utils import BraceStyleAdapter
from utils.swagger import swagger_response, swagger_parameter, \
    swagger_schema_with_properties, swagger_schema_with_description, swagger_schema_with_items, \
    UserFailCaseCollection as user_fail_case, user_response_example, user_response_example_with_access

log = BraceStyleAdapter(logging.getLogger("api.users.views"))


class SignInLoggingMixin(LoggingMixin):
    def initial(self, request, *args, **kwargs):
        super(LoggingMixin, self).initial(request, *args, **kwargs)

        user_agent = request.META.get('HTTP_USER_AGENT')
        if user_agent is None:
            user_agent = 'test'
        self.log['user_agent'] = user_agent

    def handle_log(self):
        UserLoginLog(**self.log).save()


class SignUpView(generics.CreateAPIView):
    serializer_class = SignUpSerializer
    authentication_classes = []
    throttle_classes = [AnonRateThrottle]

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
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        sign_up_serializer = self.serializer_class(data=data, partial=True)
        sign_up_serializer.is_valid(raise_exception=True)
        self.perform_create(sign_up_serializer)

        response = {
            "user": sign_up_serializer.data
        }
        return Response(response, status=status.HTTP_201_CREATED)


class VerifyView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = VerifySerializer
    authentication_classes = []
    throttle_classes = [AnonRateThrottle]

    @swagger_auto_schema(
        operation_id='verify',
        operation_description='중복 검사(이메일, 닉네임)를 수행합니다.',
        manual_parameters=[
            swagger_parameter('nickname', openapi.IN_QUERY, '닉네임', openapi.TYPE_STRING),
            swagger_parameter('email', openapi.IN_QUERY, '이메일', openapi.FORMAT_EMAIL),
        ],
        responses={
            200: swagger_response(description='USER_200_VERIFY', examples={"status": "success", "provider": "naver.com"}),
            204: swagger_response(description='USER_204_VERIFY_NO_PARAMS'),
            400:
                user_fail_case.USER_400_VERIFY_EXIST_EMAIL.as_md() +
                user_fail_case.USER_400_VERIFY_EXIST_NICKNAME.as_md() +
                user_fail_case.USER_400_VERIFY_INVALID_DOMAIN.as_md()
        },
        security=[]
    )
    def get(self, request, *args, **kwargs):
        params = request.GET
        if not params:
            return Response(None, status=status.HTTP_204_NO_CONTENT)

        response = {}
        email = params.get('email', '')
        if email:
            provider = self.serializer_class.get_email(email)
            response["provider"] = provider

        nickname = params.get('nickname', '')
        if nickname:
            self.serializer_class.get_nickname(nickname)

        return Response(response, status=status.HTTP_200_OK)


class SignInView(SignInLoggingMixin, ScribbleTokenObtainView):
    logging_methods = ['POST']
    queryset = User.objects.all()
    serializer_class = ScribbleTokenObtainPairSerializer
    authentication_classes = []
    throttle_classes = [AnonRateThrottle]

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
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        try:
            self.user = self.queryset.get(email__exact=data['email'])
        except User.DoesNotExist:
            raise ValidationError(detail=_("no_exist_email"))

        if check_password(data['password'], self.user.password) is False:
            raise ValidationError(detail=_("invalid_password"))

        user_data = SignUpSerializer(instance=self.user).data
        response = {"user": user_data}

        return Response(response, status=status.HTTP_201_CREATED)


class SignOutView(generics.CreateAPIView):
    serializer_class = SignOutSerializer

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
    def post(self, request, *args, **kwargs):
        data = {
            'refresh': request.COOKIES[settings.SIMPLE_JWT["AUTH_COOKIE"]],
            'user_id': request.user.id
        }

        logout_serializer = self.serializer_class(data=data)
        logout_serializer.is_valid(raise_exception=True)
        logout_serializer.save()

        return Response(None, status=status.HTTP_204_NO_CONTENT)

    def finalize_response(self, request, response, *args, **kwargs):
        super(SignOutView, self).finalize_response(request, response, *args, **kwargs)
        response.delete_cookie(settings.SIMPLE_JWT["AUTH_COOKIE"])

        return response


class UserView(generics.GenericAPIView, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    queryset = User.objects.all()
    serializer_class = UserSerializer

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
    def patch(self, request, *args, **kwargs):
        try:
            user = self.get_object()
        except Exception:
            raise UserNotFound()

        if request.user and request.user.id != user.id:
            raise AuthenticationFailed(detail=_("unauthorized_user"))

        data = json.loads(request.body)
        user_serializer = self.serializer_class(data=data, partial=True)
        user_serializer.is_valid(raise_exception=True)
        update_user = user_serializer.update(instance=user, validated_data=data)

        response = {
            "user": UserSerializer(instance=update_user).data
        }

        return Response(response, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_id='user_delete',
        operation_description='사용자 탈퇴 기능을 수행합니다.',
        responses={
            204: swagger_response(description='USER_204_DELETE'),
            401: user_fail_case.USER_401_UNAUTHORIZED.as_md(),
            404: user_fail_case.USER_404_DOES_NOT_EXIST.as_md()
        }
    )
    def delete(self, request, *args, **kwargs):
        try:
            user = self.get_object()
        except Exception:
            raise UserNotFound()

        if request.user and request.user.id != user.id:
            raise AuthenticationFailed(detail=_("unauthorized_user"))

        self.perform_destroy(user)
        return Response(None, status=status.HTTP_204_NO_CONTENT)


class CategoryView(generics.GenericAPIView, mixins.RetrieveModelMixin, mixins.UpdateModelMixin):
    queryset = User.objects.all()
    serializer_class = CategoryFieldSerializer

    def get_params_for_category(self, request) -> Union[Tuple[str, str], Tuple[None, None]]:
        params = self.request.GET
        if params is {}:
            return None, None

        user_id = params.get('user', '')
        event = params.get('event', '')
        if not user_id or not event:
            return None, None

        return user_id, event

    @swagger_auto_schema(
        operation_id='user_category',
        operation_description='사용자가 선택한 관심분야/카테고리 정보를 조회합니다.',
        responses={
            200: swagger_response(description='USER_200_CATEGORY_VIEW', examples={"category": {'9': '과학'}}),
            404: user_fail_case.USER_404_DOES_NOT_EXIST.as_md()
        }
    )
    def get(self, request, *args, **kwargs):
        try:
            user = self.get_object()
        except Exception:
            raise UserNotFound()

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
    def patch(self, request, *args, **kwargs):
        user_id, event = self.get_params_for_category(request)

        if user_id is None or event is None:
            return Response(None, status=status.HTTP_204_NO_CONTENT)

        try:
            user = self.queryset.get(id=user_id)
        except User.DoesNotExist:
            raise UserNotFound()

        if request.user and request.user.id != user.id:
            raise AuthenticationFailed(detail=_("unauthorized_user"))

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

        response = {
            "user": UserSerializer(instance=update_user).data
        }

        return Response(response, status=status.HTTP_201_CREATED)


class PasswordView(generics.GenericAPIView, mixins.UpdateModelMixin):
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
    def put(self, request, *args, **kwargs):
        try:
            user = self.get_object()
        except Exception:
            raise UserNotFound()

        if request.user and request.user.id != user.id:
            raise AuthenticationFailed(detail=_("unauthorized_user"))

        data = json.loads(request.body)

        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        user = serializer.check_passwd(obj=user)

        response = {
            "user": UserSerializer(instance=user).data
        }
        return Response(response, status=status.HTTP_201_CREATED)


class UserInfoByTokenView(generics.GenericAPIView, mixins.RetrieveModelMixin):
    queryset = User.objects.all()
    serializer_class = UserSerializer

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
    def get(self, request, *args, **kwargs):
        user = request.user
        if not user:
            raise UserNotFound()

        response = {"user": UserSerializer(user).data}
        return Response(response, status=status.HTTP_200_OK)
