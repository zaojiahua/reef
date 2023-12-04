from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.utils import timezone

from apiv1.module.rds.models import Rds
from apiv1.module.device.models import Device
from apiv1.module.tboard.models import TBoard, TBoardJob
from apiv1.core.test import TestTool
from apiv1.core.test import tccounter
from reef.settings import ENABLE_TCCOUNTER


class TestGetTBoardProgress(APITestCase):
    def setUp(self):
        self.default_data = TestTool.load_default_data()

    def add_extra_date(self):
        self.device_for_test = Device.objects.create(
            device_label='device_label1',
            device_name='device_name1',
            cpu_id='CPU-Z',
            rom_version=self.default_data['rom_version'],
        )
        self.tboard_for_test = TBoard.objects.create(
            author=self.default_data['user'],
            repeat_time=1,
            board_name='board_name1',
            finished_flag=False,
            board_stamp=timezone.now(),
            end_time=timezone.now(),
        )
        self.rds_for_test = Rds.objects.create(
            job_id=self.default_data['job'].id,
            device_id=self.device_for_test.id,
            tboard_id=self.tboard_for_test.id,
            start_time=timezone.now(),
            end_time=timezone.now(),
            job_assessment_value='1'
        )
        TBoardJob(tboard=self.tboard_for_test, job=self.default_data['job'], order=0).save()
        self.tboard_for_test.device.add(*[self.device_for_test])

    @tccounter("get_tboard_progress", "get", ENABLE_TCCOUNTER)
    def test_200ok(self):
        """
        Date: 2019/11/19
        Author: wengmeijia
        Describe: GET statistics/get_tboard_progress/
        """
        self.add_extra_date()
        response = self.client.get(
            reverse('get_tboard_progress') + '?tboards={}'.format(self.tboard_for_test.id)
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
