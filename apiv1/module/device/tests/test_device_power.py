from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from apiv1.module.device.models import Device, PowerPort
from reef.settings import ENABLE_TCCOUNTER


class TestDevicePower(APITestCase):
    def setUp(self):
        self.default_data = TestTool.load_default_data()
        self.default_id = self.default_data['device_power'].id

    def _extra_test_data(self):
        self.device_for_test = Device.objects.create(
            device_label='device_label',
            device_name='device',
            cabinet=self.default_data['cabinet'],
            ip_address='192.168.1.1',
            android_version=self.default_data['android_version'],
            phone_model=self.default_data['phone_model'],
            cpu_id='CPU-Z',
            rom_version=self.default_data['rom_version']
        )
        self.default_data['power_port'].device = self.device_for_test
        self.default_data['power_port'].save()

        self.power_port_for_test = PowerPort.objects.create(
            port='PA-02',
        )

    @tccounter("devicepower_list", "post", ENABLE_TCCOUNTER)
    def test_200ok(self):
        with open('apiv1/module/device/tests/file/battery_0AvZF2p.dat', 'rb') as file:
            response = self.client.post(
                reverse('devicepower_list'),
                data={
                    'battery_level': 20,
                    'charging': True,
                    'battery_file': file,
                    'device': self.default_data['device'].id,
                    'cabinet': self.default_data['cabinet'].id
                },
                format='multipart'
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertIsNotNone(response.data['cabinet'], response.data)

    @tccounter("devicepower_list", "post", ENABLE_TCCOUNTER)
    def test_create_device_power_without_power_port_1(self):
        """
        Date: 2019/07/18
        Author: Guozijun
        test create device_power without power_port, and device not related power_port
        """
        with open('apiv1/module/device/tests/file/battery_0AvZF2p.dat', 'rb') as file:
            response = self.client.post(
                reverse('devicepower_list'),
                data={
                    'battery_level': 20,
                    'charging': True,
                    'battery_file': file,
                    'device': self.default_data['device'].id,
                    'cabinet': self.default_data['cabinet'].id
                },
                format='multipart'
            )
        self.assertIsNone(response.data['power_port'], response.data)

    @tccounter("devicepower_list", "post", ENABLE_TCCOUNTER)
    def test_create_device_power_without_power_port_2(self):
        self._extra_test_data()
        """
        Date: 2019/07/18
        Author: Guozijun
        test create device_power without power_port, but device related power_port
        """
        with open('apiv1/module/device/tests/file/battery_0AvZF2p.dat', 'rb') as file:
            response = self.client.post(
                reverse('devicepower_list'),
                data={
                    'battery_level': 20,
                    'charging': True,
                    'battery_file': file,
                    'device': self.device_for_test.id,
                    'cabinet': self.default_data['cabinet'].id
                },
                format='multipart'
            )
        self.assertEqual(response.data['power_port'], self.default_data['power_port'].id)

    @tccounter("devicepower_list", "post", ENABLE_TCCOUNTER)
    def test_create_device_power_with_power_port(self):
        self._extra_test_data()
        """
        Date: 2019/07/18
        Author: Guozijun
        test create device_power with power_port, and different with device related power_port, 
        device_power power_port value is input power_port value, instead of device related power_port
        """
        with open('apiv1/module/device/tests/file/battery_0AvZF2p.dat', 'rb') as file:
            response = self.client.post(
                reverse('devicepower_list'),
                data={
                    'battery_level': 20,
                    'charging': True,
                    'battery_file': file,
                    'device': self.device_for_test.id,
                    'cabinet': self.default_data['cabinet'].id,
                    'power_port': self.power_port_for_test.id
                },
                format='multipart'
            )
        self.assertEqual(response.data['power_port'], self.power_port_for_test.id)

    @tccounter("devicepower_list", "get", ENABLE_TCCOUNTER)
    def test_get_200ok(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test get method 200 OK
        """
        response = self.client.get(reverse('devicepower_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("devicepower_list", "get", ENABLE_TCCOUNTER)
    def test_get_device_powerport_wanted_info(self):
        """
         Date: 2019/10/26
         Author: Guozijun
         test get fields you wanted
         """
        response = self.client.get(f"{reverse('devicepower_list')}?fields=device,device.id,battery_level")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("devicepower_detail", "get", ENABLE_TCCOUNTER)
    def test_get_instance_by_id(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test get a instance by id
        """
        response = self.client.get(reverse('devicepower_detail', args=[self.default_id]))
        self.assertEqual(response.data['id'], self.default_id)

    @tccounter("devicepower_detail", "get", ENABLE_TCCOUNTER)
    def test_get_instance_which_not_exist(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test get a instance by a wrong id
        """
        response = self.client.get(reverse('devicepower_detail', args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @tccounter("devicepower_detail", "put", ENABLE_TCCOUNTER)
    def test_put_200ok(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test put method 200 OK
        """
        with open('apiv1/module/device/tests/file/battery_0AvZF2p.dat', 'rb') as file:
            response = self.client.put(
                reverse('devicepower_detail', args=[self.default_id]),
                data={
                    'battery_level': 99,
                    'charging': True,
                    'battery_file': file,
                    'device': self.default_data['device'].id,
                    'cabinet': self.default_data['cabinet'].id,
                    'power_port': self.default_data['power_port'].id
                },
                format='multipart'
            )
        self.assertEqual(response.data['battery_level'], 99)

    @tccounter("devicepower_detail", "put", ENABLE_TCCOUNTER)
    def test_put_record_datetime(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test record_datetime in return data should be utc+8 time
        """
        self._extra_test_data()
        with open('apiv1/module/device/tests/file/battery_0AvZF2p.dat', 'rb') as file:
            response = self.client.put(
                reverse('devicepower_detail', args=[self.default_id]),
                data={
                    'battery_level': 50,
                    'charging': True,
                    'battery_file': file,
                    'record_datetime': '2099-10-28T00:00:00Z',
                    'device': self.device_for_test.id,
                    'cabinet': self.default_data['cabinet'].id,
                    'power_port': self.default_data['power_port'].id
                },
                format='multipart'
            )
        self.assertEqual(response.data['record_datetime'], '2099-10-28 08:00:00')

    @tccounter("devicepower_detail", "patch", ENABLE_TCCOUNTER)
    def test_patch_200ok(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test patch method 200 OK
        """
        response = self.client.patch(reverse('devicepower_detail', args=[self.default_id]), data={
            'battery_level': 80
        })
        self.assertEqual(response.data['battery_level'], 80)

    @tccounter("devicepower_detail", "patch", ENABLE_TCCOUNTER)
    def test_patch_battery_level_with_decimal(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test update battery_level field with decimal
        """
        response = self.client.patch(reverse('devicepower_detail', args=[self.default_id]), data={
            'battery_level': 99.99,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("devicepower_detail", "delete", ENABLE_TCCOUNTER)
    def test_delete_204_no_content(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test delete method 204 not content
        """
        response = self.client.delete(reverse('devicepower_detail', args=[self.default_id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @tccounter("devicepower_detail", "delete", ENABLE_TCCOUNTER)
    def test_delete_instance_do_not_exist(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test delete instance which is not exists
        """
        response = self.client.delete(reverse('devicepower_detail', args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
