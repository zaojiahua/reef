from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool
from apiv1.module.device.models import RomVersion, Device, Manufacturer
from apiv1.module.job.models import Job
from apiv1.core.test import tccounter
from reef.settings import ENABLE_TCCOUNTER


class TestCreateTBoard(APITestCase):
    """
    TBoard在创建的时候，会呼叫create_tboard
    """
    def setUp(self):
        self.default_data = TestTool.load_default_data()
        self.user = TestTool.create_test_user(1)
        Device.objects.create(
                    device_label='a',
                    cabinet=self.default_data['cabinet'],
                    rom_version=RomVersion.objects.create(
                        version='rom1',
                        manufacturer=Manufacturer.objects.create(
                            manufacturer_name='manufacturer1'
                        ),
                    )
                ),
        Device.objects.create(
                    device_label='b',
                    cabinet=self.default_data['cabinet'],
                    rom_version=RomVersion.objects.create(
                        version='rom2',
                        manufacturer=Manufacturer.objects.create(
                            manufacturer_name='manufacturer2'
                        )
                    )
                ),
        Job.objects.bulk_create(
            (
                Job(job_label='a'),
                Job(job_label='b')
            )
        )

    @tccounter("create_tboard", "post", ENABLE_TCCOUNTER)
    def test_post_create_tboard_201(self):
        """
        测试create_tboard正常操作
        """
        response = self.client.post(reverse('create_tboard'), data={
            # required fields
            'board_stamp': '2018-07-24 15:06:56',
            'owner_label': self.user.id,
            'device_label_list': ["a", "b"],
            'job_label_list': ["a", "b"],
            'repeat_time': 3,
            'board_name': 'board_name'
        })
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            response.data
        )

    @tccounter("create_tboard", "post", ENABLE_TCCOUNTER)
    def test_post_create_tboard_400(self):
        """
        Date: 2019/11/20
        Author: wengmeijia
        Describe: POST /coral/create_tboard/
        """
        response = self.client.post(reverse('create_tboard'), data={
            # required fields
            'board_stamp': '2018-07-24 15:06:56',
            'owner_label': self.user.id,
            'device_label_list': ["a", "b"],
            'job_label_list': ["a", "b"],
            'repeat_time': -1,
            'board_name': 'board_name'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)