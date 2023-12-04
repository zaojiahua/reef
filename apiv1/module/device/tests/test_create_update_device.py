from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apiv1.core.test import TestTool, tccounter
from apiv1.module.device.models import Device, Manufacturer, PhoneModel, RomVersion, AndroidVersion
from apiv1.module.device.models import MonitorPort, PowerPort, TempPort
from reef.settings import ENABLE_TCCOUNTER


class TestDeviceCreateUpdate(APITestCase):
    def __init__(self, *args, **kwargs):
        super(TestDeviceCreateUpdate, self).__init__(*args, **kwargs)
        self.url = reverse('create_update_device')

    def get_exist_device_data(self):
        return {
            'cabinet': self.default_data['cabinet'].id,
            'device_label': self.default_data['device'].device_label,
            'device_name': 'name',
            'system': self.default_data['system'].id,
            'ip_address': '10.0.0.0',
            'android_version': self.default_data['android_version'].id,
            'phone_model_name': self.default_data['phone_model'].phone_model_name,
            'cpu_id': 'cpu_id',
            'cpu_name': 'cpu_name',
            'rom_version': self.default_data['rom_version'].version,
            'start_time_key': "start_time_key",
            'power_port': self.default_data['power_port'].port,
            'monitor_index': self.default_data['monitor_port'].port,
            'temp_port': [self.default_data['temp_port'].port]
        }

    def get_unexist_device_data(self):
        data = self.get_exist_device_data()
        data['device_label'] = 'new_' + data['device_label']
        return data

    def setUp(self):
        self.default_data = TestTool.load_default_data()

    @tccounter("create_update_device", "post", ENABLE_TCCOUNTER)
    def test_create_missing_device_label(self):
        """
        测试post请求（缺少必要的device_label属性）生成device实例
        """
        data = self.get_unexist_device_data()
        data.pop('device_label')
        response = self.client.post(
            self.url,
            data=data
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("create_update_device", "post", ENABLE_TCCOUNTER)
    def test_generate_phone_model_instance(self):
        """
        测试在生成device实例过程中，是否生成了phone_model实例
        """
        response = self.client.post(
            self.url,
            data=self.get_unexist_device_data()
        )
        try:
            device = Device.objects.get(device_label='new_device0')
        except Device.DoesNotExist:
            device = None
        phone_model = device.phone_model

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(device)
        self.assertTrue(phone_model)

    @tccounter("create_update_device", "post", ENABLE_TCCOUNTER)
    def test_cpu_id_required(self):
        """
        確認cpu_id为required栏位
        """
        # 未提供cpu_id的device新增请求
        data = self.get_unexist_device_data()
        data.pop('cpu_id')
        response = self.client.post(
            self.url,
            data=data
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tccounter("create_update_device", "post", ENABLE_TCCOUNTER)
    def test_support_cabinet_in_input(self):
        """
        Input中应该要可以指定cabinet(Not required)
        """
        self.client.post(
            self.url,
            data=self.get_unexist_device_data()
        )
        try:
            device = Device.objects.get(device_label='new_device0')
        except Device.DoesNotExist:
            device = None
        self.assertIsNotNone(device)
        self.assertIsNotNone(
            Device.objects.get(device_label='new_device0').cabinet_id
        )

    @tccounter("create_update_device", "post", ENABLE_TCCOUNTER)
    def test_temp_port_list(self):
        """
        传入的temp_port应为一temp_port清单, 清单内为temp_port.port
        当传入的temp_port不存在，创建它。
        """
        tp1 = TempPort.objects.create(port='tp1')
        tp2 = TempPort.objects.create(port='tp2')
        m = Manufacturer.objects.create(manufacturer_name='manufacturer_name')
        p = PhoneModel.objects.create(
            phone_model_name='phone_model_name',
            manufacturer=m,
            cpu_name='cpu_name'
        )
        r = RomVersion.objects.create(
            manufacturer=m,
            version='version'
        )
        d = Device.objects.create(
            device_label='device_label',
            device_name='device_name',
            cpu_id='cpu_id',
            rom_version=r
        )
        response = self.client.post(
            self.url,
            data={
                'device_label': d.device_label,
                'rom_version': r.version,
                'android_version': 'android_version',
                'phone_model_name': p.phone_model_name,
                'cpu_name': p.cpu_name,
                'cpu_id': d.cpu_id,
                'temp_port': [tp1.port, tp2.port, 'tp3']
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        tps = list(TempPort.objects.filter(
            port__in=['tp1', 'tp2', 'tp3']
        ).values_list('port', flat=True))
        self.assertEqual(['tp1', 'tp2', 'tp3'], sorted(tps), response.data)

    @tccounter("create_update_device", "post", ENABLE_TCCOUNTER)
    def test_create_with_unexist_monitor(self):
        """
        传入不存在的monitor
        测试是否自动创建并更新
        """
        data = self.get_exist_device_data()
        data['monitor_index'] = 'new_monitor_index'
        response = self.client.post(
            self.url,
            data=data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        device = Device.objects.get(device_label=data['device_label'])
        self.assertEqual(
            len(device.monitor_index.all()),
            1
        )
        self.assertEqual(
            device.monitor_index.all()[0].port,
            'new_monitor_index'
        )

    @tccounter("create_update_device", "post", ENABLE_TCCOUNTER)
    def test_create_with_exist_monitor(self):
        """
        传入存在的monitor
        测试是否正常更新
        """
        monitor_port = MonitorPort.objects.create(
            port='MP-01'
        )
        data = self.get_exist_device_data()
        data['monitor_index'] = monitor_port.port
        response = self.client.post(
            self.url,
            data=data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        device = Device.objects.get(device_label=data['device_label'])
        self.assertEqual(
            len(device.monitor_index.all()),
            1
        )
        self.assertEqual(
            device.monitor_index.all()[0].port,
            monitor_port.port
        )

    @tccounter("create_update_device", "post", ENABLE_TCCOUNTER)
    def test_create_with_unexist_tempport(self):
        """
        传入不存在的temp_port
        测试是否自动创建并更新
        """
        data = self.get_exist_device_data()
        data['temp_port'] = ['new_temp_port']
        response = self.client.post(
            self.url,
            data=data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        device = Device.objects.get(device_label=data['device_label'])
        self.assertEqual(
            len(device.tempport.all()),
            1
        )
        self.assertEqual(
            device.tempport.all()[0].port,
            'new_temp_port'
        )

    @tccounter("create_update_device", "post", ENABLE_TCCOUNTER)
    def test_create_with_exist_tempport(self):
        """
        传入存在的temp_port
        测试是否正常更新
        """
        temp_port = TempPort.objects.create(
            port='TP-01'
        )
        data = self.get_exist_device_data()
        data['temp_port'] = [temp_port.port]
        response = self.client.post(
            self.url,
            data=data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        device = Device.objects.get(device_label=data['device_label'])
        self.assertEqual(
            len(device.tempport.all()),
            1
        )
        self.assertEqual(
            device.tempport.all()[0].port,
            temp_port.port
        )

    @tccounter("create_update_device", "post", ENABLE_TCCOUNTER)
    def test_create_with_unexist_powerport(self):
        """
        传入不存在的power_port
        测试是否自动创建并更新
        """
        data = self.get_exist_device_data()
        data['power_port'] = 'new_power_port'
        response = self.client.post(
            self.url,
            data=data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        device = Device.objects.get(device_label=data['device_label'])
        self.assertEqual(
            device.powerport.port,
            'new_power_port'
        )

    @tccounter("create_update_device", "post", ENABLE_TCCOUNTER)
    def test_create_with_exist_powerport(self):
        """
        传入存在的power_port
        测试是否正常更新
        """
        power_port = PowerPort.objects.create(
            port='PP-01'
        )
        data = self.get_exist_device_data()
        data['power_port'] = power_port.port
        response = self.client.post(
            self.url,
            data=data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        device = Device.objects.get(device_label=data['device_label'])
        self.assertEqual(
            device.powerport.port,
            power_port.port
        )

    @tccounter("create_update_device", "post", ENABLE_TCCOUNTER)
    def test_android_version_field(self):
        """
        Date: 2018/12/10
        Author: Raymond
        Client should provide android_version when creating or updating device.
        If android_version instance not exist, reef should auto create it.
        """
        data = self.get_unexist_device_data()
        # Change field android_version to unexist data.
        android_version = 'unexist_android_version'
        data['android_version'] = android_version
        response = self.client.post(
            self.url,
            data=data
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.data
        )
        self.assertTrue(
            AndroidVersion.objects.filter(version=android_version).exists(),
        )

    @tccounter("create_update_device", "post", ENABLE_TCCOUNTER)
    def test_add_power_port_and_check_status_busy(self):
        """
        Date: 2019/05/16
        Author: Raymond
        When assign a new power_port for device, power_port's status should change to busy
        """
        p1: PowerPort = PowerPort(port="TEST_PORT1")
        p1.save()

        data = self.get_exist_device_data()
        data["power_port"] = p1.port

        response = self.client.post(
            self.url,
            data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        p1.refresh_from_db(fields=["status"])
        self.assertEqual(p1.status, "busy")

    @tccounter("create_update_device", "post", ENABLE_TCCOUNTER)
    def test_remove_power_port_and_check_status_idle(self):
        """
        Date: 2019/05/16
        Author: Raymond
        When assign a null power_port for device, power_port's status should change to idle
        """
        p1: PowerPort = PowerPort(port="TEST_PORT1", status="busy", device=self.default_data["device"])
        p1.save()

        data = self.get_exist_device_data()
        data["power_port"] = None

        response = self.client.post(
            self.url,
            data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        p1.refresh_from_db(fields=["status"])
        self.assertEqual(p1.status, "idle")

    @tccounter("create_update_device", "post", ENABLE_TCCOUNTER)
    def test_change_power_port_and_check_status_idle(self):
        """
        Date: 2019/05/16
        Author: Raymond
        When change power_port for device, power_port's status should be changed
        """
        p1: PowerPort = PowerPort(port="TEST_PORT1", status="busy", device=self.default_data["device"])
        p1.save()

        p2: PowerPort = PowerPort(port="TEST_PORT2", status="idle")
        p2.save()

        data = self.get_exist_device_data()
        data["power_port"] = p2.port

        response = self.client.post(
            self.url,
            data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        p1.refresh_from_db(fields=["status"])
        p2.refresh_from_db(fields=["status"])
        self.assertEqual(p1.status, "idle")
        self.assertEqual(p2.status, "busy")

    @tccounter("create_update_device", "post", ENABLE_TCCOUNTER)
    def test_update_without_power_port(self):
        """
        Date: 2019/06/17
        Author: Raymond
        更新Device时，若未传入power_port参数，不更新power_port内容
        (在之前的版本内，不传入power_port默认会将device的power_port覆写为null)
        """
        data = self.get_exist_device_data()
        origin_power_port = data['power_port']
        del data['power_port']
        response = self.client.post(
            self.url,
            data=data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(PowerPort.objects.values("device_id").get(port=origin_power_port)["device_id"])
