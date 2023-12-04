from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool
from apiv1.core.test import tccounter
from reef.settings import ENABLE_TCCOUNTER

class TestGetTBoardSuccessRatio(APITestCase):
    def setUp(self):
        self.default_data = TestTool.load_default_data()

    @tccounter("get_tboard_success_ratio", "get", ENABLE_TCCOUNTER)
    def test_200ok(self):
        """
        Date: 2019/11/20
        Author: wengmeijia
        Describe: GET /statistics/get_tboard_success_ratio/
        """
        response = self.client.get(
            reverse('get_tboard_success_ratio') + '?tboards={}'.format(self.default_data['tboard'].id)
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("get_tboard_success_ratio", "get", ENABLE_TCCOUNTER)
    def test_parameter_is_str(self):
        """
        Date: 2019/11/20
        Author: wengmeijia
        Describe: GET /statistics/get_tboard_success_ratio/
        """
        response = self.client.get(
            reverse('get_tboard_success_ratio') + '?tboards={}'.format('test')
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
