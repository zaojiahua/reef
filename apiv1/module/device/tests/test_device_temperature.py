from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from apiv1.module.device.models import TempPort
from reef.settings import ENABLE_TCCOUNTER


class TestDeviceTemperature(APITestCase):
    def setUp(self):
        self.default_data = TestTool.load_default_data()
        self.default_id = self.default_data['device_tempurature'].id
        self.default_data['temp_port'].device = self.default_data['device']
        self.default_data['temp_port'].save()

    @tccounter("devicetemperature_list", "post", ENABLE_TCCOUNTER)
    def test_auto_device(self):
        """
        当传入参数不包含device讯息时
        由port取得device讯息
        """
        response = self.client.post(
            reverse('devicetemperature_list'),
            data={
                'cabinet': self.default_data['cabinet'].id,
                'description': 'description',
                'temperature': 20,
                'temp_port': self.default_data['temp_port'].id
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertIsNotNone(response.data['cabinet'], response.data)

    @tccounter("devicetemperature_list", "post", ENABLE_TCCOUNTER)
    def test_auto_cabinet(self):
        """
        当传入参数不包含cabinet讯息时
        由device取得cabinet讯息(device讯息则再由port推断出)
        """
        response = self.client.post(
            reverse('devicetemperature_list'),
            data={
                'description': 'description',
                'temperature': 20,
                'temp_port': self.default_data['temp_port'].id
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertIsNotNone(response.data['cabinet'], response.data)

    @tccounter("devicetemperature_list", "get", ENABLE_TCCOUNTER)
    def test_get_200ok(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test get method 200 OK
        """
        response = self.client.get(reverse('devicetemperature_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("devicetemperature_list", "get", ENABLE_TCCOUNTER)
    def test_get_device_temperature_wanted_info(self):
        """
         Date: 2019/10/26
         Author: Guozijun
         test get fields you wanted
         """
        response = self.client.get(f"{reverse('devicetemperature_list')}?fields=device,device.id,temperature")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("devicetemperature_detail", "get", ENABLE_TCCOUNTER)
    def test_get_instance_by_id(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test get a instance by id
        """
        response = self.client.get(reverse('devicetemperature_detail', args=[self.default_id]))
        self.assertEqual(response.data['id'], self.default_id)

    @tccounter("devicetemperature_detail", "get", ENABLE_TCCOUNTER)
    def test_get_instance_which_not_exist(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test get a instance by a wrong id
        """
        response = self.client.get(reverse('devicetemperature_detail', args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @tccounter("devicetemperature_list", "post", ENABLE_TCCOUNTER)
    def test_post_201_create(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test post method 201 create
        """
        test_temp_port = TempPort.objects.create(
            port='PA-test',
            description='top-test',
        )
        response = self.client.post(reverse('devicetemperature_list'), data={
            'device': self.default_data['device'].id,
            'cabinet': self.default_data['cabinet'].id,
            'temperature': 30,
            'description': 'test',
            'temp_port': test_temp_port.id
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @tccounter("devicetemperature_list", "post", ENABLE_TCCOUNTER)
    def test_post_missing_field(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test create a instance but missing field
        """
        test_temp_port = TempPort.objects.create(
            port='PA-test',
            description='top-test',
        )
        response = self.client.post(reverse('devicetemperature_list'), data={
            'device': self.default_data['device'].id,
            'cabinet': self.default_data['cabinet'].id,
            'temperature': 30,
            'temp_port': test_temp_port.id
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("devicetemperature_detail", "put", ENABLE_TCCOUNTER)
    def test_put_200ok(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test put method 200 OK
        """
        response = self.client.put(reverse('devicetemperature_detail', args=[self.default_id]), data={
            'device': self.default_data['device'].id,
            'cabinet': self.default_data['cabinet'].id,
            'temperature': 60.01,
            'description': 'test',
            'temp_port': self.default_data['temp_port'].id
        })
        self.assertEqual(response.data['temperature'], '60.01')

    @tccounter("devicetemperature_detail", "put", ENABLE_TCCOUNTER)
    def test_put_description_length_more_than_50(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test update a instance description more than 50
        """
        response = self.client.put(reverse('devicetemperature_detail', args=[self.default_id]), data={
            'device': self.default_data['device'].id,
            'cabinet': self.default_data['cabinet'].id,
            'temperature': 30,
            'description': 'test-test-test-test-test-test-test-test-test-test-test',
            'temp_port': self.default_data['temp_port'].id
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_200ok(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test patch method 200 OK
        """
        response = self.client.patch(reverse('devicetemperature_detail', args=[self.default_id]), data={
            'description': 'changed',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_patch_temperature_more_than_2_decimal_places(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test update temperature more than 2 decimal places
        """
        response = self.client.patch(reverse('devicetemperature_detail', args=[self.default_id]), data={
            'temperature': 66.666,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("devicetemperature_detail", "delete", ENABLE_TCCOUNTER)
    def test_delete_204_no_content(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test delete method 204 not content
        """
        response = self.client.delete(reverse('devicetemperature_detail', args=[self.default_id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @tccounter("devicetemperature_detail", "delete", ENABLE_TCCOUNTER)
    def test_delete_instance_do_not_exist(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test delete instance which is not exists
        """
        response = self.client.delete(reverse('devicetemperature_detail', args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
