from django.utils import timezone
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.module.user.models import ReefUser
from apiv1.module.tboard.models import TBoard
from apiv1.core.test import tccounter
from reef.settings import ENABLE_TCCOUNTER

class TestEndTBoard(APITestCase):
    """
    当TBoard中所有的Rds都执行完成时，会呼叫end_tboard
    """
    @tccounter("end_tboard", "put", ENABLE_TCCOUNTER)
    def test_200ok(self):
        """
        测试end_tboard正常操作
        """
        TBoard.objects.create(
            pk=1,
            board_stamp=timezone.now(),
            author=ReefUser.objects.create()
        )
        response = self.client.put(reverse('end_tboard', kwargs={'pk': 1}), data={
            'end_time': '2018_07_24_15_06_59'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("end_tboard", "put", ENABLE_TCCOUNTER)
    def test_not_found(self):
        """
        Date: 2019/11/20
        Author: wengmeijia
        Describe: PUT /coral/end_tboard/
        """
        TBoard.objects.create(
            pk=1,
            board_stamp=timezone.now(),
            author=ReefUser.objects.create()
        )
        response = self.client.put(reverse('end_tboard', kwargs={'pk': 0}), data={
            'end_time': '2018_07_24_15_06_59'
        })
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)