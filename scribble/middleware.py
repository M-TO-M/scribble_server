from django.contrib.auth.models import AnonymousUser
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject
from rest_framework.exceptions import APIException

from scribble.authentication import CustomJWTAuthentication


ALLOWED_PATH = ["/", "/users/new", "users/verify", "users/signin"]


class TokenAuthMiddleWare(MiddlewareMixin):
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response

    def __call__(self, request):
        if request.path not in ALLOWED_PATH:
            self.process_request(request)
        return self.get_response(request)

    def process_request(self, request):
        request.user = SimpleLazyObject(lambda: self.get_token_user(request))

    @staticmethod
    def get_token_user(request):
        auth = CustomJWTAuthentication()
        user, jwt_token = auth.authenticate(request)

        return user or AnonymousUser()
