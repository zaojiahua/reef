from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from apiv1.module.rds.models import Rds
from reef.settings import ENABLE_TCCOUNTER


class TestSearchRds(APITestCase):

    def setUp(self):
        self.default_data = TestTool.load_default_data()

    def bulk_create_rds(self):
        obj_list = [
            Rds(
                device=self.default_data['device'],
                job=self.default_data['job'],
                tboard=self.default_data['tboard'],
            )
            for _ in range(20000)
        ]
        Rds.objects.bulk_create(obj_list)

    @tccounter('search_rds', 'get', ENABLE_TCCOUNTER)
    def test_search_rds(self):
        """
        Date: 2019/11/5
        Author: Goufuqiang
        Describe: test (!=) parameter
        """
        response = self.client.get(
            reverse('search_rds') + f'?limit=100&device__id=2&end_time__lt=2019-05-28 11:16:33+08&'
                                     f'start_time__gt=2019-04-28 11:16:33+08&tboard_author_id!=2&'
                                     f'job__job_deleted!=True&created_by_ai_tester=False&offset=20000'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter('search_rds', 'get', ENABLE_TCCOUNTER)
    def test_high_speed_query_rds(self):
        """
        Date: 2019/11/5
        Author: Goufuqiang
        Describe: High speed query rds, get 2M rds data
        """
        self.bulk_create_rds()
        rds_queryset = Rds.objects.all().count()
        response = self.client.get(
            reverse('search_rds') + f'?limit=20000&offset=1'
        )
        self.assertEqual(len(response.data.get('rdss', [])), 20000)
