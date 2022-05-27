from rest_framework import generics

from core.pagination import MainViewPagination


class TemplateMainView(generics.ListAPIView):
    pagination_class = MainViewPagination

    def filter_data(self, params: dict, data: list):
        mode = params.get('mode', '')
        if mode == "hit":
            sort_key = mode
        elif mode == "likes" or mode == "reviews":
            sort_key = mode + "_count"
        else:
            return data

        sorting = params.get('sorting', '')
        if sorting == 'descending':
            data.sort(key=lambda x: x[sort_key], reverse=True)
        else:
            data.sort(key=lambda x: x[sort_key])

        return data

    def get_paginated_data(self, queryset):
        pagination = self.paginate_queryset(queryset)
        serializer = self.serializer_class(instance=pagination or queryset, many=True)
        filtered_data = self.filter_data(self.request.query_params, serializer.data)

        return filtered_data
