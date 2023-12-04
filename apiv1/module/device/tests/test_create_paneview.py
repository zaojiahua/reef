from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from apiv1.module.device.models import PaneSlot
from apiv1.module.system.models import Cabinet
from reef.settings import ENABLE_TCCOUNTER


class TestCreatePaneView(APITestCase):
    def setUp(self) -> None:
        """
        Date: 2022/7/27
        Author: Gfuqiang
        约束条件，一个机柜只能绑定一个PaneView
        """
        self.default_data = TestTool.load_default_data()

    @tccounter("create_paneview", "post", ENABLE_TCCOUNTER)
    def test_200ok(self):
        """
        Date: 2019/12/27
        Author: raymond
        测试基本添加功能
        """
        cabinet = TestTool.temp_cabinet('create', None, belong_to=self.default_data['system'])
        response = self.client.post(reverse('create_paneview'), data={
            "name": "Pane001@7x9",
            "type": "matrix",
            "cabinet": cabinet.id,
            "ret_level": 0
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        TestTool.temp_cabinet('delete', cabinet)

    @tccounter("create_paneview", "post", ENABLE_TCCOUNTER)
    def test_name_format_validation(self):
        """
        Date: 2019/12/27
        Author: raymond
        测试是否符合paneview.name的命名规则校验
        合法的名称只能由英文字母大小写+下划线+数字组成
        且名称后方跟随着row x col的规格标记
        x为英文字母的x，忽略大小写
        名称和规格之间使用一个@分隔符

        例如:
        Pane_001@4x5
        """
        cabinet = TestTool.temp_cabinet('create', None, belong_to=self.default_data['system'])
        response = self.client.post(reverse('create_paneview'), data={
            "name": "Pane-001@7x9",
            "type": "matrix",
            "cabinet": cabinet.id,
            "ret_level": 0
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        TestTool.temp_cabinet('delete', cabinet)

        cabinet = TestTool.temp_cabinet('create', None, belong_to=self.default_data['system'])
        response = self.client.post(reverse('create_paneview'), data={
            "name": "Pane001@a7xa9",
            "type": "matrix",
            "cabinet": cabinet.id,
            "ret_level": 0
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        TestTool.temp_cabinet('delete', cabinet)

        cabinet = TestTool.temp_cabinet('create', None, belong_to=self.default_data['system'])
        response = self.client.post(reverse('create_paneview'), data={
            "name": "Pane_001@7x9",
            "type": "matrix",
            "cabinet": cabinet.id,
            "ret_level": 0
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        TestTool.temp_cabinet('delete', cabinet)

    @tccounter("create_paneview", "post", ENABLE_TCCOUNTER)
    def test_paneslots_auto_create(self):
        """
        Date: 2019/12/27
        Author: raymond
        创建PaneView时，PaneSlots应该自动被创建，创建的数量由创建时的rows, cols决定
        """
        rows = 7
        cols = 9
        cabinet = TestTool.temp_cabinet('create', None, belong_to=self.default_data['system'])
        response = self.client.post(reverse('create_paneview'), data={
            "name": f"Pane001@{rows}x{cols}",
            "type": "matrix",
            "cabinet": cabinet.id,
            "ret_level": 0
        })
        paneview = response.data["id"]

        self.assertEqual(PaneSlot.objects.filter(paneview=paneview).count(), rows * cols)
        TestTool.temp_cabinet('delete', cabinet)

