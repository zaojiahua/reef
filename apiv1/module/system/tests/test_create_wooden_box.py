from rest_framework.test import APITestCase
from rest_framework.reverse import reverse
from rest_framework import status
from apiv1.core.test import TestTool, tccounter
from reef.settings import ENABLE_TCCOUNTER


class TestCabinetRegist(APITestCase):
    def setUp(self):
        self.default_data = TestTool.load_default_data()
        self.default_cabinet_id = self.default_data['cabinet'].id

    @tccounter('cabinet_regist', 'post', ENABLE_TCCOUNTER)
    def test_create_woodenbox_required_cabinet(self):
        """
        Date 2020/3/11
        Author: Goufuqiang
        Create WoodenBox required cabinet parameter
        """
        response = self.client.post(
            reverse('create_wooden_box'),
            data={
                'name': 'test_woodenbox',
                'type': 'power',
                'ip': '0.0.0.0',
                'config': {
                    "port": 20000,
                    "init_status": True,
                    "total_number": 8,
                    "method": "socket",
                },
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter('cabinet_regist', 'post', ENABLE_TCCOUNTER)
    def test_create_woodenbox_lock_type_field(self):
        """
        Date 2020/3/11
        Author: Goufuqiang
        lock_type_field
        """
        response = self.client.post(
            reverse('create_wooden_box'),
            data={
                'name': 'test_woodenbox',
                'ip': '0.0.0.0',
                'config': {
                    "port": 20000,
                    "init_status": True,
                    "total_number": 8,
                    "method": "socket",
                },
                'cabinet': self.default_cabinet_id
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
