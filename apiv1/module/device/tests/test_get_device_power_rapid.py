from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from apiv1.module.device.models import DevicePower
from reef.settings import ENABLE_TCCOUNTER


class TestGetDevicePowerRapid(APITestCase):
    def setUp(self):
        self.default_data = TestTool.load_default_data()
        DevicePower.objects.create(
            device=self.default_data['device'],
            cabinet=self.default_data['cabinet'],
            power_port=self.default_data['power_port'],
            battery_level=21,
            record_datetime='2018-05-05T12:00:00Z',
            charging=True
        )

    @tccounter("get_device_power_rapid", "get", ENABLE_TCCOUNTER)
    def test200ok(self):
        """
        Date: 2018/1/2
        Author: Raymond
        Base test case
        """
        response = self.client.get(
            reverse('get_device_power_rapid')
            + f'?record_datetime__gt=2018-05-05T11:00:00Z'
            + f'&record_datetime__lt=2018-05-05T13:00:00Z'
            + f'&device_id={self.default_data["device"].id}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("get_device_power_rapid", "get", ENABLE_TCCOUNTER)
    def test_record_datetime_utc8(self):
        """
        Date: 2018/1/4
        Author: Raymond
        Issue: T1B-460
        record_datetime in return data should be utc+8 time
        """
        response = self.client.get(
            reverse('get_device_power_rapid')
            + f'?record_datetime__gt=2018-05-05T11:00:00Z'
            + f'&record_datetime__lt=2018-05-05T13:00:00Z'
            + f'&device_id={self.default_data["device"].id}'
        )
        record_datetime = response.data['devicepowers'][0]['record_datetime']
        self.assertEqual(record_datetime, '2018-05-05 20:00:00')
