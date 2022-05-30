import json

from rest_framework import generics, status
from rest_framework.response import Response

from api.contents.book_object.serializers import BookCreateSerializer, BookObjectSerializer


class BookView(generics.CreateAPIView):
    serializer_class = BookCreateSerializer

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        book_create_serializer = self.serializer_class()
        book = book_create_serializer.create(validated_data=data)

        response = {
            "book": BookObjectSerializer(instance=book).data
        }
        return Response(response, status=status.HTTP_201_CREATED)
