from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from reef.settings import ENABLE_TCCOUNTER


class TestRomVersion(APITestCase):

    def setUp(self):
        self.default_data = TestTool.load_default_data()
        self.default_id = self.default_data['rom_version'].id

    @tccounter("romversion_list", "get", ENABLE_TCCOUNTER)
    def test_get_200ok(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test get method 200 OK
        """
        response = self.client.get(reverse('romversion_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("romversion_list", "get", ENABLE_TCCOUNTER)
    def test_get_rom_version_wanted_info(self):
        """
         Date: 2019/10/26
         Author: Guozijun
         test get fields you wanted
         """
        response = self.client.get(f"{reverse('romversion_list')}?fields=manufacturer,manufacturer.id,version")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("romversion_detail", "get", ENABLE_TCCOUNTER)
    def test_get_instance_by_id(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test get a instance by id
        """
        response = self.client.get(reverse('romversion_detail', args=[self.default_id]))
        self.assertEqual(response.data['id'], self.default_id)

    @tccounter("romversion_detail", "get", ENABLE_TCCOUNTER)
    def test_get_instance_which_not_exist(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test get a instance by a wrong id
        """
        response = self.client.get(reverse('romversion_detail', args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @tccounter("romversion_list", "post", ENABLE_TCCOUNTER)
    def test_post_201_create(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test post method 201 create
        """
        response = self.client.post(reverse('romversion_list'), data={
            'manufacturer': self.default_data['manufacturer'].id,
            'version': '0.1'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @tccounter("romversion_list", "post", ENABLE_TCCOUNTER)
    def test_post_version_not_unique(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test version field's unique
        """
        response = self.client.post(reverse('romversion_list'), data={
            'manufacturer': self.default_data['manufacturer'].id,
            'version': self.default_data['rom_version'].version
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("romversion_list", "post", ENABLE_TCCOUNTER)
    def test_bulk_create(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test bulk create
        """
        rom_versions = [{'manufacturer': self.default_data['manufacturer'].id,
                         'version': 'test1'},
                        {'manufacturer': self.default_data['manufacturer'].id,
                         'version': 'test2'}]
        response = self.client.post(reverse('romversion_list'), data=rom_versions)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @tccounter("romversion_detail", "put", ENABLE_TCCOUNTER)
    def test_put_200ok(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test put method 200 OK
        """
        response = self.client.put(reverse('romversion_detail', args=[self.default_id]), data={
            'manufacturer': self.default_data['manufacturer'].id,
            'version': 'changed'
        })
        self.assertEqual(response.data['version'], 'changed')

    @tccounter("romversion_detail", "put", ENABLE_TCCOUNTER)
    def test_put_a_not_exist_instance(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test update a instance which not exist
        """
        response = self.client.put(reverse('romversion_detail', args=[999]), data={
            'manufacturer': self.default_data['manufacturer'].id,
            'version': 'test'
        })
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @tccounter("romversion_detail", "patch", ENABLE_TCCOUNTER)
    def test_patch_200ok(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test patch method 200 OK
        """
        response = self.client.patch(reverse('romversion_detail', args=[self.default_id]), data={
            'version': 'changed'
        })
        self.assertEqual(response.data['version'], 'changed')

    @tccounter("romversion_detail", "patch", ENABLE_TCCOUNTER)
    def test_patch_version_length_more_than_50(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test partial update version field length more than 50
        """
        response = self.client.patch(reverse('romversion_detail', args=[self.default_id]), data={
            'version': 'test_test_test_test_test_test_test_test_test_test_test_test'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("romversion_detail", "delete", ENABLE_TCCOUNTER)
    def test_delete_204_no_content(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test delete method 204 not content
        """
        response = self.client.delete(reverse('romversion_detail', args=[self.default_id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @tccounter("romversion_detail", "delete", ENABLE_TCCOUNTER)
    def test_delete_instance_do_not_exist(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test delete instance which is not exists
        """
        response = self.client.delete(reverse('romversion_detail', args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
