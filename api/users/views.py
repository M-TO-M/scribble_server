import json
from typing import Union, Tuple

from django.contrib.auth.hashers import check_password
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema, no_body

from django.conf import settings
from django.utils.translation import gettext_lazy as _

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.status import is_client_error
from rest_framework.throttling import UserRateThrottle
from rest_framework_tracking.mixins import LoggingMixin

from api.users.logics import SocialLoginService
from apps.users.models import UserLoginLog
from api.users.serializers import *

from core.exceptions import UserNotFound
from core.serializers import ScribbleTokenObtainPairSerializer
from core.throttling import AnonRateThrottle
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


class TokenObtainViewSet(viewsets.ModelViewSet):
    def process_signin_response(self, request, response):
        token = ScribbleTokenObtainPairSerializer.get_token(request.user)
        response.data["access"] = str(token.access_token)
        response.data["refresh"] = str(token)
        response.set_cookie(
            key=settings.SIMPLE_JWT["AUTH_COOKIE"],
            value=str(token),
            expires=settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"],
            secure=settings.SIMPLE_JWT["AUTH_COOKIE_SECURE"],
            httponly=settings.SIMPLE_JWT["AUTH_COOKIE_HTTP_ONLY"]
        )
        return response

    def process_signout_response(self, request, response):
        response.delete_cookie(settings.SIMPLE_JWT["AUTH_COOKIE"])
        return response

    def finalize_response(self, request, response, *args, **kwargs):
        response = super(TokenObtainViewSet, self).finalize_response(request, response, *args, **kwargs)
        if is_client_error(response.status_code):
            return response

        if self.action == "signout":
            return self.process_signout_response(request, response)
        elif self.action == "signin":
            return self.process_signin_response(request, response)
        elif self.action == "signin_social" and not response.data["new_user"]:
            return self.process_signin_response(request, response)
        else:
            return response


