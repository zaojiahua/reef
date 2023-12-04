from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from reef.settings import ENABLE_TCCOUNTER


class TestReleaseDevice(APITestCase):

    def setUp(self):
        self.default_data = TestTool.load_default_data()
        self.device = self.default_data['device']

    @tccounter("release_device", "post", ENABLE_TCCOUNTER)
    def test_ip_address_is_empty(self):
        """
        Date: 2020/03/25
        Author: Goufuqiang
        Test ip_address parameter is empty
        """
        response = self.client.post(
            reverse('release_device'),
            data = {
                "device_label": self.device.device_label
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("release_device", "post", ENABLE_TCCOUNTER)
    def test_request_coral_error(self):
        """
         Date: 2020/03/25
         Author: Goufuqiang
         Test request Coral service error
         """
        response = self.client.post(
            reverse('release_device'),
            data={
                "device_label": self.device.device_label,
                "ip_address": self.device.ip_address
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
