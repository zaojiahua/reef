import logging, copy, requests
import os
import re
import asyncio

from django.db import transaction
from django.http import FileResponse
from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status, views, mixins
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from collections import defaultdict

from apiv1.core.cache import cache_dcr
from apiv1.core.constants import REDIS_CACHE_GET_DEVICE_TEMPERATURE_RAPID, REDIS_CACHE_GET_DEVICE_POWER_RAPID, \
    PANEVIEW_TYPE_TEST_BOX, DEVICE_STATUS_IDLE, DEVICE_STATUS_OFFLINE, DEVICE_STATUS_BUSY
from apiv1.core.request import ReefRequest, sync_info_to_coral
from apiv1.core.response import ReefResponse, reef_400_response
from apiv1.core.status import StatusCode
from apiv1.core.tool import CleanObjRelated
from apiv1.core.utils import ReefLogger
from apiv1.core.view.generic import AutoExecuteSerializerGenericAPIView
from apiv1.module.device.models import DeviceTemperature, DevicePower, DeviceScreenshot, Device, DeviceCoordinate, \
    PaneSlot, DeviceCutCoordinate, SubsidiaryDevice, PhoneModel, RomVersion, AndroidVersion, Manufacturer, \
    PhoneModelCustomCoordinate, PowerStrategy
from apiv1.module.device.models import PowerPort, TempPort
from apiv1.module.device.serializer import CreateDeviceScreenshotSerializer, CoralDeviceSerializer, \
    LogoutDeviceSerializer, ReleaseDeviceSerializer, CreateDeviceTempByPortNameSerializer, CheckoutDeviceSerializer, \
    DeviceCutCoordinateSerializer, GetDeviceCutCoordinateSerializer, CrtOrUptDeviceCutCoordinateSerializer, \
    SubsidiaryDeviceSerializer, CreateOrUpdateSubsidiaryDeviceSerializer, BindSubsidiaryDeviceSerializer, \
    UnbindSubsidiaryDeviceSerializer, RegisterSubsidiaryDeviceSerializer, CancelSubsidiaryDeviceSerializer, \
    UpdatePhoneModelSerializer, CoralDeviceReconnectSerializer, UpdatePhoneModelCustomCoordinateSerializer, \
    AddPowerStrategySerializer, PowerPortStrategySerializer, UpdateDeviceResolutionSerializer
from apiv1.module.resource.models import SIMCard, Account
from apiv1.module.system.models import Cabinet
from reef import settings
from reef.settings import MEDIA_ROOT

logger = logging.getLogger(__name__)


def _swagger_extra_param():
    record_datetime__gt = openapi.Parameter('record_datetime__gt', openapi.IN_QUERY, description="min record datetime ",
                                            type=openapi.TYPE_STRING)
    record_datetime__lt = openapi.Parameter('record_datetime__lt', openapi.IN_QUERY, description="max record datetime",
                                            type=openapi.TYPE_STRING)
    device_id = openapi.Parameter('device_id', openapi.IN_QUERY, description="device id", type=openapi.TYPE_INTEGER)
    return [record_datetime__gt, record_datetime__lt, device_id]


class GetDevicePowerRapidView(generics.GenericAPIView):
    """
    提供设备电量信息，以供图表绘制
    """

    @swagger_auto_schema(manual_parameters=_swagger_extra_param())
    @action(detail=True, methods=['get'])
    @cache_dcr(key_leading=REDIS_CACHE_GET_DEVICE_POWER_RAPID, ttl_in_second=300)
    def get(self, request):
        """
        :param request: device_id/record_datetime__gt/record_datetime__lt(3个参数可传可不传)
        :return:
            {
                'devicepowers': [
                    {
                        'device': {'id': 1},
                        'record_datetime': 2019-10-09 15:35:15 ,
                        'power_port': {'port': PA01},
                        'battery_level': 85,
                        'charging': False
                    }]
            }
        """
        query_params = request.query_params
        record_datetime__gt = query_params.get('record_datetime__gt', None)
        record_datetime__lt = query_params.get('record_datetime__lt', None)
        device_id = query_params.get('device_id', None)

        queryset = DevicePower.objects.all()

        if record_datetime__gt is not None:
            queryset = queryset.filter(record_datetime__gt=record_datetime__gt)

        if record_datetime__lt is not None:
            queryset = queryset.filter(record_datetime__lt=record_datetime__lt)

        if device_id is not None:
            queryset = queryset.filter(device_id=device_id)

        queryset = queryset.values(
            'device_id',
            'record_datetime',
            'power_port__port',
            'battery_level',
            'charging'
        ).order_by('record_datetime')

        queryset = data_reduce(queryset)

        return_data = {
            'devicepowers': [
                {
                    'device': {
                        'id': power['device_id']
                    },
                    'record_datetime': power['record_datetime'].astimezone(timezone.get_current_timezone()).strftime(
                        settings.REST_FRAMEWORK.get('DATETIME_FORMAT', '%Y-%m-%d %H:%M:%S')),
                    'power_port': {
                        'port': power['power_port__port']
                    },
                    'battery_level': power['battery_level'],
                    'charging': power['charging']
                } for power in queryset]
        }

        return Response(return_data, status=status.HTTP_200_OK)