class UserViewSet(TokenObtainViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    throttle_classes = ()
    throttle_scope = None

    resp_attrs = [
        'id',
        'social_type',
        'auth_id',
        'email',
        'nickname',
        'category',
        'profile_image',
        'created_at',
        'updated_at'
    ]

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
    @action(
        detail=False,
        methods=["post"],
        serializer_class=UserSerializer,
        throttle_classes=[AnonRateThrottle],
        url_path=r"new"
    )
    def signup(self, request, *args, **kwargs):
        """
         - action: Django Auth User SignUp
         - method: POST
         - body:
            {"email", "password, "nickname", "category", "profile_image"}
        """
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        log.debug("user signup success")

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=self.get_success_headers(serializer.data)
        )

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
                schema=UserSerializer,
                examples=user_response_example_with_access
            ),
            400:
                user_fail_case.USER_400_SIGN_IN_NO_EXIST_EMAIL.as_md() +
                user_fail_case.USER_400_SIGN_IN_INVALID_PASSWORD.as_md()
        },
        security=[]
    )
    @action(
        detail=False,
        methods=["post"],
        serializer_class=UserSerializer,
        throttle_classes=[AnonRateThrottle],
        url_path=r"signin"
    )
    def signin(self, request, *args, **kwargs):
        """
         - action: Django Auth User SignIn
         - method: POST
         - body:  { "email", "password" }
        """
        data = json.loads(request.body)
        try:
            user = self.queryset.get(email=data["email"])
            valid_passwd = check_password(data["password"], user.password)
            if not valid_passwd:
                raise ValidationError(detail=_("invalid_password"))
        except User.DoesNotExist:
            raise ValidationError(detail=_("no_exist_email"))

        request.user = user
        user_data = {attr: getattr(request.user, attr) for attr in self.resp_attrs}
        return Response({"user": user_data}, status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        methods=["post"],
        serializer_class=SocialSignInSerializer,
        throttle_classes=[AnonRateThrottle],
        url_path=r"new_social"
    )
    def signin_social(self, request, *args, **kwargs):
        """
         - action: Social User SignIn & SignUp
         - method: POST
         - body: { "social_type", "redirect_uri", "code" }
         """

        data = request.data
        social_type = data.pop("social_type")
        if social_type not in SocialAccountTypeEnum.choices_list():
            raise ValidationError(detail=_("invalid_social_type"))

        service = SocialLoginService(social_type=social_type)
        user_data, user_exists = service.kakao_auth(**data)
        user_data.update({"new_user": False})

        if user_exists:
            request.user = service.social_user
            log.debug(f"already signed up social user: {request.user.auth_id}")
            return Response(
                user_data,
                status=status.HTTP_200_OK,
                headers=self.get_success_headers(user_data)
            )

        serializer_data = {
            "nickname": user_data["kakao_account"]["profile"]["nickname"],
            "profile_image": user_data["kakao_account"]["profile"]["profile_image_url"],
        }
        serializer_data.update({"social_type": social_type, "auth_id": f"{social_type[0]}@{user_data['id']}"})
        serializer = self.get_serializer(data=serializer_data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        user_data = {attr: getattr(serializer.instance, attr) for attr in self.resp_attrs}
        user_data.update({"new_user": True})
        log.debug(f"social user signup success")

        return Response(
            user_data,
            status=status.HTTP_201_CREATED,
            headers=self.get_success_headers(serializer.data)
        )

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
    @action(
        detail=False,
        methods=["post"],
        serializer_class=SignOutSerializer,
        throttle_classes=[UserRateThrottle],
        url_path=r"signout"
    )
    def signout(self, request, *args, **kwargs):
        data = {
            'refresh': request.COOKIES[settings.SIMPLE_JWT["AUTH_COOKIE"]],
            'user_id': request.user.id
        }

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(None, status=status.HTTP_204_NO_CONTENT)

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
    @action(
        detail=False,
        methods=["get"],
        serializer_class=UserBaseSerializer,
        throttle_classes=[UserRateThrottle]
    )
    def myinfo(self, request, *args, **kwargs):
        if not request.user or request.user.is_anonymous:
            raise UserNotFound()
        user_data = {attr: getattr(request.user, attr) for attr in self.resp_attrs}
        return Response(
            {"user": user_data},
            status=status.HTTP_200_OK
        )

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
    @action(
        detail=False,
        methods=["get"],
        serializer_class=VerifySerializer,
        throttle_classes=[AnonRateThrottle],
        url_path=r"verify"
    )
    def verify(self, request, *args, **kwargs):
        if not request.GET:
            return Response(None, status=status.HTTP_204_NO_CONTENT)

        email = request.GET.get('email')
        if email:
            flag_e, e_msg = self.get_serializer_class().get_email(email)
            if not flag_e:
                raise ValidationError(detail=_(e_msg))
            return Response({"provider": email.rsplit("@", 1)[1]}, status=status.HTTP_200_OK)

        nickname = request.GET.get('nickname')
        if nickname:
            flag_n, n_msg = self.get_serializer_class().get_nickname(nickname)
            if not flag_n:
                raise ValidationError(detail={"detail": n_msg, "recommend": nickname + str(randint(1, 100))})
            return Response({"nickname": nickname}, status=status.HTTP_200_OK)

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
    @action(
        detail=False,
        methods=["patch"],
        serializer_class=UserSerializer,
        throttle_classes=[UserRateThrottle]
    )
    def edit(self, request, *args, **kwargs):
        if not request.user:
            raise UserNotFound()
        user = request.user
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        user_data = {attr: getattr(serializer.instance, attr) for attr in self.resp_attrs}
        return Response({"user": user_data}, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_id='user_delete',
        operation_description='사용자 탈퇴 기능을 수행합니다.',
        responses={
            204: swagger_response(description='USER_204_DELETE'),
            401: user_fail_case.USER_401_UNAUTHORIZED.as_md(),
            404: user_fail_case.USER_404_DOES_NOT_EXIST.as_md()
        }
    )
    @action(
        detail=True,
        methods=["delete"],
        serializer_class=UserSerializer,
        url_path=r"delete"
    )
    def delete(self, request, *args, **kwargs):
        try:
            user = self.get_object()
        except Exception:
            raise UserNotFound()
        if not request.user or request.user.id != user.id:
            raise AuthenticationFailed(detail=_("unauthorized_user"))
        self.perform_destroy(user)
        return Response(None, status=status.HTTP_204_NO_CONTENT)

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
    @action(
        detail=True,
        methods=["put"],
        serializer_class=PasswordChangeSerializer,
        url_path=r"password/change"
    )
    # TODO: 로그인하지 않은 상태에서 비밀번호를 변경할수 있도록 구현
    def password_change(self, request, *args, **kwargs):
        try:
            user = self.get_object()
        except Exception:
            raise UserNotFound()
        if not request.user or request.user.id != user.id:
            raise AuthenticationFailed(detail=_("unauthorized_user"))

        data = json.loads(request.body)
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        user = serializer.check_passwd(obj=user)
        user_data = {attr: getattr(user, attr) for attr in self.resp_attrs}
        return Response({"user": user_data}, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_id='user_category',
        operation_description='사용자가 선택한 관심분야/카테고리 정보를 조회합니다.',
        responses={
            200: swagger_response(description='USER_200_CATEGORY_VIEW', examples={"category": {'9': '과학'}}),
            404: user_fail_case.USER_404_DOES_NOT_EXIST.as_md()
        }
    )
    @action(
        detail=True,
        methods=["get"],
        serializer_class=CategoryFieldSerializer,
        url_path=r"category"
    )
    def category(self, request, *args, **kwargs):
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
    @action(
        detail=False,
        methods=["patch"],
        serializer_class=CategoryFieldSerializer,
        url_path=r"category_update"
    )
    def category_follow_unfollow(self, request, *args, **kwargs):
        user_id, event = request.GET.get('user_id'), request.GET.get('event')
        if not user_id or not event:
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

        user_data = {attr: getattr(update_user, attr) for attr in self.resp_attrs}
        return Response({"user": user_data}, status=status.HTTP_201_CREATED)
