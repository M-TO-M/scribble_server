import re
import json
from typing import Union, Tuple
from urllib import request, parse

from rest_framework.exceptions import ValidationError
from core.validators import ISBNValidator
from scribble.settings.base import NAVER_API_CLIENT_ID, NAVER_API_CLIENT_SECRET


class NaverSearchAPI:
    default_display = 20
    isbn_url = "https://openapi.naver.com/v1/search/book_adv?sort=sim&d_isbn="
    title_url = "https://openapi.naver.com/v1/search/book_adv?sort=sim&d_titl="
    query_url = "https://openapi.naver.com/v1/search/book.json?query="

    def __call__(self, param, display=None):
        self.display = display or self.default_display
        items, search_type = self.search(param)
        return search_type, self.resp(items)

    @staticmethod
    def resp(items):
        result = []
        for i, item in enumerate(items):
            isbn = re.sub('<.+?>', '', item["isbn"]).rsplit(" ", 1)
            result.append({
                "isbn": isbn[1] if len(isbn) > 1 else isbn[0],
                "title": re.sub('<.+?>', '', item["title"]).replace('^', ', '),
                "author": re.sub('<.+?>', '', item["author"]).replace('^', ', '),
                "publisher": re.sub('<.+?>', '', item["publisher"]).replace('^', ', '),
                "thumbnail": item["image"].rsplit("?", 1)[0]
            })

        return result

    @staticmethod
    def send_request(req_url) -> Union[dict, None]:
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

    def search(self, param: str) -> Union[Tuple[dict, str], None]:
        if bool(not param or param.isspace()):
            return None
        try:
            ISBNValidator(param)
            url = self.isbn_url + parse.quote('{}'.format(param))
            resp = self.send_request(req_url=url)
            if len(resp) > 1:
                raise ValidationError("invalid_result")
            return resp, 'isbn'
        except ValidationError:
            param = parse.quote(param)
            # 도서 제목으로 우선검색. 결과가 적거나 없는 경우 query paramter로 재검색 수행
            url = self.title_url + param + "&display=" + str(self.display)
            resp = self.send_request(req_url=url)
            if len(resp) > 5:
                return resp, 'title'
            url = self.query_url + param + "&display=" + str(self.display)
            resp = self.send_request(req_url=url)
            return resp, 'author_pubilsher'
