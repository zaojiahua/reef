from rest_framework.reverse import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from reef.settings import ENABLE_TCCOUNTER


class TestCreateDeviceTmpByPort(APITestCase):

    def setUp(self):
        self.default_data = TestTool.load_default_data()

    @tccounter("create_device_tmp_by_port", "post", ENABLE_TCCOUNTER)
    def test_post_201_create(self):
        """
        Date: 2020/03/28
        Author: Guozijun
        test post method 201 create
        """
        response = self.client.post(reverse('create_device_tmp_by_port'), data={
            "device": self.default_data['device'].id,
            "cabinet": self.default_data['cabinet'].id,
            "description": "description",
            "temp_port": self.default_data['temp_port'].port,
            "temperature": 62
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @tccounter("create_device_tmp_by_port", "post", ENABLE_TCCOUNTER)
    def test_create_without_device_auto_temp_port(self):
        """
        Date: 2020/03/28
        Author: Guozijun
        test create without device but auto fill with temp_port's device
        """
        self.default_data['temp_port'].device = self.default_data['device']
        self.default_data['temp_port'].save()

        response = self.client.post(reverse('create_device_tmp_by_port'), data={
            "cabinet": self.default_data['cabinet'].id,
            "description": "description",
            "temp_port": self.default_data['temp_port'].port,
            "temperature": 62
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

