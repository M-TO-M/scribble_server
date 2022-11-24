import random
from typing import Union

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.users.models import category_list
from api.users.serializers import ScribbleTokenObtainPairSerializer
from .factories import UserFactory


class UserTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin = UserFactory.create(is_staff=True, is_superuser=True)
        self.user = UserFactory.create()
        self.set_credentials()

        self.url_prefix = "http://127.0.0.1:8000/v1/users/"

    def tearDown(self):
        super(UserTestCase, self).tearDown()

    def set_credentials(self):
        token = ScribbleTokenObtainPairSerializer.get_token(self.user)

        self.access = str(token.access_token)
        self.refresh = str(token)

        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.access}'
        )
        self.client.cookies['SCRIB_TOKEN'] = self.refresh

    @classmethod
    def pick_rand_category_item(cls, item: Union[list, dict]) -> Union[None, list]:
        if not item:
            return None
        if isinstance(item, list):
            return [random.choice(item)]

        if isinstance(item, dict):
            return [random.choice(list(item.values()))]


class UserVerifyTestCase(UserTestCase):
    def setUp(self):
        super(UserVerifyTestCase, self).setUp()
        self.base_url = self.url_prefix + "verify"
        self.verify_nickname_url = self.base_url + "?nickname="
        self.verify_email_url = self.base_url + "?email="

    def test_given_empty_data_expect_user_verify_success_no_content(self):
        response = self.client.get(path=self.base_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_given_exist_nickname_expect_user_verify_fail(self):
        query_url = self.verify_nickname_url + str(self.user.nickname)

        response = self.client.get(path=query_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("exist_nickname" in response.data)

    def test_given_dummy_nickname_expect_user_verify_success(self):
        query_url = self.verify_nickname_url + "dummy_" + str(self.user.nickname)

        response = self.client.get(path=query_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {})

    def test_given_exist_email_expect_user_verify_fail(self):
        query_url = self.verify_email_url + str(self.user.email)

        response = self.client.get(path=query_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("exist_email" in response.data)

    def test_given_invalid_domain_email_addr_expect_user_verify_fail(self):
        query_url = self.verify_email_url + str(self.user.email)[:-1]

        response = self.client.get(path=query_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("invalid_domain" in response.data)

    def test_given_dummy_email_expect_user_verify_success(self):
        query_url = self.verify_email_url + "test_" + str(self.user.email)

        response = self.client.get(path=query_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['provider'], self.user.email.rsplit("@", 1)[1])


class UserSignUpTestCase(UserTestCase):
    def setUp(self):
        super(UserSignUpTestCase, self).setUp()
        self.base_url = self.url_prefix + "new"

    def test_given_exist_nickname_and_exist_email_expect_user_signup_fail(self):
        data = {
            "email": self.user.email,
            "password": "password",
            "nickname": self.user.nickname
        }

        response = self.client.post(path=self.base_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('exist_email' in response.data)
        self.assertTrue('exist_nickname' in response.data)

    def test_given_invalid_domain_email_addr_expect_user_signup_fail(self):
        data = {
            "email": "test@test.com",
            "password": "password",
            "nickname": "test_nickname"
        }

        response = self.client.post(path=self.base_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('invalid_domain' in response.data)

    def test_given_invalid_category_expect_user_signup_fail(self):
        data = {
            "email": "test@naver.com",
            "password": "password",
            "nickname": "test_nickname",
            "category": ["invalid_category"]
        }
        response = self.client.post(path=self.base_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('invalid_category' in response.data)

    def test_given_valid_user_data_expect_user_signup_success(self):
        data = {
            "email": "test@naver.com",
            "password": "password",
            "nickname": "test_nickname",
            "category": self.pick_rand_category_item(category_list)
        }

        response = self.client.post(path=self.base_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue('user' in response.data)


class UserSignInOutTestCase(UserTestCase):
    def setUp(self):
        super(UserSignInOutTestCase, self).setUp()
        self.signin_url = self.url_prefix + "signin"
        self.signout_url = self.url_prefix + "signout"

    def test_given_invalid_passwd_expect_user_signin_fail(self):
        data = {
            "email": str(self.user.email),
            "password": "invalid_password"
        }

        response = self.client.post(path=self.signin_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("invalid_password" in response.data)

    def test_given_valid_signin_data_expect_user_signin_success(self):
        data = {
            "email": str(self.user.email),
            "password": "password"
        }
        response = self.client.post(path=self.signin_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_given_valid_auth_credentials_expect_user_signout_success(self):
        data = {"refresh": self.refresh}

        response = self.client.post(path=self.signout_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class UserEditTestCase(UserTestCase):
    def setUp(self):
        super(UserEditTestCase, self).setUp()

    def test_given_valid_data_with_unauthorized_user_expect_user_edit_fail(self):
        new_user = UserFactory.create()

        base_url = self.url_prefix + str(new_user.id) + "/edit"
        data = {"nickname": "new_nickname"}

        response = self.client.patch(path=base_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue('unauthorized_user' in response.data)

    def test_given_valid_data_with_no_exist_user_expect_user_edit_fail(self):
        base_url = self.url_prefix + str(5) + "/edit"
        data = {"nickname": "new_nickname"}

        response = self.client.patch(path=base_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue('no_exist_user' in response.data)

    def test_given_invalid_category_with_authorized_user_expect_user_edit_fail(self):
        base_url = self.url_prefix + str(self.user.id) + "/edit"
        data = {"category": ["invalid_category"]}

        response = self.client.patch(path=base_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('invalid_category' in response.data)

    def test_given_valid_data_with_authorized_user_expect_user_edit_success(self):
        base_url = self.url_prefix + str(self.user.id) + "/edit"
        data = {"nickname": "new_nickname"}

        response = self.client.patch(path=base_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user"]["nickname"], data["nickname"])


class UserDeleteTestCase(UserTestCase):
    def setUp(self):
        super(UserDeleteTestCase, self).setUp()

    def test_with_no_exist_user_expect_user_delete_fail(self):
        base_url = self.url_prefix + str(5) + "/delete"

        response = self.client.delete(path=base_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue("no_exist_user" in response.data)

    def test_with_unauthorized_user_expect_user_delete_fail(self):
        new_user = UserFactory.create()
        base_url = self.url_prefix + str(new_user.id) + "/delete"

        response = self.client.delete(path=base_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue("unauthorized_user" in response.data)

    def test_with_authorized_user_expect_user_delete_success(self):
        base_url = self.url_prefix + str(self.user.id) + "/delete"

        response = self.client.delete(path=base_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class UserCategoryTestCase(UserTestCase):
    def setUp(self):
        super(UserCategoryTestCase, self).setUp()
        self.base_url = {
            "category_update": self.url_prefix + "category",
            "follow_category": self.url_prefix + "category?event=follow",
            "unfollow_category": self.url_prefix + "category?event=unfollow"
        }

    def test_with_no_exist_user_expect_user_category_search_fail(self):
        base_url = self.url_prefix + str(5) + "/category"

        response = self.client.get(path=base_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue("no_exist_user" in response.data)

    def test_with_exist_user_expect_user_category_search_success(self):
        new_user = UserFactory.create()
        base_url = self.url_prefix + str(new_user.id) + "/category"

        response = self.client.get(path=base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertListEqual(
            list(response.data['category'].values()),
            list(new_user.category.values())
        )

    def test_given_empty_data_expect_user_category_update_success_no_content(self):
        response = self.client.patch(path=self.base_url['category_update'], data=None)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_given_valid_category_data_expect_user_category_update_success(self):
        data = self.pick_rand_category_item(category_list)

        response = self.client.patch(path=self.base_url['category_update'], data={"category": data})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_given_empty_data_with_no_exist_user_expect_user_category_update_follow_fail(self):
        base_url = self.base_url["category_update"] + "?user=" + str(5)

        response = self.client.patch(path=base_url+"&event=unfollow", data=None)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue('no_exist_user' in response.data)

    def test_given_empty_data_with_no_exist_user_expect_user_category_update_unfollow_fail(self):
        base_url = self.base_url["category_update"] + "?user=" + str(5)

        response = self.client.patch(path=base_url + "&event=unfollow", data=None)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue('no_exist_user' in response.data)

    def test_given_empty_data_with_unauthorized_user_expect_user_category_update_follow_fail(self):
        new_user = UserFactory.create()
        base_url = self.base_url["category_update"] + "?user=" + str(new_user.id)

        response = self.client.patch(path=base_url + "&event=follow", data=None)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue('unauthorized_user' in response.data)

    def test_given_empty_data_with_unauthorized_user_expect_user_category_update_unfollow_fail(self):
        new_user = UserFactory.create()
        base_url = self.base_url["category_update"] + "?user=" + str(new_user.id)

        response = self.client.patch(path=base_url + "&event=unfollow", data=None)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue('unauthorized_user' in response.data)

    def test_given_exist_follow_with_authorized_user_expect_user_category_update_follow_fail(self):
        base_url = self.base_url['follow_category'] + "&user=" + str(self.user.id)
        data = self.pick_rand_category_item(self.user.category)

        response = self.client.patch(path=base_url, data={"category": data}, format='json')

        if data:
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertTrue(f'exist_follow_{data[0]}' in response.data)
        else:
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_given_valid_follow_data_with_authorized_user_expect_user_category_update_follow_success(self):
        base_url = self.base_url['follow_category'] + "&user=" + str(self.user.id)

        category_dict = {i: value for i, value in enumerate(category_choices)}
        for key in self.user.category.keys():
            del category_dict[key]
        data = self.pick_rand_category_item(category_dict)

        response = self.client.patch(path=base_url, data={"category": data}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(data[0] in list(response.data['user']['category'].values()))

    def test_given_no_exist_follow_with_authorized_user_expect_user_category_update_unfollow_fail(self):
        base_url = self.base_url['unfollow_category'] + "&user_id=" + str(self.user.id)

        category_dict = {i: value for i, value in enumerate(category_list)}
        for key in self.user.category.keys():
            del category_dict[key]
        data = self.pick_rand_category_item(category_dict)

        response = self.client.patch(path=base_url, data={"category": data}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(f'no_exist_unfollow_{data[0]}' in response.data)

    def test_given_valid_unfollow_data_with_authorized_user_expect_user_category_update_unfollow_success(self):
        base_url = self.base_url['unfollow_category'] + "&user=" + str(self.user.id)
        data = self.pick_rand_category_item(self.user.category)

        response = self.client.patch(path=base_url, data={"category": data}, format='json')

        if data:
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertTrue(data[0] not in list(response.data['user']['category'].values()))
        else:
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
