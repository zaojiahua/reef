from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from apiv1.module.rds.models import Rds
from reef.settings import ENABLE_TCCOUNTER


class TestFilterRdsValidity(APITestCase):

    def setUp(self):
        self.default_data = TestTool.load_default_data()

    def add_rds_data(self):
        for i in ['0', '1']:
            self.rds_objects = Rds.objects.create(
                job_assessment_value=i,
                device=self.default_data['device'],
                job=self.default_data['job'],
                tboard=self.default_data['tboard'],
            )

    @tccounter('filter_rds_validity', 'get', ENABLE_TCCOUNTER)
    def test_filter_rds_validity(self):
        """
        Date: 2019/11/5
        Author: Goufuqiang
        Describe: 根据rds.job_assessment_value字段进行非条件过滤
        """

        self.add_rds_data()
        response = self.client.get(
            reverse('filter_rds_validity') + f'?job_assessment_value!="",0'
        )
        self.assertIn('rdss', response.data)
        self.assertLess(len(response.data['rdss']), 2)

    @tccounter('filter_rds_validity', 'get', ENABLE_TCCOUNTER)
    def test_filter_rds_validity_200ok(self):
        """
        Date: 2019/08/19
        Author: Goufuqiang
        Describe: /cedar/filter_rds_validity
        """
        response = self.client.get(
            reverse('filter_rds_validity')
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)