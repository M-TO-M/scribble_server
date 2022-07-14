from collections import OrderedDict

from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response


class MainViewPagination(LimitOffsetPagination):
    default_limit = 4
    limit_query_param = 'limit'
    offset_query_param = 'offset'
    data_key = 'results'

    def get_next_offset(self):
        if self.offset + self.limit >= self.count:
            return None
        return self.offset + self.limit

    def get_previous_offset(self):
        if self.offset <= 0:
            return None
        return max(self.offset - self.limit, 0)

    def get_paginated_response(self, data, **kwargs):
        response = OrderedDict([
            ('count', self.count),
            ('previous_offset', self.get_previous_offset()),
            ('next_offset', self.get_next_offset()),
            (self.data_key, data)
        ])
        response.update(kwargs)

        return Response(response)
