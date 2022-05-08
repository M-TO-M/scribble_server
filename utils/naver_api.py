import re
import json
from urllib import request, parse

from rest_framework.exceptions import ValidationError
from scribble.settings import NAVER_API_CLIENT_ID, NAVER_API_CLIENT_SECRET


class NaverSearchAPI:
    default_display = 5

    def __init__(self, display=None):
        self.url = "https://openapi.naver.com/v1/search/book.json?query="
        if display is None:
            self.display = self.default_display

    def __call__(self, param):
        items = self.search_book_with_params(param=param, display=self.display)
        return self.custom_search_result_data(items) if items else None

    @staticmethod
    def custom_search_result_data(items):
        result = {}
        for i, item in enumerate(items):
            result[i] = {
                "isbn": re.sub('<.+?>', '', item["isbn"]).rsplit(" ", 1)[1],
                "title": re.sub('<.+?>', '', item["title"]),
                "author": re.sub('<.+?>', '', item["author"]),
                "publisher": re.sub('<.+?>', '', item["publisher"]),
                "thumbnail": item["image"].rsplit("?", 1)[0]
            }

        return result

    def search_book_with_params(self, param, display):
        query_params = parse.quote('{}'.format(param))
        req_url = self.url + query_params + "?display=" + str(display)
        if param == '':
            return None

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
