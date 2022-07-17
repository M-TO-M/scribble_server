from collections import defaultdict

from drf_yasg import openapi
from drf_yasg.generators import OpenAPISchemaGenerator

from rest_framework import status


class ScribbleOpenAPISchemaGenerator(OpenAPISchemaGenerator):
    def get_endpoints(self, request):
        enumerator = self.endpoint_enumerator_class(self._gen.patterns, self._gen.urlconf, request=request)
        endpoints = enumerator.get_api_endpoints()

        view_paths = defaultdict(list)
        view_cls = {}

        for path, method, callback in endpoints:
            http_method_names = callback.view_initkwargs.get('http_method_names')
            if http_method_names and method.lower() != http_method_names[0]:
                continue

            view = self.create_view(callback, method, request)
            path = self.coerce_path(path, view)
            view_paths[path].append((method, view))
            view_cls[path] = callback.cls

        return {path: (view_cls[path], methods) for path, methods in view_paths.items()}


user_response_example = {
    "id": 1,
    "email": "test@naver.com",
    "password": "pbkdf2_sha256$320000$9fPcOoSTXi4XGZHCvAX5L4$LY44j0p+vEp8FvJdFBPqWMhIwj52bur+MKefaDYRJgk=",
    "nickname": "nickname",
    "category": {
        "9": "과학"
    },
    "profile_image": "https://placekitten.com/101/37",
    "created_at": "2022-06-01T01:48:27.252426Z",
    "updated_at": "2022-06-01T01:48:27.252439Z"
}

user_response_example_with_access = {
    "id": 1,
    "email": "user@email.com",
    "password": "password",
    "nickname": "user_nickname",
    "category": {
        "9": "과학"
    },
    "profile_image": "https://placekitten.com/101/37",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXB.."
}

note_response_example = {
    'note': {
        'id': 1,
        'note_author': {
            "id": 1,
            "email": "test@naver.com",
            "password": "pbkdf2_sha256$320000$9fPcOoSTXi4XGZHCvAX5L4$LY44j0p+vEp8FvJdFBPqWMhIwj52bur+MKefaDYRJgk=",
            "nickname": "nickname",
            "category": {
                "9": "과학"
            },
            "profile_image": "https://placekitten.com/101/37",
            "created_at": "2022-06-01T01:48:27.252426Z",
            "updated_at": "2022-06-01T01:48:27.252439Z"
        },
        'book': {
            'id': 1,
            'isbn': '9791166832598',
            'created_at': '2022-06-01T03:42:31.404789Z',
            'updated_at': '2022-06-01T03:42:31.404808Z',
            'title': 'title_0',
            'author': 'author_0',
            'publisher': 'publisher_0',
            'category': {},
            'thumbnail': 'https://placekitten.com/38/611'
        },
        'like_count': 0,
        'like_user': [],
        'hit': 0,
        'pages_count': 0
    }
}

note_detail_response_example = {
    'note': {
        'id': 1,
        'note_author': {
            "id": 1,
            "email": "test@naver.com",
            "password": "pbkdf2_sha256$320000$9fPcOoSTXi4XGZHCvAX5L4$LY44j0p+vEp8FvJdFBPqWMhIwj52bur+MKefaDYRJgk=",
            "nickname": "nickname",
            "category": {
                "9": "과학"
            },
            "profile_image": "https://placekitten.com/101/37",
            "created_at": "2022-06-01T01:48:27.252426Z",
            "updated_at": "2022-06-01T01:48:27.252439Z"
        },
        'book': {
            'id': 1,
            'isbn': '9791166832598',
            'created_at': '2022-06-01T03:42:31.404789Z',
            'updated_at': '2022-06-01T03:42:31.404808Z',
            'title': 'title_0',
            'author': 'author_0',
            'publisher': 'publisher_0',
            'category': {},
            'thumbnail': 'https://placekitten.com/38/611'
        },
        'like_count': 0,
        'like_user': [],
        'hit': 0,
        'pages_count': 0,
        'pages': []
    }
}

