import json

from django.contrib.auth.hashers import check_password
from django.utils.translation import gettext_lazy as _

from rest_framework import generics, mixins, status
from rest_framework.response import Response

from api.users.serializers import *
from utils.serializers import ScribbleTokenObtainPairSerializer


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
