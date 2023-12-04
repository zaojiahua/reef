from django.utils import timezone
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool
from apiv1.module.device.models import Device
from apiv1.module.user.models import ReefUser
from apiv1.module.tboard.models import TBoard


class TestDeviceCalculateField(APITestCase):

    def setUp(self):
        self.default_data = TestTool.load_default_data()

    def add_extra_date(self):
        self.ai_tester = ReefUser.objects.create(username='AITester',
                                                 password='123456',
                                                 date_joined=timezone.now())

        self.device_for_test = Device.objects.create(device_label='device_label1',
                                                     device_name='device_name1',
                                                     cpu_id=1,
                                                     rom_version=self.default_data['rom_version']
                                                     )
        self.tboard_for_test_AItest = TBoard.objects.create(author=self.ai_tester,
                                                            repeat_time=1,
                                                            board_name='board_name1',
                                                            finished_flag=False,
                                                            board_stamp=timezone.now(),
                                                            end_time=timezone.now()
                                                            )


