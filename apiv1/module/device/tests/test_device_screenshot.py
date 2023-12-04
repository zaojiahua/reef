from django.utils import timezone
from rest_framework.reverse import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from reef.settings import ENABLE_TCCOUNTER


class TestDeviceScreenShot(APITestCase):

    def setUp(self):
        self.default_data = TestTool.load_default_data()
        self.default_id = self.default_data['device-screenshot'].id

    @tccounter("devicescreenshot_list", "get", ENABLE_TCCOUNTER)
    def test_get_200ok(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test get method 200 OK
        """
        response = self.client.get(reverse('devicescreenshot_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("devicescreenshot_list", "get", ENABLE_TCCOUNTER)
    def test_get_device_screenshot_wanted_info(self):
        """
         Date: 2019/10/26
         Author: Guozijun
         test get fields you wanted
         """
        response = self.client.get(f"{reverse('devicescreenshot_list')}?fields=device,device.device_label")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("devicescreenshot_detail", "get", ENABLE_TCCOUNTER)
    def test_get_instance_by_id(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test get a instance by id
        """
        response = self.client.get(reverse('devicescreenshot_detail', args=[self.default_id]))
        self.assertEqual(response.data['id'], self.default_id)

    @tccounter("devicescreenshot_detail", "get", ENABLE_TCCOUNTER)
    def test_get_instance_which_not_exist(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test get a instance by a wrong id
        """
        response = self.client.get(reverse('devicescreenshot_detail', args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @tccounter("devicescreenshot_list", "post", ENABLE_TCCOUNTER)
    def test_post_201_create(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test post method 201 create
        """
        with open('apiv1/module/device/tests/file/1_snap.png', 'rb') as testfile:
            response = self.client.post(
                reverse('devicescreenshot_list'),
                data={
                    'device': self.default_data['device'].id,
                    'snap_timestamp': timezone.now(),
                    'screenshot': testfile
                },
                format='multipart'
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @tccounter("devicescreenshot_list", "post", ENABLE_TCCOUNTER)
    def test_post_snap_timestamp_form_error(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test post method 201 create
        """
        with open('apiv1/module/device/tests/file/1_snap.png', 'rb') as testfile:
            response = self.client.post(
                reverse('devicescreenshot_list'),
                data={
                    'device': self.default_data['device'].id,
                    'snap_timestamp': '2019-10-26-10-20-50',
                    'screenshot': testfile
                },
                format='multipart'
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("devicescreenshot_detail", "put", ENABLE_TCCOUNTER)
    def test_put_200ok(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test put method 200 OK , snap_timestamp changed, response naive datetime
        """
        with open('apiv1/module/device/tests/file/1_snap.png', 'rb') as testfile:
            response = self.client.put(
                reverse('devicescreenshot_detail', args=[self.default_id]),
                data={
                    'device': self.default_data['device'].id,
                    'snap_timestamp': '2099-10-26T02:00:00Z',
                    'screenshot': testfile
                },
                format='multipart'
            )
        self.assertEqual(response.data['snap_timestamp'], '2099-10-26 10:00:00')

    @tccounter("devicescreenshot_detail", "put", ENABLE_TCCOUNTER)
    def test_put_relative_not_exist_device(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test create a instance relative a not exist device
        """
        with open('apiv1/module/device/tests/file/1_snap.png', 'rb') as testfile:
            response = self.client.put(
                reverse('devicescreenshot_detail', args=[self.default_id]),
                data={
                    'device': '999',
                    'snap_timestamp': timezone.now(),
                    'screenshot': testfile
                },
                format='multipart'
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("devicescreenshot_detail", "patch", ENABLE_TCCOUNTER)
    def test_patch_200ok(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test patch method 200 OK
        """
        response = self.client.patch(reverse('devicescreenshot_detail', args=[self.default_id]), data={
            'snap_timestamp': '2099-10-26T02:00:00Z'
        })
        self.assertEqual(response.data['snap_timestamp'], '2099-10-26 10:00:00')

    @tccounter("devicescreenshot_detail", "patch", ENABLE_TCCOUNTER)
    def test_patch_file_a_dat_instead_of_png(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test partial update file png to dat format
        """
        with open('apiv1/module/device/tests/file/battery_0AvZF2p.dat', 'rb') as testfile:
            response = self.client.patch(reverse('devicescreenshot_detail', args=[self.default_id]), data={
                'screenshot': testfile
            },
                                         format='multipart'
                                         )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("devicescreenshot_detail", "delete", ENABLE_TCCOUNTER)
    def test_delete_204_no_content(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test delete method 204 not content
        """
        response = self.client.delete(reverse('devicescreenshot_detail', args=[self.default_id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @tccounter("devicescreenshot_detail", "delete", ENABLE_TCCOUNTER)
    def test_delete_instance_do_not_exist(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test delete instance which is not exists
        """
        response = self.client.delete(reverse('devicescreenshot_detail', args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