page_response_example = {
    'note': {
        'id': 1,
        'note_author': {
            "id": 1,
            "email": "test@naver.com",
            "password": "pbkdf2_sha256$320000$9fPcOoSTXi4XGZHCvAX5L4$LY44j0p+vEp8FvJdFBPqWMhIwj52bur+MKefaDYRJgk=",
            "nickname": "nickname",
            "category": {
                "9": "과학"
            },
            "profile_image": "https://placekitten.com/101/37",
            "created_at": "2022-06-01T01:48:27.252426Z",
            "updated_at": "2022-06-01T01:48:27.252439Z"
        },
        'like_count': 0,
        'like_user': [],
        'hit': 0,
        'pages_count': 0
    },
    'book': {
        'id': 1,
        'isbn': '9791166832598',
        'created_at': '2022-06-01T03:42:31.404789Z',
        'updated_at': '2022-06-01T03:42:31.404808Z',
        'title': 'title_0',
        'author': 'author_0',
        'publisher': 'publisher_0',
        'category': {},
        'thumbnail': 'https://placekitten.com/38/611'
    },
    'page_detail': {
        'id': 1,
        'note_index': 0,
        'transcript': 'https://placeimg.com/77/365/any',
        'phrase': 'TFlmetrbwdCF',
        'hit': 1,
        'like_count': 0,
        'like_user': [],
        'reviews_count': 0
    }
}

page_comment_response_example = {
    'page_comment': {
        'id': 1,
        'comment_user': 3,
        'depth': 0,
        'parent': 0,
        'content': 'CzGDQozWpJXg',
        'page_id': 1
    }
}

main_response_example = {
    'count': 20,
    'previous_offset': 0,
    'next_offset': 4,
    'pages': [
        page_response_example,
    ],
}

user_main_response_example = {
    "count": 4,
    "previous_offset": 0,
    "next_offset": 0,
    "notes": [
        {
            "id": 1,
            "note_author": {
                "id": 1,
                "email": "test@naver.com",
                "password": "pbkdf2_sha256$320000$o6D1XcTjz4xtNAakuBVgup$QqF/Y0Bow3UKhboF7odffiSkWZYOcwLr8qQ1PKxR97Y=",
                "nickname": "nickname",
                "category": {
                    "9": "과학"
                },
                "profile_image": '',
                "created_at": "2022-06-01T06:38:22.250218Z",
                "updated_at": "2022-06-01T06:38:22.250230Z"
            },
            "book": {
                "id": 1,
                "isbn": "9781061744737",
                "created_at": "2022-06-01T06:44:58.634054Z",
                "updated_at": "2022-06-01T06:44:58.634083Z",
                "title": "title_0",
                "author": "author_0",
                "publisher": "publisher_0",
                "category": {},
                "thumbnail": "https://placekitten.com/479/302"
            },
            "like_count": 0,
            "like_user": [],
            "hit": 0,
            "pages_count": 0
        },
        {
            "id": 2,
            "note_author": {
                "id": 1,
                "email": "test@naver.com",
                "password": "pbkdf2_sha256$320000$o6D1XcTjz4xtNAakuBVgup$QqF/Y0Bow3UKhboF7odffiSkWZYOcwLr8qQ1PKxR97Y=",
                "nickname": "nickname",
                "category": {
                    "9": "과학"
                },
                "profile_image": '',
                "created_at": "2022-06-01T06:38:22.250218Z",
                "updated_at": "2022-06-01T06:38:22.250230Z"
            },
            "book": {
                "id": 2,
                "isbn": "9780725690014",
                "created_at": "2022-06-01T06:44:58.665196Z",
                "updated_at": "2022-06-01T06:44:58.665222Z",
                "title": "title_1",
                "author": "author_1",
                "publisher": "publisher_1",
                "category": {
                    "0": "국내소설"
                },
                "thumbnail": "https://placekitten.com/479/302"
            },
            "like_count": 0,
            "like_user": [],
            "hit": 0,
            "pages_count": 0
        },
        {
            "id": 3,
            "note_author": {
                "id": 1,
                "email": "test@naver.com",
                "password": "pbkdf2_sha256$320000$o6D1XcTjz4xtNAakuBVgup$QqF/Y0Bow3UKhboF7odffiSkWZYOcwLr8qQ1PKxR97Y=",
                "nickname": "nickname",
                "category": {
                    "9": "과학"
                },
                "profile_image": '',
                "created_at": "2022-06-01T06:38:22.250218Z",
                "updated_at": "2022-06-01T06:38:22.250230Z"
            },
            "book": {
                "id": 3,
                "isbn": "9780435085148",
                "created_at": "2022-06-01T06:47:33.377370Z",
                "updated_at": "2022-06-01T06:47:33.377400Z",
                "title": "title_2",
                "author": "author_2",
                "publisher": "publisher_2",
                "category": {
                    "0": "국내소설",
                    "1": "외국소설(유럽,북미등)"
                },
                "thumbnail": "https://placekitten.com/479/302"
            },
            "like_count": 0,
            "like_user": [],
            "hit": 0,
            "pages_count": 0
        },
        {
            "id": 4,
            "note_author": {
                "id": 1,
                "email": "test@naver.com",
                "password": "pbkdf2_sha256$320000$o6D1XcTjz4xtNAakuBVgup$QqF/Y0Bow3UKhboF7odffiSkWZYOcwLr8qQ1PKxR97Y=",
                "nickname": "nickname",
                "category": {
                    "9": "과학"
                },
                "profile_image": '',
                "created_at": "2022-06-01T06:38:22.250218Z",
                "updated_at": "2022-06-01T06:38:22.250230Z"
            },
            "book": {
                "id": 4,
                "isbn": "9780027200669",
                "created_at": "2022-06-01T06:47:33.410286Z",
                "updated_at": "2022-06-01T06:47:33.410313Z",
                "title": "title_3",
                "author": "author_3",
                "publisher": "publisher_3",
                "category": {
                    "0": "국내소설",
                    "1": "외국소설(유럽,북미등)",
                    "2": "외국소설(아시아)"
                },
                "thumbnail": "https://placekitten.com/479/302"
            },
            "like_count": 0,
            "like_user": [],
            "hit": 0,
            "pages_count": 0
        }
    ],
    "user": user_response_example
}

