from rest_framework.reverse import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from apiv1.module.job.models import JobTestArea
from reef.settings import ENABLE_TCCOUNTER


class TestCustomTag(APITestCase):

    def setUp(self):
        self.default_data = TestTool.load_default_data()
        self.default_id = self.default_data['job_test_area'].id

    @tccounter("jobtestarea_list", "get", ENABLE_TCCOUNTER)
    def test_get_200ok(self):
        """
        Date: 2019/10/22
        Author: Guozijun
        test get method 200 OK
        """
        response = self.client.get(reverse('jobtestarea_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("jobtestarea_list", "get", ENABLE_TCCOUNTER)
    def test_get_job_test_area_wanted_info(self):
        """
         Date: 2019/11/19
         Author: Guozijun
         test get fields you wanted
         """
        response = self.client.get(f"{reverse('jobtestarea_list')}?fields=id,description")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("jobtestarea_detail", "get", ENABLE_TCCOUNTER)
    def test_get_instance_by_id(self):
        """
        Date: 2019/10/22
        Author: Guozijun
        test get a instance by id
        """
        response = self.client.get(reverse('jobtestarea_detail', args=[self.default_id]))
        self.assertEqual(response.data['id'], self.default_id)

    @tccounter("jobtestarea_detail", "get", ENABLE_TCCOUNTER)
    def test_get_instance_which_id_not_exist(self):
        """
        Date: 2019/10/22
        Author: Guozijun
        test get a instance which do not exist
        """
        response = self.client.get(reverse('jobtestarea_list', args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @tccounter("jobtestarea_list", "post", ENABLE_TCCOUNTER)
    def test_post_201_create(self):
        """
        Date: 2019/10/22
        Author: Guozijun
        test post method 201 create
        """
        response = self.client.post(reverse('jobtestarea_list'), data={
            'description': 'description_test'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @tccounter("jobtestarea_list", "post", ENABLE_TCCOUNTER)
    def test_post_same_description(self):
        """
        Date: 2019/10/22
        Author: Guozijun
        test create a instance and description same with default data description
        """
        response = self.client.post(reverse('jobtestarea_list'), data={
            'description': self.default_data['job_test_area'].description
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("jobtestarea_list", "post", ENABLE_TCCOUNTER)
    def test_bulk_create(self):
        """
        Date: 2019/10/22
        Author: Guozijun
        test bulk create
        """
        custom_tags = [{'description': 'test1'},
                       {'description': 'test2'}]
        response = self.client.post(reverse('jobtestarea_list'), data=custom_tags)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @tccounter("jobtestarea_list", "post", ENABLE_TCCOUNTER)
    def test_bulk_create_with_a_instance_error(self):
        """
        Date: 2019/10/22
        Author: Guozijun
        test bulk create one error others all not be created
        """
        custom_tags = [{'description': 'test1'},
                       {'description': 'test2'},
                       {'description': None}]
        self.client.post(reverse('jobtestarea_list'), data=custom_tags)
        self.assertEqual(JobTestArea.objects.count() != 3, True)

    @tccounter("jobtestarea_detail", "put", ENABLE_TCCOUNTER)
    def test_put_200ok(self):
        """
        Date: 2019/10/22
        Author: Guozijun
        test put method 200 OK
        """
        response = self.client.put(reverse('jobtestarea_detail', args=[self.default_id]), data={
            'description': 'test'
        })
        self.assertEqual(response.data['description'], 'test')

    @tccounter("jobtestarea_detail", "put", ENABLE_TCCOUNTER)
    def test_put_error_filed(self):
        """
        Date: 2019/10/22
        Author: Guozijun
        test put a error filed
        """
        response = self.client.put(reverse('jobtestarea_detail', args=[self.default_id]), data={
            'descriptions': 'custom_tag_name1'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("jobtestarea_detail", "patch", ENABLE_TCCOUNTER)
    def test_patch_200ok(self):
        """
        Date: 2019/10/22
        Author: Guozijun
        test patch method 200 OK
        """
        response = self.client.patch(reverse('jobtestarea_detail', args=[self.default_id]), data={
            'description': 'test'
        })
        self.assertEqual(response.data['description'], 'test')

    @tccounter("jobtestarea_detail", "patch", ENABLE_TCCOUNTER)
    def test_patch_description_None(self):
        """
        Date: 2019/10/22
        Author: Guozijun
        test patch description filed to None
        """
        response = self.client.patch(reverse('jobtestarea_detail', args=[self.default_id]), data={
            'description': None
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("jobtestarea_detail", "delete", ENABLE_TCCOUNTER)
    def test_delete_204_no_content(self):
        """
        Date: 2019/10/22
        Author: Guozijun
        test delete method 204 not content
        """
        response = self.client.delete(reverse('jobtestarea_detail', args=[self.default_id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @tccounter("jobtestarea_detail", "delete", ENABLE_TCCOUNTER)
    def test_delete_instance_do_not_exist(self):
        """
        Date: 2019/10/22
        Author: Guozijun
        test delete instance which is not exists
        """
        response = self.client.delete(reverse('jobtestarea_detail', args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
