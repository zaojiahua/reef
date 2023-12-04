from rest_framework.reverse import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from reef.settings import ENABLE_TCCOUNTER


class TestAndroidVersion(APITestCase):

    def setUp(self):
        self.default_data = TestTool.load_default_data()
        self.default_id = self.default_data['android_version'].id

    @tccounter("androidversion_list", "get", ENABLE_TCCOUNTER)
    def test_get_200ok(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test get method 200 OK
        """
        response = self.client.get(reverse('androidversion_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("androidversion_list", "get", ENABLE_TCCOUNTER)
    def test_get_android_version_wanted_info(self):
        """
         Date: 2019/10/26
         Author: Guozijun
         test get fields you wanted
         """
        response = self.client.get(f"{reverse('androidversion_list')}?fields=version")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("androidversion_detail", "get", ENABLE_TCCOUNTER)
    def test_get_instance_by_id(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test get a instance by id
        """
        response = self.client.get(reverse('androidversion_detail', args=[self.default_id]))
        self.assertEqual(response.data['id'], self.default_id)

    @tccounter("androidversion_detail", "get", ENABLE_TCCOUNTER)
    def test_get_instance_which_not_exist(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test get a instance by a wrong id
        """
        response = self.client.get(reverse('androidversion_detail', args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @tccounter("androidversion_list", "post", ENABLE_TCCOUNTER)
    def test_post_201_create(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test post method 201 create
        """
        response = self.client.post(reverse('androidversion_list'), data={
            'version': '10.0'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @tccounter("androidversion_list", "post", ENABLE_TCCOUNTER)
    def test_post_version_field_unique(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test create a instance which not unique
        """
        response = self.client.post(reverse('androidversion_list'), data={
            'version': self.default_data['android_version'].version
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("androidversion_list", "post", ENABLE_TCCOUNTER)
    def test_bulk_create(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test bulk create
        """
        android_versions = [{'version': 'test1'},
                            {'version': 'test2'}]
        response = self.client.post(reverse('androidversion_list'), data=android_versions)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @tccounter("androidversion_detail", "put", ENABLE_TCCOUNTER)
    def test_put_200ok(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test put method 200 OK
        """
        response = self.client.put(reverse('androidversion_detail', args=[self.default_id]), data={
            'version': 'changed_version'
        })
        self.assertEqual(response.data['version'], 'changed_version')

    @tccounter("androidversion_detail", "put", ENABLE_TCCOUNTER)
    def test_put_version_length_more_than_50(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test update version field length more than 50
        """
        response = self.client.put(reverse('androidversion_detail', args=[self.default_id]), data={
            'version': 'test_test_test_test_test_test_test_test_test_test_test_test'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("androidversion_detail", "patch", ENABLE_TCCOUNTER)
    def test_patch_200ok(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test patch method 200 OK
        """
        response = self.client.patch(reverse('androidversion_detail', args=[self.default_id]), data={
            'version': 'changed_version'
        })
        self.assertEqual(response.data['version'], 'changed_version')

    @tccounter("androidversion_detail", "patch", ENABLE_TCCOUNTER)
    def test_patch_filed_input_error_type(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test patch version filed string type but input list
        """
        response = self.client.patch(reverse('androidversion_detail', args=[self.default_id]), data={
            'version': [1, 2]
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("androidversion_detail", "delete", ENABLE_TCCOUNTER)
    def test_delete_204_no_content(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test delete method 204 not content
        """
        response = self.client.delete(reverse('androidversion_detail', args=[self.default_id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @tccounter("androidversion_detail", "delete", ENABLE_TCCOUNTER)
    def test_delete_instance_do_not_exist(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test delete instance which is not exists
        """
        response = self.client.delete(reverse('androidversion_detail', args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
