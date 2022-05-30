from faker import Faker
from faker.providers.isbn import Provider

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient, APITestCase

from .factories import BookObjectFactory
from core.validators import ISBNValidator
from utils.naver_api import NaverSearchAPI


class BookObjectTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.book = BookObjectFactory.create()

        self.test_isbn = "9791166832598"
        self.url_prefix = "http://127.0.0.1:8000/api/contents/book/"
        self.naver_api = NaverSearchAPI()

    def test_given_empty_param_for_naver_api_expect_no_content(self):
        result = self.naver_api('')
        self.assertEqual(result, None)

    def test_given_param_for_naver_api_search_expect_search_result(self):
        result = self.naver_api('search_query')   # TODO: random string test
        if result:
            for field_name in result[0].keys():
                self.assertTrue(field_name, ['isbn', 'title', 'author', 'publisher', 'thumbnail'])

    def test_given_valid_search_result_expect_book_new_success(self):
        base_url = self.url_prefix + "new"
        search_result = self.naver_api('search_query')

        if search_result:
            for result in search_result.values():
                try:
                    ISBNValidator(result['isbn'])
                    response = self.client.post(path=base_url, data=result, format='json')
                    self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                    self.assertEqual(response.data["book"]["isbn"], result["isbn"])
                except ValidationError:
                    pass

    def test_valid_isbn_expect_book_new_success(self):
        base_url = self.url_prefix + "new"
        data = {
            "isbn": self.test_isbn,
            "title": "book_title",
            "author": "book_author",
            "publisher": "book_publisher"[:7],
            "thumbnail": Faker().image_url()
        }

        response = self.client.post(path=base_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["book"]["isbn"], data["isbn"])

    def test_given_registered_isbn_expect_book_new_success(self):
        base_url = self.url_prefix + "new"
        data = {
            "isbn": self.book.isbn,
            "title": "book_title",
            "author": "book_author",
            "publisher": "publish",
            "thumbnail": Faker().image_url()
        }

        response = self.client.post(path=base_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["book"]["isbn"], data["isbn"])

    def test_invalid_isbn_expect_book_new_fail(self):
        base_url = self.url_prefix + "new"
        data = {
            "isbn": Provider(generator=Faker()).isbn13(separator='')[1:],
            "title": "book_title",
            "author": "book_author",
            "publisher": "book_publisher",
            "thumbnail": Faker().image_url()
        }

        response = self.client.post(path=base_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(
            'invalid_isbn_not_string' or 'invalid_isbn_wrong_length' or 'invalid_isbn_failed_checksum'
            in response.data
        )
