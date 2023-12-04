from datetime import datetime

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from apiv1.module.device.models import Device
from apiv1.module.job.models import Job
from apiv1.module.rds.models import Rds
from reef.settings import ENABLE_TCCOUNTER


class TestUploadRdsScreenShot(APITestCase):
    def setUp(self):
        self.default_data = TestTool.load_default_data()
        Rds.objects.create(
            start_time=timezone.make_aware(datetime(2018, 12, 12, 20, 21, 21)),
            device=Device.objects.get(device_label='device0'),
            job=Job.objects.get(job_label='job0'),
            tboard=self.default_data['tboard']
        )

    def upload_rds_screenshot(self, data) -> Response:
        with open('apiv1/module/rds/tests/file/1_snap.png', 'rb') as default_file:
            if 'rds_screen_shot' not in data:
                data['rds_screen_shot'] = default_file
            return self.client.post(
                path=reverse('upload_rds_screen_shot'),
                data=data,
                format='multipart'
            )

    @tccounter('upload_rds_screen_shot', 'post', ENABLE_TCCOUNTER)
    def test_upload_rds_screen_shot(self):
        """
        Date: 2019/11/14
        Author: Goufuqiang
        Describe: POST create rds_screen_shot
        """
        response = self.upload_rds_screenshot({
            'device': 'device0',
            'job': 'job0',
            'start_time': '2018_12_12_20_21_21',
            'file_name': 'file_name_bla'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

    @tccounter('upload_rds_screen_shot', 'post', ENABLE_TCCOUNTER)
    def test_file_name_required(self):
        """
        Date: 2019/11/14
        Author: Goufuqiang
        测试不提供file_name，应返回400 status
        """
        response = self.upload_rds_screenshot({
            'device': 'device0',
            'job': 'job0',
            'start_time': '2018_12_12_20_21_21',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
