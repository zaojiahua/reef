from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from apiv1.module.device.models import PowerPort
from reef.settings import ENABLE_TCCOUNTER


class TestPowerPort(APITestCase):

    def setUp(self):
        self.default_data = TestTool.load_default_data()
        self.default_id = self.default_data['power_port'].id

    @tccounter("powerport_list", "get", ENABLE_TCCOUNTER)
    def test_get_200ok(self):
        response = self.client.get(reverse('powerport_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("powerport_list", "get", ENABLE_TCCOUNTER)
    def test_get_powerport_wanted_info(self):
        response = self.client.get(f"{reverse('powerport_list')}?fields=id,port,status")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("powerport_detail", "get", ENABLE_TCCOUNTER)
    def test_get_instance_by_id(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test get a instance by id
        """
        response = self.client.get(reverse('powerport_detail', args=[self.default_id]))
        self.assertEqual(response.data['id'], self.default_id)

    @tccounter("powerport_detail", "get", ENABLE_TCCOUNTER)
    def test_get_instance_which_not_exist(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test get a instance by a wrong id
        """
        response = self.client.get(reverse('powerport_detail', args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @tccounter("powerport_detail", "put", ENABLE_TCCOUNTER)
    def test_put_200ok(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test put method 200 OK
        """
        response = self.client.put(reverse('powerport_detail', args=[self.default_id]), data={
            'port': 'changed'
        })
        self.assertEqual(response.data['port'], 'changed')

    @tccounter("powerport_detail", "put", ENABLE_TCCOUNTER)
    def test_put_version_length_more_than_50(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test update port field length more than 50
        """
        response = self.client.put(reverse('powerport_detail', args=[self.default_id]), data={
            'port': 'test_test_test_test_test_test_test_test_test_test_test_test'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("powerport_detail", "patch", ENABLE_TCCOUNTER)
    def test_patch_200ok(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test patch method 200 OK
        """
        response = self.client.patch(reverse('powerport_detail', args=[self.default_id]), data={
            'port': 'changed'
        })
        self.assertEqual(response.data['port'], 'changed')

    @tccounter("powerport_detail", "patch", ENABLE_TCCOUNTER)
    def test_patch_filed_input_error_type(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test patch port filed string type but input list
        """
        response = self.client.patch(reverse('powerport_detail', args=[self.default_id]), data={
            'port': [1, 2]
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ------------------------------------------------------------------------------------------
    # test power port status
    # ------------------------------------------------------------------------------------------
    def test_create_power_port_status_idle(self):
        """
            Date: 2019/4/15
            Author: Guozijun
            PowerPort create without device status: None ---> idle
        """
        self.assertEqual(PowerPort.objects.filter(port='PA-0').first().status, 'idle')

    def test_create_power_port_status_busy(self):
        """
            Date: 2019/4/15
            Author: Guozijun
            PowerPort create with device status: None ---> busy
        """
        PowerPort.objects.create(
            port='PA-1',
            device=self.default_data['device']
        )
        self.assertEqual(PowerPort.objects.filter(port='PA-1').first().status, 'busy')

    def test_patch_power_port_status_busy(self):
        """
            Date: 2019/4/15
            Author: Guozijun
            pactch add device to powerport : None --->idle--->busy
        """
        self.client.patch(
            reverse('powerport_detail', kwargs={'pk': self.default_data['power_port'].id}),
            data={
                'device': self.default_data['device'].id
            }
        )
        self.assertEqual(PowerPort.objects.filter(port='PA-0').first().status, 'busy')
