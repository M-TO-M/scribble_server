import json

from rest_framework import generics, status
from rest_framework.response import Response

from api.contents.book_object.serializers import BookCreateSerializer, BookObjectSerializer
from utils.naver_api import NaverSearchAPI


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


class NaverSearchAPIView(generics.RetrieveAPIView):
    search_class = NaverSearchAPI()

    def retrieve(self, request, *args, **kwargs):
        param = self.request.GET
        if param is {}:
            return Response(None, status=status.HTTP_204_NO_CONTENT)

        query = param.get('query', '') or param.get('isbn', '')
        result = self.search_class(query)

        return Response(result, status=status.HTTP_200_OK)
