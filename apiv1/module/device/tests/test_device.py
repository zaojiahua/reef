from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from django.utils import timezone

from apiv1.core.test import TestTool, tccounter
from apiv1.module.device.models import Device, PowerPort
from apiv1.module.user.models import ReefUser
from apiv1.module.tboard.models import TBoard
from reef.settings import ENABLE_TCCOUNTER


class TestDevice(APITestCase):

    def setUp(self):
        self.default_data = TestTool.load_default_data()
        self.default_id = self.default_data['device'].id

    def _add_reef_user(self):
        self.ai_tester = ReefUser.objects.create(username='AITester',
                                                 password='123456',
                                                 date_joined=timezone.now()
                                                 )
        self.root = ReefUser.objects.create(username='root',
                                            password='123456',
                                            date_joined=timezone.now()
                                            )
        self.tboard_ai_tester = TBoard.objects.create(author=self.ai_tester,
                                                      repeat_time=1,
                                                      board_name='board_name_1',
                                                      finished_flag=True,
                                                      board_stamp=timezone.now(),
                                                      )

    @tccounter("device_list", "get", ENABLE_TCCOUNTER)
    def test_get_devices_all_info(self):
        response = self.client.get(reverse('device_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("device_list", "get", ENABLE_TCCOUNTER)
    def test_get_device_wanted_info(self):
        response = self.client.get(
            f"{reverse('device_list')}?fields=id,device_label,device_name,ip_address,cpu_id,start_time_key")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("device_list", "get", ENABLE_TCCOUNTER)
    def test_powert_port_relation(self):
        """
        Date: 2020/6/17
        Author: Goufuqiang
        device-list should return powerport data
        """
        response = self.client.get(reverse('device_list'), data={'fields': 'powerport'})
        self.assertIn('powerport', response.data['devices'][0])

    @tccounter("device_detail", "get", ENABLE_TCCOUNTER)
    def test_get_instance_by_id(self):
        """
        Date: 2019/111/20
        Author: Guozijun
        test get a instance by id
        """
        response = self.client.get(reverse('device_detail', args=[self.default_id]))
        self.assertEqual(response.data['id'], self.default_id)

    @tccounter("device_detail", "get", ENABLE_TCCOUNTER)
    def test_get_instance_which_not_exist(self):
        """
        Date: 2019/111/20
        Author: Guozijun
        test get a instance by a wrong id
        """
        response = self.client.get(reverse('device_detail', args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @tccounter("device_list", "post", ENABLE_TCCOUNTER)
    def test_post_201_create(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test post method 201 create
        """
        response = self.client.post(reverse('device_list'), data={
            'device_label': "label_test",
            'cpu_id': 'cpu_id',
            'rom_version': self.default_data['rom_version'].id,
            "monitor_index": [self.default_data['monitor_port'].id]
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @tccounter("device_list", "post", ENABLE_TCCOUNTER)
    def test_post_device_label_unique(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test create a instance device_label same as other device's device_label
        """
        response = self.client.post(reverse('device_list'), data={
            'device_label': self.default_data['device'].device_label,
            'cpu_id': 'cpu_id',
            'rom_version': self.default_data['rom_version'].id,
            "monitor_index": [self.default_data['monitor_port'].id]
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("device_detail", "put", ENABLE_TCCOUNTER)
    def test_put_200ok(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test put method 200 OK
        """
        response = self.client.put(reverse('device_detail', args=[self.default_id]), data={
            'device_label': self.default_data['device'].device_label,
            'cpu_id': 'cpu_id',
            'rom_version': self.default_data['rom_version'].id,
            "monitor_index": [self.default_data['monitor_port'].id]
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("device_detail", "put", ENABLE_TCCOUNTER)
    def test_put_many_to_many_filed(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test update monitor_index many_to_many filed but input not list
        """
        response = self.client.put(reverse('device_detail', args=[self.default_id]), data={
            'device_label': self.default_data['device'].device_label,
            'cpu_id': 'cpu_id',
            'rom_version': self.default_data['rom_version'].id,
            "monitor_index": [999]
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("device_detail", "patch", ENABLE_TCCOUNTER)
    def test_patch_200ok(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test patch method 200 OK
        """
        response = self.client.patch(reverse('device_detail', args=[self.default_id]), data={
            'device_label': 'change_device_label',
        })
        self.assertEqual(response.data['device_label'], 'change_device_label')

    @tccounter("device_detail", "patch", ENABLE_TCCOUNTER)
    def test_patch_power_port(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        initial : device.powerport = None    self.default_data['power_port'].device  = None
        partial_update : device.powerport = self.default_data['power_port']
        result : self.default_data['power_port'].device = device
        """
        self.assertEqual(self.default_data['power_port'].device, None)
        response = self.client.patch(reverse('device_detail', args=[self.default_id]), data={
            'powerport': self.default_data['power_port'].id,
        })
        self.assertEqual(PowerPort.objects.get(id=self.default_data['power_port'].id).device.id, self.default_id)

    @tccounter("device_detail", "delete", ENABLE_TCCOUNTER)
    def test_delete_204_no_content(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test delete method 204 not content
        """
        response = self.client.delete(reverse('device_detail', args=[self.default_id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @tccounter("device_detail", "delete", ENABLE_TCCOUNTER)
    def test_delete_instance_do_not_exist(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test delete instance which is not exists
        """
        response = self.client.delete(reverse('device_detail', args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)




