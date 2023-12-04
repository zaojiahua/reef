from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from reef.settings import ENABLE_TCCOUNTER


class TestGetPaneView(APITestCase):
    def setUp(self) -> None:
        self.default_data = TestTool.load_default_data()

    @tccounter("link_paneview_device", "post", ENABLE_TCCOUNTER)
    def test_200ok(self):
        """
        Date: 2020/03/25
        Author: raymond
        测试能够正常连接paneview和device
        """
        response = self.client.post(reverse('link_paneview_device'), data={
            "paneslot": self.default_data["paneslot"].id,
            "device": self.default_data["device"].id
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("link_paneview_device", "post", ENABLE_TCCOUNTER)
    def test_auto_assign(self):
        """
        Date: 2020/03/25
        Author: raymond
        若不提供paneslot, 提供paneview, 会自动分配空闲的paneslot给device
        """
        response = self.client.post(reverse('link_paneview_device'), data={
            "paneview": self.default_data["paneview"].id,
            "device": self.default_data["device"].id
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
