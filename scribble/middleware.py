from django.contrib.auth.models import AnonymousUser
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject

from scribble.authentication import CustomJWTAuthentication


ALLOWED_PATH = ["/", "/users/new", "users/verify", "users/signin"]


class TokenAuthMiddleWare(MiddlewareMixin):
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_request(self, request):
        if request.path in ALLOWED_PATH:
            pass
        request.user = SimpleLazyObject(lambda: self.get_token_user(request))

    @staticmethod
    def get_token_user(request):
        user, jwt_token = CustomJWTAuthentication.authenticate(request)
        return user or AnonymousUser()
