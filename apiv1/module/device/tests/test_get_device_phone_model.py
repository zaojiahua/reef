from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from apiv1.module.device.models import Device
from reef.settings import ENABLE_TCCOUNTER


class TestGetDevicePowerBatterLevel(APITestCase):
    def setUp(self):
        self.default_data = TestTool.load_default_data()

    @tccounter("get_device_phone_model", "get", ENABLE_TCCOUNTER)
    def test_get_device_phone_model(self):
        """
        Date: 2019/07/30
        Author: Guozijun
        test get device phone model
        """
        response = self.client.get(
            reverse('get_device_phone_model')
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("get_device_phone_model", "get", ENABLE_TCCOUNTER)
    def test_get_device_phone_model_not_repeating(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test 2 device and related same phone model, and API should response one
        """
        Device.objects.create(device_label="label_test",
                              cpu_id='cpu_id',
                              phone_model=self.default_data['phone_model'],
                              rom_version=self.default_data['rom_version'],
                              )
        response = self.client.get(reverse('get_device_phone_model'))
        self.assertEqual(len(response.data['device']), 1)
