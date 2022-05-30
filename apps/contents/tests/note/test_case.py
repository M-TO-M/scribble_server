from faker import Faker
from faker.providers.isbn import Provider

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from core.serializers import ScribbleTokenObtainPairSerializer
from .factories import NoteFactory, NoteLikesRelationFactory
from apps.contents.tests.book_object.factories import BookObjectFactory
from apps.users.tests.user.factories import UserFactory


class NoteTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory.create()
        self.set_credentials()

        self.url_prefix = "http://127.0.0.1:8000/api/contents/notes/"

    def tearDown(self):
        super(NoteTestCase, self).tearDown()

    def set_credentials(self):
        token = ScribbleTokenObtainPairSerializer.get_token(self.user)

        self.access = str(token.access_token)
        self.refresh = str(token)

        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.access}'
        )

    def test_with_no_note_pk_in_url_expect_note_view_fail(self):
        base_url = self.url_prefix

        response = self.client.get(path=base_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_with_single_note_object_expect_note_view_success(self):
        note = NoteFactory.create()
        base_url = self.url_prefix + str(note.id)

        response = self.client.get(path=base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(note.id, response.data['note']['id'])
        self.assertEqual(note.user.id, response.data['note']['note_author']['id'])
        self.assertEqual(note.book.id, response.data['note']['book']['id'])

    def test_with_no_exist_note_object_expect_note_view_fail(self):
        base_url = self.url_prefix + str(1)

        response = self.client.get(path=base_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue("no_exist_note" in response.data)

    def test_given_empty_data_expect_note_new_fail(self):
        base_url = self.url_prefix + "new"

        response = self.client.post(path=base_url, data=None, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('no_book_in_req_body' in response.data)

    def test_given_no_exist_book_with_valid_isbn_expect_note_new_success(self):
        base_url = self.url_prefix + "new"
        test_isbn_value = "9791166832598"
        data = {"book_isbn": test_isbn_value}

        response = self.client.post(path=base_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.user.id, response.data['note']['note_author']['id'])
        self.assertEqual(test_isbn_value, response.data['note']['book']['isbn'])

    def test_given_exist_book_with_valid_isbn_expect_note_new_success(self):
        base_url = self.url_prefix + "new"
        book = BookObjectFactory.create(isbn="9791166832598")
        data = {"book_isbn": book.isbn}

        response = self.client.post(path=base_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.user.id, response.data['note']['note_author']['id'])
        self.assertEqual(book.isbn, response.data['note']['book']['isbn'])

    def test_given_no_exist_book_with_invalid_isbn_expect_note_new_fail(self):
        base_url = self.url_prefix + "new"
        book = BookObjectFactory.create()
        data = {"book_isbn": book.isbn[1:]}

        response = self.client.post(path=base_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('invalid_isbn' in response.data)

    def test_with_no_exist_note_expect_note_delete_fail(self):
        base_url = self.url_prefix + str(1) + "/delete"

        response = self.client.delete(path=base_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue('no_exist_note' in response.data)

    def test_with_unauthorized_user_expect_user_delete_fail(self):
        user = UserFactory.create()
        note = NoteFactory.create(user=user)

        base_url = self.url_prefix + str(note.id) + "/delete"
        print(base_url)
        response = self.client.delete(path=base_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue('unauthorized_user' in response.data)

    def test_with_authorized_user_expect_user_delete_success(self):
        note = NoteFactory.create(user=self.user)

        base_url = self.url_prefix + str(note.id) + "/delete"
        response = self.client.delete(path=base_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_view_note_by_author_expect_note_hit_unchanged(self):
        note = NoteFactory.create(user=self.user)
        base_url = self.url_prefix + str(note.id)

        response = self.client.get(path=base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(note.id, response.data['note']['id'])
        self.assertEqual(note.hit, response.data['note']['hit'])

    def test_view_note_by_other_user_expect_note_hit_changed(self):
        new_user = UserFactory.create()
        note = NoteFactory.create(user=new_user)
        base_url = self.url_prefix + str(note.id)

        response = self.client.get(path=base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(note.id, response.data['note']['id'])
        self.assertEqual(note.hit + 1, response.data['note']['hit'])

    def test_with_no_exist_like_relation_expect_note_like_success(self):
        note_with_self_user = NoteFactory.create(user=self.user)
        url = self.url_prefix + str(note_with_self_user.id) + "/like"

        response = self.client.post(path=url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(note_with_self_user.note_likes_relation.count(), response.data['note']['like_count'])

        new_user = UserFactory.create()
        note_with_other_user = NoteFactory.create(user=new_user)
        new_url = self.url_prefix + str(note_with_other_user.id) + "/like"

        response = self.client.post(path=new_url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(note_with_other_user.note_likes_relation.count(), response.data['note']['like_count'])

    def test_with_no_exist_like_relation_expect_note_like_cancel_fail(self):
        note_with_self_user = NoteFactory.create(user=self.user)
        url = self.url_prefix + str(note_with_self_user.id) + "/like/cancel"

        response = self.client.delete(path=url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("no_exist_like" in response.data)

        new_user = UserFactory.create()
        note_with_other_user = NoteFactory.create(user=new_user)
        new_url = self.url_prefix + str(note_with_other_user.id) + "/like/cancel"

        response = self.client.delete(path=new_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("no_exist_like" in response.data)

    def test_with_exist_like_relation_expect_note_like_fail(self):
        note_with_self_user = NoteFactory.create(user=self.user)
        NoteLikesRelationFactory.create(like_user=self.user, note=note_with_self_user)

        url_1 = self.url_prefix + str(note_with_self_user.id) + "/like"
        response = self.client.post(path=url_1)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("exist_like" in response.data)

        new_user = UserFactory.create()
        note_user_with_other_user = NoteFactory.create(user=new_user)
        NoteLikesRelationFactory.create(like_user=self.user, note=note_user_with_other_user)

        url_2 = self.url_prefix + str(note_user_with_other_user.id) + "/like"
        response = self.client.post(path=url_2)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("exist_like" in response.data)

    def test_with_exist_like_relation_expect_note_like_cancel_success(self):
        note_with_self_user = NoteFactory.create(user=self.user)
        NoteLikesRelationFactory.create(like_user=self.user, note=note_with_self_user)

        url_1 = self.url_prefix + str(note_with_self_user.id) + "/like/cancel"
        response = self.client.delete(path=url_1)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        new_user = UserFactory.create()
        note_user_with_other_user = NoteFactory.create(user=new_user)
        NoteLikesRelationFactory.create(like_user=self.user, note=note_user_with_other_user)

        url_2 = self.url_prefix + str(note_user_with_other_user.id) + "/like/cancel"
        response = self.client.delete(path=url_2)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
