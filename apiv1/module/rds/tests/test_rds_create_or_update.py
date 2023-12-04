from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from apiv1.module.rds.models import Rds
from reef.settings import ENABLE_TCCOUNTER


class TestRdsCreateOrUpdate(APITestCase):
    def setUp(self):
        self.default_data = TestTool.load_default_data('1')

    @tccounter('rds_create_or_update', 'post', ENABLE_TCCOUNTER)
    def test_rds_create_or_update(self):
        response = self.client.post(reverse("rds_create_or_update"), data={
            'device': self.default_data['device'].device_label,
            'job': self.default_data['job'].job_label,
            'start_time': '2018_03_10_22_33_11',
            'end_time': '2018_03_11_10_22_31',
            'job_assessment_value': "value_type",
            'tboard': self.default_data['tboard'].id

        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('rds_create_or_update', 'post', ENABLE_TCCOUNTER)
    def test_return_rds_id(self):
        """
        Date: 2018/12/18
        Author: Raymond
        """
        response = self.client.post(reverse("rds_create_or_update"), data={
            'device': self.default_data['device'].device_label,
            'job': self.default_data['job'].job_label,
            'start_time': '1111_03_10_22_33_11',
            'end_time': '1111_03_11_10_22_31',
            'job_assessment_value': "value_type",
            'tboard': self.default_data['tboard'].id
        })
        self.assertIn('id', response.data)

    @tccounter('rds_create_or_update', 'post', ENABLE_TCCOUNTER)
    def test_rds_dict_binary(self):
        """
        Date: 2018/01/28
        Author: Raymond
        Field rds_dict stored in database with encoded binary string, not primative string
        and when we retrieve it, we should get a encoded dict, not primative string
        """
        response = self.client.post(
            reverse('rds_create_or_update'),
            data={
                'device': self.default_data['device'].device_label,
                'job': self.default_data['job'].job_label,
                'tboard': self.default_data['tboard'].id,
                'start_time': '1111_03_10_22_33_12',
                'rds_dict': "{\"1\":1, \"2\":2, \"3\":{\"a\":\"a\", \"b\":\"b\"}}"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        rds = Rds.objects.get(pk=response.data['id'])
        self.assertIsInstance(rds.rds_dict, dict)

    @tccounter('rds_create_or_update', 'post', ENABLE_TCCOUNTER)
    def test_rds_create_or_update_without_board_stamp(self):
        """
        Date: 2019/06/11
        Author: Guozijun
        """
        response = self.client.post(reverse("rds_create_or_update"), data={
            'device': self.default_data['device'].device_label,
            'job': self.default_data['job'].job_label,
            'start_time': '2018_03_10_22_33_11',
            'end_time': '2018_03_11_10_22_31',
            'job_assessment_value': "value_type",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter('tboard_detail', 'delete', ENABLE_TCCOUNTER)
    def test_tboard_delete_related_rds_deleted(self):
        """
        Date: 2019/06/11
        Author: Guozijun
        """
        self.client.delete(reverse('tboard_detail', kwargs={'pk': self.default_data['tboard'].id})),
        exists = Rds.objects.filter(id=self.default_data['rds'].id).exists()
        self.assertEqual(exists, False)

    @tccounter('rds_create_or_update', 'post', ENABLE_TCCOUNTER)
    def test_update_rds(self):
        """
        Date: 2018/01/28
        Author: Goufuqiang
        add tboard parameter update rds
        """
        Rds.objects.create(
            device=self.default_data['device'],
            job=self.default_data['job'],
            tboard=self.default_data['tboard'],
            start_time='2018-03-10 22:33:11+08'
        )
        response = self.client.post(reverse("rds_create_or_update"), data={
            'device': self.default_data['device'].device_label,
            'job': self.default_data['job'].job_label,
            'start_time': '2018_03_10_22_33_11',
            'end_time': '2018_03_11_10_22_31',
            'job_assessment_value': "value_type",
            'tboard': self.default_data['tboard'].id

        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('rds_create_or_update', 'post', ENABLE_TCCOUNTER)
    def test_update_rds_typical_job_temp_consumption_field(self):
        """
        Date: 2018/01/28
        Author: Goufuqiang
        Update rds typical_job_temp_consumption field
        """
        # 创建rds
        Rds.objects.create(
            device=self.default_data['device'],
            job=self.default_data['job'],
            tboard=self.default_data['tboard'],
            start_time='2019-10-21 22:33:11+08'
        )
        # 更新
        response = self.client.post(reverse("rds_create_or_update"), data={
            'device': self.default_data['device'].device_label,
            'job': self.default_data['job'].job_label,
            'start_time': '2019_10_21_22_33_11',
            'end_time': '2019_10_21_22_40_11',
            'job_assessment_value': "1",
            'tboard': self.default_data['tboard'].id,
            'typical_job_temp_consumption': 50.01
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)