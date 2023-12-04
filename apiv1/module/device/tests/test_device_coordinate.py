from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from reef.settings import ENABLE_TCCOUNTER


class TestDeviceCoordinate(APITestCase):

    def setUp(self):
        self.default_data = TestTool.load_default_data()
        self.default_id = self.default_data['device_coordinate'].id

    @tccounter("devicecoordinate_list", "get", ENABLE_TCCOUNTER)
    def test_get_200ok(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test get method 200 OK
        """
        response = self.client.get(reverse('devicecoordinate_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("devicecoordinate_list", "get", ENABLE_TCCOUNTER)
    def test_get_device_coordinate_wanted_info(self):
        """
         Date: 2019/10/26
         Author: Guozijun
         test get fields you wanted
         """
        response = self.client.get(f"{reverse('devicecoordinate_list')}?fields=upper_left_x,bottom_left_x")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("devicecoordinate_detail", "get", ENABLE_TCCOUNTER)
    def test_get_instance_by_id(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test get a instance by id
        """
        response = self.client.get(reverse('devicecoordinate_detail', args=[self.default_id]))
        self.assertEqual(response.data['id'], self.default_id)

    @tccounter("devicecoordinate_detail", "get", ENABLE_TCCOUNTER)
    def test_get_instance_which_not_exist(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test get a instance by a wrong id
        """
        response = self.client.get(reverse('devicecoordinate_detail', args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @tccounter("devicecoordinate_list", "post", ENABLE_TCCOUNTER)
    def test_post_201_create(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test post method 201 create
        """
        response = self.client.post(reverse('devicecoordinate_list'), data={
            'bottom_left_x': 10,
            'bottom_left_y': 10,
            'upper_left_x': 10,
            'upper_left_y': 10,
            'bottom_right_x': 10,
            'bottom_right_y': 10,
            'upper_right_x': 10,
            'upper_right_y': 10
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @tccounter("devicecoordinate_list", "post", ENABLE_TCCOUNTER)
    def test_post_missing_bottom_left_x(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test create instance missing bottom_left_x field
        """
        response = self.client.post(reverse('devicecoordinate_list'), data={
            'bottom_left_y': 10,
            'upper_left_x': 10,
            'upper_left_y': 10,
            'bottom_right_x': 10,
            'bottom_right_y': 10,
            'upper_right_x': 10,
            'upper_right_y': 10
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("devicecoordinate_list", "post", ENABLE_TCCOUNTER)
    def test_bulk_create(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test bulk create
        """
        device_coordinates = [{
            'bottom_left_x': i,
            'bottom_left_y': i,
            'upper_left_x': i,
            'upper_left_y': i,
            'bottom_right_x': i,
            'bottom_right_y': i,
            'upper_right_x': i,
            'upper_right_y': i
        } for i in range(1, 2)]
        response = self.client.post(reverse('devicecoordinate_list'), data=device_coordinates)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @tccounter("devicecoordinate_detail", "put", ENABLE_TCCOUNTER)
    def test_put_200ok(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test put method 200 OK
        """
        response = self.client.put(reverse('devicecoordinate_detail', args=[self.default_id]), data={
            'bottom_left_x': 10,
            'bottom_left_y': 0,
            'upper_left_x': 0,
            'upper_left_y': 0,
            'bottom_right_x': 0,
            'bottom_right_y': 0,
            'upper_right_x': 0,
            'upper_right_y': 0
        })
        self.assertEqual(response.data['bottom_left_x'], 10)

    @tccounter("devicecoordinate_detail", "put", ENABLE_TCCOUNTER)
    def test_put_bottom_left_x_with_negative_number(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test update bottom_left_x field with negative number
        """
        response = self.client.put(reverse('devicecoordinate_detail', args=[self.default_id]), data={
            'bottom_left_x': -10,
            'bottom_left_y': 0,
            'upper_left_x': 0,
            'upper_left_y': 0,
            'bottom_right_x': 0,
            'bottom_right_y': 0,
            'upper_right_x': 0,
            'upper_right_y': 0
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("devicecoordinate_detail", "patch", ENABLE_TCCOUNTER)
    def test_patch_200ok(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test patch method 200 OK
        """
        response = self.client.patch(reverse('devicecoordinate_detail', args=[self.default_id]), data={
            'bottom_left_x': 20
        })
        self.assertEqual(response.data['bottom_left_x'], 20)

    @tccounter("devicecoordinate_detail", "patch", ENABLE_TCCOUNTER)
    def test_patch_bottom_left_x_with_decimal(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test update bottom_left_x field with decimal
        """
        response = self.client.patch(reverse('devicecoordinate_detail', args=[self.default_id]), data={
            'bottom_left_x': 99.99,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("devicecoordinate_detail", "delete", ENABLE_TCCOUNTER)
    def test_delete_204_no_content(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test delete method 204 not content
        """
        response = self.client.delete(reverse('devicecoordinate_detail', args=[self.default_id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @tccounter("devicecoordinate_detail", "delete", ENABLE_TCCOUNTER)
    def test_delete_instance_do_not_exist(self):
        """
        Date: 2019/10/26
        Author: Guozijun
        test delete instance which is not exists
        """
        response = self.client.delete(reverse('devicecoordinate_detail', args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
