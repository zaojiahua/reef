import datetime

import requests
from django.db import transaction
from django.utils import timezone

from rest_framework import mixins, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet as RestFrameworkGenericViewSet
from apiv1.core.constants import REEF_DEFAULT_MANUFACTURER, DEVICE_STATUS_BUSY, DEVICE_STATUS_IDLE, DEVICE_STATUS_ERROR
from apiv1.core.tool import explain_abnormity_policy
from apiv1.core.utils import ReefLogger
from apiv1.core.view.generic import GenericViewSet, ListModelMixin, RetrieveModelMixin
from apiv1.module.abnormity.models import Abnormity, AbnormityPolicy, AbnormityType, AbnormityDetail
from apiv1.module.device.models import AndroidVersion, Device, DeviceCoordinate, DevicePower, DeviceScreenshot, \
    DeviceTemperature, Manufacturer, PhoneModel, RomVersion, PaneView, DeviceCutCoordinate, SubsidiaryDevice, \
    PhoneModelCustomCoordinate, PowerStrategy
from apiv1.module.device.models import PowerPort, TempPort, MonitorPort
from apiv1.module.device.serializer import AndroidVersionSerializer, DeviceSerializer, DeviceCoordinateSerializer, \
    DevicePowerSerializer, DeviceScreenshotSerializer, DeviceTemperatureSerializer, ManufacturerSerializer, \
    PhoneModelSerializer, RomVersionSerializer, PaneviewSerializer, DeviceCutCoordinateSerializer, \
    SubsidiaryDeviceSerializer, RegisterSubsidiaryDeviceSerializer, PhoneModelCustomCoordinateSerializer, \
    PowerStrategySerializer
from apiv1.module.device.serializer import MonitorPortSerializer, PowerPortSerializer, TempPortSerializer, \
    TempPortCreateSerializer
from apiv1.module.device.signal import update_device_status
from apiv1.module.device.view import update_subsidiary_device_count
from apiv1.module.job.error import ValidationError
from reef import settings


class DynamicAndroidVersionViewSet(GenericViewSet):
    serializer_class = AndroidVersionSerializer
    queryset = AndroidVersion.objects.all()
    return_key = 'androidversions'
    queryset_filter = {}
    instance_filter = {}


class DynamicDeviceViewSet(GenericViewSet):
    serializer_class = DeviceSerializer
    queryset = Device.objects.all()
    return_key = 'devices'
    queryset_filter = {}

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if 'tempport' in data:
            # device: tempport = 1:n
            # self.device.tempports  all update to None
            #   tempports.device     all update to self.device
            for tempport in TempPort.objects.filter(device=self.get_object()):
                tempport.device = None
                tempport.save()

            for tempport in TempPort.objects.filter(id__in=[tempport.id for tempport in data['tempport']]):
                tempport.device = self.get_object()
                tempport.save()

        if 'powerport' in data:
            # device:powerport = 1:1
            # if powerport  None : update powerport.device = None
            # if powerport !None : update powerport.device = self.device

            if data['powerport'] is None:
                for powerport in PowerPort.objects.filter(device=self.get_object()):
                    powerport.device = None
                    powerport.save()
            else:
                data['powerport'].device = self.get_object()
                data['powerport'].save()
        # 记录更新device status
        if 'status' in data:
            log_content = f'Parameter: \n' \
                          f'device_id: {self.get_object().id} \n' \
                          f'status: {data.get("status")}'
            reef_logger = ReefLogger('debug')
            reef_logger.debug(log_content)
            # sub_dev busy --> idle
            if data.get('status') in [DEVICE_STATUS_IDLE, DEVICE_STATUS_ERROR]:
                update_device_status.update_subsidiary_device(self.get_object(), DEVICE_STATUS_BUSY, DEVICE_STATUS_IDLE)
        return super(DynamicDeviceViewSet, self).partial_update(request, *args, **kwargs)

    def create(self, *args, **kwargs):
        return super(DynamicDeviceViewSet, self).create(*args, **kwargs)


class DynamicDeviceCoordinateViewSet(GenericViewSet):
    serializer_class = DeviceCoordinateSerializer
    queryset = DeviceCoordinate.objects.all()
    return_key = 'devicecoordinates'
    queryset_filter = {}
    instance_filter = {}


