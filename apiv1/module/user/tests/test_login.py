from rest_framework.test import APITestCase
from rest_framework.reverse import reverse
from rest_framework import status
from apiv1.core.test import TestTool, tccounter
from reef.settings import ENABLE_TCCOUNTER


class TestLogin(APITestCase):

    def setUp(self):
        self.create_label = "1"
        self.default_data = TestTool.load_default_data(self.create_label)

    @tccounter('login', 'post', ENABLE_TCCOUNTER)
    def test_login_200ok(self):
        """
        Date 2019/10/22
        Author: Goufuqiang
        POST /api/v1/login/
        """
        response = self.client.post(
            reverse('login'),
            data={
                "username": f"user{self.create_label}",
                "password": f"user{self.create_label}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    @tccounter('login', 'post', ENABLE_TCCOUNTER)
    def test_login_username_is_null(self):
        """
        Date 2019/10/22
        Author: Goufuqiang
        POST /api/v1/login/
        Test username is null
        """
        response = self.client.post(
            reverse('login'),
            data={
                "username": None,
                "password": f"user{self.create_label}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter('login', 'post', ENABLE_TCCOUNTER)
    def test_login_password_error(self):
        """
        Date 2019/10/22
        Author: Goufuqiang
        POST /api/v1/login/
        Test password error
        """
        response = self.client.post(
            reverse('login'),
            data={
                "username": f"user{self.create_label}",
                "password": 123456
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
