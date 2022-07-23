import json

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.response import Response

from api.contents.book_object.serializers import BookCreateSerializer, BookObjectSerializer
from utils.naver_api import NaverSearchAPI
from utils.swagger import swagger_response, swagger_schema_with_properties, swagger_schema_with_description, \
    BookObjectFailCaseCollection as book_fail_case, swagger_parameter


class BookView(generics.CreateAPIView):
    serializer_class = BookCreateSerializer

    @swagger_auto_schema(
        operation_id='book_new',
        operation_description='노트 생성을 위한 도서정보를 생성합니다.',
        request_body=swagger_schema_with_properties(
            openapi.TYPE_OBJECT,
            {
                'isbn': swagger_schema_with_description(openapi.TYPE_STRING, '도서 isbn 문자열'),
                'title': swagger_schema_with_description(openapi.TYPE_STRING, '제목'),
                'author': swagger_schema_with_description(openapi.TYPE_STRING, '작가'),
                'publisher': swagger_schema_with_description(openapi.TYPE_STRING, '출판사'),
                'thumbnail': swagger_schema_with_description(openapi.FORMAT_URI, '도서 이미지')
            }
        ),
        responses={
            201: swagger_response(
                description='BOOK_201_NEW',
                schema=serializer_class,
                examples={
                    "id": 1,
                    "isbn": "9788949114118",
                    "created_at": "2022-06-01T03:36:31.725317Z",
                    "updated_at": "2022-06-01T03:36:31.725358Z",
                    "title": "여름이 온다",
                    "author": "이수지",
                    "publisher": "비룡소",
                    "category": {},
                    "thumbnail": "https://bookthumb-phinf.pstatic.net/cover/208/162/20816223.jpg"
                }
            ),
            400:
                book_fail_case.BOOK_400_INVALID_ISBN_NOT_STRING.as_md() +
                book_fail_case.BOOK_400_INVALID_ISBN_WRONG_LENGTH.as_md() +
                book_fail_case.BOOK_400_INVALID_ISBN_FAILED_CHECKSUM.as_md() +
                book_fail_case.BOOK_400_INVALID_ISBN.as_md()
        },
        security=[]
    )
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
    serializer_class = None
    queryset = None

    @swagger_auto_schema(
        operation_id='naver_search',
        operation_description='도서 검색을 수행합니다. parameter로는 검색어 또는 isbn 문자열 중 하나의 값만 전달할 수 있습니다.',
        manual_parameters=[
            swagger_parameter('query', openapi.IN_QUERY, '검색어', openapi.TYPE_STRING),
            swagger_parameter('isbn', openapi.IN_QUERY, 'isbn 문자열', openapi.TYPE_STRING),
            swagger_parameter('display', openapi.IN_QUERY, '검색결과 수', openapi.TYPE_INTEGER),
        ],
        responses={
            200: swagger_response(
                description='BOOK_200_SEARCH',
                examples={
                    "0": {
                        'isbn': '9788949114118',
                        'title': '여름이 온다',
                        'author': '이수지',
                        'publisher': '비룡소',
                        'thumbnail': 'https://bookthumb-phinf.pstatic.net/cover/208/162/20816223.jpg'
                    }
                }
            ),
            204: swagger_response(description='BOOK_204_SEARCH_NO_RESULT')
        },
        security=[]
    )
    def get(self, request, *args, **kwargs):
        param = self.request.GET
        if param is {}:
            return Response(None, status=status.HTTP_204_NO_CONTENT)

        query = param.get('query', '') or param.get('isbn', '')
        display = param.get('display', '')
        result = self.search_class(query, display)

        return Response(result, status=status.HTTP_200_OK)
