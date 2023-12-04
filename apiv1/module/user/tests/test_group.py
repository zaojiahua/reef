from rest_framework.test import APITestCase
from rest_framework.reverse import reverse
from rest_framework import status
from apiv1.core.test import TestTool, tccounter
from reef.settings import ENABLE_TCCOUNTER


class TestGroup(APITestCase):

    def setUp(self):
        self.create_label = "1"
        self.default_data = TestTool.load_default_data(self.create_label)
        response = self.client.post(
            reverse('group_list'),
            data={
                "name": "test_group"
            }
        )
        self.group_id = response.data.get('id', None)

    @tccounter('group_list', 'get', ENABLE_TCCOUNTER)
    def test_get_group_200ok(self):
        """
        Date 2019/10/22
        Author: Goufuqiang
        Describe: GET /cedar/group/
        """
        response = self.client.get(
            reverse('group_list')
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('group_list', 'get', ENABLE_TCCOUNTER)
    def test_get_group_response_type(self):
        response = self.client.get(
            reverse('group_list')
        )
        self.assertIsInstance(response.data.get('groups', None), list)

    @tccounter('group_detail', 'get', ENABLE_TCCOUNTER)
    def test_get_group_id_200ok(self):
        """
        Date 2019/10/22
        Author: Goufuqiang
        Describe: GET /cedar/group/{id}/
        """
        response = self.client.get(
            reverse('group_detail', args=(self.group_id,))
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('group_detail', 'get', ENABLE_TCCOUNTER)
    def test_get_group_id_response_data(self):
        """
        Date 2019/10/22
        Author: Goufuqiang
        Describe: get response data
        """
        response = self.client.get(
            reverse('group_detail', args=(self.group_id,))
        )
        self.assertEqual(response.data.get('name', None), 'test_group')

    @tccounter('group_list', 'post', ENABLE_TCCOUNTER)
    def test_post_group_200ok(self):
        response = self.client.post(
            reverse('group_list'),
            data={
                "name": "test_group1"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @tccounter('group_list', 'post', ENABLE_TCCOUNTER)
    def test_post_group_name_is_empty(self):
        response = self.client.post(
            reverse('group_list'),
            data={
                "name": ""
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter('group_detail', 'put', ENABLE_TCCOUNTER)
    def test_put_group_200ok(self):
        response = self.client.put(
            reverse('group_detail', args=(self.group_id,)),
            data={
                "name": "test_group2"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('group_detail', 'put', ENABLE_TCCOUNTER)
    def test_put_group_response_data(self):
        response = self.client.put(
            reverse('group_detail', args=(self.group_id,)),
            data={
                "name": "test_group3"
            }
        )
        self.assertEqual(response.data.get("name"), "test_group3")

    @tccounter('group_detail', 'patch', ENABLE_TCCOUNTER)
    def test_patch_group_200ok(self):
        response = self.client.patch(
            reverse('group_detail', args=(self.group_id,)),
            data={
                "name": "test_group3"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('group_detail', 'patch', ENABLE_TCCOUNTER)
    def test_patch_group_response_data(self):
        response = self.client.patch(
            reverse('group_detail', args=(self.group_id,)),
            data={
                "name": "test_group4"
            }
        )
        self.assertEqual(response.data.get("name"), "test_group4")

    @tccounter('group_detail', 'delete', ENABLE_TCCOUNTER)
    def test_delete_group_200ok(self):
        response = self.client.delete(
            reverse('group_detail', args=(self.group_id,))
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @tccounter('group_detail', 'delete', ENABLE_TCCOUNTER)
    def test_delete_group_repeat_delete(self):
        response = self.client.delete(
            reverse('group_detail', args=(self.group_id,))
        )
        response = self.client.delete(
            reverse('group_detail', args=(self.group_id,))
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
