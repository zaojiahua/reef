from rest_framework.test import APITestCase
from rest_framework.reverse import reverse
from rest_framework import status
from apiv1.core.test import TestTool, tccounter
from reef.settings import ENABLE_TCCOUNTER


class TestCabinetRegist(APITestCase):
    def setUp(self):
        self.default_data = TestTool.load_default_data()
        self.default_cabinet_id = self.default_data['cabinet'].id

    @tccounter('cabinet_list', 'get', ENABLE_TCCOUNTER)
    def test_get_cabinet_200ok(self):
        """
        Date 2019/11/11
        Author: Goufuqiang
        Describe: GET /cedar/cabinet/
        """
        response = self.client.get(
            reverse('cabinet_list')
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('cabinet_list', 'get', ENABLE_TCCOUNTER)
    def test_get_cabinet_response_data(self):
        """
        Date 2019/11/11
        Author: Goufuqiang
        Describe: check response data cabinets type
        """
        response = self.client.get(
            reverse('cabinet_list')
        )
        self.assertIsInstance(response.data.get('cabinets'), list)

    @tccounter('cabinet_list', 'post', ENABLE_TCCOUNTER)
    def test_post_cabinet_200ok(self):
        """
        Date 2019/11/11
        Author: Goufuqiang
        Describe: POST /cedar/cabinet/
        """
        response = self.client.post(
            reverse('cabinet_list'),
            data={
                'cabinet_name': 'cabinet_test_name',
                'ip_address': '192.168.1.113',
                'belong_to': self.default_data['system'].id,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @tccounter('cabinet_list', 'post', ENABLE_TCCOUNTER)
    def test_post_cabinet_response_data(self):
        """
        Date 2019/11/11
        Author: Goufuqiang
        Describe: Create cabinet
        """
        response = self.client.post(
            reverse('cabinet_list'),
            data={
                'cabinet_name': 'cabinet_test_name',
                'ip_address': '192.168.1.112',
                'belong_to': self.default_data['system'].id,
            }
        )
        self.assertEqual(response.data.get('cabinet_name'), 'cabinet_test_name')

    @tccounter('cabinet_detail', 'get', ENABLE_TCCOUNTER)
    def test_get_cabinet_id_200ok(self):
        """
        Date 2019/11/11
        Author: Goufuqiang
        Describe: GET /cedar/cabinet/{id}
        """
        response = self.client.get(
            reverse('cabinet_detail', args=(self.default_cabinet_id,))
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('cabinet_detail', 'get', ENABLE_TCCOUNTER)
    def test_get_cabinet_id_cabinet_name(self):
        """
        Date 2019/11/11
        Author: Goufuqiang
        Describe: Get cabinet_name value
        """
        response = self.client.get(
            reverse('cabinet_detail', args=(self.default_cabinet_id,))
        )
        self.assertEqual(response.data.get('cabinet_name'), 'cabinet0')

    @tccounter('cabinet_detail', 'put', ENABLE_TCCOUNTER)
    def test_put_cabinet_200ok(self):
        """
        Date 2019/11/11
        Author: Goufuqiang
        Describe: PUT /cedar/cabinet/{id}
        """
        response = self.client.put(
            reverse('cabinet_detail', args=(self.default_cabinet_id,)),
            data={
                'cabinet_name': 'cabinet_test_name1',
                'ip_address': '192.168.1.100',
                'belong_to': self.default_data['system'].id,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('cabinet_detail', 'put', ENABLE_TCCOUNTER)
    def test_put_cabinet_update_cabinet_name(self):
        """
        Date 2019/11/11
        Author: Goufuqiang
        Describe: Update cabinet_name field
        """
        response = self.client.put(
            reverse('cabinet_detail', args=(self.default_cabinet_id,)),
            data={
                'cabinet_name': 'cabinet_test_name1',
                'ip_address': '10.0.0.11',
                'belong_to': self.default_data['system'].id,
            }
        )
        self.assertEqual(response.data.get('cabinet_name'), 'cabinet_test_name1')
        self.assertEqual(response.data.get('ip_address'), '10.0.0.11')

    @tccounter('cabinet_detail', 'patch', ENABLE_TCCOUNTER)
    def test_patch_cabinet_200ok(self):
        """
        Date 2019/11/11
        Author: Goufuqiang
        Describe: PATCH /cedar/cabinet/{id}
        """
        response = self.client.patch(
            reverse('cabinet_detail', args=(self.default_cabinet_id,)),
            data={
                'ip_address': '10.0.0.11',
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('cabinet_detail', 'patch', ENABLE_TCCOUNTER)
    def test_patch_cabinet_update_ip_address(self):
        """
        Date 2019/11/11
        Author: Goufuqiang
        Describe: Update ip_address field
        """
        response = self.client.patch(
            reverse('cabinet_detail', args=(self.default_cabinet_id,)),
            data={
                'ip_address': '10.0.0.11',
            }
        )
        self.assertEqual(response.data.get('ip_address'), '10.0.0.11')


    @tccounter('cabinet_detail', 'delete', ENABLE_TCCOUNTER)
    def test_delete_cabinet_no_existent_obj(self):
        """
        Date 2019/11/11
        Author: Goufuqiang
        Describe: Delete no existent cabinet data
        """
        response = self.client.delete(
            reverse('cabinet_detail', args=(0,))
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
