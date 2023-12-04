from rest_framework.test import APITestCase
from rest_framework.reverse import reverse
from rest_framework import status
from apiv1.core.test import TestTool, tccounter
from reef.settings import ENABLE_TCCOUNTER


class TestLogin(APITestCase):

    def setUp(self):
        self.create_label = "1"
        self.default_data = TestTool.load_default_data(self.create_label)

    @tccounter('user_login', 'post', ENABLE_TCCOUNTER)
    def test_user_login_200ok(self):
        """
        Date 2019/10/30
        Author: Goufuqiang
        POST /cedar/user_login/
        """
        response = self.client.post(
                reverse('user_login'),
                data={
                    "username": f"user{self.create_label}",
                    "password": f"user{self.create_label}"
                }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('user_login', 'post', ENABLE_TCCOUNTER)
    def test_user_login_username_is_error(self):
        """
        Date 2019/10/30
        Author: Goufuqiang
        Describe: username is error
        """
        response = self.client.post(
            reverse('user_login'),
            data={
                "username": "1111",
                "password": f"user{self.create_label}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)