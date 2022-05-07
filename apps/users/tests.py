
import random

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from .models import category_choices
from .factories import UserFactory
from core.serializers import ScribbleTokenObtainPairSerializer


class UserTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin = UserFactory.create(is_staff=True, is_superuser=True)
        self.user = UserFactory.create()
        self.set_credentials()

        self.url_prefix = "http://127.0.0.1:8000/api/users/"
        self.base_url = {
            "verify": self.url_prefix + "verify",
            "verify_nickname": self.url_prefix + "verify?nickname=",
            "verify_email": self.url_prefix + "verify?email=",
            "signup": self.url_prefix + "new",
            "signin": self.url_prefix + "signin",
            "signout": self.url_prefix + "signout",
            "category_update": self.url_prefix + "category",
            "follow_category": self.url_prefix + "category?event=follow",
            "unfollow_category": self.url_prefix + "category?event=unfollow"
        }

    def tearDown(self):
        super(UserTestCase, self).tearDown()

    def set_credentials(self):
        token = ScribbleTokenObtainPairSerializer.get_token(self.user)

        self.access = str(token.access_token)
        self.refresh = str(token)

        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.access}'
        )

    @classmethod
    def pick_rand_category_item(cls, item_dict) -> dict:
        key, value = random.choice(list(item_dict.items()))
        return {key: value}

    def test_user_verify_empty_data(self):
        response = self.client.get(path=self.base_url['verify'])
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_user_verify_exist_nickname(self):
        query_url = self.base_url['verify_nickname'] + str(self.user.nickname)

        response = self.client.get(path=query_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("exist_nickname" in response.data)

    def test_user_verify_dummy_nickname(self):
        query_url = self.base_url['verify_nickname'] + str(self.user.nickname) + 'dummy'

        response = self.client.get(path=query_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {})

    def test_user_verify_exist_email(self):
        query_url = self.base_url['verify_email'] + str(self.user.email)

        response = self.client.get(path=query_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("exist_email" in response.data)

    def test_user_verify_invalid_domain_email(self):
        query_url = (self.base_url['verify_email'] + str(self.user.email))[:-1]

        response = self.client.get(path=query_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("invalid_domain" in response.data)

    def test_user_verify_dummy_email(self):
        query_url = self.base_url['verify_email'] + "test_" + str(self.user.email)

        response = self.client.get(path=query_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['provider'], self.user.email.rsplit("@", 1)[1])

    def test_user_signup_fail_with_exist_email_nickname(self):
        data = {
            "email": self.user.email,
            "password": "password",
            "nickname": self.user.nickname,
            "category": {
                0: "국내소설",
                4: "경제/경영"
            }
        }

        response = self.client.post(path=self.base_url['signup'], data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('exist_email' in response.data)
        self.assertTrue('exist_nickname' in response.data)

    def test_user_signup_fail_with_invalid_domain_email(self):
        data = {
            "email": "test@test.com",
            "password": "password",
            "nickname": "test_nickname",
            "category": {
                0: "국내소설",
                4: "경제/경영"
            }
        }

        response = self.client.post(path=self.base_url['signup'], data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('invalid_domain' in response.data)

    def test_user_signup_fail_with_invalid_category(self):
        data = {
            "email": "test@naver.com",
            "password": "password",
            "nickname": "test_nickname",
            "category": {0: "invalid_category"}
        }
        response = self.client.post(path=self.base_url['signup'], data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('invalid_category' in response.data)

    def test_user_signup_success(self):
        data = {
            "email": "test@naver.com",
            "password": "password",
            "nickname": "test_nickname",
            "category": {
                0: "국내소설",
                4: "경제/경영"
            }
        }

        response = self.client.post(path=self.base_url['signup'], data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue('user' in response.data)

    def test_user_signin_fail_with_invalid_password(self):
        data = {
            "email": str(self.user.email),
            "password": "invalid_password"
        }

        response = self.client.post(path=self.base_url['signin'], data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("invalid_password" in response.data)

    def test_user_signin_success(self):
        data = {
            "email": str(self.user.email),
            "password": "password"
        }
        response = self.client.post(path=self.base_url['signin'], data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        token = response.data.get('auth', '')
        self.assertTrue('access_token' in token)
        self.assertTrue('refresh_token' in token)

    def test_user_signout(self):
        data = {"refresh": self.refresh}

        response = self.client.post(path=self.base_url['signout'], data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_user_edit_fail_with_unauthorized_user(self):
        new_user = UserFactory.create()

        base_url = self.url_prefix + str(new_user.id) + "/edit"
        data = {"nickname": "new_nickname"}

        response = self.client.patch(path=base_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue('unauthorized_user' in response.data)

    def test_user_edit_fail_with_no_exist_user(self):
        base_url = self.url_prefix + str(5) + "/edit"
        data = {"nickname": "new_nickname"}

        response = self.client.patch(path=base_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue('no_exist_user' in response.data)

    def test_user_edit_fail_with_invalid_category(self):
        base_url = self.url_prefix + str(self.user.id) + "/edit"
        data = {"category": {"1": "invalid_category"}}

        response = self.client.patch(path=base_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('invalid_category' in response.data)

    def test_user_edit_success(self):
        base_url = self.url_prefix + str(self.user.id) + "/edit"
        data = {"nickname": "new_nickname"}

        response = self.client.patch(path=base_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user"]["nickname"], data["nickname"])

    def test_user_delete_fail_with_no_exist_user(self):
        base_url = self.url_prefix + str(5) + "/delete"

        response = self.client.delete(path=base_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue("no_exist_user" in response.data)

    def test_user_delete_fail_with_unauthorized_user(self):
        new_user = UserFactory.create()
        base_url = self.url_prefix + str(new_user.id) + "/delete"

        response = self.client.delete(path=base_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue("unauthorized_user" in response.data)

    def test_user_delete_success(self):
        base_url = self.url_prefix + str(self.user.id) + "/delete"

        response = self.client.delete(path=base_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_user_category_fail_with_no_exist_user(self):
        base_url = self.url_prefix + str(5) + "/category"

        response = self.client.get(path=base_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue("no_exist_user" in response.data)

    def test_user_category_success(self):
        new_user = UserFactory.create()
        base_url = self.url_prefix + str(new_user.id) + "/category"

        response = self.client.get(path=base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertListEqual(
            list(response.data['category'].values()),
            list(new_user.category.values())
        )

    def test_user_category_update_with_empty_data(self):
        data = {
            '0': '국내소설',
            '5': '자기계발',
            '6': '역사'
        }
        response = self.client.patch(path=self.base_url['category_update'], data=None)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = self.client.patch(path=self.base_url['category_update'], data=data)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_user_category_update_fail_with_no_exist_user(self):
        base_url = self.base_url["category_update"] + "?user=" + str(5)

        response = self.client.patch(path=base_url+"&event=follow", data=None)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue('no_exist_user' in response.data)

        response = self.client.patch(path=base_url+"&event=unfollow", data=None)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue('no_exist_user' in response.data)

    def test_user_category_update_fail_with_unauthorized_user(self):
        new_user = UserFactory.create()
        base_url = self.base_url["category_update"] + "?user=" + str(new_user.id)

        response = self.client.patch(path=base_url + "&event=follow", data=None)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue('unauthorized_user' in response.data)

        response = self.client.patch(path=base_url + "&event=unfollow", data=None)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue('unauthorized_user' in response.data)

    def test_user_update_category_fail_with_exist_follow(self):
        base_url = self.base_url['follow_category'] + "&user=" + str(self.user.id)
        data = self.pick_rand_category_item(self.user.category)

        response = self.client.patch(path=base_url, data={"category": data}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(f'exist_follow_{list(data.values())[0]}' in response.data)

    def test_user_update_category_success_follow(self):
        base_url = self.base_url['follow_category'] + "&user=" + str(self.user.id)

        category_dict = {i: value for i, value in enumerate(category_choices)}
        for key in self.user.category.keys():
            del category_dict[key]
        data = self.pick_rand_category_item(category_dict)

        response = self.client.patch(path=base_url, data={"category": data}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(list(data.values())[0] in list(response.data['user']['category'].values()))

    def test_user_update_category_fail_with_no_exist_unfollow(self):
        base_url = self.base_url['unfollow_category'] + "&user=" + str(self.user.id)

        category_dict = {i: value for i, value in enumerate(category_choices)}
        for key in self.user.category.keys():
            del category_dict[key]
        data = self.pick_rand_category_item(category_dict)

        response = self.client.patch(path=base_url, data={"category": data}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(f'no_exist_follow_{list(data.values())[0]}' in response.data)

    def test_user_update_category_success_unfollow(self):
        base_url = self.base_url['unfollow_category'] + "&user=" + str(self.user.id)
        data = self.pick_rand_category_item(self.user.category)

        response = self.client.patch(path=base_url, data={"category": data}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(list(data.values())[0] not in list(response.data['user']['category'].values()))
