import importlib

from django.contrib.auth.models import AnonymousUser
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject

from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from scribble.authentication import CustomJWTAuthentication
from django.conf import settings

REQ_ALLOWED_PATH = [
    "/main/",
    "/users/new",
    "/users/new_social",
    "/users/verify",
    "/users/signin",
    "/contents/books/search/navbar",
    "/contents/books/search/tagging"
]

VERSION = getattr(settings, 'VERSION', '')
VERSION_ALLOWED_PATH = ['/' + VERSION + path for path in REQ_ALLOWED_PATH]


class TokenAuthMiddleWare(MiddlewareMixin):
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response

    def __call__(self, request):
        self.process_request(request)

        response = None
        if request.path_info not in VERSION_ALLOWED_PATH:
            response = self.process_response(request, response)

        return response or self.get_response(request)

    def process_request(self, request):
        request.user = SimpleLazyObject(lambda: self.get_token_user(request))

    def process_response(self, request, response):
        attr = getattr(settings, 'REST_FRAMEWORK', None)
        assert attr
        m_name, c_name = attr['DEFAULT_RENDERER_CLASSES'][0].rsplit('.', 1)
        cls_renderer = getattr(importlib.import_module(m_name), c_name) or JSONRenderer

        if request.user.is_anonymous:
            response = Response({"user": "is_anonymous"}, status=status.HTTP_403_FORBIDDEN)
            response.accepted_renderer = cls_renderer()
            response.accepted_media_type = "application/json"
            response.renderer_context = {}
            response.render()

        return response

    @staticmethod
    def get_token_user(request):
        auth = CustomJWTAuthentication()
        user, jwt_token = auth.authenticate(request)

        return user or AnonymousUser()