class GetDevicePowerBatteryLevel(generics.GenericAPIView):
    """获取device的最新电量信息"""
    device_id = openapi.Parameter('device_id', openapi.IN_QUERY, description="device_id", type=openapi.TYPE_STRING)

    @swagger_auto_schema(manual_parameters=[device_id])
    @action(detail=True, methods=['get'])
    def get(self, request):
        """
        :param request: device_id
        :return: 在线设备（busy/idle） {'device': 1, 'battery_level': 85}
                  离线设备（error/offline） {'device': 2, 'battery_level': None}
        """
        device_id = request.query_params.get('device_id', None)

        if device_id is None:
            return Response({'error': 'Missing parameters'}, status=status.HTTP_400_BAD_REQUEST)

        if device_id == '':
            return Response({'error': 'device_id field cannot be blank'}, status=status.HTTP_400_BAD_REQUEST)

        return_data = []

        for dev_id in device_id.split(','):
            device_power = DevicePower.objects.filter(device_id=dev_id).order_by('-record_datetime').first()

            if not hasattr(device_power, 'device'):
                return_data.append({'device': int(dev_id), 'battery_level': None})
            else:
                if device_power.device.status in ['busy', 'idle']:
                    return_data.append({'device': device_power.device.id, 'battery_level': device_power.battery_level})
                else:
                    return_data.append({'device': int(dev_id), 'battery_level': None})

        return Response(return_data, status=status.HTTP_200_OK)


class GetDevicePhoneModel(generics.GenericAPIView):
    """获取所有device的phone_model(不重复)"""

    def get(self, request):
        """
        :param request:
        :return: {
                    "device": [
                    {
                        "id": 1,
                        "phone_model_name": "redmin"
                    }
                ]}
        """
        device_type = request.query_params.get('device_type', None)
        if device_type == 'subsidiary_device' and device_type:
            queryset = SubsidiaryDevice.objects.values('phone_model__id', 'phone_model__phone_model_name').distinct()
        else:
            queryset = Device.objects.values('phone_model__id', 'phone_model__phone_model_name').distinct()

        if queryset is None:
            return Response({}, status=status.HTTP_200_OK)

        return_data = {
            'device': [
                {
                    'id': qs['phone_model__id'],
                    'phone_model_name': qs['phone_model__phone_model_name']
                } for qs in queryset if qs['phone_model__phone_model_name']
            ]
        }

        return Response(return_data, status=status.HTTP_200_OK)


class GetDeviceTemperatureRapidView(generics.GenericAPIView):
    """
    提供设备温度信息，以供图表绘制
    """

    @swagger_auto_schema(manual_parameters=_swagger_extra_param())
    @action(detail=True, methods=['get'])
    @cache_dcr(key_leading=REDIS_CACHE_GET_DEVICE_TEMPERATURE_RAPID, ttl_in_second=300)
    def get(self, request):
        """
        :param request:  device_id/record_datetime__gt/record_datetime__lt(3个参数可传可不传)
        :return: {
                    "devicetemperatures": [
                        {
                            "device": {"id": 2},
                            "record_datetime": "2019-10-09 07:40:11",
                            "temp_port": {"port": "8082"},
                            "temperature": 54
                        }]
                    }
        """
        query_params = request.query_params
        record_datetime__gt = query_params.get('record_datetime__gt', None)
        record_datetime__lt = query_params.get('record_datetime__lt', None)
        device_id = query_params.get('device_id', None)

        queryset = DeviceTemperature.objects.all()

        if record_datetime__gt is not None:
            queryset = queryset.filter(record_datetime__gt=record_datetime__gt)

        if record_datetime__lt is not None:
            queryset = queryset.filter(record_datetime__lt=record_datetime__lt)

        if device_id == '':
            return Response({'error': 'device_id field cannot be blank'}, status=status.HTTP_400_BAD_REQUEST)

        if device_id is not None:
            queryset = queryset.filter(device_id=device_id)

        queryset = queryset.values(
            'device_id',
            'record_datetime',
            'temp_port__port',
            'temperature'
        ).order_by('record_datetime')

        queryset = data_reduce(queryset)

        return_data = {
            'devicetemperatures': [
                {
                    'device': {
                        'id': temp['device_id']
                    },
                    'record_datetime': temp['record_datetime'].astimezone(timezone.get_current_timezone()).strftime(
                        settings.REST_FRAMEWORK.get('DATETIME_FORMAT', '%Y-%m-%d %H:%M:%S'))
                    ,
                    'temp_port': {
                        'port': temp['temp_port__port']
                    },
                    'temperature': temp['temperature']
                } for temp in queryset]
        }
        return Response(return_data, status=status.HTTP_200_OK)


