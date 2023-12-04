from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from reef.settings import ENABLE_TCCOUNTER


class TestCreateDeviceScreenshot(APITestCase):
    def setUp(self):
        self.default_data = TestTool.load_default_data()

    @tccounter("create_device_screenshot", "post", ENABLE_TCCOUNTER)
    def test200ok(self):
        with open('apiv1/module/device/tests/file/1_snap.png', 'rb') as testfile:
            response = self.client.post(
                reverse('create_device_screenshot'),
                data={
                    'device': self.default_data['device'].device_label,
                    'snap_timestamp': '2018-11-11 00:00:00',
                    'screenshot': testfile
                },
                format='multipart'
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("create_device_screenshot", "post", ENABLE_TCCOUNTER)
    def test_request_device_is_label(self):
        """
        传入的参数中
        device代表的是device_label而不是device_id
        """
        with open('apiv1/module/device/tests/file/1_snap.png', 'rb') as testfile:
            response = self.client.post(
                reverse('create_device_screenshot'),
                data={
                    'device': self.default_data['device'].id,
                    'snap_timestamp': '2018-11-11 00:00:00',
                    'screenshot': testfile
                },
                format='multipart'
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
