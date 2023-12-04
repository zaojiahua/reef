from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.core.constants import PANESLOT_STATUS_OK
from apiv1.core.test import TestTool, tccounter
from reef.settings import ENABLE_TCCOUNTER


class TestUnlinkPaneViewDevice(APITestCase):
    def setUp(self) -> None:
        self.default_data = TestTool.load_default_data()

    @tccounter("unlink_paneview_device", "post", ENABLE_TCCOUNTER)
    def test_200OK(self):
        """
        Date: 2020/03/25
        Author: raymond
        测试能够正常移除paneview中的device
        """
        ps = self.default_data["paneslot"]
        ps.device = self.default_data["device"]
        ps.status = PANESLOT_STATUS_OK
        ps.save()

        response = self.client.post(reverse("unlink_paneview_device"), data={
            "device": self.default_data["device"].id
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("unlink_paneview_device", "post", ENABLE_TCCOUNTER)
    def test_unlink_not_linked(self):
        """
        Date: 2020/03/25
        Author: raymond
        unlink未link到paneview的device时，返回错误400
        """
        response = self.client.post(reverse("unlink_paneview_device"), data={
            "device": self.default_data["device"].id
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