class CreateDeviceScreenshotView(generics.GenericAPIView):
    """
    新增设备截图
    """
    queryset = DeviceScreenshot.objects.all()
    serializer_class = CreateDeviceScreenshotSerializer

    def post(self, request):
        """
        :param request:{
                            device: device_label_3,
                            snap_timestamp: 2019_10_25_16_24_45,
                            screenshot: test.png
                        }
        :return:{
                    device: device_label_3,
                    snap_timestamp: 2019-10-25 16:24:45,
                    screenshot: test.png
                }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class DeviceCreateUpdateView(generics.GenericAPIView):
    """
    Coral 新增/更新 设备所使用的接口
    """
    serializer_class = CoralDeviceSerializer
    queryset = Device.objects.all()

    def post(self, request):
        device_serializer = CoralDeviceSerializer(data=request.data)
        device_serializer.is_valid(raise_exception=True)
        device = device_serializer.save()
        return Response(
            {'id': device.id},
            status=status.HTTP_200_OK
        )


class DeviceUpdateView(CreateAPIView):
    serializer_class = CoralDeviceReconnectSerializer
    queryset = Device.objects.all()

    def create(self, request, *args, **kwargs):
        """
        设备重连接口：
            1. 根据传递的rom_version, android_version参数 没有创建，
            2. manufacture不进行创建，使用设备注册时关联的设备
            3. status传参就更新，否则不更新
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device_obj = serializer.validated_data.get('device_label')
        manufacturer_obj = serializer.validated_data.get(
            'manufacturer',
            device_obj.rom_version.manufacturer.id
        )
        rom_version = serializer.validated_data.get('rom_version')
        if isinstance(manufacturer_obj, Manufacturer):
            manufacturer_id = manufacturer_obj.id
        else:
            manufacturer_id = manufacturer_obj
        rom_obj, _ = RomVersion.objects.get_or_create(
            version=rom_version,
            defaults={'version': rom_version, 'manufacturer_id': manufacturer_id}
        )
        android_version = serializer.validated_data.get('android_version')
        android_obj, _ = AndroidVersion.objects.get_or_create(
            version=android_version,
            defaults={'version': android_version}
        )
        serializer.validated_data.pop('manufacturer', '')
        serializer.validated_data.pop('device_label', '')
        serializer.validated_data['rom_version'] = rom_obj
        serializer.validated_data['android_version'] = android_obj
        Device.objects.filter(id=device_obj.id).update(**serializer.validated_data)

        return ReefResponse()


class LogoutDeviceView(generics.GenericAPIView):
    """
    Coral注销Device时使用的接口
    用户取出设备时，会调用此接口，注销设备信息
    """
    serializer_class = LogoutDeviceSerializer
    queryset = Device.objects.all()

    @transaction.atomic
    def post(self, request):
        """
        :param request:  { "device_id": 1}
        :return: {}
        清理设备关联信息
        """
        serializer: LogoutDeviceSerializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device = serializer.validated_data['id']
        # 指定要清除的device关联信息
        filters = [
            'powerport', 'tempport', 'cabinet', 'coordinate', 'device_name',
            'simcard', 'account', 'monitor_index'
        ]
        clean_obj = CleanObjRelated(device, filters)
        fail_list = clean_obj.clean()

        # 将auto_test置为Flase
        device.auto_test = False
        device.status = 'offline'

        # 当前没有主机多对一僚机需求，所以僚机伴随主机的注销移除关联关系。
        subsidiary_device_queryset = SubsidiaryDevice.objects.filter(device=device)
        subsidiary_device_queryset.update(
            status='unbound', device=None
        )
        device.save()
        return ReefResponse(data=fail_list)


