from datetime import datetime

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers


class StringListField(serializers.ListField):
    child = serializers.CharField()


class ScribbleTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["iat"] = datetime.now()
        token["username"] = user.nickname

        return token
