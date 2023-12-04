from rest_framework import serializers, status
from rest_framework.generics import GenericAPIView
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apiv1.core.constants import REDIS_DEVICE_PREFIX, DELAYED_TASK_TIME, DELAYED_TASK_EXPIRES_TIME, \
    DEVICE_STATUS_OCCUPIED
from reef.celery import celery_app

from apiv1.module.device.models import PaneSlot, Device
from apiv1.module.device.tasks.tasks import set_device_status
from django.core.cache import cache


class ControlDeviceSerializer(serializers.Serializer):

    device_id_list = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=True
    )
    occupy_type = serializers.CharField(
        required=True
    )

    @staticmethod
    def validate_device_id_list(device_id_list: list):
        if len(device_id_list) == 0:
            raise ValidationError('device id list is empty')
        if not Device.objects.filter(id__in=device_id_list).exists():
            raise ValidationError('Not Found device in table')
        return device_id_list


class ControlDevice(GenericAPIView):

    serializer_class = ControlDeviceSerializer

    def post(self, request):
        """
        1. job editor control device
        2. half hour auto release device
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device_id_list = serializer.validated_data.get('device_id_list', None)
        if not device_id_list:
            return Response('device list is empty', status=status.HTTP_200_OK)
        occupy_type = serializer.validated_data.get('occupy_type', None)
        device_queryset = Device.objects.filter(id__in=device_id_list)

        for device in device_queryset:
            # update device status
            device.occupy_type = occupy_type
            device.status = DEVICE_STATUS_OCCUPIED
            device.save()
            redis_key = get_redis_key_fun(REDIS_DEVICE_PREFIX, device.id)
            task_id = cache.get(redis_key, None)
            if task_id:
                # 删除没有执行的延时任务
                celery_app.control.revoke(task_id, terminate=True)
                # apply_async 参数必须是可以json序列化的
                task = set_device_status.apply_async(args=(device.id, ), countdown=DELAYED_TASK_TIME, expires=DELAYED_TASK_EXPIRES_TIME)
                cache.set(redis_key, task.id, timeout=DELAYED_TASK_TIME)
            else:
                task = set_device_status.apply_async(args=(device.id, ), countdown=DELAYED_TASK_TIME, expires=DELAYED_TASK_EXPIRES_TIME)
                cache.set(redis_key, task.id, timeout=DELAYED_TASK_TIME)
        return Response({'message': 'success'}, status=status.HTTP_200_OK)


def get_redis_key_fun(*args):
    return ':'.join(map(lambda n: str(n), args))