class GetDeviceBat(APIView):
    def get(self, request):
        ip = request.query_params.get("ip", "0.0.0.0")
        if ip == "0.0.0.0":
            return Response({'reason': "需要先选择一个设备"}, status=status.HTTP_400_BAD_REQUEST)
        cmd = f"COLOR 0f \nD://screenShow//adb start-server \ntimeout /T 2  \nD://screenShow//adb  tcpip 5555  \n" \
              f'@for /f "tokens=*"' \
              f" %%i in ('D://screenShow//adb connect {ip}:5555') do @set vars=%%i  \n" \
              f'echo  %vars%| findstr "connected" >nul && ( \n' \
              f"timeout /T 1  \nD://screenShow//scrcpy.exe -s {ip}:5555 -b2M -m800 \n" \
              f"D://screenShow//adb disconnect {ip}:5555 \npause \n) || ( \nCOLOR 0c \n" \
              f"echo [Warrning] adb wifi connect fail [Warrning] \npause ) \n"
        with open(os.path.join(MEDIA_ROOT, "startScreen.bat"), 'w') as f:
            f.write(cmd)
        f_res = open(os.path.join(MEDIA_ROOT, "startScreen.bat"), 'rb')
        response = FileResponse(f_res, content_type='APPLICATION/OCTET-STREAM')
        response['Content-Disposition'] = 'attachment; filename=' + "startScreen.bat"
        return response


class DeviceTemperatureView(generics.GenericAPIView):
    """
    取得设备温度数据
    """

    @swagger_auto_schema(manual_parameters=_swagger_extra_param(),
                         responses={200: "{'record_datetimes': [],'temp_ports':{'port': 'PA-01','temperatures': []}]}"})
    @action(detail=True, methods=['get'])
    def get(self, request):
        """
        :param request:  device_id/record_datetime__gt/record_datetime__lt
        :return:  {
                        "record_datetimes": ["2019-10-09 07:40:11"],
                        "temp_ports": {"PA_01": {"temperatures": [45,-100.1]}}
                    }
        """
        threshold = 100

        query_params = request.query_params
        device_id = query_params.get('device_id', None)
        record_datetime__gt = query_params.get('record_datetime__gt', None)
        record_datetime__lt = query_params.get('record_datetime__lt', None)

        queryset = DeviceTemperature.objects.all()

        if device_id is not None:
            queryset = queryset.filter(device_id=device_id)

        if record_datetime__gt is not None:
            queryset = queryset.filter(record_datetime__gt=record_datetime__gt)

        if record_datetime__lt is not None:
            queryset = queryset.filter(record_datetime__lt=record_datetime__lt)

        queryset = queryset.values(
            'temp_port__port',
            'record_datetime',
            'temperature'
        ).order_by('record_datetime')

        num_of_result = queryset.count()
        # 以100为阈值取步长  3 = 389//100
        slice_step = num_of_result // threshold
        if slice_step == 0:
            slice_step = 1

        temps = queryset[::slice_step]

        record_datetimes = [
            temp['record_datetime'].astimezone(
                timezone.get_current_timezone()
            ).strftime(settings.REST_FRAMEWORK['DATETIME_FORMAT'])
            for temp in temps
        ]
        temp_ports = {}
        for temp in temps:
            port = temp['temp_port__port']
            if port not in temp_ports:
                temp_ports[port] = {
                    'temperatures': []
                }
            temp_ports[port]['temperatures'].append(temp['temperature'])

        return_data = {
            'record_datetimes': record_datetimes,
            'temp_ports': temp_ports
        }

        return Response(
            return_data,
            status=status.HTTP_200_OK
        )


