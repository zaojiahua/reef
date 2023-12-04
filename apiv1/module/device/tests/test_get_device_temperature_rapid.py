from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from apiv1.module.device.models import DeviceTemperature
from reef.settings import ENABLE_TCCOUNTER


class TestGetDeviceTemperatureRapid(APITestCase):
    def setUp(self):
        self.default_data = TestTool.load_default_data()
        DeviceTemperature.objects.create(
            device=self.default_data['device'],
            cabinet=self.default_data['cabinet'],
            temp_port=self.default_data['temp_port'],
            temperature=21,
            record_datetime='2018-05-05T12:00:00Z'
        )

    @tccounter("get_device_temperature_rapid", "get", ENABLE_TCCOUNTER)
    def test200ok(self):
        """
        Date: 2018/1/2
        Author: Raymond
        Base test case
        """
        response = self.client.get(
            reverse('get_device_temperature_rapid')
            + f'?record_datetime__gt=2018-05-05T11:00:00Z'
            + f'&record_datetime__lt=2018-05-05T13:00:00Z'
            + f'&device_id={self.default_data["device"].id}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("get_device_temperature_rapid", "get", ENABLE_TCCOUNTER)
    def test_record_datetime_utc8(self):
        """
        Date: 2018/1/4
        Author: Raymond
        Issue: T1B-460
        record_datetime in return data should be utc+8 time
        """
        response = self.client.get(
            reverse('get_device_temperature_rapid')
            + f'?record_datetime__gt=2018-05-05T11:00:00Z'
            + f'&record_datetime__lt=2018-05-05T13:00:00Z'
            + f'&device_id={self.default_data["device"].id}'
        )
        record_datetime = response.data['devicetemperatures'][0]['record_datetime']
        self.assertEqual(record_datetime, '2018-05-05 20:00:00')

    @tccounter("get_device_temperature_rapid", "get", ENABLE_TCCOUNTER)
    def test_device_id_is_null(self):
        """
        Date: 2019/7/2
        Author: gfq
        description: 测试传入device_id参数为空返回400
        """
        response = self.client.get(reverse('get_device_temperature_rapid') + f'?device_id=')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
