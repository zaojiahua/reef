from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.core.constants import PANESLOT_STATUS_OK
from apiv1.core.test import TestTool, tccounter
from reef.settings import ENABLE_TCCOUNTER


class TestRemovePaneView(APITestCase):
    def setUp(self) -> None:
        self.default_data = TestTool.load_default_data()

    @tccounter("remove_paneview", "delete", ENABLE_TCCOUNTER)
    def test_200ok(self):
        """
        Date: 2020/03/25
        Author: raymond
        测试能够正常移除paneview
        """
        response = self.client.delete(reverse("remove_paneview"), data={
            "id": self.default_data["paneview"].id
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tccounter("remove_paneview", "delete", ENABLE_TCCOUNTER)
    def test_dirty_remove(self):
        """
        Date: 2020/03/25
        Author: raymond
        当paneview中仍有paneslot关联到device时，拒绝删除paneview
        """
        ps = self.default_data["paneslot"]
        ps.device = self.default_data["device"]
        ps.status = PANESLOT_STATUS_OK
        ps.save()

        response = self.client.delete(reverse("remove_paneview"), data={
            "id": self.default_data["paneview"].id
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