main_book_list_response_example = [
    {
        "note_id": 1,
        "isbn": "9781501923579",
        "datetime": "2022-07-14T13:07:05.350Z"
    },
    {
        "note_id": 2,
        "isbn": "9781088978511",
        "datetime": "2022-07-14T13:07:05.323Z"
    },
    {
        "note_id": 3,
        "isbn": "9780357355565",
        "datetime": "2022-07-14T13:07:05.296Z"
    }
]


def swagger_response(description=None, schema=None, examples=None):
    return openapi.Response(
        description=description,
        schema=schema,
        examples={'application/json': examples}
    )


def swagger_parameter(name, in_, description, type_, pattern=None):
    return openapi.Parameter(
        name=name,
        in_=in_,
        description=description,
        type=type_,
        pattern=pattern
    )


def swagger_schema_with_properties(type_, properties):
    return openapi.Schema(
        type=type_,
        properties=properties
    )


def swagger_schema_with_items(type_, items, description):
    return openapi.Schema(
        type=type_,
        items=items,
        description=description
    )


def swagger_schema_with_description(type_, description):
    return openapi.Schema(
        type=type_,
        description=description
    )


class FailCaseCollection:
    def __init__(self, response_code, status_code, description):
        self.response_code = response_code
        self.status_code = status_code
        self.description = description

    def as_md(self):
        return '\n\n> **%s**\n\n```\n{\n\n\t"code": "%s"\n\n\t"message": "%s"\n\n}\n\n```' % \
               (self.response_code, self.status_code, self.description)


