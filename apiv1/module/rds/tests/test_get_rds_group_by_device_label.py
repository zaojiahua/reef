from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.core.test import tccounter, TestTool
from reef.settings import ENABLE_TCCOUNTER


class TestGetRdsGroupByDeviceLabel(APITestCase):

    def setUp(self):
        self.create_label = '1'
        self.default_data = TestTool.load_default_data(self.create_label)

    @tccounter('get_rds_group_by_device_label', 'get', ENABLE_TCCOUNTER)
    def test200ok(self):
        """
        Date: 2018/12/28
        Author: Raymond
        Base API test case
        """
        response = self.client.get(
            reverse('get_rds_group_by_device_label')
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('get_rds_group_by_device_label', 'get', ENABLE_TCCOUNTER)
    def test_get_rds_group_by_device_label_data(self):
        """
       Date: 2019/11/14
       Author: Goufuqiang
       Describe: Test group by data
       """
        response = self.client.get(
            reverse('get_rds_group_by_device_label')
        )
        self.assertIn(f'device{self.create_label}', response.data)