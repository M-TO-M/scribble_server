import json

from rest_framework import generics, mixins, status
from rest_framework.response import Response

from api.contents.serializers import *


class BookView(generics.CreateAPIView):
    serializer_class = BookObjectSerializer

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        book_object_serializer = self.serializer_class(data=data)
        book_object_serializer.is_valid(raise_exception=True)
        self.perform_create(book_object_serializer)

        response = {
            "book": book_object_serializer.validated_data
        }
        return Response(response, status=status.HTTP_201_CREATED)
