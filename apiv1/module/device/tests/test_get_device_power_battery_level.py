from django.urls import reverse
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from reef.settings import ENABLE_TCCOUNTER


class TestGetDevicePowerBatterLevel(APITestCase):
    def setUp(self):
        self.default_data = TestTool.load_default_data()

    @tccounter("get_device_power_battery_level", "get", ENABLE_TCCOUNTER)
    def test_get_device_power_battery_info1(self):
        """
        Date: 2019/07/29
        Author: Guozijun
        test get device_power_battery : device status is offline
        """
        device = self.default_data['device']
        device.cabinet = None
        device.save()
        response = self.client.get(
            reverse('get_device_power_battery_level')
            + f'?device_id={device.id}'
        )
        self.assertEqual(response.data, [{'device': device.id, 'battery_level': None}])

    @tccounter("get_device_power_battery_level", "get", ENABLE_TCCOUNTER)
    def test_get_device_power_battery_info2(self):
        """
        Date: 2019/07/29
        Author: Guozijun
        test get device_power_battery : device status is busy
        """
        device = self.default_data['device']
        # update device status to busy
        device.status = 'busy'
        device.save()
        response = self.client.get(
            reverse('get_device_power_battery_level')
            + f'?device_id={device.id}'
        )
        self.assertEqual(response.data, [{'device': device.id,
                                          'battery_level': self.default_data['device_power'].battery_level}])
