from rest_framework.reverse import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from apiv1.module.job.models import Job
from reef.settings import ENABLE_TCCOUNTER


class TestJobResFile(APITestCase):

    def setUp(self):
        self.default_data = TestTool.load_default_data()
        self.default_id = self.default_data['job_res_file'].id

    def add_extra_data(self):
        self.job_for_test = Job.objects.create(
            job_label='job1',
            job_name='job1',
            description='description',
            job_type='Sysjob'
        )

    @tccounter("job_res_file", "get", ENABLE_TCCOUNTER)
    def test_get_200ok(self):
        """
        Date: 2019/12/15
        Author: Guozijun
        test get method 200 OK
        """
        response = self.client.get(reverse('job_res_file'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)


