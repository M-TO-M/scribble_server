from rest_framework.exceptions import AuthenticationFailed
from rest_framework_tracking.mixins import LoggingMixin

from django.utils.translation import gettext_lazy as _

from api.users.exceptions import UserNotFound
from apps.users.models import UserLoginLog


class SignInLoggingMixin(LoggingMixin):
    def initial(self, request, *args, **kwargs):
        super(LoggingMixin, self).initial(request, *args, **kwargs)

        user_agent = request.META.get('HTTP_USER_AGENT')
        if user_agent is None:
            user_agent = 'test'
        self.log['user_agent'] = user_agent

    def handle_log(self):
        UserLoginLog(**self.log).save()


class AuthorizingMixin:
    def authorize_request_user(self, request, user):
        if not request.user or request.user.id != user.id:
            raise AuthenticationFailed(detail=_("unauthorized_user"))
        return user
