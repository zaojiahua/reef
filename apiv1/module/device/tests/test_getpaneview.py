from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from reef.settings import ENABLE_TCCOUNTER


class TestGetPaneView(APITestCase):
    def setUp(self) -> None:
        self.default_data = TestTool.load_default_data()

    @tccounter("get_paneview", "get", ENABLE_TCCOUNTER)
    def test_200ok(self):
        """
        Date: 2020/03/25
        Author: raymond
        测试PaneView基本get功能
        """
        response = self.client.get(reverse('get_paneview'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("get_paneview", "get", ENABLE_TCCOUNTER)
    def test_limit_offset(self):
        """
        Date: 2020/03/25
        Author: raymond
        测试PaneView分页功能
        """
        response = self.client.get(reverse('get_paneview')+f"?limit=5&offset=0")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

