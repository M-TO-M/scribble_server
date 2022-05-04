import json
from typing import Union, Tuple

from django.contrib.auth.hashers import check_password
from django.utils.translation import gettext_lazy as _

from rest_framework import generics, mixins, status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response

from api.users.serializers import *
from core.exceptions import UserNotFound
from core.serializers import ScribbleTokenObtainPairSerializer


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
            return Response(None)

        response = {}
        email = params.get('email', '')
        if email:
            provider = self.serializer_class.get_email(email)
            response["provider"] = provider

        nickname = params.get('nickname', '')
        if nickname:
            self.serializer_class.get_nickname(nickname)

        return Response(response, status=status.HTTP_200_OK)


class SignInView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = ScribbleTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        try:
            user = self.queryset.get(email__exact=data['email'])
        except User.DoesNotExist:
            raise ValidationError(detail=_("no_exist_email"))

        if check_password(data['password'], user.password) is False:
            raise ValidationError(detail=_("invalid_password"))

        user_data = SignUpSerializer(instance=user).data
        token_data = self.serializer_class.get_token(user)
        # auth.login()
        response = {
            "user": user_data,
            "auth": {
                "access_token": str(token_data.access_token),
                "refresh_token": str(token_data)
            }
        }

        return Response(response, status=status.HTTP_201_CREATED)


class SignOutView(generics.CreateAPIView):
    serializer_class = SignOutSerializer

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        data['user_id'] = request.user.id

        logout_serializer = self.serializer_class(data=data)
        logout_serializer.is_valid(raise_exception=True)
        logout_serializer.save()

        return Response(None, status=status.HTTP_204_NO_CONTENT)


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

    def get_params_for_category(self, request) -> Union[Tuple[str, str], Response]:
        params = self.request.GET
        if not params:
            return Response(None)

        user_id = params.get('user', '')
        event = params.get('event', '')
        if not user_id or not event:
            return Response(None)

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
        try:
            user = self.queryset.get(id=user_id)
        except User.DoesNotExist:
            raise ValidationError(detail=_("no_exist_user"))

        if request.user and request.user.id != user.id:
            raise AuthenticationFailed(detail=_("unauthorized_user"))

        data = json.loads(request.body)

        req_data = data['category']
        if event == 'follow':
            valid_data = self.serializer_class.get_follow(user=user, req_data=req_data)
            valid_data.update(user.category)
        elif event == 'unfollow':
            valid_data = self.serializer_class.get_unfollow(user=user, req_data=req_data)
        else:
            return Response(None)

        user_serializer = UserSerializer(data=valid_data, partial=True)
        user_serializer.is_valid(raise_exception=True)
        update_user = user_serializer.update(instance=user, validated_data={'category': valid_data})

        response = {
            "user": UserSerializer(instance=update_user).data
        }

        return Response(response, status=status.HTTP_201_CREATED)
