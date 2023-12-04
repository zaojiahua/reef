from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from django.db.models.deletion import ProtectedError

from apiv1.core.test import TestTool, tccounter
from reef.settings import ENABLE_TCCOUNTER


class TestSystem(APITestCase):

    def setUp(self):
        TestTool.load_default_data()

    @tccounter('system_list', 'get', ENABLE_TCCOUNTER)
    def test_get_systems_200ok(self):
        """
        Date 2019/10/30
        Author: Goufuqiang
        Describe: GET /cedar/system
        """
        response = self.client.get(reverse('system_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('system_list', 'get', ENABLE_TCCOUNTER)
    def test_get_system_response_data(self):
        """
        Date 2019/10/30
        Author: Goufuqiang
        Describe: GET /cedar/system
        """
        response = self.client.get(reverse('system_list'))
        self.assertIsInstance(response.data['systems'], list)

    @tccounter('system_detail', 'get', ENABLE_TCCOUNTER)
    def test_get_system_id_200ok(self):
        """
        Date 2019/10/30
        Author: Goufuqiang
        Describe: GET /cedar/system/{id}/
        """
        response = self.client.get(reverse('system_detail', args=(1,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('system_detail', 'get', ENABLE_TCCOUNTER)
    def test_get_system_id_response_data(self):
        """
        Date 2019/10/30
        Author: Goufuqiang
        Describe: ip_address in response data
        """
        response = self.client.get(reverse('system_detail', args=(1,)))
        self.assertIn('ip_address', response.data)

    @tccounter('system_list', 'post', ENABLE_TCCOUNTER)
    def test_post_system_200ok(self):
        """
        Date 2019/10/30
        Author: Goufuqiang
        Describe: POST /cedar/system
        """
        response = self.client.post(
            reverse('system_list'),
            data={
                'system_name': 'system',
                'ip_address': '192.168.1.100'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @tccounter('system_list', 'post', ENABLE_TCCOUNTER)
    def test_post_system_ip_address_is_empty(self):
        """
        Date 2019/11/20
        Author: Goufuqiang
        Describe: Test IP address is empty
        """
        response = self.client.post(
            reverse('system_list'),
            data={
                'system_name': 'system',
                'ip_address': ''
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter('system_list', 'get', ENABLE_TCCOUNTER)
    def test_get_system_wanted_info(self):
        """
        Date 2019/10/30
        Author: Goufuqiang
        Describe: POST /cedar/system
        """
        response = self.client.get(f"{reverse('system_list')}?fields=id,system_name")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('system_detail', 'put', ENABLE_TCCOUNTER)
    def test_put_system_200ok(self):
        """
        Date 2019/10/30
        Author: Goufuqiang
        Describe: PUT /cedar/system/{id}
        """
        response = self.client.put(
            reverse('system_detail', args=(1,)),
            data={
                'ip_address': '10.0.0.2',
                'system_name': 'system_test1',
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('system_detail', 'put', ENABLE_TCCOUNTER)
    def test_put_system_only_system_name_field(self):
        """
        Date 2019/10/30
        Author: Goufuqiang
        Describe: only put system_name field
        """
        response = self.client.put(
            reverse('system_detail', args=(1,)),
            data={
                'system_name': 'system_test'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter('system_detail', 'patch', ENABLE_TCCOUNTER)
    def test_patch_system_200ok(self):
        """
        Date 2019/10/30
        Author: Goufuqiang
        Describe: PATCH /cedar/system/{id}
        """
        response = self.client.patch(
            reverse('system_detail', args=(1,)),
            data={
                'system_name': 'system_test2'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('system_detail', 'patch', ENABLE_TCCOUNTER)
    def test_patch_system_only_update_system_name_field(self):
        """
        Date 2019/10/30
        Author: Goufuqiang
        Describe: only update system_name field
        """
        response = self.client.patch(
            reverse('system_detail', args=(1,)),
            data={
                'system_name': 'system_test2'
            }
        )
        self.assertEqual(response.data.get('system_name'), 'system_test2')

    @tccounter('system_detail', 'delete', ENABLE_TCCOUNTER)
    def test_delete_system_200ok(self):
        """
        Date 2019/10/30
        Author: Goufuqiang
        Describe: DELETE /cedar/system/{id}
        """

        with self.assertRaises(ProtectedError):
            response = self.client.delete(
                reverse('system_detail', args=(1,)),
            )

    @tccounter('system_detail', 'delete', ENABLE_TCCOUNTER)
    def test_delete_system_parameter_error(self):
        """
        Date 2019/10/30
        Author: Goufuqiang
        Describe:
        """
        response = self.client.delete(
            reverse('system_detail', args=(0,))
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)






