from factory import fuzzy

from rest_framework import status

from apps.contents.tests.page.factories import NoteFactory, PageFactory
from apps.contents.tests.page_comment.factories import PageCommentFactory

from apps.users.tests.user.factories import UserFactory
from apps.users.tests.user.test_case import UserTestCase


class PageCommentTestCase(UserTestCase):
    def setUp(self):
        super(PageCommentTestCase, self).setUp()
        self.url_prefix = "http://127.0.0.1:8000/api/contents/page_comments/"

    def test_with_no_page_comment_pk_in_url_expect_page_comment_fail(self):
        base_url = self.url_prefix

        response = self.client.get(path=base_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_with_page_comment_pk_in_url_expect_page_comment_success(self):
        page_comment = PageCommentFactory.create()
        base_url = self.url_prefix + str(page_comment.id)

        response = self.client.get(path=base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(page_comment.id, response.data['page_comment']['id'])

    def test_given_no_exist_page_expect_page_comment_new_fail(self):
        base_url = self.url_prefix + "new"
        data = {
            "page": 1,
            "content": fuzzy.FuzzyText().fuzz()
        }

        response = self.client.post(path=base_url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue("no_exist_page" in response.data)

    def test_given_exist_page_and_default_parent_expect_page_comment_new_success(self):
        page = PageFactory.create()
        base_url = self.url_prefix + "new"
        data = {
            "page": int(page.id),
            "content": fuzzy.FuzzyText().fuzz()
        }

        response = self.client.post(path=base_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(page.id, response.data["page_comment"]["page_id"])
        self.assertEqual(0, response.data["page_comment"]["depth"])
        self.assertEqual(0, response.data["page_comment"]["parent"])

    def test_given_exist_page_and_no_exist_parent_comment_expect_page_comment_new_fail(self):
        page = PageFactory.create()
        base_url = self.url_prefix + "new"
        data = {
            "page": int(page.id),
            "parent": 100,
            "content": fuzzy.FuzzyText().fuzz()
        }

        response = self.client.post(path=base_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue("no_exist_parent_comment" in response.data)

    def test_given_exist_page_and_exist_but_invalid_parent_comment_expect_page_comment_new_fail(self):
        page = PageFactory.create()
        page_comment = PageCommentFactory.create(page=PageFactory.create())
        base_url = self.url_prefix + "new"
        data = {
            "page": int(page.id),
            "parent": int(page_comment.id),
            "content": fuzzy.FuzzyText().fuzz()
        }

        response = self.client.post(path=base_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("invalid_parent_comment_pk" in response.data)

    def test_given_exist_page_and_exist_and_valid_parent_comment_expect_page_comment_new_success(self):
        page = PageFactory.create()
        page_comment = PageCommentFactory.create(page=page)
        base_url = self.url_prefix + "new"
        data = {
            "page": int(page.id),
            "parent": int(page_comment.id),
            "content": fuzzy.FuzzyText().fuzz()
        }

        response = self.client.post(path=base_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(page.id, response.data["page_comment"]["page_id"])
        self.assertEqual(page_comment.depth + 1, response.data["page_comment"]["depth"])
        self.assertEqual(page_comment.id, response.data["page_comment"]["parent"]["id"])

    def test_given_no_exist_page_comment_pk_expect_page_comment_edit_fail(self):
        base_url = self.url_prefix + str(1) + "/edit"

        response = self.client.patch(path=base_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue("no_exist_page_comment" in response.data)

    def test_given_exist_page_comment_pk_with_unauthorized_user_expect_page_comment_edit_fail(self):
        new_user = UserFactory.create()
        page_comment = PageCommentFactory.create(page__note__user=new_user)
        base_url = self.url_prefix + str(page_comment.id) + "/edit"
        data = {"content": "new_content"}

        response = self.client.patch(path=base_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue("unauthorized_user" in response.data)

    def test_given_exist_page_comment_pk_with_authorized_user_expect_page_comment_edit_success(self):
        page_comment = PageCommentFactory.create(comment_user=self.user)
        base_url = self.url_prefix + str(page_comment.id) + "/edit"
        data = {"content": "new_content"}

        response = self.client.patch(path=base_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(data["content"], response.data["page_comment"]["content"])

    def test_given_no_exist_page_comment_pk_expect_page_comment_delete_fail(self):
        base_url = self.url_prefix + str(1) + "/delete"

        response = self.client.delete(path=base_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue("no_exist_page_comment" in response.data)

    def test_given_exist_page_comment_pk_with_unauthorized_user_expect_page_comment_delete_fail(self):
        new_user = UserFactory.create()
        page_comment = PageCommentFactory.create(page__note__user=new_user)
        base_url = self.url_prefix + str(page_comment.id) + "/delete"

        response = self.client.delete(path=base_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue("unauthorized_user" in response.data)

    def test_given_exist_page_comment_pk_with_authorized_user_expect_page_comment_delete_success(self):
        page_comment = PageCommentFactory.create(comment_user=self.user)
        base_url = self.url_prefix + str(page_comment.id) + "/delete"

        response = self.client.delete(path=base_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

