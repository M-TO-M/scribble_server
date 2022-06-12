import re
import json
from typing import Union
from urllib import request, parse

from rest_framework.exceptions import ValidationError
from core.validators import ISBNValidator
from scribble.settings import NAVER_API_CLIENT_ID, NAVER_API_CLIENT_SECRET


class NaverSearchAPI:
    default_display = 5

    def __init__(self, display=None):
        self.isbn_url = "https://openapi.naver.com/v1/search/book_adv?d_isbn="
        self.query_url = "https://openapi.naver.com/v1/search/book.json?query="

        if display is None:
            self.display = self.default_display

        self.items = {
            'query': lambda x: self.search_book_with_params(param=x, display=self.display),
            'isbn': lambda x: self.search_book_with_isbn_value(isbn=x)
        }

    def __call__(self, param, display=None):
        if display:
            self.display = display

        option = 'isbn'
        try:
            ISBNValidator(param)
        except ValidationError:
            option = 'query'
        finally:
            _item = self.items[option](param)

        return self.custom_search_result_data(_item) if _item else None

    @staticmethod
    def custom_search_result_data(items):
        result = []
        for i, item in enumerate(items):
            result.append({
                "isbn": re.sub('<.+?>', '', item["isbn"]).rsplit(" ", 1)[1],
                "title": re.sub('<.+?>', '', item["title"]),
                "author": re.sub('<.+?>', '', item["author"]),
                "publisher": re.sub('<.+?>', '', item["publisher"]),
                "thumbnail": item["image"].rsplit("?", 1)[0]
            })

        return result

    def send_request(self, req_url) -> Union[dict, None]:
        req = request.Request(url=req_url)
        req.add_header("X-Naver-Client-Id", NAVER_API_CLIENT_ID)
        req.add_header("X-Naver-Client-Secret", NAVER_API_CLIENT_SECRET)

        response = request.urlopen(req)

        res_code = response.getcode()
        if res_code != 200:
            raise ValidationError("invalid_response")

        res_body = response.read().decode('utf-8')
        data = json.loads(res_body)
        return data['items'] if 'items' in data else None

    def search_book_with_params(self, param, display) -> Union[dict, None]:
        if param == '':
            return None

        query_params = parse.quote(param)
        req_url = self.query_url + query_params + "&display=" + str(display)
        return self.send_request(req_url=req_url)

    def search_book_with_isbn_value(self, isbn) -> Union[dict, None]:
        if isbn == '':
            return None

        req_url = self.isbn_url + parse.quote('{}'.format(isbn))
        result = self.send_request(req_url=req_url)
        if len(result) > 1:
            raise ValidationError("invalid_result")

        return result
