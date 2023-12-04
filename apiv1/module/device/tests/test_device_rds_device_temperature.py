from rest_framework.reverse import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from reef.settings import ENABLE_TCCOUNTER


class TestDeviceTemperature1(APITestCase):

    def setUp(self):
        self.default_data = TestTool.load_default_data()

    @tccounter("device_temperature", "get", ENABLE_TCCOUNTER)
    def test_get_200ok(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test get method 200 OK
        """
        response = self.client.get(reverse('device_temperature')
                                   + f'?record_datetime__gt=2019-10-26T11:00:00Z'
                                   + f'&record_datetime__lt=2019-10-26T13:00:00Z'
                                   + f'&device_id={self.default_data["device"].id}'
                                   )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("device_temperature", "get", ENABLE_TCCOUNTER)
    def test_filter_device_not_exist(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test filter device does not exist
        """
        response = self.client.get(reverse('device_temperature')
                                   + '&device_id=9999'
                                   )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
