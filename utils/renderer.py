import json
from rest_framework import renderers
from rest_framework.status import is_success, is_client_error, is_server_error


class ResponseRenderer(renderers.JSONRenderer):
    charset = 'utf-8'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response_context = renderer_context.get('response')
        code = response_context.status_code

        if is_success(code):
            status_msg, data_key = 'success', 'data'
        elif is_client_error(code):
            status_msg, data_key = 'fail', 'fail_case'
        elif is_server_error(code):
            status_msg, data_key = 'error', 'message'
        else:
            status_msg, data_key = 'undefined', 'message'

        return json.dumps({'status': status_msg, data_key: data})
