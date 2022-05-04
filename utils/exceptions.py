from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response

    code, data = response.status_code, response.data
    if isinstance(data, dict):
        _data = [
            str(val[0]) if isinstance(val, list) else str(val)
            for val in data.values()
        ]
    elif isinstance(data, list):
        _data = [str(val) for val in data]
    else:
        _data = data

    response.data = _data
    return response


class UserNotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = _('no_exist_user')
    default_code = 'not_found'
