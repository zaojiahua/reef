from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from apiv1.module.device.models import TempPort
from reef.settings import ENABLE_TCCOUNTER


class TestTempPort(APITestCase):
    def setUp(self):
        self.default_data = TestTool.load_default_data()
        self.default_id = self.default_data['temp_port'].id

    """
    Coral会在初始化的时候，推送已连接的感温片讯息至Reef
    在这个当下，感温片不可能保证已被使用者配置
    所以TempPort.description於新增时可为空
    但空的description对于使用者来说没有意义
    故description不可为空(null, empty)
    """

    @tccounter("tempport_detail", "put", ENABLE_TCCOUNTER)
    def test_description_cannot_be_null_when_update(self):
        """
        Date: 2018/12/29
        Latest updated: 2019/1/2 by Raymond
        Author: Raymond
        TempPort.description can not be null
        """
        tempport = TempPort.objects.create(
            port='PA-01',
        )
        response = self.client.put(
            reverse('tempport_detail', kwargs={'pk': tempport.id}),
            data={
                'port': 'PA-01',
                'description': None
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("tempport_detail", "patch", ENABLE_TCCOUNTER)
    def test_description_cannot_be_null_when_partial_update(self):
        """
        Date: 2018/12/29
        Latest updated: 2019/1/2 by Raymond
        Author: Raymond
        TempPort.description can not be null
        """
        tempport = TempPort.objects.create(
            port='PA-01',
        )
        response = self.client.patch(
            reverse('tempport_detail', kwargs={'pk': tempport.id}),
            data={
                'port': 'PA-01',
                'description': None
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    @tccounter("tempport_detail", "put", ENABLE_TCCOUNTER)
    def test_description_cannot_be_omit_in_update(self):
        """
        Date: 2019/1/2
        Author: Raymond
        TempPort.description can be omit except in updating
        """
        tempport = TempPort.objects.create(
            port='PA-01',
        )
        response = self.client.put(
            reverse('tempport_detail', kwargs={'pk': tempport.id}),
            data={
                'port': 'PA-01',
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)

    @tccounter("tempport_list", "get", ENABLE_TCCOUNTER)
    def test_get_200ok(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test get method 200 OK
        """
        response = self.client.get(reverse('tempport_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("tempport_list", "get", ENABLE_TCCOUNTER)
    def test_get_temp_port_wanted_info(self):
        """
         Date: 2019/10/26
         Author: Guozijun
         test get fields you wanted
         """
        response = self.client.get(f"{reverse('tempport_list')}?fields=port,description")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("tempport_detail", "get", ENABLE_TCCOUNTER)
    def test_get_instance_by_id(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test get a instance by id
        """
        response = self.client.get(reverse('tempport_detail', args=[self.default_id]))
        self.assertEqual(response.data['id'], self.default_id)

    @tccounter("tempport_detail", "get", ENABLE_TCCOUNTER)
    def test_get_instance_which_not_exist(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test get a instance by a wrong id
        """
        response = self.client.get(reverse('tempport_detail', args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @tccounter("tempport_detail", "put", ENABLE_TCCOUNTER)
    def test_put_200ok(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test put method 200 OK
        """
        response = self.client.put(reverse('tempport_detail', args=[self.default_id]), data={
            'port': 'changed',
            'description': self.default_data['temp_port'].description
        })
        self.assertEqual(response.data['port'], 'changed')

    @tccounter("tempport_detail", "patch", ENABLE_TCCOUNTER)
    def test_patch_200ok(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test patch method 200 OK
        """
        response = self.client.patch(reverse('tempport_detail', args=[self.default_id]), data={
            'port': 'changed'
        })
        self.assertEqual(response.data['port'], 'changed')

    # ------------------------------------------------------------------------------------
    # test temp_port status
    # ------------------------------------------------------------------------------------
    def test_create_temp_port_status_idle(self):
        """
            Date: 2019/4/15
            Author: Guozijun
            TempPort create without device status: None ---> idle
        """
        self.assertEqual(TempPort.objects.filter(port='PA-0').first().status, 'idle')

    def test_create_temp_port_status_busy(self):
        """
            Date: 2019/4/15
            Author: Guozijun
            TempPort create with device status: None ---> busy
        """
        TempPort.objects.create(
            port='PA-1',
            description='top1',
            device=self.default_data['device']
        )
        self.assertEqual(TempPort.objects.filter(port='PA-1').first().status, 'busy')

    def test_patch_temp_port_status_busy(self):
        """
            Date: 2019/4/15
            Author: Guozijun
            pactch add device to tempport: None --->idle--->busy
        """
        self.client.patch(
            reverse('tempport_detail', kwargs={'pk': self.default_data['temp_port'].id}),
            data={
                'device': self.default_data['device'].id
            }
        )
        self.assertEqual(TempPort.objects.filter(port='PA-0').first().status, 'busy')

    def test_temp_port_create(self):
        """
        Date: 2019/06/12
        Author: Guozijun
        tempport: create   -->  trigger save signal    (null-->busy)
        """
        TempPort.objects.create(
            port='PA-1',
            description='top_1',
            device=self.default_data['device']
        )
        self.assertEqual(TempPort.objects.get(port='PA-1').status, 'busy')

    def test_temp_port_get_or_create(self):
        """
        Date: 2019/06/12
        Author: Guozijun
        tempport: get_or_create(create)   -->  trigger save signal  (null-->idel)
        """
        TempPort.objects.get_or_create(
            port='PA-1',
            description='top_1',
        )
        self.assertEqual(TempPort.objects.get(port='PA-1').status, 'idle')

    def test_temp_port_update(self):
        """
        Date: 2019/06/12
        Author: Guozijun
        tempport: update   -->  trigger update signal     (null-->idle-->busy)
        """
        TempPort.objects.create(
            port='PA-1',
            description='top_1',
        )
        self.assertEqual(TempPort.objects.get(port='PA-1').status, 'idle')
        TempPort.objects.filter(port='PA-1').update(device=self.default_data['device'])
        self.assertEqual(TempPort.objects.get(port='PA-1').status, 'busy')

    def test_temp_port_update_or_create(self):
        """
        Date: 2019/06/12
        Author: Guozijun
        tempport: update_or_create(update)   -->  trigger update signal   (null-->idle-->busy)
        """
        self.assertEqual(TempPort.objects.get(id=self.default_data['temp_port'].id).status, 'idle')
        TempPort.objects.update_or_create(
            port=self.default_data['temp_port'].port,
            device=self.default_data['device']
        )
        self.assertEqual(TempPort.objects.get(id=self.default_data['temp_port'].id).status, 'busy')
