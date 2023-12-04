from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from apiv1.module.job.models import Job
from reef.settings import ENABLE_TCCOUNTER


class TestJobImport(APITestCase):

    def setUp(self):
        self.default_data = TestTool.load_default_data()

    @tccounter("job_import", "post", ENABLE_TCCOUNTER)
    def test_post_200ok(self):
        """
        Date: 2020/02/24
        Author: Guozijun
        test post method 200 OK
        """
        before = Job.objects.count()
        with open('apiv1/module/job/tests/file/job-27-28.zip', 'rb') as f:
            response = self.client.post(reverse('job_import'), data={
                'file': f
            }, format='multipart')
        after = Job.objects.count()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(after-before, 2)

    @tccounter("job_import", "post", ENABLE_TCCOUNTER)
    def test_post_error_file(self):
        """
        Date: 2020/02/24
        Author: Guozijun
        test post method 200 OK
        """
        with open('apiv1/module/job/tests/file/4c-blueTooth.png', 'rb') as f:
            response = self.client.post(reverse('job_import'), data={
                'file': f
            }, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