class ReleaseDevice(generics.GenericAPIView):
    serializer_class = ReleaseDeviceSerializer

    def post(self, request):
        """
        逻辑：注销单个设备
            1. 通知coral（传递所需参数）
            2. 更新设备 cabinet，coordinate，auto_test 属性
            3. 删除PowerPort, TempPort，PaneSlot，DeviceCoordinate 和当前设备关联
            4. 清除关联僚机
            5. 释放绑定的sim，account 资源
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device = serializer.validated_data['device_label']
        if not device.cabinet:
            return reef_400_response(description='设备没有关联机柜，不能移除', message=f"{device.device_label}")
        force = serializer.validated_data['force']
        subsidiary_device_queryset = device.subsidiarydevice.all()
        serializer.validated_data['assistance_ip_address'] = list(subsidiary_device_queryset.values_list(
            'serial_number', flat=True
        ))
        # force True 为不通知coral，强制移除
        if not force:
            try:
                ip = device.cabinet.ip_address
                serializer.validated_data['device_label'] = device.device_label
                res = requests.post(
                    f"http://{ip}:{settings.CORAL_PORT}/pane/device_leave/",
                    json=serializer.validated_data,
                    timeout=60
                )
            except Exception as e:
                return reef_400_response(
                    custom_code=StatusCode.DEVICE_REQUEST_CORAL_FAILED.value,
                    message=f"Request coral fail: {e}",
                    description=f"{device.cabinet.cabinet_name}"
                )

            if res.status_code != 200:
                return Response(res.content, status=res.status_code)

        device.cabinet = None
        device.coordinate = None
        device.auto_test = False
        device.status = DEVICE_STATUS_OFFLINE

        for powerport in PowerPort.objects.filter(device_id=device.id):
            powerport.device_id = None
            powerport.save()

        for tempport in TempPort.objects.filter(device_id=device.id):
            tempport.device_id = None
            tempport.save()

        PaneSlot.objects.filter(device=device).update(device=None, status='empty')

        DeviceCoordinate.objects.filter(device=device).delete()
        # 清除附属设备, 更新附属设备属性，请求设备绑定信息
        subsidiary_device_queryset.update(
            **{'order': None, 'update_time': timezone.now(), 'device': None, 'status': 'unbound'}
        )
        update_subsidiary_device_count(device_list=[device], operate='clear')
        # 解绑主机关联资源（sim card, account）
        if serializer.validated_data.get('unbind_resource', False):
            SIMCard.objects.filter(device=device).update(
                device=None, status=DEVICE_STATUS_IDLE, history_relevance=device.device_name
            )
            for account in device.account.all():
                account.status = DEVICE_STATUS_IDLE
                account.save()
            device.account.clear()
        # 2021/9/7 保留设备名称
        # device.device_name = None
        device.save()
        # 通知coral主僚机关系更新
        sync_info_to_coral({"resource_name": "device"}, {"execute_space": "注销主机"})
        return ReefResponse()


class CreateDeviceTempByPortNameView(generics.GenericAPIView):
    """
     可以根据temp_port的port字段创建device_temperature
    """
    serializer_class = CreateDeviceTempByPortNameSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CheckoutDeviceView(generics.GenericAPIView):
    serializer_class = CheckoutDeviceSerializer
    queryset = Device.objects.all()

    def get(self, request):
        """
        校验test_box 类型设备是否配置对应类型的paneview
        """
        query_params = request.query_params.dict()
        query_params['devices'] = query_params.get('devices', '0').split(',')
        serializer = self.get_serializer(data=query_params)
        serializer.is_valid(raise_exception=True)
        device_obj_list = serializer.validated_data.get('devices', [])
        results = []
        for device in device_obj_list:
            if device.device_type == PANEVIEW_TYPE_TEST_BOX:
                if getattr(device, 'paneslot', None) and device.paneslot.paneview.type != device.device_type:
                    results.append(device.device_name)
        return Response(results, status=status.HTTP_200_OK)


class ControlDeviceCutCoordinate(generics.GenericAPIView):
    serializer_class = CrtOrUptDeviceCutCoordinateSerializer
    queryset = DeviceCutCoordinate.objects.all()

    def get(self, request):
        query_params = request.query_params.dict()
        get_serializer = GetDeviceCutCoordinateSerializer(data=query_params)
        get_serializer.is_valid(raise_exception=True)
        device_cut_cdn = DeviceCutCoordinate.objects.filter(**get_serializer.validated_data)
        serializer = DeviceCutCoordinateSerializer(device_cut_cdn, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pane_view = serializer.validated_data.get('pane_view', None)
        phone_model = serializer.validated_data.get('phone_model', None)
        DeviceCutCoordinate.objects.update_or_create(defaults=serializer.validated_data,
                                                     pane_view=pane_view, phone_model=phone_model)
        ip_address_list = [cabinet.ip_address for cabinet in Cabinet.objects.filter(is_delete=False)]
        for ip in ip_address_list:
            try:
                res = requests.post(
                    f"http://{ip}:{settings.CORAL_PORT}/door/door_info/",
                    json={
                        "resource_name": "device"
                    },
                    timeout=0.2
                )
            except Exception as e:
                reef_logger = ReefLogger('debug')
                reef_logger.debug(
                    f'Parameter: \n'
                    f'coral ip: {ip}\n'
                    f'eroor info: {e}'
                )
        return Response('success', status=status.HTTP_200_OK)


class CreateOrUpdateSubsidiaryDeviceView(generics.GenericAPIView):
    serializer_class = CreateOrUpdateSubsidiaryDeviceSerializer
    queryset = SubsidiaryDevice.objects.all()

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serial_number = serializer.validated_data['serial_number']
        try:
            # 僚机已经注册过，更新关联关系和状态
            subsidiary_device = SubsidiaryDevice.objects.filter(serial_number=serial_number)
            if not subsidiary_device:
                raise ValueError
            devices = serializer.validated_data.pop('devices')
            serializer.validated_data['update_time'] = timezone.now()
            subsidiary_device.update(**serializer.validated_data)
            subsidiary_device.first().devices.add(*devices)
            if serializer.validated_data.get('is_active', True):
                update_subsidiary_device_count(devices, 'add', 1)
        except Exception as e:
            # 新的僚机直接创建
            serializer.save()
            devices = serializer.validated_data.get('devices', [])
            update_subsidiary_device_count(devices, 'add', 1)
        return Response(status=status.HTTP_201_CREATED)


class FilterSubsidiaryDeviceCount(views.APIView):

    def get(self, request):
        subsidiary_device_count_list = Device.objects.filter(
            status='idle').values_list('subsidiary_device_count', flat=True)
        subsidiary_device_count_list = list(set(subsidiary_device_count_list))
        return Response(subsidiary_device_count_list)


class BindSubsidiaryDeviceView(generics.GenericAPIView):
    serializer_class = BindSubsidiaryDeviceSerializer
    queryset = SubsidiaryDevice

    # @transaction.atomic()
    def post(self, request):
        """
        1. 校验僚机是否被绑定
        2. 校验僚机phone model与主机相同 (22/1/17 取消校验)
        3. 更新僚机同步状态
        4. 维护主僚机绑定状态
        """
        with transaction.atomic():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            device = data['device_id']
            subsidiary_device = data['subsidiary_device_id']
            order = data['order']
            # checkout subsidiary device bind device relation
            if subsidiary_device.device:
                reef_400_response(message='subsidiary device bound device is exist. Please unbind first')
            # checkout device phone model equal
            # if device.phone_model != subsidiary_device.phone_model:
            #     reef_400_response(message='subsidiary device phone model not equal')
            # 更新僚机绑定设备，状态
            subsidiary_device.device = device
            subsidiary_device.status = DEVICE_STATUS_BUSY if device.status == DEVICE_STATUS_BUSY else DEVICE_STATUS_IDLE
            subsidiary_device.order = order
            subsidiary_device.save()
            # 更新主机关联设备
            update_subsidiary_device_count(device_list=[device], operate='add')
        # 通知coral主机主僚机关系更新
        sync_info_to_coral({"resource_name": "device"}, {"execute_space": "绑定僚机"})
        return ReefResponse()


class UnbindSubsidiaryDeviceView(generics.GenericAPIView):
    serializer_class = UnbindSubsidiaryDeviceSerializer
    queryset = SubsidiaryDevice.objects.all()

    def post(self, request):
        with transaction.atomic():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            subsidiary_device = serializer.validated_data['subsidiary_device_id']
            # update device and subsidiary_device relation
            device = subsidiary_device.device
            if device is not None:
                update_subsidiary_device_count(device_list=[device], operate='delete')
            # update status
            subsidiary_device.device = None
            subsidiary_device.status = 'unbound'
            subsidiary_device.order = None
            subsidiary_device.save()
        # 通知coral主僚机关系更新
        sync_info_to_coral({"resource_name": "device"}, {"execute_space": "解绑僚机"})
        return ReefResponse()


class RegisterSubsidiaryDeviceView(generics.GenericAPIView):
    serializer_class = RegisterSubsidiaryDeviceSerializer
    queryset = SubsidiaryDevice.objects.all()

    def post(self, request):
        device_serializer = RegisterSubsidiaryDeviceSerializer(data=request.data)
        device_serializer.is_valid(raise_exception=True)
        custom_name = device_serializer.validated_data.get('custom_name', None)
        # checkout custom_name unique and is_active property is True
        if custom_name:
            queryset = SubsidiaryDevice.objects.filter(
                custom_name=custom_name,
                is_active=True,
            )
            if queryset.exists():
                return reef_400_response(
                    message='自定义名称已存在',
                    description='custom_name field must be unique.'
                )
        subsidiary_device = device_serializer.save()
        return Response(
            {'id': subsidiary_device.id},
            status=status.HTTP_200_OK
        )


class CancelSubsidiaryDeviceView(generics.GenericAPIView):
    serializer_class = CancelSubsidiaryDeviceSerializer
    queryset = SubsidiaryDevice.objects.all()

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        subsidiary_device = validated_data['id']
        if subsidiary_device.status == 'busy':
            reef_400_response(
                message="device is busy status, can't unbind",
                custom_code=StatusCode.DEVICE_IS_BUSY.value,
                description='busy 状态僚机不允许注销'
            )
        device_cancel_checkout(subsidiary_device)
        # update 主机绑定关系
        device = subsidiary_device.device
        if device is not None:
            update_subsidiary_device_count(device_list=[device], operate='delete')

        subsidiary_device.cabinet = None
        subsidiary_device.order = None
        subsidiary_device.device = None
        subsidiary_device.is_active = False
        subsidiary_device.status = 'unbound'
        subsidiary_device.save()
        # 通知coral主僚机关系更新
        sync_info_to_coral({"resource_name": "device"}, {"execute_space": "注销僚机"})
        return ReefResponse()


class UpdatePhoneModelView(generics.GenericAPIView):
    serializer_class = UpdatePhoneModelSerializer
    queryset = PhoneModel.objects.all()

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_model = serializer.validated_data.pop('phone_model_id')
        serializer.validated_data['phone_model_name'] = serializer.validated_data['phone_model_name'].phone_model_name
        cabinet_ip_list = Cabinet.objects.filter(
            is_delete=False,
            type__in=['Tcab_5', 'Tcab_4']  # 暂时使用硬编码匹配符合条件的机柜，后期改进
        ).values_list('ip_address', flat=True)
        request_failed_list = []
        is_success = False
        for ip in cabinet_ip_list:
            try:
                res = requests.post(
                    f"http://{ip}:{settings.CORAL_PORT}/pane/phone_module_update/",
                    json=serializer.validated_data,
                    timeout=0.1
                )
            except Exception as e:
                request_failed_list.append(ip)
            else:
                is_success = True
        if is_success:
            serializer.validated_data.pop('phone_model_name', None)
            phone_model.__dict__.update(**serializer.validated_data)
            phone_model.save()
        return ReefResponse(data=request_failed_list)


class UpdatePhoneModelCustomCoordinateView(AutoExecuteSerializerGenericAPIView):

    serializer_class = UpdatePhoneModelCustomCoordinateSerializer
    queryset = PhoneModelCustomCoordinate.objects.all()

    def post(self, request):
        serializer = self.execute(request=request)
        create_or_update_list = serializer.validated_data.get('create_or_update_list')
        delete_list = serializer.validated_data.get('delete_list')

        create_obj_list = []
        if create_or_update_list:
            for dict_data in create_or_update_list:
                # id存在更新数据，不存在则创建数据
                table_id = dict_data.get('id')
                if table_id:
                    dict_data.pop('id', None)
                    PhoneModelCustomCoordinate.objects.filter(id=table_id).update(**dict_data)
                else:
                    create_obj_list.append(PhoneModelCustomCoordinate(**dict_data))
            try:
                PhoneModelCustomCoordinate.objects.bulk_create(create_obj_list)
            except Exception as e:
                description = ''
                if 'already exists' in str(e):
                    pattern = re.compile(r'=[(](.*),(.*)[)]')
                    m = pattern.search(str(e))
                    if hasattr(m, 'group'):
                        description = m.group(2)
                reef_400_response(message=f'create data error: {e}', description=f'同一机型，不允许创建相同项 {description}')
        if delete_list:
            for delete_dict in delete_list:
                table_id = delete_dict.get('id')
                if table_id:
                    PhoneModelCustomCoordinate.objects.filter(id=table_id).delete()

        # 通知coral更新设备信息
        sync_info_to_coral({"resource_name": "device"}, {"execute_space": "UpdatePhoneModelCustomCoordinate"})
        return ReefResponse()


class AddPowerStrategy(generics.GenericAPIView):

    serializer_class = AddPowerStrategySerializer
    queryset = PowerStrategy.objects.all()

    def post(self, request):
        data = request.data
        request_dict = defaultdict(list)
        for power_port_data in data:
            serializer = self.get_serializer(data=power_port_data)
            serializer.is_valid(raise_exception=True)
            power_port = serializer.validated_data.get('power_port')
            power_strategy_list = serializer.validated_data.get('power_strategy')
            with transaction.atomic():
                # 清除该端口旧策略
                PowerStrategy.objects.filter(power_port=power_port).delete()
                for power_strategy in power_strategy_list:
                    power_strategy.update({"power_port_id": power_port.id})
                    PowerStrategy.objects.create(**power_strategy)
            ip_address = power_port.woodenbox.cabinet.ip_address
            power_port_serializer = PowerPortStrategySerializer(power_port)
            if ip_address in request_dict.keys():
                request_dict[ip_address].append(power_port_serializer.data)
            else:
                request_dict[ip_address] = [power_port_serializer.data]
        task_gather = [
            request_coral(ip_address, {"powerports": request_dict[ip_address]}) for ip_address in request_dict
        ]
        loop1 = asyncio.new_event_loop()
        asyncio.set_event_loop(loop1)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.wait(task_gather))
        loop.close()
        # for ip_address in request_dict:
        #     url = f'http://{ip_address}:5000/resource/update_port_slg'
        #     parameter = {"json": {"powerports": request_dict[ip_address]}, "timeout": 2}
        #     req = ReefRequest(url, **parameter)
        #     req.post({"url": ip_address, "req_body": {"powerports": request_dict[ip_address]}})
        return ReefResponse()


class UpdateDeviceResolution(AutoExecuteSerializerGenericAPIView):

    serializer_class = UpdateDeviceResolutionSerializer
    queryset = Device.objects.all()

    def post(self, request):
        serializer = self.execute(request)
        device = serializer.validated_data.pop('device_label')
        if not device or not device.phone_model:
            return reef_400_response(description='设备没有关联机型信息', message=f"phone_model: {device.phone_model}")
        PhoneModel.objects.filter(id=device.phone_model.id).update(**serializer.validated_data)
        return ReefResponse()



#############################################################
# helper function                                           #
#############################################################
def data_reduce(data):
    """
    由于数据的量级可能很大，在绘图时不需要这么多的数据，因此当数据量达到一定程度时，
    我们会对所有取回来的数据进行抽样，只返回部分的数据
    """
    threshold = 2000

    # 如果数据量未超过阈值，直接回传
    if data.count() <= threshold:
        return data

    step = data.count() // threshold

    return data[::step]


def update_subsidiary_device_count(device_list: [Device], operate=None, num=1):
    """
    维护Job,Device subsidiary_device_count 字段数据
    """
    for device in device_list:
        if operate == 'add':
            device.subsidiary_device_count += num
            device.save()
        elif operate == 'delete':
            device.subsidiary_device_count -= num if device.subsidiary_device_count - num >= 0 else 0
            device.save()
        elif operate == 'clear':
            device.subsidiary_device_count = 0
            device.save()


def device_cancel_checkout(obj):
    assert hasattr(obj, 'simcard'), reef_400_response(message=f'{obj}: lack simcard attribute ')
    if obj.simcard.all().exists():
        return reef_400_response(
            message="设备绑定SIM卡资源，请先解除绑定",
            description='设备绑定SIM卡资源，请先解除绑定'
        )
    assert hasattr(obj, 'account'), reef_400_response(message=f'{obj}: lack account attribute')
    if obj.account.all().exists():
        return reef_400_response(
            message="设备绑定账号资源，请先解除绑定",
            description='设备绑定账号资源，请先解除绑定'
        )


async def request_coral(ip_address, body):

    url = f'http://{ip_address}:5000/resource/update_port_slg'
    parameter = {"json": body, "timeout": 5}
    req = ReefRequest(url, **parameter)
    loop = asyncio.get_event_loop()
    from functools import partial
    p = partial(req.post, {"url": ip_address, "req_body": body})
    await loop.run_in_executor(None, p)


