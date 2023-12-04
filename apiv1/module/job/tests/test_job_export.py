import json
import os
from io import StringIO

from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework.reverse import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from apiv1.module.job.models import Job
from reef.settings import ENABLE_TCCOUNTER, JOB_EXPORT_ZIP_ROOT


class TestJobExport(APITestCase):

    def setUp(self):
        self.default_data = TestTool.load_default_data()

    def _add_extra_data(self):
        f = StringIO()
        f.write(json.dumps({'test': 'test'}))
        up_file = InMemoryUploadedFile(f, None, "ui.json", None, None, None, None)
        self.job_test = Job.objects.create(
                        job_label='label',
                        job_name='name',
                        description='description',
                        author=self.default_data['user'],
                        ui_json_file=up_file
                    )

    @tccounter("job_export", "post", ENABLE_TCCOUNTER)
    def test_post_200ok(self):
        """
        Date: 2020/02/24
        Author: Guozijun
        test post method 200 OK
        """
        self._add_extra_data()
        response = self.client.post(reverse('job_export'), data={
            'job_ids': [self.job_test.id],
            'user_id': self.default_data['user'].id
        })
        print(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("job_export", "post", ENABLE_TCCOUNTER)
    def test_post_id_witch_is_not_exist(self):
        """
        Date: 2020/02/24
        Author: Guozijun
        test post export job id which not exist
        """
        self._add_extra_data()
        response = self.client.post(reverse('job_export'), data={
            'id': 999
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

