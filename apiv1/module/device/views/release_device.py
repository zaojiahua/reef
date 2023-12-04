from rest_framework import serializers, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from apiv1.core.constants import REDIS_DEVICE_PREFIX, DEVICE_STATUS_IDLE, DEVICE_STATUS_OCCUPIED
from django.core.cache import cache
from apiv1.module.device.models import Device
from apiv1.module.device.views.job_editor_control_device import get_redis_key_fun
from reef import celery_app


class ReleaseOccupyDeviceSerializer(serializers.Serializer):

    device_id_list = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=True
    )


class ReleaseOccupyDevice(GenericAPIView):

    serializer_class = ReleaseOccupyDeviceSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device_id_list = serializer.validated_data.get('device_id_list', None)

        device_queryset = Device.objects.filter(id__in=device_id_list)
        if not device_queryset.exists():
            return Response({'message': "Not found device instance"}, status=status.HTTP_200_OK)
        for device in device_queryset:
            delayed_key = get_redis_key_fun(REDIS_DEVICE_PREFIX, device.id)
            task_id = cache.get(delayed_key)
            celery_app.control.revoke(task_id, terminate=True)
            if device.status in [DEVICE_STATUS_OCCUPIED]:
                device.status = DEVICE_STATUS_IDLE
                device.occupy_type = ''
            device.save()
            cache.delete(delayed_key)
        return Response({'message': "success"}, status=status.HTTP_200_OK)