class UserFailCaseCollection:
    USER_404_DOES_NOT_EXIST = FailCaseCollection(
        response_code='no_exist_user',
        status_code=status.HTTP_404_NOT_FOUND,
        description='존재하지 않는 유저입니다.'
    )
    USER_401_UNAUTHORIZED = FailCaseCollection(
        response_code='unauthorized_user',
        status_code=status.HTTP_401_UNAUTHORIZED,
        description='접근이 허가되지 않은 유저입니다.'
    )
    USER_400_VERIFY_EXIST_NICKNAME = FailCaseCollection(
        response_code='exist_nickname',
        status_code=status.HTTP_400_BAD_REQUEST,
        description='이미 존재하는 닉네임입니다.'
    )
    USER_400_VERIFY_EXIST_EMAIL = FailCaseCollection(
        response_code='exist_email',
        status_code=status.HTTP_400_BAD_REQUEST,
        description='이미 등록된 이메일입니다.'
    )
    USER_400_VERIFY_INVALID_DOMAIN = FailCaseCollection(
        response_code='invalid_domain',
        status_code=status.HTTP_400_BAD_REQUEST,
        description='사용할 수 없는 이메일 도메인입니다.'
    )
    USER_400_INVALID_CATEGORY = FailCaseCollection(
        response_code='invalid_category',
        status_code=status.HTTP_400_BAD_REQUEST,
        description='유효하지 않은 카테고리입니다. "category_list"를 참조하세요.'
    )
    USER_400_SIGN_IN_NO_EXIST_EMAIL = FailCaseCollection(
        response_code='no_exist_email',
        status_code=status.HTTP_400_BAD_REQUEST,
        description='존재하지 않는 이메일입니다.'
    )
    USER_400_SIGN_IN_INVALID_PASSWORD = FailCaseCollection(
        response_code='invalid_password',
        status_code=status.HTTP_400_BAD_REQUEST,
        description='잘못된 비밀번호입니다.'
    )
    USER_400_SIGN_OUT_INVALID_REFRESH_TOKEN = FailCaseCollection(
        response_code='invalid_refresh_token',
        status_code=status.HTTP_400_BAD_REQUEST,
        description='잘못된 refresh token입니다. 제거할 수 없습니다.'
    )
    USER_400_EDIT_VALIDATION_ERROR = FailCaseCollection(
        response_code='invalid_user_data',
        status_code=status.HTTP_400_BAD_REQUEST,
        description='유효하지 않은 필드값입니다. 사용자 정보를 수정할 수 없습니다.'
    )
    USER_400_FOLLOW_EXIST_CATEGORY = FailCaseCollection(
        response_code='exist_follow',
        status_code=status.HTTP_400_BAD_REQUEST,
        description='이미 선택한 카테고리입니다.'
    )
    USER_400_FOLLOW_CANCEL_NO_EXIST_CATEGORY = FailCaseCollection(
        response_code='no_exist_follow',
        status_code=status.HTTP_400_BAD_REQUEST,
        description='선택하지 않은 카테고리를 삭제할 수 없습니다.'
    )


class BookObjectFailCaseCollection:
    BOOK_400_INVALID_ISBN_NOT_STRING = FailCaseCollection(
        response_code='invalid_isbn_not_string',
        status_code=status.HTTP_400_BAD_REQUEST,
        description='isbn의 형태가 문자열이 아닙니다.'
    )
    BOOK_400_INVALID_ISBN_WRONG_LENGTH = FailCaseCollection(
        response_code='invalid_isbn_wrong_length',
        status_code=status.HTTP_400_BAD_REQUEST,
        description='잘못된 길이의 isbn 문자열입니다. 13자리 isbn을 입력해주세요.'
    )
    BOOK_400_INVALID_ISBN_FAILED_CHECKSUM = FailCaseCollection(
        response_code='invalid_isbn_failed_checksum',
        status_code=status.HTTP_400_BAD_REQUEST,
        description='유효하지 않은 isbn 값입니다.'
    )
    BOOK_400_INVALID_ISBN = FailCaseCollection(
        response_code='invalid_isbn',
        status_code=status.HTTP_400_BAD_REQUEST,
        description='유효하지 않은 isbn 값입니다.'
    )


