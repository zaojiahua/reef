from rest_framework.reverse import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from reef.settings import ENABLE_TCCOUNTER


class TestUnit(APITestCase):

    def setUp(self):
        self.default_data = TestTool.load_default_data()
        self.default_id = self.default_data['unit'].id

    @tccounter("unit_list", "get", ENABLE_TCCOUNTER)
    def test_get_200ok(self):
        """
        Date: 2019/12/15
        Author: Guozijun
        test get method 200 OK
        """
        response = self.client.get(reverse('unit_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("unit_list", "get", ENABLE_TCCOUNTER)
    def test_get_custom_tag_wanted_info(self):
        """
        Date: 2019/12/15
        Author: Guozijun
        test get fields you wanted
        """
        response = self.client.get(f"{reverse('unit_list')}?fields=unit_name,unit_content")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("unit_detail", "get", ENABLE_TCCOUNTER)
    def test_get_instance_by_id(self):
        """
        Date: 2019/12/15
        Author: Guozijun
        test get a instance by id
        """
        response = self.client.get(reverse('unit_detail', args=[self.default_id]))
        self.assertEqual(response.data['id'], self.default_id)

    @tccounter("unit_detail", "get", ENABLE_TCCOUNTER)
    def test_get_instance_which_id_not_exist(self):
        """
        Date: 2019/12/15
        Author: Guozijun
        test get a instance which do not exist
        """
        response = self.client.get(reverse('unit_detail', args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @tccounter("unit_list", "post", ENABLE_TCCOUNTER)
    def test_post_201_create(self):
        """
        Date: 2019/12/15
        Author: Guozijun
        test post method 201 create
        """
        response = self.client.post(reverse('unit_list'), data={
            'unit_name': 'name',
            'unit_content': {'unit': 'content'},
            'type': 'ADBC'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @tccounter("unit_list", "post", ENABLE_TCCOUNTER)
    def test_post_filed_which_is_unique(self):
        """
        Date: 2019/12/15
        Author: Guozijun
        test post a instance unit_name same as default ,but unit_name is unique
        """
        response = self.client.post(reverse('unit_list'), data={
            'unit_name': self.default_data['unit'].unit_name,
            'unit_content': {'unit': 'content'},
            'type': 'ADBC'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("unit_detail", "put", ENABLE_TCCOUNTER)
    def test_put_200ok(self):
        """
        Date: 2019/12/15
        Author: Guozijun
        test put method 200 OK
        """
        response = self.client.put(reverse('unit_detail', args=[self.default_id]), data={
            'unit_name': 'name',
            'unit_content': {},
            'type': 'changed'
        })
        self.assertEqual(response.data['type'], 'changed')

    @tccounter("unit_detail", "put", ENABLE_TCCOUNTER)
    def test_put_error_filed(self):
        """
        Date: 2019/12/15
        Author: Guozijun
        test put a error filed
        """
        response = self.client.put(reverse('unit_detail', args=[self.default_id]), data={
            'unit_name': 'name',
            'content': {'unit': 'content'},
            'type': 'ADBC'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("unit_detail", "patch", ENABLE_TCCOUNTER)
    def test_patch_200ok(self):
        """
        Date: 2019/12/15
        Author: Guozijun
        test patch method 200 OK
        """
        response = self.client.patch(reverse('unit_detail', args=[self.default_id]), data={
            'type': 'changed'
        })
        self.assertEqual(response.data['type'], 'changed')

    @tccounter("unit_detail", "patch", ENABLE_TCCOUNTER)
    def test_patch_unit_type_is_not_json(self):
        """
        Date: 2019/12/15
        Author: Guozijun
        test patch unit type field is not json
        """
        response = self.client.patch(reverse('unit_detail', args=[self.default_id]), data={
            'unit_content': 'str'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("unit_detail", "delete", ENABLE_TCCOUNTER)
    def test_delete_204_no_content(self):
        """
        Date: 2019/12/15
        Author: Guozijun
        test delete method 204 not content
        """
        response = self.client.delete(reverse('unit_detail', args=[self.default_id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @tccounter("unit_detail", "delete", ENABLE_TCCOUNTER)
    def test_delete_instance_do_not_exist(self):
        """
        Date: 2019/12/15
        Author: Guozijun
        test delete instance which is not exists
        """
        response = self.client.delete(reverse('unit_detail', args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


