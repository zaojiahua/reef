from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from reef.settings import ENABLE_TCCOUNTER


class TestGetRdsGroupByPhoneModelName(APITestCase):

    def setUp(self):
        self.label = "1"
        self.default_data = TestTool.load_default_data(self.label)

    @tccounter('get_rds_group_by_phone_model_name', 'get', ENABLE_TCCOUNTER)
    def test200ok(self):
        """
        Date: 2018/12/28
        Author: Raymond
        Base API test case
        """
        response = self.client.get(
            reverse('get_rds_group_by_phone_model_name')
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('get_rds_group_by_phone_model_name', 'get', ENABLE_TCCOUNTER)
    def test_phone_model_name_in_response(self):
        """
        Date: 2018/12/28
        Author: Raymond
        Base API test case
        """
        response = self.client.get(
            reverse('get_rds_group_by_phone_model_name')
        )
        self.assertIn(f'phone_model{self.label}', response.data)