class DynamicDevicePowerViewSet(GenericViewSet):
    serializer_class = DevicePowerSerializer
    queryset = DevicePower.objects.all()
    return_key = 'devicepowers'
    queryset_filter = {}
    instance_filter = {}

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        记录电量信息及下降异常
        异常判断规则
        1. 和上笔电量做比较，没有上笔电量不做异常判断逻辑
        2. 比上笔电量下降一定百分比（在数据库中进行配置），算作异常。没有下降4%表示电量没有异常，将该设备上笔异常记录为结束
        3. 出现异常后记录到异常概要表和异常详情表中。

        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        device_id = serializer.validated_data['device']
        battery_level = serializer.validated_data['battery_level']
        record_datetime = serializer.validated_data.get('record_datetime', None)
        try:
            abnm_policy_obj = AbnormityPolicy.objects.get(code=1)
            abnm_type_obj = AbnormityType.objects.get(code=1)
        except Exception as e:
            return Response({'error_message': f'{e}'}, status=status.HTTP_404_NOT_FOUND)
        # 获取异常定义格则
        rule_data = explain_abnormity_policy(abnm_policy_obj)

        device_power_obj = DevicePower.objects.filter(device_id=device_id).order_by('record_datetime').last()
        is_abnormity = True
        # 获取电量时间间隔单位分钟
        time = 4
        # 取不到前一笔数据不进行异常判断
        if device_power_obj and record_datetime:
            time_difference = round((record_datetime - device_power_obj.record_datetime).total_seconds() / 60, 2)
            # 距离上笔电量数据时间过长(大于time数)，将可能没有正常结束的异常数据更新为异常结束
            if time_difference > time:
                Abnormity.objects.filter(is_end=False, device_id=device_id).update(**{'is_end': True})
                is_abnormity = False
            # 电量异常
            power_difference = device_power_obj.battery_level - battery_level
            if round(power_difference/time_difference, 2) >= rule_data and is_abnormity:
                abnormity = Abnormity.objects.filter(device_id=device_id, is_end=False).order_by('start_time').last()
                # device 有未结束异常,更新详情和概要表
                if abnormity:
                    abnormity.end_time = record_datetime
                    abnormity.save()
                    parameter = {'time': record_datetime, 'abnormity': abnormity, 'result_data': {'power': battery_level}}
                    AbnormityDetail.objects.create(**parameter)
                else:
                    # device没有未结束的异常，创建新的异常
                    parameter = {'start_time': device_power_obj.record_datetime, 'end_time': record_datetime, 'device': device_id,
                                 'abnormity_type': abnm_type_obj, 'abnormity_policy':abnm_policy_obj, 'tboard': None}
                    abnormity = Abnormity.objects.create(**parameter)
                    now_abnm_detail = AbnormityDetail(time=record_datetime,
                                                      abnormity=abnormity, result_data={'power': battery_level})
                    last_abnm_detail = AbnormityDetail(time=device_power_obj.record_datetime,
                                                       abnormity=abnormity,
                                                       result_data={'power': device_power_obj.battery_level})
                    AbnormityDetail.objects.bulk_create([now_abnm_detail, last_abnm_detail])
            else:
                Abnormity.objects.filter(is_end=False, device_id=device_id).update(**{'is_end': True})
        # save power data
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class DynamicDeviceScreenshotViewSet(GenericViewSet):
    serializer_class = DeviceScreenshotSerializer
    queryset = DeviceScreenshot.objects.all()
    return_key = 'devicescreenshots'
    queryset_filter = {}
    instance_filter = {}


class DynamicDeviceTemperatureViewSet(GenericViewSet):
    serializer_class = DeviceTemperatureSerializer
    queryset = DeviceTemperature.objects.all()
    return_key = 'devicetemperatures'
    queryset_filter = {}
    instance_filter = {}


class DynamicManufacturerViewSet(GenericViewSet):
    serializer_class = ManufacturerSerializer
    queryset = Manufacturer.objects.all()
    return_key = 'manufacturers'
    queryset_filter = {}
    instance_filter = {}

    def get_queryset(self):
        action = self.action.lower()
        if action == 'retrieve' or action == 'list':
            return Manufacturer.objects.all()
        else:
            return Manufacturer.objects.exclude(manufacturer_name=REEF_DEFAULT_MANUFACTURER)  # 预设的Manufacturer不能修改


class DynamicPhoneModelViewSet(GenericViewSet):
    serializer_class = PhoneModelSerializer
    queryset = PhoneModel.objects.all()
    return_key = 'phonemodels'
    queryset_filter = {}
    instance_filter = {}


class DynamicRomVersionViewSet(GenericViewSet):
    serializer_class = RomVersionSerializer
    queryset = RomVersion.objects.all()
    return_key = 'romversions'
    queryset_filter = {}
    instance_filter = {}


class DynamicMonitorPortViewSet(GenericViewSet):
    serializer_class = MonitorPortSerializer
    queryset = MonitorPort.objects.all()
    return_key = 'monitorports'
    queryset_filter = {}
    instance_filter = {}


class DynamicPowerPortViewSet(ListModelMixin,
                              RetrieveModelMixin,
                              mixins.UpdateModelMixin,
                              RestFrameworkGenericViewSet):
    serializer_class = PowerPortSerializer
    queryset = PowerPort.objects.all()
    return_key = 'powerports'
    queryset_filter = {}


class DynamicTempPortViewSet(ListModelMixin,
                              RetrieveModelMixin,
                              mixins.UpdateModelMixin,
                              RestFrameworkGenericViewSet):
    serializer_class = TempPortSerializer
    queryset = TempPort.objects.all()
    return_key = 'tempports'
    queryset_filter = {}

    def get_serializer_class(self):
        """
        由於不帶description的TempPort對使用者來說難以識別
        TempPort.description不允許為null
        但當Coral掃描到新的可用TempPort並新增至reef時
        不可能有description值
        所以TempPort在create時description可為空
        但update時不可為空
        """
        if self.action == 'create':
            return TempPortCreateSerializer
        return super(DynamicTempPortViewSet, self).get_serializer_class()


class DynamicPaneViewViewSet(GenericViewSet):

    serializer_class = PaneviewSerializer
    queryset = PaneView.objects.all()
    return_key = 'paneview'
    queryset_filter = {}


class DeviceCutCoordinateViewViewSet(GenericViewSet):

    serializer_class = DeviceCutCoordinateSerializer
    queryset = DeviceCutCoordinate.objects.all()
    return_key = 'devicecutcoordinate'
    queryset_filter = {}


class SubsidiaryDeviceView(GenericViewSet):

    serializer_class = SubsidiaryDeviceSerializer
    queryset = SubsidiaryDevice.objects.all()
    return_key = 'subsidiarydevice'
    queryset_filter = {}


class PhoneModelCustomCoordinateView(GenericViewSet):

    serializer_class = PhoneModelCustomCoordinateSerializer
    queryset = PhoneModelCustomCoordinate.objects.all()
    return_key = 'phonemodelcustomcoordinate'
    queryset_filter = {}


class PowerStrategyView(GenericViewSet):
    serializer_class = PowerStrategySerializer
    queryset = PowerStrategy.objects.all()
    return_key = 'powerstrategy'
    queryset_filter = {}









