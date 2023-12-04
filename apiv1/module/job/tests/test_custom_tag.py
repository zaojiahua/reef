from rest_framework.reverse import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from reef.settings import ENABLE_TCCOUNTER


class TestCustomTag(APITestCase):

    def setUp(self):
        self.default_data = TestTool.load_default_data()
        self.default_id = self.default_data['custom_tag'].id

    @tccounter("customtag_list", "get", ENABLE_TCCOUNTER)
    def test_get_200ok(self):
        """
        Date: 2019/10/22
        Author: Guozijun
        test get method 200 OK
        """
        response = self.client.get(reverse('customtag_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("customtag_list", "get", ENABLE_TCCOUNTER)
    def test_get_custom_tag_wanted_info(self):
        """
         Date: 2019/11/19
         Author: Guozijun
         test get fields you wanted
         """
        response = self.client.get(f"{reverse('customtag_list')}?fields=custom_tag_name")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("customtag_detail", "get", ENABLE_TCCOUNTER)
    def test_get_instance_by_id(self):
        """
        Date: 2019/10/22
        Author: Guozijun
        test get a instance by id
        """
        response = self.client.get(reverse('customtag_detail', args=[self.default_id]))
        self.assertEqual(response.data['id'], self.default_id)

    @tccounter("customtag_detail", "get", ENABLE_TCCOUNTER)
    def test_get_instance_which_id_not_exist(self):
        """
        Date: 2019/10/22
        Author: Guozijun
        test get a instance which do not exist
        """
        response = self.client.get(reverse('customtag_detail', args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @tccounter("customtag_list", "post", ENABLE_TCCOUNTER)
    def test_post_201_create(self):
        """
        Date: 2019/10/22
        Author: Guozijun
        test post method 201 create
        """
        response = self.client.post(reverse('customtag_list'), data={
            'custom_tag_name': 'custom_test'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @tccounter("customtag_list", "post", ENABLE_TCCOUNTER)
    def test_post_custom_tag_name_length_more_than_50(self):
        """
        Date: 2019/10/22
        Author: Guozijun
        test post custom_tag_name field length more than 50
        """
        response = self.client.post(reverse('customtag_list'), data={
            'custom_tag_name': 'test_test_test_test_test_test_test_test_test_test_test_test'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("customtag_list", "post", ENABLE_TCCOUNTER)
    def test_bulk_create(self):
        """
        Date: 2019/10/22
        Author: Guozijun
        test bulk create
        """
        custom_tags = [{'custom_tag_name': 'test1'},
                       {'custom_tag_name': 'test2'}]
        response = self.client.post(reverse('customtag_list'), data=custom_tags)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @tccounter("customtag_detail", "put", ENABLE_TCCOUNTER)
    def test_put_200ok(self):
        """
        Date: 2019/10/22
        Author: Guozijun
        test put method 200 OK
        """
        response = self.client.put(reverse('customtag_detail', args=[self.default_id]), data={
            'custom_tag_name': 'custom_tag_name1'
        })
        # 更改之前custom_tag_name=custom_tag_name1
        self.assertEqual(response.data['custom_tag_name'], 'custom_tag_name1')

    @tccounter("customtag_detail", "put", ENABLE_TCCOUNTER)
    def test_put_error_filed(self):
        """
        Date: 2019/10/22
        Author: Guozijun
        test put a error filed
        """
        response = self.client.put(reverse('customtag_detail', args=[self.default_id]), data={
            'custom_tag': 'custom_tag_name1'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("customtag_detail", "patch", ENABLE_TCCOUNTER)
    def test_patch_200ok(self):
        """
        Date: 2019/10/22
        Author: Guozijun
        test patch method 200 OK
        """
        response = self.client.patch(reverse('customtag_detail', args=[self.default_id]), data={
            'custom_tag_name': 'custom_tag_name1'
        })
        self.assertEqual(response.data['custom_tag_name'], 'custom_tag_name1')

    @tccounter("customtag_detail", "patch", ENABLE_TCCOUNTER)
    def test_patch_filed_input_error_type(self):
        """
        Date: 2019/10/22
        Author: Guozijun
        test patch custom_tag_name filed string type but input json
        """
        response = self.client.patch(reverse('customtag_detail', args=[self.default_id]), data={
            'custom_tag_name': {'test': 123}
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("customtag_detail", "delete", ENABLE_TCCOUNTER)
    def test_delete_204_no_content(self):
        """
        Date: 2019/10/22
        Author: Guozijun
        test delete method 204 not content
        """
        response = self.client.delete(reverse('customtag_detail', args=[self.default_id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @tccounter("customtag_detail", "delete", ENABLE_TCCOUNTER)
    def test_delete_instance_do_not_exist(self):
        """
        Date: 2019/10/22
        Author: Guozijun
        test delete instance which is not exists
        """
        response = self.client.delete(reverse('customtag_detail', args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
