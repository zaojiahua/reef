from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from reef.settings import ENABLE_TCCOUNTER


class TestPhoneModel(APITestCase):

    def setUp(self):
        self.default_data = TestTool.load_default_data()
        self.default_id = self.default_data['phone_model'].id

    @tccounter("phonemodel_list", "get", ENABLE_TCCOUNTER)
    def test_get_200ok(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test get method 200 OK
        """
        response = self.client.get(reverse('phonemodel_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("phonemodel_list", "get", ENABLE_TCCOUNTER)
    def test_get_phone_model_wanted_info(self):
        """
         Date: 2019/10/26
         Author: Guozijun
         test get fields you wanted
         """
        response = self.client.get(f"{reverse('phonemodel_list')}?fields=phone_model_name,cpu_name")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("phonemodel_detail", "get", ENABLE_TCCOUNTER)
    def test_get_instance_by_id(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test get a instance by id
        """
        response = self.client.get(reverse('phonemodel_detail', args=[self.default_id]))
        self.assertEqual(response.data['id'], self.default_id)

    @tccounter("phonemodel_detail", "get", ENABLE_TCCOUNTER)
    def test_get_instance_which_not_exist(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test get a instance by a wrong id
        """
        response = self.client.get(reverse('phonemodel_detail', args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @tccounter("phonemodel_list", "post", ENABLE_TCCOUNTER)
    def test_post_201_create(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test post method 201 create
        """
        response = self.client.post(reverse('phonemodel_list'), data={
            'phone_model_name': 'test_name',
            'manufacturer': self.default_data['manufacturer'].id,
            'cpu_name': 'test_cpu_name'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @tccounter("phonemodel_list", "post", ENABLE_TCCOUNTER)
    def test_post_phone_model_name_not_unique(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test phone_model_name field's unique
        """
        response = self.client.post(reverse('phonemodel_list'), data={
            'phone_model_name': self.default_data['phone_model'].phone_model_name,
            'manufacturer': self.default_data['manufacturer'].id,
            'cpu_name': None
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("phonemodel_list", "post", ENABLE_TCCOUNTER)
    def test_bulk_create(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test bulk create
        """
        android_versions = [{'phone_model_name': 'test_name1',
                             'manufacturer': self.default_data['manufacturer'].id,
                             'cpu_name': 'test_cpu_name1'},
                            {'phone_model_name': 'test_name2',
                             'manufacturer': self.default_data['manufacturer'].id,
                             'cpu_name': 'test_cpu_name2'}]
        response = self.client.post(reverse('phonemodel_list'), data=android_versions)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @tccounter("phonemodel_detail", "put", ENABLE_TCCOUNTER)
    def test_put_200ok(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test put method 200 OK
        """
        response = self.client.put(reverse('phonemodel_detail', args=[self.default_id]), data={
            'phone_model_name': 'changed',
            'manufacturer': self.default_data['manufacturer'].id
        })
        self.assertEqual(response.data['phone_model_name'], 'changed')

    @tccounter("phonemodel_detail", "put", ENABLE_TCCOUNTER)
    def test_put_cpu_name_can_be_none(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test update a instance cup_name field can be None
        """
        response = self.client.put(reverse('phonemodel_detail', args=[self.default_id]), data={
            'phone_model_name': 'test_name',
            'manufacturer': self.default_data['manufacturer'].id,
            'cpu_name': None
        })
        self.assertEqual(response.data['cpu_name'], None)

    @tccounter("phonemodel_detail", "patch", ENABLE_TCCOUNTER)
    def test_patch_200ok(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test patch method 200 OK
        """
        response = self.client.patch(reverse('phonemodel_detail', args=[self.default_id]), data={
            'phone_model_name': 'changed'
        })
        self.assertEqual(response.data['phone_model_name'], 'changed')

    @tccounter("phonemodel_detail", "patch", ENABLE_TCCOUNTER)
    def test_patch_cpu_name_length_more_than_50(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test partial update cpu_name field length more than 50
        """
        response = self.client.patch(reverse('phonemodel_detail', args=[self.default_id]), data={
            'phone_model_name': 'test_test_test_test_test_test_test_test_test_test_test_test'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("phonemodel_detail", "delete", ENABLE_TCCOUNTER)
    def test_delete_204_no_content(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test delete method 204 not content
        """
        response = self.client.delete(reverse('phonemodel_detail', args=[self.default_id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @tccounter("phonemodel_detail", "delete", ENABLE_TCCOUNTER)
    def test_delete_instance_do_not_exist(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test delete instance which is not exists
        """
        response = self.client.delete(reverse('phonemodel_detail', args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
