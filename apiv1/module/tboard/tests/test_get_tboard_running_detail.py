from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool
from apiv1.module.device.models import Manufacturer, RomVersion, Device
from apiv1.module.job.models import Job
from apiv1.module.rds.models import Rds
from apiv1.module.user.models import ReefUser
from apiv1.module.tboard.models import TBoard, TBoardJob
from apiv1.core.test import tccounter
from reef.settings import ENABLE_TCCOUNTER

class TestGetTboardRunningDetail(APITestCase):
    @tccounter("get_tboard_running_detail", "get", ENABLE_TCCOUNTER)
    def test_200ok(self):
        """
        测试get_tboard_running_detail正常操作
        """
        self.default_data = TestTool.load_default_data()
        response = self.client.get(
            reverse('get_tboard_running_detail') + '?tboard_id={}'.format(self.default_data['tboard'].id)
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("get_tboard_running_detail", "get", ENABLE_TCCOUNTER)
    def test_outer_devices_is_union_of_inner_devices(self):
        """
        外层的devices，应为内层(jobs下的devices)的联集
        """
        manufacturer = Manufacturer.objects.create(
            manufacturer_name='manufacturer_name_1'
        )
        rom_version = RomVersion.objects.create(
            manufacturer=manufacturer,
            version='version_1'
        )
        device1 = Device.objects.create(device_label='device_label_1', cpu_id='cpu_id_1', rom_version=rom_version)
        device2 = Device.objects.create(device_label='device_label_2', cpu_id='cpu_id_2', rom_version=rom_version)
        device3 = Device.objects.create(device_label='device_label_3', cpu_id='cpu_id_3', rom_version=rom_version)
        job1 = Job.objects.create(job_label='job_label_1', job_name='job_name_1', job_type='Sysjob',
                                  description='description_1', )
        job2 = Job.objects.create(job_label='job_label_2', job_name='job_name_2', job_type='Sysjob',
                                  description='description_2', )
        job3 = Job.objects.create(job_label='job_label_3', job_name='job_name_3', job_type='Sysjob',
                                  description='description_3', )
        # Default user should exist, if not, let raise error
        author_id = ReefUser.objects.get(username='user-default000000000001').id
        tboard = TBoard.objects.create(author_id=author_id, board_stamp='2018-01-01 00:00:00+0000', end_time='2018-01-01 12:00:00+0000')
        tboard.device.add(device1)
        tboard.device.add(device2)
        tboard.device.add(device3)
        TBoardJob(
            tboard=tboard,
            job=job1,
            order=0
        ).save()
        TBoardJob(
            tboard=tboard,
            job=job2,
            order=1
        ).save()
        TBoardJob(
            tboard=tboard,
            job=job3,
            order=2
        ).save()

        Rds.objects.create(start_time='2018-01-01 06:00:00+0000', end_time=None,
                           job_assessment_value='0', tboard=tboard, device=device1, job=job1)

        Rds.objects.create(start_time='2018-01-01 06:00:00+0000', end_time='2018-01-01 08:00:00+0000',
                           job_assessment_value='1', tboard=tboard, device=device1, job=job1)

        Rds.objects.create(start_time='2018-01-01 06:00:00+0000', end_time='2018-01-01 08:00:00+0000',
                           job_assessment_value='2', tboard=tboard, device=device2, job=job1)

        Rds.objects.create(start_time='2018-01-01 06:00:00+0000', end_time='2018-01-01 08:00:00+0000',
                           job_assessment_value='0', tboard=tboard, device=device2, job=job2)

        Rds.objects.create(start_time='2018-01-01 06:00:00+0000', end_time=None,
                           job_assessment_value='0', tboard=tboard, device=device1, job=job2)

        Rds.objects.create(start_time='2018-01-01 06:00:00+0000', end_time='2018-01-01 08:00:00+0000',
                           job_assessment_value='1', tboard=tboard, device=device2, job=job2)

        Rds.objects.create(start_time='2018-01-01 06:00:00+0000', end_time='2018-01-01 08:00:00+0000',
                           job_assessment_value='1', tboard=tboard, device=device1, job=job2)

        Rds.objects.create(start_time='2018-01-01 06:00:00+0000', end_time='2018-01-01 08:00:00+0000',
                           job_assessment_value='0', tboard=tboard, device=device1, job=job2)

        Rds.objects.create(start_time='2018-01-01 06:00:00+0000', end_time='2018-01-01 08:00:00+0000',
                           job_assessment_value='0', tboard=tboard, device=device1, job=job3)


        response = self.client.get(
            reverse('get_tboard_running_detail') + f'?tboard_id={tboard.id}'
        )

        outer_devices = {device['id'] for device in response.data['devices']}
        inner_devices = []
        for job in response.data['jobs']:
            inner_devices += job['devices']
        inner_devices_union = {device['id'] for device in inner_devices}

        self.assertEqual(outer_devices, inner_devices_union)

    @tccounter("get_tboard_running_detail", "get", ENABLE_TCCOUNTER)
    def test_0_pass_1_fail(self):
        """
        rds.job_assessment_value的值
        0代表pass
        1代表fail
        """
        default_data = TestTool.load_default_data()
        tboard = default_data['tboard']
        TBoardJob(
            tboard=tboard,
            job=default_data['job'],
            order=0
        ).save()
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
            reverse('get_tboard_running_detail') + f'?tboard_id={default_data["tboard"].id}'
        )
        self.assertEqual(response.data['jobs'][0]['fail'], 1)
        self.assertEqual(response.data['jobs'][0]['devices'][0]['fail'], 1)