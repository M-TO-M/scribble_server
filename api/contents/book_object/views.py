import json

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.response import Response

from django.db.models import Q

from api.contents.book_object.serializers import BookCreateSerializer, BookObjectSerializer, DetailBookListSerializer
from apps.contents.models import BookObject, Note
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


class TaggingBookSearchAPIView(generics.RetrieveAPIView):
    search_class = NaverSearchAPI()
    serializer_class = DetailBookListSerializer
    queryset = BookObject.objects.all()

    def get_params(self, request):
        param = self.request.GET
        if param is {}:
            return None

        q = param.get('query', '') or param.get('isbn', '')
        display = param.get('display', '')

        return q, display

    @swagger_auto_schema(
        operation_id='tagging_book_search',
        operation_description='페이지 생성시 등록할 도서에 대한 검색을 수행합니다.\n\n'
                              'parameter로는 검색어 또는 isbn 문자열 중 하나의 값만 전달할 수 있습니다.\n\n'
                              '두 개의 값을 모두 전달할 경우, 검색어가 우선 적용됩니다.',
        manual_parameters=[
            swagger_parameter('query', openapi.IN_QUERY, '검색어', openapi.TYPE_STRING, required=True),
            swagger_parameter('isbn', openapi.IN_QUERY, 'isbn 문자열', openapi.TYPE_STRING, required=True),
            swagger_parameter('display', openapi.IN_QUERY, '검색결과 수', openapi.TYPE_INTEGER),
        ],
        responses={
            200: swagger_response(
                description='BOOK_200_TAGGING_SEARCH',
                schema=serializer_class,
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
            204: swagger_response(description='BOOK_204_TAGGING_SEARCH_NO_RESULT')
        },
        security=[]
    )
    def get(self, request, *args, **kwargs):
        q, display = self.get_params(request)
        result = self.search_class(q, display)
        if result is None:
            return Response(None, status=status.HTTP_204_NO_CONTENT)

        return Response(result, status=status.HTTP_200_OK)


class NavbarBookSearchAPIView(TaggingBookSearchAPIView):
    @swagger_auto_schema(
        operation_id='navbar_book_search',
        operation_description='네브바에서 모든 도서에 대한 검색을 수행합니다.'
                              '필사된 노트가 많은 책 순으로 정렬한 결과를 리턴합니다.\n\n'
                              'parameter로는 검색어 또는 isbn 문자열 중 하나의 값만 전달할 수 있습니다.\n\n'
                              '두 개의 값을 모두 전달할 경우, 검색어가 우선 적용됩니다.',
        manual_parameters=[
            swagger_parameter('query', openapi.IN_QUERY, '검색어', openapi.TYPE_STRING, required=True),
            swagger_parameter('isbn', openapi.IN_QUERY, 'isbn 문자열', openapi.TYPE_STRING, required=True),
            swagger_parameter('display', openapi.IN_QUERY, '검색결과 수', openapi.TYPE_INTEGER),
        ],
        responses={}
    )
    def get(self, request, *args, **kwargs):
        q, display = self.get_params(request)
        db_search_result = self.queryset.filter(
            Q(title__contains=q) |
            Q(author__contains=q) |
            Q(publisher__contains=q) |
            Q(isbn__exact=q)
        )
        api_search_result = self.search_class(q, display)

        results = self.serializer_class(instance=db_search_result, many=True).data
        db_search_isbn_keys = [re['isbn'] for re in results]
        for api_re in api_search_result:
            if api_re['isbn'] not in db_search_isbn_keys:
                results.append(api_re)

        if results is None:
            return Response(None, status=status.HTTP_204_NO_CONTENT)

        # TODO: async
        for result in results:
            note_cnt = Note.objects.filter(book__isbn__exact=result['isbn']).count()
            result.update({'note_cnt': note_cnt})
        results.sort(key=lambda x: x['note_cnt'], reverse=True)

        return Response(results, status=status.HTTP_200_OK)
