from factory import fuzzy
from faker import Faker

from rest_framework import status

from .factories import NoteFactory, PageFactory, UserFactory
from .test_user import UserTestCase


class PageTestCase(UserTestCase):
    def setUp(self):
        super(PageTestCase, self).setUp()
        self.url_prefix = "http://127.0.0.1:8000/v1/contents/pages/"

        self.test_isbn = "9791166832598"
        self.test_page_data = [
            {
                "transcript": Faker().image_url(),
                "phrase": fuzzy.FuzzyText().fuzz()
            },
            {
                "transcript": Faker().image_url(),
                "phrase": fuzzy.FuzzyText().fuzz()
            },
            {
                "transcript": Faker().image_url(),
                "phrase": fuzzy.FuzzyText().fuzz()
            }
        ]

    def test_given_no_exist_note_and_invalid_isbn_expect_page_new_fail(self):
        base_url = self.url_prefix + "new"
        data = {"note": False, "book_isbn": self.test_isbn[1:], "pages": self.test_page_data}

        response = self.client.post(path=base_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("invalid_isbn" in response.data)

    def test_given_no_exist_note_but_valid_isbn_expect_page_new_success(self):
        base_url = self.url_prefix + "new"
        data = {"note": False, "book_isbn": self.test_isbn, "pages": self.test_page_data}

        response = self.client.post(path=base_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(self.test_page_data), len(response.data['pages']))

    def test_given_exist_note_expect_page_new_success(self):
        base_url = self.url_prefix + "new"
        note = NoteFactory.create(user=self.user)
        data = {"note": True, "note_pk": note.pk, "pages": self.test_page_data}

        response = self.client.post(path=base_url, data=data, format='json')
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(self.test_page_data), len(response.data['pages']))

    def test_given_no_page_pk_in_url_expect_page_view_fail(self):
        base_url = self.url_prefix

        response = self.client.get(path=base_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_given_no_exist_page_pk_in_url_expect_page_view_fail(self):
        base_url = self.url_prefix + str(1)

        response = self.client.get(path=base_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue("no_exist_page" in response.data)

    def test_given_exist_page_pk_in_url_expect_page_view_success(self):
        note = NoteFactory.create()
        page = PageFactory.create(note=note)
        base_url = self.url_prefix + str(page.id)

        response = self.client.get(path=base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(page.id, response.data["page_detail"]["id"])

    def test_given_no_exist_page_pk_expect_page_edit_fail(self):
        base_url = self.url_prefix + str(1) + "/edit"

        response = self.client.patch(path=base_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue("no_exist_page" in response.data)

    def test_given_exist_page_pk_with_unauthorized_user_expect_page_edit_fail(self):
        new_user = UserFactory.create()
        page = PageFactory.create(note__user=new_user)
        base_url = self.url_prefix + str(page.id) + "/edit"

        response = self.client.patch(path=base_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue("unauthorized_user" in response.data)

    def test_given_exist_page_pk_with_authorized_user_expect_page_edit_success(self):
        page = PageFactory.create(note__user=self.user)
        base_url = self.url_prefix + str(page.id) + "/edit"
        data = {"transcript": Faker().image_url(), "phrase": fuzzy.FuzzyText().fuzz()}

        response = self.client.patch(path=base_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(page.id, response.data["page"]["id"])
        self.assertEqual(page.note.id, response.data["note"]["id"])
        self.assertEqual(data["transcript"], response.data["page"]["transcript"])
        self.assertEqual(data["phrase"], response.data["page"]["phrase"])

    def test_given_no_exist_page_pk_expect_page_delete_fail(self):
        base_url = self.url_prefix + str(1) + "/delete"

        response = self.client.delete(path=base_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue("no_exist_page" in response.data)

    def test_given_exist_page_pk_with_unauthorized_user_expect_page_delete_fail(self):
        new_user = UserFactory.create()
        page = PageFactory.create(note__user=new_user)
        base_url = self.url_prefix + str(page.id) + "/delete"

        response = self.client.delete(path=base_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue("unauthorized_user" in response.data)

    def test_given_exist_page_pk_with_authorized_user_expect_page_delete_success(self):
        page = PageFactory.create(note__user=self.user)
        base_url = self.url_prefix + str(page.id) + "/delete"

        response = self.client.delete(path=base_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
