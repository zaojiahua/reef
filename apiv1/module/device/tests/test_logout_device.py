from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apiv1.core.test import TestTool, tccounter
from apiv1.module.device.models import Device, DeviceCoordinate
from apiv1.module.device.models import PowerPort, TempPort
from reef.settings import ENABLE_TCCOUNTER


class TestLogoutDevice(APITestCase):
    def setUp(self):
        self.default_data = TestTool.load_default_data()

    @tccounter("logout_device", "post", ENABLE_TCCOUNTER)
    def test_200ok(self):
        response = self.client.post(
            reverse('logout_device'),
            data={
                "id": self.default_data['device'].id
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("logout_device", "post", ENABLE_TCCOUNTER)
    def test_logout_release_resource(self):
        """
        Date: 2019/03/15
        Author: Raymond
        logout device should release tempport, powerport, and delete coordinate
        """
        tempport = self.default_data['temp_port']
        powerport = self.default_data['power_port']
        device = self.default_data['device']
        device.tempport.add(tempport)
        device.powerport = powerport
        device.coordinate = self.default_data['device_coordinate']
        device.save()

        response = self.client.post(
            reverse('logout_device'),
            data={
                "id": self.default_data['device'].id
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(PowerPort.objects.filter(device=device).count(), 0)
        self.assertEqual(TempPort.objects.filter(device=device).count(), 0)
        self.assertIsNone(Device.objects.get(id=device.id).coordinate)
        self.assertIsNone(Device.objects.get(id=device.id).device_name)
        self.assertEqual(DeviceCoordinate.objects.count(), 0)
        self.assertEqual(Device.objects.get(id=device.id).auto_test, False)
