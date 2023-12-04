from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from reef.settings import BASE_DIR, ENABLE_TCCOUNTER


class TestRdsScreenshot(APITestCase):

    def setUp(self):
        self.default_data = TestTool.load_default_data()
        with open(f'{BASE_DIR}/apiv1/module/rds/tests/file/1_snap.png', 'rb') as image:
            data = {
                'img_file': image,
                'rds': self.default_data['rds'].id,
                'file_name': '1_snap.png',
            }
            response = self.client.post(
                reverse('rds_screenshot_list'),
                data=data,
                format='multipart'
            )
        self.rds_scrennshot_id = response.data.get('id', None)

    @tccounter('rds_screenshot_list', 'delete', ENABLE_TCCOUNTER)
    def test_bulk_delete(self):
        """
        Date: 2019/11/7
        Author: Goufuqiang
        Describe: bulk delete rds screenshot
        """
        response = self.client.delete(
            reverse('rds_screenshot_list') + '?id=1,2,3'
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.data)

    @tccounter('rds_screenshot_list', 'delete', ENABLE_TCCOUNTER)
    def test_bulk_delete_lock_id_parameter(self):
        """
        Date: 2019/11/25
        Author: Goufuqiang
        Describe: lock id parameter
        """
        response = self.client.delete(
            reverse('rds_screenshot_list')
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter('rds_screenshot_list', 'get', ENABLE_TCCOUNTER)
    def test_get_rds_screnshot_200ok(self):
        """
        Date: 2019/11/7
        Author: Goufuqiang
        Describe: GET /cedar/rds_screenshot/
        """
        response = self.client.get(
            reverse('rds_screenshot_list')
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('rds_screenshot_list', 'get', ENABLE_TCCOUNTER)
    def test_get_rds_screnshot_response_data(self):
        """
        Date: 2019/11/7
        Author: Goufuqiang
        Describe: Check file_name
        """
        response = self.client.get(
            reverse('rds_screenshot_list')
        )
        self.assertEqual(response.data.get('rdsscreenshots', None)[0].get('file_name'), '1_snap.png')

    @tccounter('rds_screenshot_detail', 'get', ENABLE_TCCOUNTER)
    def test_get_rds_screnshot_id_200ok(self):
        """
        Date: 2019/11/7
        Author: Goufuqiang
        Describe: GET /cedar/rds_screenshot/{id}
        """
        response = self.client.get(
            reverse('rds_screenshot_detail', args=(self.rds_scrennshot_id,))
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('rds_screenshot_detail', 'get', ENABLE_TCCOUNTER)
    def test_get_rds_screnshot_id_response_data(self):
        """
        Date: 2019/11/7
        Author: Goufuqiang
        Describe: Get response data
        """
        response = self.client.get(
            reverse('rds_screenshot_detail', args=(self.rds_scrennshot_id,))
        )
        self.assertEqual(response.data.get('file_name', None), '1_snap.png')

    @tccounter('rds_screenshot_list', 'post', ENABLE_TCCOUNTER)
    def test_post_rds_screenshot_200ok(self):
        """
        Date: 2019/11/7
        Author: Goufuqiang
        Describe: POST /cedar/rds_screenshot/{id}
        """
        with open(f'{BASE_DIR}/apiv1/module/rds/tests/file/1_snap.png', 'rb') as image:
            response = self.client.post(
                reverse('rds_screenshot_list'),
                data={
                    'img_file': image,
                    'rds': self.default_data['rds'].id,
                    'file_name': '2_snap.png',
                },
                format='multipart'
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @tccounter('rds_screenshot_list', 'post', ENABLE_TCCOUNTER)
    def test_post_rds_screenshot_file_name_empty(self):
        """
        Date: 2019/11/7
        Author: Goufuqiang
        Describe: create rds_screenshot, file_name field is empty
        """
        with open(f'{BASE_DIR}/apiv1/module/rds/tests/file/1_snap.png', 'rb') as image:
            response = self.client.post(
                reverse('rds_screenshot_list'),
                data={
                    'img_file': image,
                    'rds': self.default_data['rds'].id,
                    'file_name': '',
                },
                format='multipart'
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter('rds_screenshot_detail', 'put', ENABLE_TCCOUNTER)
    def test_put_rds_screenshot_200ok(self):
        """
        Date: 2019/11/7
        Author: Goufuqiang
        Describe: PUT /cedar/rds_screenshot/{id}
        """
        with open(f'{BASE_DIR}/apiv1/module/rds/tests/file/1_snap.png', 'rb') as image:
            response = self.client.put(
                reverse('rds_screenshot_detail', args=(self.rds_scrennshot_id,)),
                data={
                    'img_file': image,
                    'rds': self.default_data['rds'].id,
                    'file_name': '2_snap.png',
                },
                format='multipart'
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('rds_screenshot_detail', 'put', ENABLE_TCCOUNTER)
    def test_put_rds_screenshot_response_data(self):
        """
        Date: 2019/11/7
        Author: Goufuqiang
        Describe: Update file_name field
        """
        with open(f'{BASE_DIR}/apiv1/module/rds/tests/file/1_snap.png', 'rb') as image:
            response = self.client.put(
                reverse('rds_screenshot_detail', args=(self.rds_scrennshot_id,)),
                data={
                    'img_file': image,
                    'rds': self.default_data['rds'].id,
                    'file_name': '2_snap.png',
                },
                format='multipart'
            )
        self.assertEqual(response.data.get('file_name', None), '2_snap.png')

    @tccounter('rds_screenshot_detail', 'patch', ENABLE_TCCOUNTER)
    def test_patch_rds_screenshot_200ok(self):
        """
        Date: 2019/11/7
        Author: Goufuqiang
        Describe:PATCH /cedar/rds_screenshot/{id}
        """
        response = self.client.patch(
            reverse('rds_screenshot_detail', args=(self.rds_scrennshot_id,)),
            data={
                'file_name': '2_snap.png',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('rds_screenshot_detail', 'patch', ENABLE_TCCOUNTER)
    def test_patch_rds_screenshot_response_data(self):
        """
        Date: 2019/11/7
        Author: Goufuqiang
        Describe: Update file_name field
        """
        response = self.client.patch(
            reverse('rds_screenshot_detail', args=(self.rds_scrennshot_id,)),
            data={
                'file_name': '2_snap.png',
            },
        )
        self.assertEqual(response.data.get('file_name'), '2_snap.png')

    @tccounter('rds_screenshot_detail', 'delete', ENABLE_TCCOUNTER)
    def test_delete_rds_screenshot_200ok(self):
        """
        Date: 2019/11/7
        Author: Goufuqiang
        Describe: DELETE /cedar/rds_screenshot/{id}
        """
        response = self.client.delete(
            reverse('rds_screenshot_detail', args=(self.rds_scrennshot_id,))
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @tccounter('rds_screenshot_detail', 'delete', ENABLE_TCCOUNTER)
    def test_delete_rds_screenshot_no_existent(self):
        """
        Date: 2019/11/7
        Author: Goufuqiang
        Describe: Delete no existent instance
        """
        response = self.client.delete(
            reverse('rds_screenshot_detail', args=(0,))
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