class NoteFailCaseCollection:
    NOTE_404_DOES_NOT_EXIST = FailCaseCollection(
        response_code='no_exist_note',
        status_code=status.HTTP_404_NOT_FOUND,
        description='존재하지 않는 노트입니다.'
    )
    NOTE_400_NO_BOOK_INFO_IN_REQUEST_BODY = FailCaseCollection(
        response_code='no_book_in_req_body',
        status_code=status.HTTP_400_BAD_REQUEST,
        description='도서 정보 없이 새로운 노트를 등록할 수 없습니다.'
    )
    NOTE_400_LIKE_EXIST_LIKE_RELATION = FailCaseCollection(
        response_code='exist_like',
        status_code=status.HTTP_400_BAD_REQUEST,
        description='이미 좋아요를 눌렀습니다.'
    )
    NOTE_400_LIKE_CANCEL_NO_EXIST_LIKE_RELATION = FailCaseCollection(
        response_code='no_exist_like',
        status_code=status.HTTP_400_BAD_REQUEST,
        description='취소할 좋아요가 없습니다.'
    )


class PageFailCaseCollection:
    PAGE_404_DOES_NOT_EXIST = FailCaseCollection(
        response_code='no_exist_page',
        status_code=status.HTTP_400_BAD_REQUEST,
        description='존재하지 않는 페이지입니다.'
    )
    PAGE_400_NO_NOTE_PK_IN_REQUEST_BODY = FailCaseCollection(
        response_code='no_note_pk_in_req_body',
        status_code=status.HTTP_400_BAD_REQUEST,
        description='존재하는 노트에 페이지를 추가하는 경우, 노트 id값을 전달해야 합니다.'
    )
    PAGE_400_NO_BOOK_ISBN_IN_REQUEST_BODY = FailCaseCollection(
        response_code='no_book_in_req_body',
        status_code=status.HTTP_400_BAD_REQUEST,
        description='도서 isbn 값 없이 새로운 노트를 등록할 수 없습니다.'
    )
    PAGE_400_EDIT_VALIDATION_ERROR = FailCaseCollection(
        response_code='invalid_page_data',
        status_code=status.HTTP_400_BAD_REQUEST,
        description='유효하지 않은 필드값입니다. 페이지 정보를 수정할 수 없습니다.'
    )
    PAGE_400_LIKE_EXIST_LIKE_RELATION = FailCaseCollection(
        response_code='exist_like',
        status_code=status.HTTP_400_BAD_REQUEST,
        description='이미 좋아요를 눌렀습니다.'
    )
    PAGE_400_LIKE_CANCEL_NO_EXIST_LIKE_RELATION = FailCaseCollection(
        response_code='no_exist_like',
        status_code=status.HTTP_400_BAD_REQUEST,
        description='취소할 좋아요가 없습니다.'
    )


class PageCommentFailCaseCollection:
    PAGE_COMMENT_404_DOES_NOT_EXIST = FailCaseCollection(
        response_code='no_exist_page_comment',
        status_code=status.HTTP_404_NOT_FOUND,
        description='존재하지 않는 페이지 댓글입니다.'
    )
    PAGE_COMMENT_404_PARENT_COMMENT_DOES_NOT_EXIST = FailCaseCollection(
        response_code='no_exist_parent_comment',
        status_code=status.HTTP_404_NOT_FOUND,
        description='존재하지 않는 상위 댓글 id입니다. 대댓글을 작성할 수 없습니다.'
    )
    PAGE_COMMENT_400_INVALID_PARENT_COMMENT = FailCaseCollection(
        response_code='invalid_parent_comment_pk',
        status_code=status.HTTP_400_BAD_REQUEST,
        description='댓글을 달 페이지에 존재하는 상위 댓글이 아닙니다. 대댓글을 작성할 수 없습니다.'
    )
    PAGE_COMMENT_400_NO_PAGE_PK_IN_REQUEST_BODY = FailCaseCollection(
        response_code='no_page_pk_in_body',
        status_code=status.HTTP_400_BAD_REQUEST,
        description='페이지 id값 없이 댓글을 생성할 수 없습니다.'
    )
    PAGE_COMMENT_400_EDIT_VALIDATION_ERROR = FailCaseCollection(
        response_code='invalid_page_comment_data',
        status_code=status.HTTP_400_BAD_REQUEST,
        description='유효하지 않은 필드값입니다. 페이지 댓글 정보를 수정할 수 없습니다.'
    )
