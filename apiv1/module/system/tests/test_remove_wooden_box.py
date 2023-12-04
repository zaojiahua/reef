from rest_framework.test import APITestCase
from rest_framework.reverse import reverse
from rest_framework import status
from apiv1.core.test import TestTool, tccounter
from reef.settings import ENABLE_TCCOUNTER
from apiv1.module.system.models import WoodenBox


class TestCabinetRegist(APITestCase):
    def setUp(self):
        self.default_data = TestTool.load_default_data()
        self.default_data['woodenbox'] = WoodenBox.objects.create(
            name='TA-01',
            type='power',
            ip= '127.0.0.1',
            config= {},
            cabinet= self.default_data['cabinet']
        )

    @tccounter('remove_wooden_box', 'delete', ENABLE_TCCOUNTER)
    def test_remove_woodenbox_obj_not_exist(self):
        """
        Date 2020/3/30
        Author: Goufuqiang
        Remove WoodenBox instance not exist
        """
        response = self.client.delete(
            reverse('remove_wooden_box', args=[0,])
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @tccounter('remove_wooden_box', 'delete', ENABLE_TCCOUNTER)
    def test_remove_woodenbox_coral_error(self):
        """
        Date 2020/3/30
        Author: Goufuqiang
        Test request coral error
        """
        response = self.client.delete(
            reverse('remove_wooden_box', args=[self.default_data['woodenbox'].id]),
        )
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
