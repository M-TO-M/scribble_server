from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.exceptions import APIException


class NoteNotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = _('no_exist_note')
    default_code = 'not_found'


class PageNotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = _('no_exist_page')
    default_code = 'not_found'


class PageCommentNotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = _('no_exist_page_comment')
    default_code = 'not_found'
