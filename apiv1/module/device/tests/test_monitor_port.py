from rest_framework.reverse import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from reef.settings import ENABLE_TCCOUNTER


class TestMonitorPort(APITestCase):

    def setUp(self):
        self.default_data = TestTool.load_default_data()
        self.default_id = self.default_data['monitor_port'].id

    @tccounter("monitorport_list", "get", ENABLE_TCCOUNTER)
    def test_get_200ok(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test get method 200 OK
        """
        response = self.client.get(reverse('monitorport_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("monitorport_list", "get", ENABLE_TCCOUNTER)
    def test_get_monitor_port_wanted_info(self):
        """
         Date: 2019/10/26
         Author: Guozijun
         test get fields you wanted
         """
        response = self.client.get(f"{reverse('monitorport_list')}?fields=port")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("monitorport_detail", "get", ENABLE_TCCOUNTER)
    def test_get_instance_by_id(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test get a instance by id
        """
        response = self.client.get(reverse('monitorport_detail', args=[self.default_id]))
        self.assertEqual(response.data['id'], self.default_id)

    @tccounter("monitorport_detail", "get", ENABLE_TCCOUNTER)
    def test_get_instance_which_not_exist(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test get a instance by a wrong id
        """
        response = self.client.get(reverse('monitorport_detail', args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @tccounter("monitorport_list", "post", ENABLE_TCCOUNTER)
    def test_post_201_create(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test post method 201 create
        """
        response = self.client.post(reverse('monitorport_list'), data={
            'port': '01'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @tccounter("monitorport_list", "post", ENABLE_TCCOUNTER)
    def test_post_port_field_same_as_exist(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test port's unique
        """
        response = self.client.post(reverse('monitorport_list'), data={
            'port': self.default_data['monitor_port'].port
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("monitorport_list", "post", ENABLE_TCCOUNTER)
    def test_bulk_create(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test bulk create
        """
        monitor_ports = [{'port': '01'},
                         {'port': '02'}]
        response = self.client.post(reverse('monitorport_list'), data=monitor_ports)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @tccounter("monitorport_detail", "put", ENABLE_TCCOUNTER)
    def test_put_200ok(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test put method 200 OK
        """
        response = self.client.put(reverse('monitorport_detail', args=[self.default_id]), data={
            'port': 'changed'
        })
        self.assertEqual(response.data['port'], 'changed')

    @tccounter("monitorport_detail", "put", ENABLE_TCCOUNTER)
    def test_put_version_length_more_than_50(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test update port field length more than 50
        """
        response = self.client.put(reverse('monitorport_detail', args=[self.default_id]), data={
            'port': 'test_test_test_test_test_test_test_test_test_test_test_test'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("monitorport_detail", "patch", ENABLE_TCCOUNTER)
    def test_patch_200ok(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test patch method 200 OK
        """
        response = self.client.patch(reverse('monitorport_detail', args=[self.default_id]), data={
            'port': 'changed'
        })
        self.assertEqual(response.data['port'], 'changed')

    @tccounter("monitorport_detail", "patch", ENABLE_TCCOUNTER)
    def test_patch_filed_input_error_type(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test patch port filed string type but input list
        """
        response = self.client.patch(reverse('monitorport_detail', args=[self.default_id]), data={
            'port': [1, 2]
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("monitorport_detail", "delete", ENABLE_TCCOUNTER)
    def test_delete_204_no_content(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test delete method 204 not content
        """
        response = self.client.delete(reverse('monitorport_detail', args=[self.default_id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @tccounter("monitorport_detail", "delete", ENABLE_TCCOUNTER)
    def test_delete_instance_do_not_exist(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test delete instance which is not exists
        """
        response = self.client.delete(reverse('monitorport_detail', args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
