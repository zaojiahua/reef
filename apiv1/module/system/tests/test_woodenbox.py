from rest_framework.test import APITestCase
from rest_framework.reverse import reverse
from rest_framework import status
from apiv1.core.test import TestTool, tccounter
from apiv1.module.system.models import WoodenBox
from reef.settings import ENABLE_TCCOUNTER
from collections import OrderedDict


class TestWoodenBox(APITestCase):

    def setUp(self):
        self.default_data = TestTool.load_default_data()
        self.default_data['woodenbox'] = WoodenBox.objects.create(
            name='TA-01',
            type='power',
            ip='127.0.0.1',
            config={},
            cabinet=self.default_data['cabinet']
        )
        self.woodenbox_id = self.default_data['woodenbox'].id

    @tccounter('woodenbox_list', 'get', ENABLE_TCCOUNTER)
    def test_get_200ok(self):
        """
        Date 2020/3/30
        Author: Goufuqiang
        Get woodenbox ok
        """
        response = self.client.get(
            reverse('woodenbox_list')
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('woodenbox_list', 'get', ENABLE_TCCOUNTER)
    def test_get_response_data(self):
        """
        Date 2020/3/30
        Author: Goufuqiang
        Checkout response data
        """
        response = self.client.get(
            reverse('woodenbox_list'), data={'fields': 'cabinet.id'}
        )
        self.assertEqual(response.data['woodenbox'][0].get('cabinet', None)['id'], self.default_data['cabinet'].id)

    @tccounter('woodenbox_detail', 'get', ENABLE_TCCOUNTER)
    def test_get_object_200ok(self):
        """
        Date 2020/3/30
        Author: Goufuqiang
        Get the object woodenbox
        """
        response = self.client.get(
            reverse('woodenbox_detail', args=(self.default_data['woodenbox'].id,))
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('woodenbox_detail', 'get', ENABLE_TCCOUNTER)
    def test_get_object_response_data(self):
        """
        Date 2020/3/30
        Author: Goufuqiang
        Get the object woodenbox. Checkout cabinet
        """
        response = self.client.get(
            reverse('woodenbox_detail', args=(self.woodenbox_id,)), data={'fields': 'cabinet.id'}
        )
        self.assertIsInstance(response.data, dict)
        self.assertEqual(response.data.get('cabinet', None).get('id', None), self.default_data['cabinet'].id)

    @tccounter('woodenbox_list', 'post', ENABLE_TCCOUNTER)
    def test_post_200ok(self):
        """
        Date 2020/3/30
        Author: Goufuqiang
        Create WoodenBox
        """
        response = self.client.post(
            reverse('woodenbox_list'),
            data={
                'name': 'TA-02',
                'type': 'power',
                'ip': '127.0.0.2',
                'config': {},
                'cabinet': self.default_data['cabinet'].id
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @tccounter('woodenbox_list', 'post', ENABLE_TCCOUNTER)
    def test_post_ip_and_cabinet_unique_together(self):
        """
        Date 2020/3/30
        Author: Goufuqiang
        ip, cabinet unique together
        """
        response = self.client.post(
            reverse('woodenbox_list'),
            data={
                'name': 'TA-02',
                'type': 'power',
                'ip': '127.0.0.1',
                'config': {},
                'cabinet': self.default_data['cabinet'].id
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter('woodenbox_detail', 'put', ENABLE_TCCOUNTER)
    def test_put_200ok(self):
        """
        Date 2020/3/30
        Author: Goufuqiang
        PUT
        """
        response = self.client.put(
            reverse('woodenbox_detail', args=(self.woodenbox_id,)),
            data={
                'name': 'TA-02',
                'type': 'power',
                'ip': '127.0.0.2',
                'config': {},
                'cabinet': self.default_data['cabinet'].id
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('woodenbox_detail', 'put', ENABLE_TCCOUNTER)
    def test_put_ip_exist(self):
        """
        Date 2020/3/30
        Author: Goufuqiang
        update ip exist woodenbox
        """
        # create ip is 127.0.0.2 woodenbox
        self.default_data['woodenbox'] = WoodenBox.objects.create(
            name='TA-02',
            type='power',
            ip='127.0.0.2',
            config={},
            cabinet=self.default_data['cabinet']
        )
        response = self.client.put(
            reverse('woodenbox_detail', args=(self.woodenbox_id,)),
            data={
                'name': 'TA-02',
                'type': 'power',
                'ip': '127.0.0.2',
                'config': {},
                'cabinet': self.default_data['cabinet'].id
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter('woodenbox_detail', 'patch', ENABLE_TCCOUNTER)
    def test_put_200ok(self):
        """
        Date 2020/3/30
        Author: Goufuqiang
        PATCH
        """
        response = self.client.patch(
            reverse('woodenbox_detail', args=(self.woodenbox_id,)),
            data={
                'ip': '127.0.0.2',
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('woodenbox_detail', 'patch', ENABLE_TCCOUNTER)
    def test_put_200ok(self):
        """
        Date 2020/3/30
        Author: Goufuqiang
        update ip to exist data
        """
        self.default_data['woodenbox'] = WoodenBox.objects.create(
            name='TA-02',
            type='power',
            ip='127.0.0.2',
            config={},
            cabinet=self.default_data['cabinet']
        )
        response = self.client.patch(
            reverse('woodenbox_detail', args=(self.woodenbox_id,)),
            data={
                'ip': '127.0.0.2',
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter('woodenbox_detail', 'delete', ENABLE_TCCOUNTER)
    def test_delete_200ok(self):
        """
        Date 2020/3/30
        Author: Goufuqiang
        update ip to exist data
        """
        response = self.client.delete(
            reverse('woodenbox_detail', args=(self.woodenbox_id,))
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @tccounter('woodenbox_detail', 'delete', ENABLE_TCCOUNTER)
    def test_delete_object_not_exist(self):
        """
        Date 2020/3/30
        Author: Goufuqiang
        delete not exist object
        """
        response = self.client.delete(
            reverse('woodenbox_detail', args=(0,))
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
