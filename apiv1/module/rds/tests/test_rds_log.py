from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from apiv1.module.rds.models import RdsLog
from reef.settings import BASE_DIR, ENABLE_TCCOUNTER


class TestRdsLog(APITestCase):

    def setUp(self):
        self.default_data=TestTool.load_default_data()
        self.rds_obj = RdsLog.objects.create(
                            rds=self.default_data['rds'],
                            log_file='rds_logs/system_Tz4pVwv.log',
                            file_name='system.log'
                        )

    @tccounter('rds_log_list', 'get', ENABLE_TCCOUNTER)
    def test_get_rds_log_200ok(self):
        """
        Date: 2019/11/7
        Author: Goufuqiang
        Describe: DELETE /cedar/rds_log/
        """
        response = self.client.get(
            reverse('rds_log_list')
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('rds_log_list', 'get', ENABLE_TCCOUNTER)
    def test_get_rds_log_response_data(self):
        """
        Date: 2019/11/7
        Author: Goufuqiang
        Describe: Get rds_log response data len
        """
        response = self.client.get(
            reverse('rds_log_list')
        )
        self.assertEqual(len(response.data), 1)

    @tccounter('rds_log_detail', 'get', ENABLE_TCCOUNTER)
    def test_get_rds_log_id_200ok(self):
        """
        Date: 2019/11/7
        Author: Goufuqiang
        Describe: GET /cedar/rds_log/{id}
        """
        response = self.client.get(
            reverse('rds_log_detail', args=(self.rds_obj.id,))
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('rds_log_detail', 'get', ENABLE_TCCOUNTER)
    def test_get_rds_log_id_response_data(self):
        """
        Date: 2020/6/17
        Author: Goufuqiang
        Describe: Get rds id
        """
        response = self.client.get(
            reverse('rds_log_detail', args=(self.rds_obj.id,))
        )
        self.assertEqual(response.data.get('id', None), self.rds_obj.id)

    @tccounter('rds_log_list', 'post', ENABLE_TCCOUNTER)
    def test_post_rds_log_post(self):
        """
        Date: 2019/11/7
        Author: Goufuqiang
        Describe: POST /cedar/rds_log/{id}
        """
        with open(f'{BASE_DIR}/apiv1/module/rds/tests/file/system_2vde3NF.log', 'rb') as f:
            data = {
                       'rds': self.default_data['rds'].id,
                       'log_file': f,
                       'file_name': 'system.log'
                   }
            response = self.client.post(
                reverse('rds_log_list'),
                data=data,
                format='multipart'
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @tccounter('rds_log_list', 'post', ENABLE_TCCOUNTER)
    def test_post_rds_log_response_data(self):
        """
        Date: 2019/11/7
        Author: Goufuqiang
        Describe: create rds_log
        """
        with open(f'{BASE_DIR}/apiv1/module/rds/tests/file/system_2vde3NF.log', 'rb') as f:
            response = self.client.post(
                reverse('rds_log_list'),
                data={
                    'rds': self.default_data['rds'].id,
                    'log_file': f,
                    'file_name': 'system.log'
                },
                format='multipart'
            )
        self.assertEqual(response.data.get('file_name', None), 'system.log')

    @tccounter('rds_log_detail', 'patch', ENABLE_TCCOUNTER)
    def test_patch_rds_log_200ok(self):
        """
        Date: 2019/11/7
        Author: Goufuqiang
        Describe: PATCH /cedar/rds_log/{id}
        """
        response = self.client.patch(
            reverse('rds_log_detail', args=(self.rds_obj.id,)),
            data={
                'file_name': 'system_test.log'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('rds_log_detail', 'patch', ENABLE_TCCOUNTER)
    def test_patch_rds_log_response_data(self):
        """
        Date: 2019/11/7
        Author: Goufuqiang
        Describe: Update file_name field
        """
        response = self.client.patch(
            reverse('rds_log_detail', args=(self.rds_obj.id,)),
            data={
                'file_name': 'system_test.log'
            }
        )
        self.assertEqual(response.data.get('file_name', None), 'system_test.log')

    @tccounter('rds_log_detail', 'put', ENABLE_TCCOUNTER)
    def test_put_rds_log_200ok(self):
        """
        Date: 2019/11/7
        Author: Goufuqiang
        Describe: PUT /cedar/rds_log/{id}
        """
        with open(f'{BASE_DIR}/apiv1/module/rds/tests/file/system_2vde3NF.log', 'rb') as f:
            response = self.client.put(
                reverse('rds_log_detail', args=(self.rds_obj.id,)),
                data={
                    'rds': self.default_data['rds'].id,
                    'log_file': f,
                    'file_name': 'system_test.log'
                },
                format='multipart'
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('rds_log_detail', 'put', ENABLE_TCCOUNTER)
    def test_put_rds_log_response_data(self):
        """
        Date: 2019/11/7
        Author: Goufuqiang
        Describe: Update file_name field
        """
        with open(f'{BASE_DIR}/apiv1/module/rds/tests/file/system_2vde3NF.log', 'rb') as f:
            response = self.client.put(
                reverse('rds_log_detail', args=(self.rds_obj.id,)),
                data={
                    'rds': self.default_data['rds'].id,
                    'log_file': f,
                    'file_name': 'system_test.log'
                },
                format='multipart'
            )
        self.assertEqual(response.data.get('file_name', None), 'system_test.log')

    @tccounter('rds_log_detail', 'delete', ENABLE_TCCOUNTER)
    def test_delete_rds_log_200ok(self):
        """
        Date: 2019/11/7
        Author: Goufuqiang
        Describe: DELETE /cedar/rds_log/{id}
        """
        response = self.client.delete(
            reverse('rds_log_detail', args=(self.rds_obj.id,)),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @tccounter('rds_log_detail', 'delete', ENABLE_TCCOUNTER)
    def test_delete_rds_log_no_existent(self):
        """
        Date: 2019/11/7
        Author: Goufuqiang
        Describe: Delete no existent instance
        """
        response = self.client.delete(
            reverse('rds_log_detail', args=(100,)),
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

