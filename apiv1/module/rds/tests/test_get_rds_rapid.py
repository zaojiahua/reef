from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from apiv1.module.rds.models import Rds
from reef.settings import ENABLE_TCCOUNTER


class TestGetRdsRapid(APITestCase):
    def setUp(self):
        self.default_data = TestTool.load_default_data()

    @tccounter('get_rds_rapid', 'get', ENABLE_TCCOUNTER)
    def test_rds_performance(self):
        """
        Date: 2018/12/02
        Author: Raymond
        When get large rds set(assume 10,000), used time should less than 10 sec
        """
        # Create 10000 rds row
        rdss = [
            Rds(device_id=self.default_data['device'].id,
                job_id=self.default_data['job'].id,
                tboard_id=self.default_data['tboard'].id)
            for i in range(0, 10000)]
        Rds.objects.bulk_create(rdss)
        timestamp = timezone.now()
        response = self.client.get(
            reverse('get_rds_rapid')
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        time_used = timezone.now() - timestamp
        self.assertLessEqual(time_used.seconds, 10, f'Used time {time_used}, over 10 sec')

    @tccounter('get_rds_rapid', 'get', ENABLE_TCCOUNTER)
    def test_rds_accuracy(self):
        """
        Date: 2019/7/10
        Author: gfq
        对未完成的rds进行过滤
        """
        rds_data = {
            "device_id":self.default_data['device'].id,
            "job_id": self.default_data['job'].id,
            "tboard_id": self.default_data['tboard'].id,
            "start_time": timezone.now(),
            "job_assessment_value": 0
        }
        Rds.objects.create(**rds_data)
        response = self.client.get(reverse('get_rds_rapid'))
        self.assertEqual(len(response.data['rdss']), 1)