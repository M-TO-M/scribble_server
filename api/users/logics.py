import os
import json
from typing import Tuple
from urllib import request, parse
from dotenv import load_dotenv

from rest_framework.exceptions import ValidationError

from api.users.serializers import UserSerializer
from apps.users.models import User

load_dotenv()

KAKAO_REST_API_KEY = os.environ.get('KAKAO_REST_API_KEY')

REQUEST_URL = {
    "KAKAO": {
        "auth_url": "https://kauth.kakao.com/oauth/token",
        "profile_url": "https://kapi.kakao.com/v2/user/me"
    }
}


class SocialLoginService:
    def __init__(self, social_type):
        self.social_user = None
        self.social_type = social_type

    def kakao_auth_url(self, code, redirect_uri):
        base_url = REQUEST_URL["KAKAO"]["auth_url"]
        p = {
            "grant_type": "authorization_code",
            "client_id": KAKAO_REST_API_KEY,
            "code": code,
            "redirect_uri": redirect_uri
        }
        params = "&".join([f"{key}={value}" for key, value in p.items()])
        url = base_url + f"?{params}"
        return url

    def kakao_profile_url(self):
        base_url = REQUEST_URL["KAKAO"]["profile_url"]
        url = base_url + "?property_keys=[\"kakao_account.email\",\"kakao_account.profile\"]"
        return url

    def get_kakao_token(self, code, redirect_uri):
        url = self.kakao_auth_url(code=code, redirect_uri=redirect_uri)

        req = request.Request(url=url)
        req.add_header("Content-type", "application/x-www-form-urlencoded")

        response = request.urlopen(req)
        res_code = response.getcode()
        if res_code != 200:
            raise ValidationError("invalid_code")

        res_body = response.read().decode('utf-8')
        res_data = json.loads(res_body)

        access_token = res_data.get("access_token")
        return access_token

    def get_kakao_user(self, access_token):
        url = self.kakao_profile_url()

        req = request.Request(url=url)
        req.add_header("Authorization", f"Bearer {access_token}")
        req.add_header("Content-type", "application/x-www-form-urlencoded; charset=utf-8")

        response = request.urlopen(req)
        res_code = response.getcode()
        if res_code != 200:
            raise ValidationError("invalid_token")

        res_body = response.read().decode('utf-8')
        res_data = json.loads(res_body)

        return res_data

    def kakao_auth(self, code, redirect_uri) -> Tuple[dict, bool]:
        token = self.get_kakao_token(code=code, redirect_uri=redirect_uri)
        if not token:
            raise ValidationError("token_not_exists")

        user_data = self.get_kakao_user(access_token=token)
        auth_id = f"k@{user_data.get('id')}"
        try:
            user = User.objects.get(auth_id=auth_id)
            serialized_data = UserSerializer(instance=user).data
            self.social_user = user
        except User.DoesNotExist:
            return user_data, False
        return serialized_data, True
