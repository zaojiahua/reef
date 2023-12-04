from django.db.models import Max
from rest_framework.test import APITestCase
from rest_framework.reverse import reverse
from rest_framework import status
from apiv1.core.test import TestTool, tccounter
from apiv1.module.system.models import Cabinet
from reef.settings import ENABLE_TCCOUNTER


class TestCabinetRegist(APITestCase):
    def setUp(self):
        self.default_data = TestTool.load_default_data()
        self.default_cabinet_id = self.default_data['cabinet'].id

    @tccounter('cabinet_regist', 'post', ENABLE_TCCOUNTER)
    def test_cabinet_regist_200ok(self):
        """
        Date 2019/11/11
        Author: Goufuqiang
        Describe: Update cabinet info
        """
        response = self.client.post(
            reverse('cabinet_regist', args=(self.default_cabinet_id,)),
            data={
                'cabinet_name': 'cabinet_test_name',
                'ip_address': '192.168.1.111',
                'belong_to': self.default_data['system'].id,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('cabinet_regist', 'post', ENABLE_TCCOUNTER)
    def test_cabinet_regist_no_existent_instance(self):
        """
        Date 2019/11/11
        Author: Goufuqiang
        Describe: Create cabinet info
        """
        max_id = Cabinet.objects.annotate(max_id=Max('id'))[0].max_id
        if max_id is None:
            max_id = 0
        response = self.client.post(
            reverse('cabinet_regist', args=(max_id + 1,)),
            data={
                'cabinet_name': 'cabinet_test_name',
                'ip_address': '192.168.1.101',
                'belong_to': self.default_data['system'].id,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
