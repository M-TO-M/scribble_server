import json
from typing import Union, Tuple

from django.contrib.auth.hashers import check_password
from django.utils.translation import gettext_lazy as _

from rest_framework import generics, mixins, status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework_tracking.mixins import LoggingMixin

from apps.users.models import UserLoginLog
from api.users.serializers import *

from core.views import ScribbleTokenObtainView
from core.exceptions import UserNotFound
from core.serializers import ScribbleTokenObtainPairSerializer

from scribble import settings


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

    def get(self, request, *args, **kwargs):
        try:
            user = self.get_object()
        except Exception:
            raise UserNotFound()

        response = {"category": user.category}

        return Response(response, status=status.HTTP_200_OK)

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
