from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from reef.settings import ENABLE_TCCOUNTER


class TestManufacturer(APITestCase):

    def setUp(self):
        self.default_data = TestTool.load_default_data()
        self.default_id = self.default_data['manufacturer'].id

    @tccounter("manufacturer_list", "get", ENABLE_TCCOUNTER)
    def test_get_200ok(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test get method 200 OK
        """
        response = self.client.get(reverse('manufacturer_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("manufacturer_list", "get", ENABLE_TCCOUNTER)
    def test_get_manufacturer_wanted_info(self):
        """
         Date: 2019/10/26
         Author: Guozijun
         test get fields you wanted
         """
        response = self.client.get(f"{reverse('manufacturer_list')}?fields=manufacturer_name")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("manufacturer_detail", "get", ENABLE_TCCOUNTER)
    def test_get_instance_by_id(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test get a instance by id
        """
        response = self.client.get(reverse('manufacturer_detail', args=[self.default_id]))
        self.assertEqual(response.data['id'], self.default_id)

    @tccounter("manufacturer_detail", "get", ENABLE_TCCOUNTER)
    def test_get_instance_which_not_exist(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test get a instance by a wrong id
        """
        response = self.client.get(reverse('manufacturer_detail', args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @tccounter("manufacturer_list", "post", ENABLE_TCCOUNTER)
    def test_post_201_create(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test post method 201 create
        """
        response = self.client.post(reverse('manufacturer_list'), data={
            'manufacturer_name': 'test'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @tccounter("manufacturer_list", "post", ENABLE_TCCOUNTER)
    def test_post_manufacturer_name_not_unique(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test create a instance which not unique
        """
        response = self.client.post(reverse('manufacturer_list'), data={
            'manufacturer_name': self.default_data['manufacturer'].manufacturer_name
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("manufacturer_list", "post", ENABLE_TCCOUNTER)
    def test_bulk_create(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test bulk create
        """
        manufacturers = [{'manufacturer_name': 'test1'},
                         {'manufacturer_name': 'test2'}]
        response = self.client.post(reverse('manufacturer_list'), data=manufacturers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @tccounter("manufacturer_detail", "put", ENABLE_TCCOUNTER)
    def test_put_200ok(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test put method 200 OK
        """
        response = self.client.put(reverse('manufacturer_detail', args=[self.default_id]), data={
            'manufacturer_name': 'changed'
        })
        self.assertEqual(response.data['manufacturer_name'], 'changed')

    @tccounter("manufacturer_detail", "put", ENABLE_TCCOUNTER)
    def test_put_manufacturer_name_length_more_than_50(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test update manufacturer_name field length more than 50
        """
        response = self.client.put(reverse('manufacturer_detail', args=[self.default_id]), data={
            'manufacturer_name': 'test_test_test_test_test_test_test_test_test_test_test_test'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("manufacturer_detail", "patch", ENABLE_TCCOUNTER)
    def test_patch_200ok(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test patch method 200 OK
        """
        response = self.client.patch(reverse('manufacturer_detail', args=[self.default_id]), data={
            'manufacturer_name': 'changed'
        })
        self.assertEqual(response.data['manufacturer_name'], 'changed')

    @tccounter("manufacturer_detail", "patch", ENABLE_TCCOUNTER)
    def test_patch_manufacturer_name_input_error_type(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test patch manufacturer_name filed string type but input list
        """
        response = self.client.patch(reverse('manufacturer_detail', args=[self.default_id]), data={
            'manufacturer_name': [1, 2]
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("manufacturer_detail", "delete", ENABLE_TCCOUNTER)
    def test_delete_204_no_content(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test delete method 204 not content
        """
        response = self.client.delete(reverse('manufacturer_detail', args=[self.default_id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @tccounter("manufacturer_detail", "delete", ENABLE_TCCOUNTER)
    def test_delete_instance_do_not_exist(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test delete instance which is not exists
        """
        response = self.client.delete(reverse('manufacturer_detail', args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
