from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from reef.settings import ENABLE_TCCOUNTER


class TestGetReefSpaceUsage(APITestCase):
    def setUp(self):
        self.default_data = TestTool.load_default_data()

    @tccounter('get_reef_space_usage', 'get', ENABLE_TCCOUNTER)
    def test_200ok(self):
        response = self.client.get(
            reverse('get_reef_space_usage') + '?unit=MB',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('get_reef_space_usage', 'get', ENABLE_TCCOUNTER)
    def test_no_parameter(self):
        """
        Date 2019/11/11
        Author: Goufuqiang
        Describe: Tets no parameter
        """
        response = self.client.get(
            reverse('get_reef_space_usage')
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)