import math

from rest_framework.exceptions import Throttled
from rest_framework.views import exception_handler


fail_case_key = ['detail', 'email', 'nickname', 'category', 'isbn']


def _get_custom_response_data(data):
    if isinstance(data, str):
        return str(data)

    result = []
    if isinstance(data, list):
        result += [str(val) for val in data]
    elif isinstance(data, dict):
        for k, v in data.items():
            sub_data = _get_custom_response_data(v)
            if k not in fail_case_key:
                result.append({k: sub_data})
            else:
                if isinstance(sub_data, list):
                    result.extend(sub_data)
                elif isinstance(sub_data, str):
                    result.append(sub_data)
    else:
        return None

    return result


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response

    if isinstance(exc, Throttled):
        wait = math.ceil(exc.wait) if exc.wait else exc.wait
        response.data = {"detail": "throttled", "wait": wait}
        return response

    code, data = response.status_code, response.data
    response.data = _get_custom_response_data(data)

    return response
