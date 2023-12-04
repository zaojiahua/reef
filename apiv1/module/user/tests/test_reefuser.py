from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from apiv1.module.user.models import ReefUser
from reef.settings import ENABLE_TCCOUNTER


class TestReefuser(APITestCase):

    def setUp(self):
        self.default_data = TestTool.load_default_data()
        response_group = self.client.post(
            reverse('group_list'),
            data={
                "name": "test_group"
            }
        )
        self.group_name = response_group.data.get("name", None)
        self.user_id = ReefUser.objects.filter()[0].id

    @tccounter('reefuser_list', 'get', ENABLE_TCCOUNTER)
    def test_get_200ok(self):
        """
        Date 2019/10/22
        Author: Goufuqiang
        Describe: GET /cedar/reefuser/ 200
        """
        # create group
        response = self.client.get(
            reverse('reefuser_list')
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('reefuser_list', 'get', ENABLE_TCCOUNTER)
    def test_get_response_type(self):
        """
        Date 2019/10/22
        Author: Goufuqiang
        Describe:
        """
        response = self.client.get(
            reverse('reefuser_list')
        )
        self.assertIsInstance(response.data, dict)

    @tccounter('reefuser_detail', 'get', ENABLE_TCCOUNTER)
    def test_get_id_200ok(self):
        """
        Date 2019/10/22
        Author: Goufuqiang
        Describe: GET /cedar/reefuser/{id}/ 200
        """
        response = self.client.get(
            reverse('reefuser_detail', args=(self.user_id,))
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('reefuser_detail', 'get', ENABLE_TCCOUNTER)
    def test_get_id_search(self):
        """
        Date 2019/10/22
        Author: Goufuqiang
        Describe: 查询不存在用户
        """
        response = self.client.get(
            reverse('reefuser_detail', args=(10,))
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @tccounter('reefuser_list', 'post', ENABLE_TCCOUNTER)
    def test_post_reefuser_200ok(self):
        """
        Date 2019/10/30
        Author: Goufuqiang
        Describe: POST /cedar/reefuser/
        """
        response = self.client.post(
            reverse('reefuser_list'),
            data={
                "username": "test_user",
                "password": "test_user_password",
                "groups": [
                    self.group_name
                ],
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @tccounter('reefuser_list', 'post', ENABLE_TCCOUNTER)
    def test_post_reefuser_id_in_response(self):
        """
        Date 2019/10/30
        Author: Goufuqiang
        Describe: "id" in response
        """
        response = self.client.post(
            reverse('reefuser_list'),
            data={
                "username": "test_user",
                "password": "test_user_password",
                "groups": [
                    self.group_name
                ],
            }
        )
        self.assertIn("id", response.data)

    @tccounter('reefuser_detail', 'put', ENABLE_TCCOUNTER)
    def test_put_reefuser_200ok(self):
        """
        Date 2019/10/30
        Author: Goufuqiang
        Describe: PUT /cedar/reefuser/{id}
        """
        response = self.client.put(
            reverse('reefuser_detail', args=(self.user_id,)),
            data={
                "username": "test_user1",
                "password": "test_user_password1",
                "groups": [
                    self.group_name
                ]
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('username', None), "test_user1")

    @tccounter('reefuser_detail', 'put', ENABLE_TCCOUNTER)
    def test_put_reefuser_usernmae_is_empty(self):
        """
        Date 2019/10/30
        Author: Goufuqiang
        Describe: username is empty
        """
        response = self.client.put(
            reverse('reefuser_detail', args=(self.user_id,)),
            data={
                "username": "",
                "password": "test_user_password1",
                "groups": [
                    self.group_name
                ]
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter('reefuser_detail', 'patch', ENABLE_TCCOUNTER)
    def test_patch_reefuser_200ok(self):
        """
        Date 2019/10/30
        Author: Goufuqiang
        Describe: PATCH /cedar/reefuser/{id}
        """
        #
        response = self.client.patch(
            reverse('reefuser_detail', args=(self.user_id,)),
            data={
                "username": "test_user2"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter('reefuser_detail', 'patch', ENABLE_TCCOUNTER)
    def test_patch_reefuser(self):
        """
        Date 2019/10/30
        Author: Goufuqiang
        Describe: 修改username group不变
        """
        group_name = self.client.get(
            reverse('reefuser_detail', args=(self.user_id,)), data={'fields': "groups"}
        ).data.get('groups', None)
        response = self.client.patch(
            reverse('reefuser_detail', args=(self.user_id,)),
            data={
                "username": "test_user2"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(group_name, response.data.get('groups', None))

    @tccounter('reefuser_detail', 'delete', ENABLE_TCCOUNTER)
    def test_delete_reefuser_406ok(self):
        """
        Date 2019/10/30
        Author: Goufuqiang
        Describe: DELETE /cedar/reefuser/{id}
        """
        response = self.client.delete(
            reverse('reefuser_detail', args=(self.user_id,)),
        )
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    @tccounter('reefuser_detail', 'delete', ENABLE_TCCOUNTER)
    def test_delete_reefuser_repeat_delete(self):
        """
        Date 2019/10/30
        Author: Goufuqiang
        Describe: repeat delete reefuser
        """
        user_id = ReefUser.objects.create(
                        username='user{}'.format('1'),
                        email='user{}@tests.com'.format('1'),
                        password='user{}'.format('1')
                    ).id
        self.client.delete(
            reverse('reefuser_detail', args=(user_id,)),
        )
        response = self.client.delete(
            reverse('reefuser_detail', args=(user_id,)),
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)