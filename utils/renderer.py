import json
from rest_framework import renderers
from rest_framework.status import is_success, is_client_error, is_server_error


class ResponseRenderer(renderers.JSONRenderer):
    charset = 'utf-8'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response_context = renderer_context.get('response')
        code = response_context.status_code

        response_case = {
            'success': is_success(code),
            'fail': is_client_error(code),
            'error': is_server_error(code)
        }

        renderer = 'success', 'data' if response_case['success'] \
            else 'fail', 'fail_case' if response_case['fail'] \
            else 'error', 'message' if response_case['error'] \
            else 'undefined', 'message'

        return json.dumps({'status': renderer[0], renderer[1]: data})
