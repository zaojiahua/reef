from rest_framework.reverse import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from reef.settings import ENABLE_TCCOUNTER


class TestJobUploadMultiResFile(APITestCase):

    def setUp(self):
        self.default_data = TestTool.load_default_data()

    @tccounter("job_upload_multi_res_file", "post", ENABLE_TCCOUNTER)
    def test_post_ok(self):
        """
        Date: 2019/12/15
        Author: Guozijun
        test post method 201 CREATED
        """
        file1 = open('apiv1/module/job/tests/file/0JBblockDict4front.json', 'rb')
        file2 = open('apiv1/module/job/tests/file/4c-blueTooth.png', 'rb')
        response = self.client.post(reverse('job_upload_multi_res_file'), data={
            "file": [file1, file2],
            "job_flow": self.default_data['job_flow'].id,
        }, format='multipart')
        file1.close()
        file2.close()
        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['res_file']), 2)

    @tccounter("job_upload_multi_res_file", "post", ENABLE_TCCOUNTER)
    def test_post_duplicate_file(self):
        """
        Date: 2019/12/15
        Author: Guozijun
        test post same file against job name unique_together
        """
        file1 = open('apiv1/module/job/tests/file/0JBblockDict4front.json', 'rb')
        file2 = open('apiv1/module/job/tests/file/0JBblockDict4front.json', 'rb')
        response = self.client.post(reverse('job_upload_multi_res_file'), data={
            "file": [file1, file2],
            "job_flow": self.default_data['job_flow'].id,
        }, format='multipart')
        file1.close()
        file2.close()
        self.assertEquals(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @tccounter("job_upload_multi_res_file", "post", ENABLE_TCCOUNTER)
    def test_post_file_name_is_chinese(self):
        """
        Date: 2020/03/04
        Author: Guozijun
        test post a file which file name use chinese
        """
        file1 = open('apiv1/module/job/tests/file/中文测试.json', 'rb')
        response = self.client.post(reverse('job_upload_multi_res_file'), data={
            "file": [file1],
            "job_flow": self.default_data['job_flow'].id,
        }, format='multipart')
        file1.close()
        print(response.content)
        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
