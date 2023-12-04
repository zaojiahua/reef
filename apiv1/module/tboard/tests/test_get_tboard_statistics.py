from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool
from apiv1.module.tboard.models import TBoardJob
from apiv1.core.test import tccounter
from reef.settings import ENABLE_TCCOUNTER

class TestGetTboardStatistics(APITestCase):
    @tccounter("get_tboard_statistics", "get", ENABLE_TCCOUNTER)
    def test_200ok(self):
        self.default_data = TestTool.load_default_data()
        response = self.client.get(
            reverse('get_tboard_statistics')
            + '?tboard_id={}'.format(self.default_data['tboard'].id)
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

    @tccounter("get_tboard_statistics", "get", ENABLE_TCCOUNTER)
    def test_0_pass_1_fail(self):
        """
        rds.job_assessment_value的值
        0代表pass
        1代表fail
        """
        default_data = TestTool.load_default_data()
        tboard = default_data['tboard']
        TBoardJob(tboard=tboard, job=default_data['job'], order=0).save()
        tboard.device.add(default_data['device'])
        tboard.end_time = '2018-11-11 00:00:00+0000'
        tboard.save()
        rds = default_data['rds']
        rds.tboard = default_data['tboard']
        rds.job = default_data['job']
        rds.device = default_data['device']
        rds.job_assessment_value = '1'  # fail
        rds.end_time = '2018-11-11 00:00:00+0000'
        rds.save()
        response = self.client.get(
            reverse('get_tboard_statistics') + f'?tboard_id={tboard.id}'
        )
        self.assertEqual(response.data['fail'], 1)
