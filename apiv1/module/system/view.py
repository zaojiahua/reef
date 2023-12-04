import datetime
import json
import logging
import shutil
import copy

import requests
from asgiref.sync import async_to_sync
from django.db import transaction
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apiv1.core.constants import REDIS_LOG_DELETE, LOG_DELETE_GROUP
from apiv1.core.request import ReefRequest
from apiv1.core.response import ReefResponse
from apiv1.core.view.generic import AutoExecuteSerializerGenericAPIView
from apiv1.core.view.server_test import ServerTestView
from apiv1.module.device.serializer import PowerPortStrategySerializer
from apiv1.module.system.models import System, Cabinet, WoodenBox
from apiv1.module.device.models import PowerPort, TempPort, PowerStrategy
from apiv1.module.system.serializer import GetReefSpaceUsageSerialzier, CabinetRegistSerializer, \
    CreateWoodenBoxSerializer, \
    WoodenBoxSerializer, GetCabinetTypeInfoSerializer, UpdateCabinetMLocationSerializer, DeleteLogSerializer
from apiv1.module.system.tasks.tasks import delete_log, send_message
from apiv1.module.tboard.tasks.tasks import channel_layer
from reef import settings
from reef.settings import REEF_VERSION, CORAL_PORT, redis_pool_connect

logger = logging.getLogger(__name__)


class GetReefSpaceUsageView(generics.GenericAPIView):
    """
    取得Reef主机硬盘使用信息
    """
    serializer_class = GetReefSpaceUsageSerialzier

    def get(self, request: Request):
        qp = request.query_params
        unit = qp.get('unit', 'BYTE')
        # 获取换算参数类型
        shift = 0
        if unit == 'BYTE':
            shift = 0
        elif unit == 'KB':
            shift = 10
        elif unit == 'MB':
            shift = 20
        elif unit == 'GB':
            shift = 30
        # 获取 '/' 盘总容量，使用量，剩余量
        total, used, free = shutil.disk_usage("/")
        # 换算单位
        data = {
            'total': total >> shift,
            'used': used >> shift,
            'free': free >> shift
        }
        return Response(
            data,
            status=status.HTTP_200_OK
        )


class CabinetRegistView(generics.GenericAPIView):
    """
    Coral向Reef注册机柜信息
    """
    serializer_class = CabinetRegistSerializer

    def post(self, request, pk):
        # 参数校验
        serializer = CabinetRegistSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data['id'] = pk
        # 参数缺少belong_to_id时，使用默认system
        if 'belong_to_id' not in serializer.validated_data:
            serializer.validated_data['belong_to_id'] = System.objects.order_by('id').first().id
        # 不存在常见，否则更新信息
        cabinet, created = Cabinet.objects.update_or_create(
            defaults=serializer.validated_data,
            id=pk
        )

        return Response(
            CabinetRegistSerializer(instance=cabinet).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )


class CreateWoodenBoxView(generics.GenericAPIView):

    serializer_class = CreateWoodenBoxSerializer

    @transaction.atomic
    def post(self, request: Request):
        serializer = CreateWoodenBoxSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request_data = copy.deepcopy(serializer.validated_data)
        config = request_data.pop('config', {})
        if isinstance(config, str):
            try:
                config = json.loads(config)
            except:
                return Response(f'Config data not json type', status=status.HTTP_400_BAD_REQUEST)
        request_data.update(config)
        cabinet = request_data.pop('cabinet', None)
        if cabinet is None:
            return Response(f'lack cabinet parameter', status=status.HTTP_400_BAD_REQUEST)

        # 将木盒信息通知Coral
        try:
            res = requests.post(
                f"http://{cabinet.ip_address}:{settings.CORAL_PORT}/resource/box",
                json=request_data,
            )
            res_data = json.loads(res.text)
        except Exception as e:
            return Response(f'Connection fail or proxy server error: {str(e)}', status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if res.status_code != 200:
            return Response(res.content, status=res.status_code)
        # 存储木盒信息，并添加木盒对应的port数据
        wooden_box = WoodenBox.objects.create(**serializer.validated_data)
        verified_list = res_data.get('verified_list', None)
        wooden_box_type = serializer.validated_data.get('type', None)
        if wooden_box_type == 'power' and verified_list:
            body = []
            for power_port in verified_list:
                obj, created = PowerPort.all_objects.update_or_create(port=power_port, defaults={"is_active": True, "woodenbox": wooden_box})
                # 创建power port 添加default power strategy
                if created:
                    PowerStrategy.objects.create(**{
                        "power_port": obj,
                        "min_value": 30,
                        "max_value": 100,
                        "is_default": True
                    })
                else:
                    # update power port, 没有默认充电策略的进行添加。(策略版本之前，系统中已有的power port在此添加默认策略)
                    if not obj.powerstrategy.all().exists():
                        PowerStrategy.objects.create(**{
                            "power_port": obj,
                            "min_value": 30,
                            "max_value": 100,
                            "is_default": True
                        })
            # 通知coral
                power_port_serializer = PowerPortStrategySerializer(obj)
                body.append(power_port_serializer.data)
            ip_address = wooden_box.cabinet.ip_address
            url = f'http://{ip_address}:5000/resource/update_port_slg'
            parameter = {"json": {"powerports": body}, "timeout": 2}
            req = ReefRequest(url, **parameter)
            req.post({"url": ip_address, "req_body": body})

        elif wooden_box_type == 'temp' and verified_list:
            for temp_port in verified_list:
                TempPort.all_objects.update_or_create(port=temp_port, defaults={"is_active": True, "woodenbox": wooden_box})
        else:
            return Response(f'Config type fields error or Coral return {(res_data)}', status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_200_OK)


class RemoveWoodenBoxView(generics.DestroyAPIView):

    queryset = WoodenBox.objects.all()

    def perform_destroy(self, instance):
        power_port_queryset = PowerPort.objects.filter(woodenbox=instance)
        temp_port_queryset = TempPort.objects.filter(woodenbox=instance)
        if instance.type == 'power' and power_port_queryset.exists():
            power_port_queryset.update(is_active=False)
        elif instance.type == 'temp' and temp_port_queryset.exists():
            temp_port_queryset.update(is_active=False)
        instance.delete()

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        # 木盒关联Device数量是为0，才可以删除木盒
        if instance and instance.type == 'power':
            bound_device_num = instance.powerport.exclude(device=None).count()
        elif instance and instance.type == 'temp':
            bound_device_num = instance.tempport.exclude(device=None).count()
        else:
            bound_device_num = -1

        if bound_device_num == 0:

            try:
                res = requests.delete(
                    f"http://{instance.cabinet.ip_address}:{settings.CORAL_PORT}/resource/box/{instance.name}",
                )
            except Exception as e:
                return Response(f'Connection fail or proxy server error: {str(e)}', status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            if res.status_code != 204:
                return Response(res.content, status=res.status_code)

            return self.destroy(request, *args, **kwargs)
        return Response(f'The number of devices associated with the box is {bound_device_num}, not 0', status=status.HTTP_400_BAD_REQUEST)


class GetCabinetTypeInfoView(generics.GenericAPIView):

    serializer_class = GetCabinetTypeInfoSerializer
    queryset = Cabinet.objects.filter(is_delete=False).exclude(type=None)

    def get(self, request):
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data_type = serializer.validated_data.get('data_type', None)

        type_list = list(Cabinet.objects.filter(is_delete=False).exclude(type=None).distinct('type').values_list('type', flat=True))
        if not data_type:
            return ReefResponse(data=type_list)
        if data_type == 'cabinet_type_data':
            result = [
                {"type": type, "val": Cabinet.objects.filter(is_delete=False, type=type).values('cabinet_name',
                                                                                                'id', 'ip_address')}
                for type in type_list if type is not None]
            return Response(data=result)
        return ReefResponse()


class GetReefVersionView(APIView):

    def get(self, request):
        return ReefResponse(REEF_VERSION)


class UpdateCabinetMLocationView(AutoExecuteSerializerGenericAPIView):

    queryset = Cabinet.objects.filter(is_delete=False)
    serializer_class = UpdateCabinetMLocationSerializer

    def post(self, request):
        serializer = self.execute(request)
        validated_data = serializer.validated_data
        cabinet = validated_data.pop('cabinet_id')
        device = validated_data.pop('device_label')
        Cabinet.objects.filter(id=cabinet.id).update(**validated_data)
        m_location_x = validated_data.get('m_location_x', 0)
        m_location_y = validated_data.get('m_location_y', 0)
        m_location_z = validated_data.get('m_location_z', 0)
        # 通知coral
        url = f"http://{cabinet.ip_address}:{CORAL_PORT}/pane/update_m_location/"
        body = {"m_location": [m_location_x, m_location_y, m_location_z], "device_label": device.device_label}
        req = ReefRequest(url, **{"json": body, "timeout": 2})
        req.post({"coral_ip": cabinet.ip_address, "body": body})
        return ReefResponse()


class DeleteLogView(AutoExecuteSerializerGenericAPIView):

    serializer_class = DeleteLogSerializer

    """
    function: 异步清理日志，当前（rds_log, screen_shot）
    流程：
        选择时间段 --> 异步清理 ---------> websocket 通知清理完成
                        |        成功
                        |
                        |  失
                        |  败
                websocket 通知清理失败 
    状态： 
        EXCEPTION celery服务异常
        SUCCESS   清理成功
        FAIL      清理失败
    执行逻辑：
        1.建立ws连接，redis获取异步任务task数据并取出最近一条，判断是否有正在清理的任务。（celery服务异常不进行判断直接上报）。
        2.请求该接口，创建celery task，并保存 task_id 到redis。
        3.异步清理异常，删除redis存储的task_id,并通过ws上报清理失败。（异常信息会存储在celery日志中）
    
    调试方法：
        浏览器开启ws连接，执行删除，信息会返回到ws消息中。
    """

    def get_queryset(self):
        pass

    def post(self, request):
        # 清理前，判断celery服务是否正常
        result = ServerTestView().celery_server_test()
        if result.get('celery_server_success', None) is None:
            async_to_sync(channel_layer.group_send)(LOG_DELETE_GROUP, {
                "type": "send_message",
                "message": {"status": "EXCEPTION", "description": f"celery service exception: {result}"}
            })
            return ReefResponse(data={'status': 'success', "description": f"celery service exception: {result}"})
        serializer = self.execute(request)
        start_date = serializer.validated_data.get('start_date')
        end_date = serializer.validated_data.get('end_date')
        res_time = end_date - start_date

        start_date = datetime.datetime.strftime(start_date, '%Y_%m_%d')
        async_res = delete_log.apply_async(args=(start_date, res_time.days), link=send_message.s())

        task_time = timezone.localtime().strftime('%Y-%m-%d %H:%M:%S')
        # crate task save to redis
        redis_pool_connect.hmset(
            f"{REDIS_LOG_DELETE}:{async_res.id}",
            {"task_time": task_time, "task_id": async_res.id}
        )
        redis_pool_connect.expire(f"{REDIS_LOG_DELETE}:{async_res.id}", 82000)

        async_to_sync(channel_layer.group_send)(LOG_DELETE_GROUP, {
            "type": "send_message",
            "message": {"status": async_res.state, "task_id": async_res.id}
        })

        return ReefResponse(data={'status': 'success', "task_id": async_res.id})








